"""Testes da arquitetura unificada (API + Frontend compilado + Lançador Desktop)."""

from fastapi.testclient import TestClient

from desktop_app import find_free_port
from main import FRONTEND_DIST, app

client = TestClient(app)


def test_health_endpoint_responde_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["frontend_ready"] is True


def test_raiz_entrega_frontend_compilado():
    assert (FRONTEND_DIST / "index.html").is_file()
    res = client.get("/")
    assert res.status_code == 200
    assert "Power Request" in res.text


def test_rotas_api_continuam_isoladas_no_modo_unificado():
    res = client.get("/api/hub/providers")
    assert res.status_code == 200
    assert "providers" in res.json()


def test_find_free_port_retorna_porta_valida():
    port = find_free_port(8765)
    assert isinstance(port, int)
    assert 1024 <= port <= 65535
