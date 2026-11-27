"""Fase 8: prompt que vira opção no Abrir no Terminal e origens de desenvolvimento no uso normal."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import ai_hub
import desktop_app
import main
from ai_hub import AIHubClient, AIHubSecurityError

APP = "http://127.0.0.1:8765"
VITE = ["http://localhost:5173", "http://127.0.0.1:5173"]
client = TestClient(main.app, base_url=APP)


@pytest.fixture
def mac(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path.resolve()))
    monkeypatch.setattr(ai_hub.sys, "platform", "darwin")
    monkeypatch.setattr(
        AIHubClient, "_resolve_local_binary",
        staticmethod(lambda provider: ("claude", "/usr/local/bin/claude")),
    )
    return tmp_path.resolve()


@pytest.mark.parametrize(
    "prompt",
    [
        "--dangerously-skip-permissions",
        '--settings={"hooks":{}}',
        "-p",
        "  \n\t--add-dir=/",
        "- primeiro item de uma lista",
    ],
)
def test_claude_no_terminal_recusa_prompt_que_comeca_com_hifen(mac, prompt):
    with patch("ai_hub.subprocess.run") as run:
        with pytest.raises(AIHubSecurityError, match="começa com"):
            AIHubClient().abrir_no_terminal({"provider": "claude_cli"}, prompt, "proj")
    run.assert_not_called()
    assert not (mac / "proj").exists()


def test_rota_do_terminal_responde_403_para_prompt_com_hifen(mac):
    corpo = {"prompt": "--dangerously-skip-permissions", "pasta": "proj",
             "ai_config": {"provider": "claude_cli"}}
    with patch("ai_hub.subprocess.run") as run:
        resposta = client.post("/api/abrir-terminal", json=corpo, headers={"origin": APP})
    assert resposta.status_code == 403
    assert "começa com" in resposta.json()["detail"]
    run.assert_not_called()


@pytest.fixture
def uso_normal(monkeypatch):
    """Estado do app aberto pelo desktop_app (make run e Power Request.app)."""
    # setitem: no app.state, o setattr do monkeypatch apaga o valor ao desfazer (pytest 9.2).
    monkeypatch.setitem(main.app.state._state, "origens_dev", False)


@pytest.mark.parametrize("origem", VITE)
def test_uso_normal_recusa_alteracao_vinda_da_porta_5173(uso_normal, origem):
    cabecalhos = {"origin": origem, "sec-fetch-site": "same-site"}
    assert client.put("/api/contexto", json={"contexto": "x"}, headers=cabecalhos).status_code == 403
    assert client.delete("/api/historico", headers=cabecalhos).status_code == 403
    assert client.post("/api/envio-automatico", json={}, headers=cabecalhos).status_code == 403
    assert client.post("/api/abrir-terminal", json={}, headers=cabecalhos).status_code == 403


@pytest.mark.parametrize("origem", VITE)
def test_uso_normal_nao_deixa_a_porta_5173_ler_respostas(uso_normal, origem):
    leitura = client.get("/api/historico", headers={"origin": origem})
    assert "access-control-allow-origin" not in leitura.headers
    previa = client.options(
        "/api/historico",
        headers={"origin": origem, "access-control-request-method": "DELETE"},
    )
    assert previa.status_code == 400
    assert "access-control-allow-origin" not in previa.headers


def test_uso_normal_continua_aceitando_o_proprio_app(uso_normal):
    resposta = client.put("/api/contexto", json={"contexto": ""}, headers={"origin": APP})
    assert resposta.status_code == 200


def test_abrir_o_app_desliga_as_origens_de_desenvolvimento(monkeypatch):
    monkeypatch.setitem(main.app.state._state, "origens_dev", True)
    monkeypatch.setitem(main.app.state._state, "porta", 8765)
    vistos = []

    class ServidorFalso:
        should_exit = False

        def __init__(self, config):
            vistos.append(main.app.state.origens_dev)

        def run(self):
            pass

    monkeypatch.setattr(desktop_app.uvicorn, "Server", ServidorFalso)
    monkeypatch.setattr(desktop_app, "find_free_port", lambda preferida: 8765)
    monkeypatch.setattr(desktop_app, "wait_for_server", lambda url: False)
    monkeypatch.setattr(desktop_app.registro_local, "ativar", lambda: True)
    desktop_app.main()
    assert vistos == [False]
