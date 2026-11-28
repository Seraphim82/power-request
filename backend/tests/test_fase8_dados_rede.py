"""Fase 8, PR B: limite do corpo, endereço do Ollama, chave em redirecionamento, erros e histórico.

Nada aqui acessa a internet nem usa chave de verdade: o redirecionamento é testado entre dois
servidores de mentira em 127.0.0.1.
"""

import asyncio
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

import main
from ai_hub import AIHubClient, AIHubSecurityError
from history_store import HistoryStore
from limite_corpo import LimiteDoCorpo

client = TestClient(main.app)
JSON = {"Content-Type": "application/json"}
SEGREDO = "valor-inventado-que-nao-pode-voltar"


# 1) Limite do corpo ------------------------------------------------------------------------

def _em_partes(total: int, parte: int = 65_536):
    enviado = 0
    while enviado < total:
        n = min(parte, total - enviado)
        yield b" " * n
        enviado += n


def test_corpo_em_partes_acima_do_limite_e_recusado():
    resposta = client.post("/api/analisar-intencao", content=_em_partes(1_200_000), headers=JSON)
    assert resposta.status_code == 413
    assert resposta.json()["detail"] == "Requisição grande demais."
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"


def test_corpo_em_partes_dentro_do_limite_chega_inteiro():
    corpo = json.dumps({"intencao": "organizar a minha agenda da semana"}).encode()
    pedacos = (corpo[i : i + 7] for i in range(0, len(corpo), 7))
    direto = client.post("/api/analisar-intencao", content=corpo, headers=JSON)
    em_partes = client.post("/api/analisar-intencao", content=pedacos, headers=JSON)
    assert direto.status_code == 200
    assert (em_partes.status_code, em_partes.json()) == (200, direto.json())


def test_para_de_ler_assim_que_passa_do_limite():
    lidas, enviadas = [], []

    async def receive():
        lidas.append(1)
        return {"type": "http.request", "body": b"x" * 40, "more_body": True}  # nunca termina

    async def send(mensagem):
        enviadas.append(mensagem)

    async def app_que_nao_pode_ser_chamado(scope, receive, send):
        raise AssertionError("o app recebeu um corpo acima do limite")

    asyncio.run(LimiteDoCorpo(app_que_nao_pode_ser_chamado, limite=100)({"type": "http"}, receive, send))
    assert len(lidas) == 3
    assert enviadas[0]["status"] == 413


# 2) Endereço do Ollama ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "endereco",
    [
        "http://usuario:senha@127.0.0.1:11434",
        "http://alguem@localhost",
        "http://127.0.0.1:11434/outro/caminho",
        "http://127.0.0.1:11434?x=1",
        "http://127.0.0.1:11434#x",
        "http://127.0.0.1:abc",
        "http://127.0.0.1:0",
        "http://127.0.0.1:99999",
        "http://127.0.0.1\\@exemplo.invalid",
        "http://127.0.0.1\n:11434",
        "http://127.0.0.1.exemplo.invalid",
        "http://[::1",
        "file://localhost/etc/hosts",
    ],
)
def test_ollama_recusa_endereco_fora_do_formato(endereco):
    with pytest.raises(AIHubSecurityError, match="SSRF"):
        AIHubClient().validate_config({"provider": "ollama", "base_url": endereco})


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("", "http://127.0.0.1:11434"),
        ("http://127.0.0.1:11434", "http://127.0.0.1:11434"),
        ("HTTP://LocalHost:11434/", "http://localhost:11434"),
        ("https://127.0.0.1", "https://127.0.0.1"),
    ],
)
def test_ollama_aceita_endereco_local_simples(entrada, esperado):
    cfg = AIHubClient().validate_config({"provider": "ollama", "base_url": entrada})
    assert cfg["base_url"] == esperado


# 3) A chave não segue redirecionamento -----------------------------------------------------

@pytest.mark.parametrize(
    "provedor,cabecalho",
    [
        ("openai", "authorization"),
        ("openrouter", "authorization"),
        ("claude", "x-api-key"),
        ("gemini", "x-goog-api-key"),
    ],
)
def test_chave_nao_segue_redirecionamento(provedor, cabecalho, monkeypatch):
    recebidos = {}

    def servidor(nome, destino=None):
        class Falso(BaseHTTPRequestHandler):
            def _atender(self):
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                recebidos[nome] = {k.lower(): v for k, v in self.headers.items()}
                self.send_response(302 if destino else 200)
                if destino:
                    self.send_header("Location", destino)
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = _atender

            def log_message(self, *args):
                pass

        s = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        threading.Thread(target=s.serve_forever, daemon=True).start()
        return s

    for variavel in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        monkeypatch.delenv(variavel, raising=False)
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    outro = servidor("outro")
    primeiro = servidor("primeiro", f"http://127.0.0.1:{outro.server_port}/destino")
    try:
        cliente = AIHubClient()
        cfg = cliente.validate_config({"provider": provedor, "api_key": SEGREDO, "model": "modelo-teste"})
        pedido = cliente._build_request(cfg, "sistema", "oi")
        pedido.full_url = f"http://127.0.0.1:{primeiro.server_port}/inicio"
        with urllib.request.urlopen(pedido, timeout=5):
            pass
    finally:
        for s in (primeiro, outro):
            s.shutdown()
            s.server_close()
    assert SEGREDO in recebidos["primeiro"][cabecalho]
    assert cabecalho not in recebidos["outro"]
    assert SEGREDO not in str(recebidos["outro"])


# 4) Erro de formato não devolve o que foi enviado ------------------------------------------

@pytest.mark.parametrize(
    "corpo",
    [
        {"intencao": {"api_key": SEGREDO}},
        {"api_key": SEGREDO},
        [SEGREDO],
    ],
)
def test_erro_de_formato_nao_devolve_o_que_foi_enviado(corpo):
    resposta = client.post("/api/analisar-intencao", json=corpo)
    assert resposta.status_code == 422
    assert SEGREDO not in resposta.text
    for item in resposta.json()["detail"]:
        assert set(item) <= {"type", "loc", "msg"}
        assert item["msg"]


def test_json_quebrado_tambem_nao_devolve_o_enviado():
    resposta = client.post("/api/analisar-intencao", content='{"api_key": "' + SEGREDO, headers=JSON)
    assert resposta.status_code == 422
    assert SEGREDO not in resposta.text


# 5) Histórico apagado sai do arquivo -------------------------------------------------------

MARCA = "MARCA-FICTICIA-DO-HISTORICO-"


def _arquivos_do_banco(caminho) -> bytes:
    return b"".join(p.read_bytes() for p in caminho.parent.glob(caminho.name + "*"))


def _com_marca(store: HistoryStore) -> int:
    texto = MARCA * 400
    return store.salvar_pedido(
        categoria="geral", objetivo=texto, stack="", entrada="", saida="", regras=[],
        tratamento_erros="", prompt_final=texto, tokens_estimados=1, gerado_por="teste",
    )["id"]


def test_remover_um_pedido_tira_o_texto_do_arquivo(tmp_path):
    caminho = tmp_path / "historico.db"
    store = HistoryStore(caminho)
    pedido = _com_marca(store)
    assert MARCA.encode() in _arquivos_do_banco(caminho)
    assert store.remover_pedido(pedido)
    assert MARCA.encode() not in _arquivos_do_banco(caminho)


def test_limpar_tudo_tira_o_texto_e_compacta_o_arquivo(tmp_path):
    caminho = tmp_path / "historico.db"
    store = HistoryStore(caminho)
    for _ in range(20):
        _com_marca(store)
    antes = caminho.stat().st_size
    assert store.limpar_historico() == 20
    assert MARCA.encode() not in _arquivos_do_banco(caminho)
    assert caminho.stat().st_size < antes
