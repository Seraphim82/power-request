"""API FastAPI unificada do Power Request (API + Frontend compilado)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, TypeVar

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_hub import (
    AIHubClient,
    AIHubError,
    AIHubSecurityError,
    PROVIDERS_CATALOG,
    exchange_openrouter_oauth_code,
)
from history_store import HistoryStore, HistoryStoreError
from prompt_engine import PowerRequestEngine, SecurityError, ValidationError

T = TypeVar("T")

APP_VERSION = "2.0.0"
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

FORBIDDEN_ERRORS = (SecurityError, AIHubSecurityError)
BAD_REQUEST_ERRORS = (ValidationError, AIHubError, HistoryStoreError)

app = FastAPI(title="Power Request API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = PowerRequestEngine()
ai_hub = AIHubClient()
history_store = HistoryStore()


class AIConfigModel(BaseModel):
    provider: str
    api_key: str = ""
    model: str = ""
    alias: str = ""
    base_url: str = ""


class OAuthExchangeRequest(BaseModel):
    code: str
    code_verifier: str


class IntencaoRequest(BaseModel):
    intencao: str


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

    def extract_engine_payload(self) -> dict:
        return self.model_dump(
            exclude={"categoria", "ai_config", "otimizar_com_ia", "salvar_historico"}
        )


def _run_domain_action(action: Callable[[], T]) -> T:
    try:
        return action()
    except FORBIDDEN_ERRORS as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BAD_REQUEST_ERRORS as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "frontend_ready": (FRONTEND_DIST / "index.html").is_file(),
    }


@app.get("/api/hub/providers")
def listar_provedores():
    return {"providers": PROVIDERS_CATALOG}


@app.get("/api/hub/local-tools")
def detectar_ferramentas_locais():
    return {"tools": ai_hub.detectar_ferramentas_locais()}


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


@app.post("/api/revisar-pedido")
def revisar_pedido(req: PayloadRequest):
    def _executar():
        dados = req.extract_engine_payload()
        limpo = engine.validar_sequencia(dados)
        revisao_local = engine.revisar_pedido(dados)

        if req.ai_config:
            return ai_hub.revisar_com_ia(req.ai_config.model_dump(), limpo, revisao_local)

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

        if req.otimizar_com_ia and req.ai_config:
            resultado = ai_hub.otimizar_prompt_com_ia(
                req.ai_config.model_dump(), base["prompt_final"]
            )
        else:
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


@app.get("/")
def serve_frontend_root():
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Frontend ainda não compilado. Execute 'npm run build' na pasta frontend.",
        )
    return FileResponse(index_file)
