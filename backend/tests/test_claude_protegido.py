"""Claude (Local) dentro do app: sempre sem ferramentas, sem MCP e em pasta temporária vazia.

Tudo aqui é simulação (subprocess falso). A prova com o Claude real é feita no Mac.
"""

import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import ai_hub
import main
from ai_hub import AIHubClient, AIHubError, AIHubSecurityError, CLAUDE_ARGS_PROTEGIDOS
from main import app

client = TestClient(app, base_url="http://127.0.0.1:8765")
CFG = {"provider": "claude_cli"}
PROMPT = "### Objetivo\nCriar um painel de teste com dados falsos"
PAYLOAD = {
    "categoria": "web",
    "objetivo": "Criar um painel de clientes fictícios",
    "stack": "Python com FastAPI",
    "entrada": "Lista de clientes inventados em CSV",
    "saida": "Tabela HTML com nome e cidade",
    "regras": ["Não usar dados reais"],
    "tratamento_erros": "Mostrar mensagem simples",
}


class ClaudeFalso:
    """Guarda cada chamada e confere a pasta no momento em que o Claude 'roda'."""

    def __init__(self, stdout="OK", stderr="", returncode=0, erro=None):
        self.chamadas = []
        self.stdout, self.stderr, self.returncode, self.erro = stdout, stderr, returncode, erro

    def __call__(self, cmd, **kw):
        pasta = kw.get("cwd")
        self.chamadas.append(
            {
                "cmd": list(cmd),
                "kw": kw,
                "pasta_existia": bool(pasta) and os.path.isdir(pasta),
                "pasta_vazia": bool(pasta) and os.path.isdir(pasta) and not os.listdir(pasta),
            }
        )
        if self.erro:
            raise self.erro
        return subprocess.CompletedProcess(cmd, self.returncode, self.stdout, self.stderr)


@pytest.fixture
def claude(monkeypatch):
    falso = ClaudeFalso()
    monkeypatch.setattr(
        AIHubClient, "_resolve_local_binary", staticmethod(lambda p: ("claude", "/usr/bin/claude"))
    )
    monkeypatch.setattr(ai_hub.subprocess, "run", falso)
    return falso


def _conferir_protegido(chamada):
    assert chamada["cmd"] == ["/usr/bin/claude", *CLAUDE_ARGS_PROTEGIDOS]
    assert chamada["kw"]["shell"] is False
    assert chamada["kw"]["env"]["CLAUDE_CODE_SAFE_MODE"] == "1"
    pasta = chamada["kw"]["cwd"]
    assert Path(pasta).name.startswith(ai_hub.PREFIXO_PASTA_CLAUDE)
    assert chamada["pasta_existia"] and chamada["pasta_vazia"]
    assert not os.path.exists(pasta), "a pasta temporária deveria ter sido apagada"


def test_argumentos_protegidos_tem_todas_as_travas():
    args = list(CLAUDE_ARGS_PROTEGIDOS)
    assert args[0] == "-p" and "--safe-mode" in args and "--strict-mcp-config" in args
    assert args[args.index("--tools") + 1] == ""
    assert args[args.index("--disallowedTools") + 1] == "mcp__*"


# ---------- os cinco usos do app ----------
def test_testar_conexao_usa_a_protecao(claude):
    res = client.post("/api/hub/testar", json=CFG)
    assert res.status_code == 200 and res.json()["conectado"] is True
    assert len(claude.chamadas) == 1
    _conferir_protegido(claude.chamadas[0])


def test_revisao_com_ia_usa_a_protecao(claude):
    claude.stdout = '{"score_qualidade": 90, "pendencias": [], "dica_extra": "ok"}'
    res = client.post("/api/revisar-pedido", json={**PAYLOAD, "ai_config": CFG})
    assert res.status_code == 200 and "Claude" in res.json()["revisado_por"]
    _conferir_protegido(claude.chamadas[0])


def test_otimizacao_com_ia_usa_a_protecao(claude):
    claude.stdout = "### Objetivo\nPainel otimizado"
    res = client.post(
        "/api/gerar-prompt",
        json={**PAYLOAD, "ai_config": CFG, "otimizar_com_ia": True, "salvar_historico": False},
    )
    assert res.status_code == 200 and res.json()["prompt_final"].startswith("### Objetivo")
    _conferir_protegido(claude.chamadas[0])


def test_enviar_usa_a_protecao(claude):
    res = client.post("/api/enviar-prompt", json={"prompt": PROMPT, "ai_config": CFG})
    assert res.status_code == 200
    _conferir_protegido(claude.chamadas[0])


def test_sequenciar_usa_a_protecao(claude):
    res = client.post(
        "/api/sequenciar",
        json={
            "prompt_base": PROMPT,
            "rodadas": [{"pedido": "", "resposta": "resposta anterior inventada"}],
            "novo_pedido": "continue",
            "ai_config": CFG,
        },
    )
    assert res.status_code == 200
    _conferir_protegido(claude.chamadas[0])


# ---------- quem chama não consegue tirar a proteção ----------
def test_argumentos_e_pasta_de_quem_chama_sao_ignorados(claude, tmp_path):
    AIHubClient().call_llm(CFG, "sys", "usr", cli_args=["-p"], cwd=str(tmp_path))
    chamada = claude.chamadas[0]
    _conferir_protegido(chamada)
    assert chamada["kw"]["cwd"] != str(tmp_path)


def test_cada_uso_ganha_uma_pasta_nova(claude):
    AIHubClient().call_llm(CFG, "sys", "um")
    AIHubClient().call_llm(CFG, "sys", "dois")
    assert claude.chamadas[0]["kw"]["cwd"] != claude.chamadas[1]["kw"]["cwd"]


def test_provedor_local_sem_trava_e_recusado(monkeypatch, claude):
    cfg = AIHubClient().validate_config(CFG)
    cfg["provider"] = "outro_cli"
    monkeypatch.setitem(ai_hub.LOCAL_CLI_SPECS, "outro_cli", ai_hub.LOCAL_CLI_SPECS["claude_cli"])
    with pytest.raises(AIHubSecurityError, match="sem trava"):
        AIHubClient()._call_local_cli(cfg, "sys", "usr")
    assert claude.chamadas == []


# ---------- pasta apagada mesmo com falha ----------
@pytest.mark.parametrize(
    "erro,mensagem",
    [(subprocess.TimeoutExpired("claude", 60), "Tempo esgotado"), (OSError("falhou"), "Falha ao executar")],
)
def test_pasta_e_apagada_no_tempo_esgotado_e_na_falha(claude, erro, mensagem):
    claude.erro = erro
    with pytest.raises(AIHubError, match=mensagem):
        AIHubClient().call_llm(CFG, "sys", "usr")
    assert not os.path.exists(claude.chamadas[0]["kw"]["cwd"])


def test_pasta_e_apagada_quando_o_claude_devolve_erro(claude):
    claude.returncode, claude.stderr = 1, "Please login first"
    with pytest.raises(AIHubError, match="Please login first"):
        AIHubClient().call_llm(CFG, "sys", "usr")
    assert not os.path.exists(claude.chamadas[0]["kw"]["cwd"])


# ---------- versão sem o modo seguro: bloqueia e não tenta sem proteção ----------
@pytest.mark.parametrize("onde", ["stderr", "stdout"])
def test_versao_antiga_bloqueia_com_aviso_e_nao_repete_sem_protecao(claude, onde):
    claude.returncode = 1
    setattr(claude, onde, "error: unknown option '--safe-mode'")
    with pytest.raises(AIHubError) as erro:
        AIHubClient().call_llm(CFG, "sys", "usr")
    assert str(erro.value) == ai_hub.AVISO_CLAUDE_SEM_MODO_SEGURO
    assert len(claude.chamadas) == 1


def test_versao_antiga_no_testar_conexao_mostra_o_aviso(claude):
    claude.returncode, claude.stderr = 1, "error: unknown option '--strict-mcp-config'"
    res = client.post("/api/hub/testar", json=CFG)
    assert res.status_code == 400 and "modo seguro" in res.json()["detail"]
    assert len(claude.chamadas) == 1


def test_versao_antiga_na_revisao_usa_o_motor_local_e_explica(claude):
    claude.returncode, claude.stderr = 1, "error: unknown option '--safe-mode'"
    res = client.post("/api/revisar-pedido", json={**PAYLOAD, "ai_config": CFG})
    assert res.status_code == 200
    assert "IA indisponível" in res.json()["revisado_por"]
    assert "modo seguro" in res.json()["dica_extra"]
    assert len(claude.chamadas) == 1


def test_versao_antiga_na_otimizacao_usa_o_motor_local_e_explica(claude):
    claude.returncode, claude.stderr = 1, "error: unknown option '--safe-mode'"
    res = client.post(
        "/api/gerar-prompt",
        json={**PAYLOAD, "ai_config": CFG, "otimizar_com_ia": True, "salvar_historico": False},
    )
    assert res.status_code == 200 and "modo seguro" in res.json()["aviso"]
    assert len(claude.chamadas) == 1


def test_versao_antiga_no_enviar_nao_envia(claude):
    claude.returncode, claude.stderr = 1, "error: unknown option '--safe-mode'"
    res = client.post("/api/enviar-prompt", json={"prompt": PROMPT, "ai_config": CFG})
    assert res.status_code == 400 and "modo seguro" in res.json()["detail"]
    assert len(claude.chamadas) == 1


# ---------- o que não muda ----------
def test_abrir_no_terminal_continua_sem_a_protecao(monkeypatch, tmp_path):
    """O Abrir no Terminal é de propósito com as ferramentas do próprio Claude."""
    monkeypatch.setattr(ai_hub.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(
        AIHubClient, "_resolve_local_binary", staticmethod(lambda p: ("claude", "/usr/bin/claude"))
    )
    scripts = []

    def falso(cmd, **kw):
        if cmd[:3] == ["open", "-a", "Terminal"]:
            scripts.append(Path(cmd[3]).read_text(encoding="utf-8"))
            shutil.rmtree(Path(cmd[3]).parent)  # o script de verdade se apaga ao rodar
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(ai_hub.subprocess, "run", falso)
    AIHubClient().abrir_no_terminal(CFG, PROMPT, "projeto-teste")
    assert scripts and "--safe-mode" not in scripts[0] and "--tools" not in scripts[0]
    assert 'exec /usr/bin/claude "$PROMPT"' in scripts[0]


def test_antigravity_nao_recebe_os_argumentos_do_claude(monkeypatch):
    usados = []
    monkeypatch.setattr(
        AIHubClient, "_resolve_local_binary", staticmethod(lambda p: ("agy", "/usr/bin/agy"))
    )
    monkeypatch.setattr(AIHubClient, "_call_agy", lambda self, *a, **k: usados.append(a) or "ok")
    monkeypatch.setattr(ai_hub.subprocess, "run", lambda *a, **k: pytest.fail("não deveria rodar"))
    assert AIHubClient().call_llm({"provider": "antigravity_cli"}, "sys", "usr") == "ok"
    assert len(usados) == 1
