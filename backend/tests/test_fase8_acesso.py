"""Fase 8: no uso normal só vale 127.0.0.1; Abrir no Terminal recusa prompt de uma palavra."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import ai_hub
import main
from ai_hub import AIHubClient, AIHubSecurityError

APP = "http://127.0.0.1:8765"
client = TestClient(main.app, base_url=APP)


@pytest.fixture
def uso_normal(monkeypatch):
    # setitem: no app.state, o setattr do monkeypatch apaga o valor ao desfazer (pytest 9.2).
    monkeypatch.setitem(main.app.state._state, "origens_dev", False)
    monkeypatch.setitem(main.app.state._state, "porta", 8765)


@pytest.mark.parametrize("nome", ["localhost:8765", "LOCALHOST:8765", "testserver", "localhost"])
def test_uso_normal_recusa_outros_nomes_tambem_na_leitura(uso_normal, nome):
    resposta = client.get("/api/health", headers={"host": nome})
    assert resposta.status_code == 400
    assert resposta.headers["x-frame-options"] == "DENY"


@pytest.mark.parametrize(
    "cabecalhos",
    [
        {"origin": "http://localhost:8765"},
        {"origin": "http://localhost:8765", "host": "localhost:8765"},
        {"origin": "http://testserver", "host": "testserver"},
    ],
)
def test_uso_normal_recusa_alteracao_por_localhost_e_testserver(uso_normal, cabecalhos):
    with patch.object(main.history_store, "limpar_historico") as limpar:
        resposta = client.delete("/api/historico", headers=cabecalhos)
    assert resposta.status_code in (400, 403)
    limpar.assert_not_called()


def test_uso_normal_aceita_127_0_0_1(uso_normal):
    assert client.get("/api/health").status_code == 200
    resposta = client.put("/api/contexto", json={"contexto": ""}, headers={"origin": APP})
    assert resposta.status_code == 200


def test_desenvolvimento_continua_aceitando_localhost():
    resposta = client.put(
        "/api/contexto", json={"contexto": ""},
        headers={"origin": "http://localhost:8765", "host": "localhost:8765"},
    )
    assert resposta.status_code == 200


@pytest.fixture
def mac(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path.resolve()))
    monkeypatch.setattr(ai_hub.sys, "platform", "darwin")
    monkeypatch.setattr(
        AIHubClient, "_resolve_local_binary",
        staticmethod(lambda provider: ("falso", "/usr/local/bin/falso")),
    )
    return tmp_path.resolve()


@pytest.mark.parametrize("prompt", ["update", "  doctor \n", "mcp"])
def test_claude_no_terminal_recusa_prompt_de_uma_palavra(mac, prompt):
    with patch("ai_hub.subprocess.run") as run:
        with pytest.raises(AIHubSecurityError, match="uma palavra só"):
            AIHubClient().abrir_no_terminal({"provider": "claude_cli"}, prompt, "proj")
    run.assert_not_called()
    assert not (mac / "proj").exists()


def test_claude_no_terminal_aceita_uma_frase(mac, tmp_path):
    with patch("ai_hub.subprocess.run") as run, patch("ai_hub.tempfile.mkdtemp") as mkdtemp:
        temporaria = tmp_path / "temporaria"
        temporaria.mkdir()
        mkdtemp.return_value = str(temporaria)
        saida = AIHubClient().abrir_no_terminal({"provider": "claude_cli"}, "criar painel", "proj")
    assert saida["aberto"] is True
    run.assert_called_once()
