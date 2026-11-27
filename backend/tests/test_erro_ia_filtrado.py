"""Revisão e otimização com IA: o motivo da falha passa por mensagem_publica (sem caminhos)."""

from fastapi.testclient import TestClient

import main
from ai_hub import AIHubError
from main import app

client = TestClient(app, base_url="http://127.0.0.1:8765")
PAYLOAD = {
    "categoria": "web",
    "objetivo": "Criar um painel de clientes fictícios",
    "stack": "Python com FastAPI",
    "entrada": "Lista de clientes inventados em CSV",
    "saida": "Tabela HTML com nome e cidade",
    "regras": ["Não usar dados reais"],
    "tratamento_erros": "Mostrar mensagem simples",
    "ai_config": {"provider": "claude_cli"},
}
ERRO = "Falha ao executar claude localmente: [Errno 13] /Users/fulano/segredo/claude\nlinha 2"


def _falha(*_a, **_k):
    raise AIHubError(ERRO)


def _conferir(texto: str):
    assert "/Users" not in texto and "fulano" not in texto and "\n" not in texto
    assert "<caminho>" in texto and "Falha ao executar" in texto
    assert len(texto) <= 400


def test_revisao_com_ia_indisponivel_nao_mostra_caminho(monkeypatch):
    monkeypatch.setattr(main.ai_hub, "revisar_com_ia", _falha)
    res = client.post("/api/revisar-pedido", json=PAYLOAD)
    assert res.status_code == 200 and "IA indisponível" in res.json()["revisado_por"]
    _conferir(res.json()["dica_extra"])


def test_otimizacao_com_ia_indisponivel_nao_mostra_caminho(monkeypatch):
    monkeypatch.setattr(main.ai_hub, "otimizar_prompt_com_ia", _falha)
    res = client.post(
        "/api/gerar-prompt", json={**PAYLOAD, "otimizar_com_ia": True, "salvar_historico": False}
    )
    assert res.status_code == 200 and "IA indisponível" in res.json()["gerado_por"]
    _conferir(res.json()["aviso"])
