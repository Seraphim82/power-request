"""Envio do prompt final para a IA ativa (respostas longas, limites e segurança)."""

import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import ai_hub
import main
from ai_hub import AIHubClient, AIHubError
from main import app

client = TestClient(app, base_url="http://127.0.0.1:8765")
PROMPT = "### Objetivo\nCriar um painel de clientes\n\n### Stack\nPython"


def _enviar(prompt=PROMPT, **cfg):
    return client.post(
        "/api/enviar-prompt",
        json={"prompt": prompt, "ai_config": {"provider": "claude_cli", **cfg}},
    )


# ---------- endpoint ----------
def test_envia_prompt_para_cli_local_com_limites_longos(monkeypatch):
    chamada = {}

    def falso(self, config, system_prompt, user_prompt, **kw):
        chamada.update(system=system_prompt, user=user_prompt, **kw)
        return "Aqui está o código completo."

    monkeypatch.setattr(AIHubClient, "call_llm", falso)
    res = _enviar()
    data = res.json()
    assert res.status_code == 200
    assert data["resposta"] == "Aqui está o código completo."
    assert data["provider"] == "claude_cli" and data["alias"] and data["model"]
    assert chamada["user"] == PROMPT
    assert chamada["system"] == ai_hub.SEND_SYSTEM_PROMPT
    assert chamada["max_tokens"] == ai_hub.SEND_MAX_TOKENS
    assert chamada["timeout"] == ai_hub.SEND_CLI_TIMEOUT
    assert chamada["cwd"].startswith(tempfile.gettempdir()) and "power-request-" in chamada["cwd"]
    assert chamada["cli_args"] == ["-p", "--tools", ""]


def test_envio_para_api_usa_timeout_http(monkeypatch):
    chamada = {}
    monkeypatch.setattr(
        AIHubClient, "call_llm", lambda self, c, s, u, **kw: chamada.update(kw) or "ok"
    )
    res = client.post(
        "/api/enviar-prompt",
        json={"prompt": PROMPT, "ai_config": {"provider": "openai", "api_key": "sk-teste12345"}},
    )
    assert res.status_code == 200
    assert chamada["timeout"] == ai_hub.SEND_HTTP_TIMEOUT


def test_envio_recusa_prompt_vazio_gigante_ou_sem_chave():
    assert _enviar(prompt="   ").status_code == 400
    assert _enviar(prompt="a" * (ai_hub.MAX_SEND_PROMPT_CHARS + 1)).status_code == 400
    sem_chave = client.post(
        "/api/enviar-prompt", json={"prompt": PROMPT, "ai_config": {"provider": "openai"}}
    )
    assert sem_chave.status_code == 400 and "chave API" in sem_chave.json()["detail"]


def test_envio_com_provedor_falso_e_bloqueado():
    res = client.post(
        "/api/enviar-prompt", json={"prompt": PROMPT, "ai_config": {"provider": "inexistente"}}
    )
    assert res.status_code == 403


def test_envio_bloqueia_origem_externa(monkeypatch):
    monkeypatch.setattr(AIHubClient, "call_llm", lambda *a, **k: pytest.fail("não deveria chamar a IA"))
    res = client.post(
        "/api/enviar-prompt",
        json={"prompt": PROMPT, "ai_config": {"provider": "claude_cli"}},
        headers={"Origin": "https://site-malicioso.example"},
    )
    assert res.status_code == 403


def test_falha_da_ia_vira_erro_legivel_sem_vazar_a_chave(monkeypatch):
    def quebra(self, *a, **k):
        raise AIHubError("Erro HTTP 401 ao chamar OpenAI")

    monkeypatch.setattr(AIHubClient, "call_llm", quebra)
    res = client.post(
        "/api/enviar-prompt",
        json={"prompt": PROMPT, "ai_config": {"provider": "openai", "api_key": "sk-segredo-123456"}},
    )
    assert res.status_code == 400
    assert "401" in res.json()["detail"] and "sk-segredo" not in res.text


# ---------- limites de resposta por provedor ----------
def _corpo(provider, max_tokens=None, **extra):
    cfg = AIHubClient().validate_config({"provider": provider, "api_key": "chave12345678", **extra})
    req = AIHubClient()._build_request(cfg, "sys", "usr", max_tokens=max_tokens)
    return json.loads(req.data)


def test_claude_api_mantem_900_por_padrao_e_aceita_limite_maior():
    assert _corpo("claude")["max_tokens"] == 900
    assert _corpo("claude", 4096)["max_tokens"] == 4096


def test_outros_provedores_so_recebem_limite_quando_pedido():
    assert "max_tokens" not in _corpo("openai") and _corpo("openai", 4096)["max_tokens"] == 4096
    assert "maxOutputTokens" not in _corpo("gemini")["generationConfig"]
    assert _corpo("gemini", 4096)["generationConfig"]["maxOutputTokens"] == 4096
    assert "options" not in _corpo("ollama") and _corpo("ollama", 4096)["options"]["num_predict"] == 4096


# ---------- execução (timeout e pasta de trabalho) ----------
def test_cli_recebe_timeout_longo_e_pasta_temporaria():
    proc = MagicMock(returncode=0, stdout="pronto", stderr="")
    with patch("ai_hub.shutil.which", return_value="/usr/bin/claude"), \
         patch("subprocess.run", return_value=proc) as run:
        out = AIHubClient().enviar_prompt({"provider": "claude_cli"}, PROMPT)
    assert out["resposta"] == "pronto"
    kw = run.call_args.kwargs
    assert kw["timeout"] == ai_hub.SEND_CLI_TIMEOUT
    assert "power-request-" in kw["cwd"]
    assert run.call_args.args[0][1:] == ["-p", "--tools", ""]
    assert kw["shell"] is False


def test_chamadas_antigas_continuam_sem_cwd_e_com_timeout_curto():
    proc = MagicMock(returncode=0, stdout="ok", stderr="")
    with patch("ai_hub.shutil.which", return_value="/usr/bin/claude"), \
         patch("subprocess.run", return_value=proc) as run:
        AIHubClient().call_llm({"provider": "claude_cli"}, "sys", "usr")
    assert "cwd" not in run.call_args.kwargs
    assert run.call_args.kwargs["timeout"] == AIHubClient.LOCAL_CLI_TIMEOUT


def test_api_recebe_timeout_http_longo():
    resp = MagicMock()
    resp.read.return_value = json.dumps({"choices": [{"message": {"content": "feito"}}]}).encode()
    resp.__enter__.return_value = resp
    with patch("urllib.request.urlopen", return_value=resp) as abre:
        out = AIHubClient().enviar_prompt({"provider": "openai", "api_key": "sk-teste12345"}, PROMPT)
    assert out["resposta"] == "feito"
    assert abre.call_args.kwargs["timeout"] == ai_hub.SEND_HTTP_TIMEOUT


# ---------- endurecimento de segurança ----------
def test_cabecalhos_de_seguranca_em_todas_as_respostas():
    from fastapi.testclient import TestClient
    import main
    r = TestClient(main.app).get("/api/health")
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_envio_cross_site_e_corpo_gigante_sao_barrados():
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    r = c.post("/api/enviar-prompt", json={}, headers={"Sec-Fetch-Site": "cross-site"})
    assert r.status_code == 403
    r = c.post("/api/enviar-prompt", content=b"x", headers={"Content-Length": "5000000"})
    assert r.status_code in (413, 400)


def test_limite_de_envios_simultaneos_devolve_429(monkeypatch):
    import main
    tomados = [main.envios_em_andamento.acquire(blocking=False) for _ in range(main.MAX_ENVIOS_SIMULTANEOS)]
    try:
        assert _enviar().status_code == 429
    finally:
        for ok in tomados:
            if ok:
                main.envios_em_andamento.release()


def test_documentacao_interativa_desligada():
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    assert c.get("/openapi.json").status_code == 404
    assert "swagger" not in c.get("/docs").text.lower()
