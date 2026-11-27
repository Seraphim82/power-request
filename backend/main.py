"""API FastAPI unificada do Power Request (API + Frontend compilado)."""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Callable, Optional, TypeVar

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_hub import (
    AIHubClient,
    AIHubError,
    AIHubSecurityError,
    MAX_SEND_PROMPT_CHARS,
    exchange_openrouter_oauth_code,
    providers_for_ui,
)
import envio_automatico
import registro_local
from history_store import HistoryStore, HistoryStoreError
from prompt_engine import PowerRequestEngine, SecurityError, ValidationError

T = TypeVar("T")

# Vai junto da resposta guardada no histórico, para o aviso não sumir ao reabrir.
# A tela usa o mesmo texto (frontend/src/tamanhoEnvio.ts).
MARCA_RESPOSTA_CORTADA = "\n\n[... resposta cortada pelo limite de tamanho ...]"


def _resposta_para_historico(resultado: dict) -> str:
    return resultado["resposta"] + (MARCA_RESPOSTA_CORTADA if resultado.get("cortada") else "")

APP_VERSION = "2.1.0"
CONTEXTO_CHAVE = "contexto_fixo"
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

FORBIDDEN_ERRORS = (SecurityError, AIHubSecurityError)
BAD_REQUEST_ERRORS = (ValidationError, AIHubError, HistoryStoreError)

app = FastAPI(
    title="Power Request API", version=APP_VERSION, docs_url=None, redoc_url=None, openapi_url=None
)

# Segurança do servidor local: só aceita chamadas vindas do próprio app (mesma origem)
# ou do servidor de desenvolvimento do Vite. Impede que sites abertos no navegador
# leiam/apaguem o histórico ou disparem o CLI local (CSRF / DNS rebinding).
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
PORTA_PADRAO = 8765
DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)


def _origin_permitida(origin: str, host: str) -> bool:
    """Compara a origem inteira (protocolo, nome e porta): outro programa local não passa."""
    porta = getattr(app.state, "porta", PORTA_PADRAO)
    aceitas = {f"http://127.0.0.1:{porta}", f"http://localhost:{porta}", *DEV_ORIGINS}
    if host:  # a própria origem do servidor; o nome já passou pelo TrustedHostMiddleware
        aceitas.add(f"http://{host}")
    return origin in aceitas


def _registrar(request: Request, codigo: object, tipo: str) -> None:
    """Rastro da falha. Usa o modelo da rota, nunca o endereço real (que pode levar busca)."""
    rota = getattr(request.scope.get("route"), "path", "sem-rota")
    registro_local.registrar_falha(request.method, rota, codigo, tipo)


MAX_BODY_BYTES = 1_000_000
MAX_ENVIOS_SIMULTANEOS = 2
envios_em_andamento = threading.BoundedSemaphore(MAX_ENVIOS_SIMULTANEOS)

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
        "base-uri 'none'; form-action 'none'; object-src 'none'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
}


@app.middleware("http")
async def protecao_do_servidor_local(request: Request, call_next):
    """Bloqueia origens externas e corpos gigantes; acrescenta cabeçalhos de segurança."""
    resposta = None
    if request.method not in SAFE_METHODS:
        origin = request.headers.get("origin")
        site = request.headers.get("sec-fetch-site")
        host = request.headers.get("host", "")
        if (origin is not None and not _origin_permitida(origin, host)) or site == "cross-site":
            resposta = JSONResponse(
                status_code=403, content={"detail": "Origem não autorizada para esta operação."}
            )
        else:
            tamanho = request.headers.get("content-length", "0")
            if tamanho.isdigit() and int(tamanho) > MAX_BODY_BYTES:
                resposta = JSONResponse(
                    status_code=413, content={"detail": "Requisição grande demais."}
                )
    if resposta is None:
        try:
            resposta = await call_next(request)
        except Exception as exc:
            _registrar(request, 500, type(exc).__name__)
            raise
    if resposta.status_code >= 400:
        _registrar(request, resposta.status_code, getattr(request.state, "tipo_erro", "-"))
    for nome, valor in SECURITY_HEADERS.items():
        resposta.headers[nome] = valor
    return resposta


engine = PowerRequestEngine()
ai_hub = AIHubClient()
history_store = HistoryStore()


class AIConfigModel(BaseModel):
    provider: str
    api_key: str = ""
    model: str = ""
    alias: str = ""
    base_url: str = ""
    aceito_ganchos: bool = False


class OAuthExchangeRequest(BaseModel):
    code: str
    code_verifier: str


class IntencaoRequest(BaseModel):
    intencao: str


class AbrirTerminalRequest(BaseModel):
    prompt: str = Field(max_length=200_000)
    pasta: str = Field(max_length=500)
    ai_config: AIConfigModel


class EnviarPromptRequest(BaseModel):
    prompt: str = Field(max_length=200_000)
    ai_config: AIConfigModel
    pedido_id: Optional[int] = Field(default=None, ge=1)  # se vier, a resposta vira a rodada 1


class RodadaModel(BaseModel):
    pedido: str = Field(default="", max_length=2000)
    resposta: str = Field(max_length=60_000)


class SequenciarRequest(BaseModel):
    prompt_base: str = Field(max_length=200_000)
    rodadas: list[RodadaModel] = Field(default_factory=list, max_length=30)
    novo_pedido: str = Field(min_length=1, max_length=2000)
    # Rodadas mais antigas que a tela não reenvia (só para numerar e contar certo).
    rodadas_anteriores: int = Field(default=0, ge=0, le=1000)
    ai_config: AIConfigModel
    pedido_id: Optional[int] = Field(default=None, ge=1)


class EnvioAutomaticoRequest(BaseModel):
    prompt: str = Field(max_length=200_000)
    ia: str = Field(max_length=40)
    navegador: Optional[str] = Field(default=None, max_length=40)
    aviso_aceito: bool = False


class TestarAutomacaoRequest(BaseModel):
    navegador: Optional[str] = Field(default=None, max_length=40)


class OrganizarPromptRequest(BaseModel):
    texto: str = Field(max_length=20_000)


class ContextoRequest(BaseModel):
    contexto: str = ""


class PayloadRequest(BaseModel):
    categoria: str = "geral"
    objetivo: str = ""
    stack: str = ""
    entrada: str = ""
    saida: str = ""
    regras: list[str] = []
    tratamento_erros: str = ""
    ai_config: Optional[AIConfigModel] = None
    otimizar_com_ia: bool = False
    salvar_historico: bool = True
    contexto_fixo: str = ""

    def extract_engine_payload(self) -> dict:
        return self.model_dump(
            exclude={"categoria", "ai_config", "otimizar_com_ia", "salvar_historico"}
        )


# Erros de domínio viram respostas HTTP por tratadores centrais (abaixo), que limpam a mensagem.
_CAMINHO_RE = re.compile(
    r"(?:/(?:Users|home|private|var|tmp|opt|usr|etc|Volumes|Library|System)(?:/[^\s'\"):,;]+)+)"
    r"|(?:[A-Za-z]:\\[^\s'\"):,;]+)"
)
MAX_MENSAGEM_ERRO = 400


def mensagem_publica(exc: Exception) -> str:
    """Texto de erro seguro para o cliente: sem caminhos de arquivo, sem quebras e com limite."""
    texto = _CAMINHO_RE.sub("<caminho>", str(exc))
    texto = " ".join(texto.split())
    if not texto:
        return "Não foi possível concluir a operação."
    return texto[:MAX_MENSAGEM_ERRO]


def _erro_http(status: int):
    def tratador(request: Request, exc: Exception) -> JSONResponse:
        request.state.tipo_erro = type(exc).__name__  # só o nome do tipo vai para o log
        return JSONResponse(status_code=status, content={"detail": mensagem_publica(exc)})

    return tratador


for _classe in FORBIDDEN_ERRORS:
    app.add_exception_handler(_classe, _erro_http(403))
for _classe in BAD_REQUEST_ERRORS:
    app.add_exception_handler(_classe, _erro_http(400))


def _run_domain_action(action: Callable[[], T]) -> T:
    return action()


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "frontend_ready": (FRONTEND_DIST / "index.html").is_file(),
        "limite_envio": MAX_SEND_PROMPT_CHARS,
    }


@app.get("/api/hub/providers")
def listar_provedores():
    return {"providers": providers_for_ui()}


@app.get("/api/hub/local-tools")
def detectar_ferramentas_locais():
    return {"tools": ai_hub.ferramentas_locais_para_ui()}


@app.post("/api/hub/openrouter/exchange")
def concluir_login_openrouter(req: OAuthExchangeRequest):
    return _run_domain_action(
        lambda: exchange_openrouter_oauth_code(req.code, req.code_verifier)
    )


@app.post("/api/hub/testar")
def testar_conexao_ia(cfg: AIConfigModel):
    return _run_domain_action(lambda: ai_hub.testar_conexao(cfg.model_dump()))


@app.post("/api/analisar-intencao")
def analisar_intencao(req: IntencaoRequest):
    return _run_domain_action(lambda: engine.analisar_intencao(req.intencao))


@app.post("/api/organizar-prompt")
def organizar_prompt(req: OrganizarPromptRequest):
    """Lê um prompt já escrito, encaixa nos campos e devolve perguntas sobre o que falta."""
    return _run_domain_action(lambda: engine.organizar_prompt(req.texto))


@app.post("/api/revisar-pedido")
def revisar_pedido(req: PayloadRequest):
    def _executar():
        dados = req.extract_engine_payload()
        limpo = engine.validar_sequencia(dados)
        revisao_local = engine.revisar_pedido(dados)

        if req.ai_config:
            try:
                return ai_hub.revisar_com_ia(req.ai_config.model_dump(), limpo, revisao_local)
            except AIHubSecurityError:
                raise
            except AIHubError as exc:
                return {
                    **revisao_local,
                    "dica_extra": f"IA indisponível, usei a revisão local. Motivo: {exc}"[:400],
                    "revisado_por": "Motor Local (IA indisponível)",
                }

        return {
            **revisao_local,
            "dica_extra": "",
            "revisado_por": "Motor Local (Offline)",
        }

    return _run_domain_action(_executar)


@app.post("/api/gerar-prompt")
def gerar_prompt(req: PayloadRequest):
    def _executar():
        dados = req.extract_engine_payload()
        limpo = engine.validar_sequencia(dados)
        base = engine.gerar_prompt_final(dados)

        resultado = None
        if req.otimizar_com_ia and req.ai_config:
            try:
                resultado = ai_hub.otimizar_prompt_com_ia(
                    req.ai_config.model_dump(), base["prompt_final"]
                )
            except AIHubSecurityError:
                raise
            except AIHubError as exc:
                resultado = {
                    **base,
                    "gerado_por": "Motor Local (IA indisponível)",
                    "aviso": f"Não foi possível otimizar com a IA: {exc}"[:400],
                }
        if resultado is None:
            resultado = {
                **base,
                "gerado_por": "Motor Local (Compactação Estruturada)",
            }

        if req.salvar_historico:
            salvo = history_store.salvar_pedido(
                categoria=req.categoria,
                objetivo=limpo["objetivo"],
                stack=limpo["stack"],
                entrada=limpo["entrada"],
                saida=limpo["saida"],
                regras=limpo["regras"],
                tratamento_erros=limpo["tratamento_erros"],
                prompt_final=resultado["prompt_final"],
                tokens_estimados=resultado["tokens_estimados"],
                gerado_por=resultado["gerado_por"],
            )
            resultado["historico_id"] = salvo["id"]

        return resultado

    return _run_domain_action(_executar)


@app.post("/api/enviar-prompt")
def enviar_prompt(req: EnviarPromptRequest):
    # Cada envio pode abrir um processo local por até 10 minutos: limita a simultaneidade.
    if not envios_em_andamento.acquire(blocking=False):
        raise HTTPException(
            status_code=429, detail="Já há envios em andamento. Aguarde um terminar e tente de novo."
        )
    try:
        resultado = _run_domain_action(
            lambda: ai_hub.enviar_prompt(req.ai_config.model_dump(), req.prompt)
        )
    finally:
        envios_em_andamento.release()
    if req.pedido_id:
        # Novo envio do prompt original recomeça a sequência guardada deste pedido.
        history_store.reiniciar_rodadas(req.pedido_id)
        history_store.salvar_rodada(
            req.pedido_id, "", _resposta_para_historico(resultado), f"{resultado['alias']} ({resultado['model']})"
        )
    return resultado


@app.post("/api/sequenciar")
def sequenciar(req: SequenciarRequest):
    """Próxima rodada: reenvia pedido original + últimas respostas + novo pedido."""
    montado = _run_domain_action(
        lambda: engine.montar_continuacao(
            req.prompt_base,
            [r.model_dump() for r in req.rodadas],
            req.novo_pedido,
            req.rodadas_anteriores,
        )
    )
    if not envios_em_andamento.acquire(blocking=False):
        raise HTTPException(
            status_code=429, detail="Já há envios em andamento. Aguarde um terminar e tente de novo."
        )
    try:
        resultado = _run_domain_action(
            lambda: ai_hub.enviar_prompt(req.ai_config.model_dump(), montado["prompt"])
        )
    finally:
        envios_em_andamento.release()
    if req.pedido_id:
        history_store.salvar_rodada(
            req.pedido_id,
            req.novo_pedido.strip(),
            _resposta_para_historico(resultado),
            f"{resultado['alias']} ({resultado['model']})",
        )
    return {
        **resultado,
        "tokens_estimados": montado["tokens_estimados"],
        "rodadas_enviadas": montado["rodadas_enviadas"],
        "rodadas_omitidas": montado["rodadas_omitidas"],
        "rodadas_cortadas": montado["rodadas_cortadas"],
    }


@app.get("/api/historico/{pedido_id}/rodadas")
def listar_rodadas_do_pedido(pedido_id: int):
    return {"rodadas": history_store.listar_rodadas(pedido_id)}


@app.post("/api/abrir-terminal")
def abrir_terminal(req: AbrirTerminalRequest):
    return _run_domain_action(
        lambda: ai_hub.abrir_no_terminal(req.ai_config.model_dump(), req.prompt, req.pasta)
    )


@app.get("/api/envio-automatico/perfis")
def perfis_envio_automatico():
    return _run_domain_action(envio_automatico.perfis_para_ui)


@app.post("/api/envio-automatico/testar")
def testar_envio_automatico(req: TestarAutomacaoRequest):
    return _run_domain_action(lambda: envio_automatico.testar_automacao(req.navegador))


@app.post("/api/envio-automatico")
def enviar_automatico(req: EnvioAutomaticoRequest, request: Request):
    resultado = _run_domain_action(
        lambda: envio_automatico.enviar_automatico(
            req.prompt, req.ia, req.navegador, aviso_aceito=req.aviso_aceito
        )
    )
    if resultado.get("status") != envio_automatico.STATUS_CONFIRMADO:
        _registrar(request, 200, f"envio_{resultado.get('status')}")
    return resultado


@app.get("/api/contexto")
def obter_contexto_fixo():
    return {"contexto": history_store.obter_config(CONTEXTO_CHAVE)}


@app.put("/api/contexto")
def salvar_contexto_fixo(req: ContextoRequest):
    def _executar():
        limpo = (
            engine._sanitizar_e_validar_seguranca(req.contexto, "contexto_fixo")
            if req.contexto.strip()
            else ""
        )
        history_store.salvar_config(CONTEXTO_CHAVE, limpo)
        return {"contexto": limpo}

    return _run_domain_action(_executar)


@app.get("/api/historico")
def listar_historico(q: str = "", limite: int = 30):
    return {"itens": history_store.listar_pedidos(busca=q, limite=limite)}


@app.delete("/api/historico/{pedido_id}")
def remover_item_historico(pedido_id: int):
    removido = history_store.remover_pedido(pedido_id)
    if not removido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado no histórico.")
    return {"removido": True, "id": pedido_id}


@app.delete("/api/historico")
def limpar_todo_historico():
    removidos = history_store.limpar_historico()
    return {"removidos": removidos}


if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/logo.svg", include_in_schema=False)
def serve_logo():
    logo_file = FRONTEND_DIST / "logo.svg"
    if not logo_file.is_file():
        raise HTTPException(status_code=404, detail="Logo não encontrado.")
    return FileResponse(logo_file, media_type="image/svg+xml")


@app.get("/")
def serve_frontend_root():
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Frontend ainda não compilado. Execute 'npm run build' na pasta frontend.",
        )
    return FileResponse(index_file)
