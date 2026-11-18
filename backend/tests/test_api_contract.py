"""Contrato backend <-> frontend e segurança do servidor local (CORS, origem e host)."""

import pytest
from fastapi.testclient import TestClient

import main
from ai_hub import AIHubError
from main import app

client = TestClient(app, base_url="http://127.0.0.1:8765")

PROVIDER_KEYS = {
    "id", "nome", "auth_mode", "cli_command", "modelo_padrao",
    "modelos_sugeridos", "base_url_padrao", "console_url", "dica",
}
AUTH_MODES = {"local_cli", "api_key", "oauth_pkce", "local_server"}


def _payload(**extra):
    base = {
        "objetivo": "Criar um painel para cadastrar clientes e exportar resumo",
        "stack": "React + FastAPI (Python)",
        "entrada": "Formulário com nome e e-mail",
        "saida": "Tabela com clientes cadastrados",
        "regras": ["Layout responsivo", "Validar campos"],
        "tratamento_erros": "Mostrar mensagem amigável",
        "salvar_historico": False,
    }
    base.update(extra)
    return base


# ---------- contrato consumido pelo frontend ----------
def test_providers_e_lista_com_campos_esperados_pela_interface():
    providers = client.get("/api/hub/providers").json()["providers"]
    assert isinstance(providers, list) and providers
    for p in providers:
        assert PROVIDER_KEYS <= set(p)
        assert p["auth_mode"] in AUTH_MODES
        assert p["modelo_padrao"] in p["modelos_sugeridos"]
    ids = {p["id"] for p in providers}
    assert {"claude_cli", "antigravity_cli", "ollama", "openrouter"} <= ids


def test_provedores_cli_tem_modo_local_e_ollama_tem_url_padrao():
    por_id = {p["id"]: p for p in client.get("/api/hub/providers").json()["providers"]}
    assert por_id["claude_cli"]["auth_mode"] == "local_cli"
    assert por_id["claude_cli"]["cli_command"]
    assert por_id["ollama"]["auth_mode"] == "local_server"
    assert por_id["ollama"]["base_url_padrao"].startswith("http://127.0.0.1")
    assert por_id["gemini"]["auth_mode"] == "api_key"


def test_local_tools_e_lista_com_provider_id_command_installed():
    tools = client.get("/api/hub/local-tools").json()["tools"]
    assert isinstance(tools, list) and tools
    for t in tools:
        assert set(t) == {"provider_id", "command", "installed"}
        assert isinstance(t["installed"], bool)


def test_analisar_intencao_devolve_formato_do_frontend():
    res = client.post("/api/analisar-intencao", json={"intencao": "Quero um bot de WhatsApp"})
    data = res.json()
    assert res.status_code == 200
    assert data["categoria_sugerida"] == "bot"
    assert data["confianca"] in {"alta", "media"}
    assert data["motivo"]
    assert set(data["rascunho"]) == {
        "objetivo", "stack", "entrada", "saida", "regras", "tratamento_erros",
    }
    assert data["rascunho"]["objetivo"] == "Quero um bot de WhatsApp"


@pytest.mark.parametrize(
    "texto,esperada",
    [
        ("Quero um jogo de damas", "jogo"),
        ("Script para ler PDFs", "automacao"),
        ("App de celular para vendas", "mobile"),
        ("Sistema web de clientes", "web"),
        ("Uma ideia qualquer sem pista", "geral"),
    ],
)
def test_categorias_sugeridas_usam_ids_da_interface(texto, esperada):
    data = client.post("/api/analisar-intencao", json={"intencao": texto}).json()
    assert data["categoria_sugerida"] == esperada


def test_ids_de_categoria_da_api_existem_no_frontend():
    from pathlib import Path
    import re

    fonte = (Path(main.__file__).parent.parent / "frontend/src/constants.ts").read_text()
    ids_front = set(re.findall(r"CategoriaId = ([^;]+);", fonte)[0].replace("'", "").split(" | "))
    assert set(main.engine.CATEGORIA_UI.values()) == ids_front


def test_chaves_do_historico_batem_com_item_do_frontend():
    res = client.post("/api/gerar-prompt", json=_payload(categoria="web", salvar_historico=True))
    hid = res.json()["historico_id"]
    try:
        item = next(i for i in client.get("/api/historico").json()["itens"] if i["id"] == hid)
        assert {
            "id", "criado_em", "categoria", "objetivo", "stack", "entrada", "saida",
            "regras", "tratamento_erros", "prompt_final", "tokens_estimados", "gerado_por",
        } <= set(item)
    finally:
        client.delete(f"/api/historico/{hid}")


def test_testar_conexao_devolve_mensagem_para_a_interface(monkeypatch):
    monkeypatch.setattr(main.ai_hub, "call_llm", lambda *a, **k: "OK")
    res = client.post("/api/hub/testar", json={"provider": "claude_cli"})
    assert res.status_code == 200
    assert res.json()["mensagem"]


# ---------- degradação graciosa quando a IA falha ----------
def _ia_quebrada(*_a, **_k):
    raise AIHubError("claude não encontrado")


def test_revisao_cai_para_motor_local_se_ia_indisponivel(monkeypatch):
    monkeypatch.setattr(main.ai_hub, "revisar_com_ia", _ia_quebrada)
    res = client.post("/api/revisar-pedido", json=_payload(ai_config={"provider": "claude_cli"}))
    data = res.json()
    assert res.status_code == 200
    assert "IA indisponível" in data["revisado_por"]
    assert "claude não encontrado" in data["dica_extra"]
    assert 0 <= data["score_qualidade"] <= 100


def test_geracao_cai_para_motor_local_com_aviso_se_ia_indisponivel(monkeypatch):
    monkeypatch.setattr(main.ai_hub, "otimizar_prompt_com_ia", _ia_quebrada)
    res = client.post(
        "/api/gerar-prompt",
        json=_payload(otimizar_com_ia=True, ai_config={"provider": "claude_cli"}),
    )
    data = res.json()
    assert res.status_code == 200
    assert "### Objetivo" in data["prompt_final"]
    assert "claude não encontrado" in data["aviso"]


def test_erro_de_seguranca_da_ia_continua_bloqueando(monkeypatch):
    res = client.post(
        "/api/revisar-pedido",
        json=_payload(ai_config={"provider": "provedor_falso"}),
    )
    assert res.status_code == 403


# ---------- segurança do servidor local ----------
def test_origem_externa_nao_pode_alterar_dados():
    for metodo, url in [("delete", "/api/historico"), ("post", "/api/analisar-intencao")]:
        res = getattr(client, metodo)(
            url, headers={"Origin": "https://site-malicioso.example"},
            **({"json": {"intencao": "teste de origem"}} if metodo == "post" else {}),
        )
        assert res.status_code == 403, url


def test_origem_do_proprio_app_e_do_vite_sao_aceitas():
    for origem in ("http://127.0.0.1:8765", "http://localhost:5173"):
        res = client.post(
            "/api/analisar-intencao",
            json={"intencao": "Quero um site simples"},
            headers={"Origin": origem},
        )
        assert res.status_code == 200, origem


def test_cors_nao_libera_site_externo_nem_credenciais():
    res = client.options(
        "/api/historico",
        headers={
            "Origin": "https://site-malicioso.example",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert "access-control-allow-origin" not in {k.lower() for k in res.headers}
    ok = client.options(
        "/api/historico",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "DELETE"},
    )
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in {k.lower() for k in ok.headers}


def test_host_desconhecido_e_rejeitado_contra_dns_rebinding():
    res = TestClient(app, base_url="http://evil.example:8765").get("/api/health")
    assert res.status_code == 400
