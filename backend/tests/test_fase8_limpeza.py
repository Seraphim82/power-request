"""Fase 8, PR C: rota sem uso removida e ações do CI presas a um commit exato."""

import re
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import main

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
ROTA = "/api/hub/openrouter/exchange"


def test_rota_do_login_openrouter_nao_existe_mais():
    assert ROTA not in {getattr(r, "path", "") for r in main.app.routes}
    with patch("urllib.request.urlopen") as internet:
        resposta = TestClient(main.app).post(
            ROTA,
            json={"code": "codigo_inventado_12345678", "code_verifier": "verificador_inventado_1234"},
        )
    assert resposta.status_code in {404, 405}
    internet.assert_not_called()


def test_acoes_do_ci_ficam_presas_a_um_commit():
    usos = [
        uso
        for arquivo in [*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")]
        for uso in re.findall(r"^\s*(?:-\s+)?uses:\s*(\S+)", arquivo.read_text(encoding="utf-8"), re.M)
    ]
    assert usos, "nenhuma ação encontrada: o teste deixou de olhar o lugar certo"
    soltas = [u for u in usos if not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", u)]
    assert soltas == []
