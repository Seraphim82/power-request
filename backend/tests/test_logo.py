"""Logo: a cópia usada pela interface precisa ser igual ao arquivo oficial em assets/."""

from pathlib import Path

from fastapi.testclient import TestClient

from main import FRONTEND_DIST, app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app, base_url="http://127.0.0.1:8765")


def test_copia_do_logo_no_frontend_igual_ao_oficial():
    oficial = (ROOT / "assets" / "logo-power-request.svg").read_bytes()
    copia = (ROOT / "frontend" / "public" / "logo.svg").read_bytes()
    assert oficial == copia, "Rode 'make icon' para sincronizar o logo."


def test_servidor_entrega_logo_compilado():
    assert (FRONTEND_DIST / "logo.svg").is_file()
    res = client.get("/logo.svg")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in res.content


def test_pagina_inicial_referencia_o_logo_como_favicon():
    assert 'href="/logo.svg"' in client.get("/").text
