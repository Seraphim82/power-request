"""Botão Fechar Power Request: só a própria tela desliga, e nunca no meio de um envio."""

import json
import socket
import threading
import urllib.request
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import desktop_app
import main

APP = "http://127.0.0.1:8765"
client = TestClient(main.app, base_url=APP)
CONFIRMADO = {"confirmar": True}


@pytest.fixture
def desligar(monkeypatch):
    """Uso normal, com um desligamento de mentira. Devolve as vagas de envio no fim."""
    falso = Mock()
    monkeypatch.setattr(main, "envios_em_andamento", threading.BoundedSemaphore(main.MAX_ENVIOS_SIMULTANEOS))
    # setitem: no app.state, o setattr do monkeypatch apaga o valor ao desfazer (pytest 9.2).
    monkeypatch.setitem(main.app.state._state, "origens_dev", False)
    monkeypatch.setitem(main.app.state._state, "porta", 8765)
    monkeypatch.setitem(main.app.state._state, "encerrar", falso)
    return falso


def test_a_propria_tela_fecha_o_app(desligar):
    resposta = client.post("/api/encerrar", json=CONFIRMADO, headers={"origin": APP})
    assert resposta.status_code == 200
    assert resposta.json() == {"encerrando": True}
    desligar.assert_called_once_with()


def test_depois_de_fechar_nenhum_envio_novo_comeca(desligar):
    client.post("/api/encerrar", json=CONFIRMADO, headers={"origin": APP})
    assert not main.envios_em_andamento.acquire(blocking=False)


@pytest.mark.parametrize(
    "cabecalhos",
    [
        {},
        {"origin": "https://exemplo.com"},
        {"origin": "null"},
        {"origin": "http://127.0.0.1:9999"},
        {"origin": "http://127.0.0.1:5173"},
        {"origin": "http://localhost:8765", "host": "localhost:8765"},
        {"origin": APP, "sec-fetch-site": "cross-site"},
        {"origin": APP, "host": "exemplo.com"},
    ],
)
def test_outra_origem_nao_fecha(desligar, cabecalhos):
    resposta = client.post("/api/encerrar", json=CONFIRMADO, headers=cabecalhos)
    assert resposta.status_code in (400, 403)
    desligar.assert_not_called()


@pytest.mark.parametrize("corpo", [{}, {"confirmar": False}, {"confirmar": "true"}, {"confirmar": 1}])
def test_sem_confirmacao_nao_fecha(desligar, corpo):
    resposta = client.post("/api/encerrar", json=corpo, headers={"origin": APP})
    assert resposta.status_code in (400, 422)
    desligar.assert_not_called()


def test_formulario_nao_fecha(desligar):
    resposta = client.post("/api/encerrar", data={"confirmar": "true"}, headers={"origin": APP})
    assert resposta.status_code == 422
    desligar.assert_not_called()


@pytest.mark.parametrize("metodo", ["get", "put", "delete"])
def test_so_post_fecha(desligar, metodo):
    resposta = getattr(client, metodo)("/api/encerrar", headers={"origin": APP})
    assert resposta.status_code in (404, 405)
    desligar.assert_not_called()


@pytest.mark.parametrize("ocupadas", [1, 2])
def test_com_envio_em_andamento_nao_fecha_e_nao_prende_vaga(desligar, ocupadas):
    for _ in range(ocupadas):
        assert main.envios_em_andamento.acquire(blocking=False)
    resposta = client.post("/api/encerrar", json=CONFIRMADO, headers={"origin": APP})
    assert resposta.status_code == 409
    assert "envio em andamento" in resposta.json()["detail"]
    desligar.assert_not_called()
    livres = 0
    while main.envios_em_andamento.acquire(blocking=False):
        livres += 1
    assert livres == main.MAX_ENVIOS_SIMULTANEOS - ocupadas


def test_no_modo_de_desenvolvimento_nao_ha_botao_nem_fechamento(monkeypatch):
    monkeypatch.setitem(main.app.state._state, "encerrar", None)
    assert client.get("/api/health").json()["pode_encerrar"] is False
    resposta = client.post("/api/encerrar", json=CONFIRMADO, headers={"origin": APP})
    assert resposta.status_code == 409


def test_health_avisa_a_tela_que_pode_fechar(desligar):
    assert client.get("/api/health").json()["pode_encerrar"] is True


def test_servidor_de_verdade_desliga(monkeypatch):
    """Sobe o desktop_app.main() numa porta livre (sem abrir navegador) e fecha pela rota."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    for nome in ("porta", "origens_dev", "encerrar"):
        monkeypatch.setitem(main.app.state._state, nome, main.app.state._state.get(nome))
    monkeypatch.setattr(main, "envios_em_andamento", threading.BoundedSemaphore(main.MAX_ENVIOS_SIMULTANEOS))
    monkeypatch.setattr(desktop_app, "find_free_port", lambda preferred: porta)
    monkeypatch.setattr(desktop_app.registro_local, "ativar", lambda: None)
    pronto = threading.Event()
    monkeypatch.setattr(desktop_app.webbrowser, "open", lambda url: pronto.set())

    programa = threading.Thread(target=desktop_app.main, daemon=True)
    programa.start()
    assert pronto.wait(15)
    url = f"http://127.0.0.1:{porta}"
    pedido = urllib.request.Request(
        f"{url}/api/encerrar",
        data=json.dumps(CONFIRMADO).encode(),
        headers={"Content-Type": "application/json", "Origin": url},
        method="POST",
    )
    with urllib.request.urlopen(pedido, timeout=5) as resposta:
        assert json.load(resposta) == {"encerrando": True}
    programa.join(15)
    assert not programa.is_alive()
    with socket.socket() as s:
        assert s.connect_ex(("127.0.0.1", porta)) != 0
