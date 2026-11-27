"""Antigravity: pedido pela entrada padrão, ferramentas travadas e prova antes de liberar.

O agy é simulado. Estes testes não provam o comportamento do programa real.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import agy_seguro
import main
from ai_hub import AIHubClient, AIHubError

AGY = ("agy", "/opt/homebrew/bin/agy")
CFG = {"provider": "antigravity_cli"}
RECUSA = f"tool call denied by pre-tool hook: {agy_seguro.MARCA_RECUSA}"


@pytest.fixture(autouse=True)
def isolado(tmp_path, monkeypatch):
    monkeypatch.setattr(agy_seguro, "estado", agy_seguro._Estado())
    monkeypatch.setattr(agy_seguro, "pasta_gemini", lambda: tmp_path / "gemini")
    monkeypatch.setattr(AIHubClient, "_resolve_local_binary", staticmethod(lambda _p: AGY))
    return tmp_path


def passo(indice=2, estado="ERROR", erro=RECUSA, tipo="tool"):
    info = {"name": "read_file"}
    if erro:
        info["error"] = {"type": "TOOL_ERROR", "message": erro}
    return {"event": "step_update", "step_update": {
        "step_index": indice, "state": estado, "step_type": tipo,
        "tool_name": "read_file", "tool_info": info}}


def saida(*passos, resposta="OK", status="SUCCESS", init=True):
    eventos = ([{"event": "init", "init": {}}] if init else []) + list(passos)
    eventos.append({"event": "result", "result": {"status": status, "response": resposta}})
    return "\n".join(json.dumps(e) for e in eventos)


class AgyFalso:
    """Substitui o subprocess.run e guarda como o agy foi chamado."""

    def __init__(self, texto="", versao="1.5.18", codigo=0):
        self.texto, self.versao, self.codigo = texto, versao, codigo
        self.chamadas = []
        self.hooks = None

    def __call__(self, cmd, **kw):
        if cmd[1:] == ["--version"]:
            return MagicMock(returncode=0, stdout=self.versao, stderr="")
        self.chamadas.append((cmd, kw))
        pasta = Path(kw["cwd"])
        self.hooks = json.loads((pasta / ".agents" / "hooks.json").read_text())
        return MagicMock(returncode=self.codigo, stdout=self.texto, stderr="detalhe interno")


def liberar(client, falso):
    """Faz a prova e depois deixa o agy falso responder como num envio normal."""
    falso.texto = saida(passo())
    client.testar_conexao(CFG)
    falso.texto = saida(resposta="resposta final")


def test_prompt_vai_pela_entrada_padrao_com_trava_e_pasta_nova():
    client, falso = AIHubClient(), AgyFalso()
    with patch("subprocess.run", falso):
        liberar(client, falso)
        out = client.enviar_prompt(CFG, "pedido $(rm -rf /) sigiloso")

    assert out["resposta"] == "resposta final"
    cmd, kw = falso.chamadas[-1]
    assert cmd == [AGY[1], *agy_seguro.ARGS_AGY]
    assert kw["shell"] is False
    linha = json.loads(kw["input"])
    assert linha["event"] == "user" and "sigiloso" in linha["message"]["content"]
    regra = falso.hooks["trava-power-request"]["PreToolUse"][0]
    assert regra["matcher"] == "*"
    assert falso.chamadas[0][1]["cwd"] != kw["cwd"]
    assert not Path(kw["cwd"]).exists()


def test_script_do_gancho_recusa_de_verdade(tmp_path):
    trabalho = agy_seguro._preparar_trava(tmp_path / "pasta com espaco")
    config = json.loads((trabalho / ".agents" / "hooks.json").read_text())
    comando = config["trava-power-request"]["PreToolUse"][0]["hooks"][0]["command"]
    proc = subprocess.run(comando, shell=True, input="{}", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {"decision": "deny", "reason": agy_seguro.MARCA_RECUSA}


def test_envio_sem_prova_nao_chama_o_agy():
    falso = AgyFalso(saida())
    with patch("subprocess.run", falso), pytest.raises(AIHubError, match="Testar Conexão"):
        AIHubClient().enviar_prompt(CFG, "oi")
    assert falso.chamadas == []


def test_mudanca_de_versao_exige_nova_prova():
    client, falso = AIHubClient(), AgyFalso()
    with patch("subprocess.run", falso):
        liberar(client, falso)
        falso.versao = "1.6.0"
        with pytest.raises(AIHubError, match="Testar Conexão"):
            client.enviar_prompt(CFG, "oi")
    assert len(falso.chamadas) == 1


@pytest.mark.parametrize("texto", [
    saida(),  # não tentou usar ferramenta
    saida(passo(erro="permission denied")),  # recusa que não veio da nossa trava
])
def test_prova_sem_a_nossa_recusa_nao_libera(texto):
    with patch("subprocess.run", AgyFalso(texto)), pytest.raises(AIHubError):
        AIHubClient().testar_conexao(CFG)
    assert agy_seguro.estado.provado is None


@pytest.mark.parametrize("ruim", [
    passo(estado="DONE", erro=None),
    passo(estado="ACTIVE", erro=None),
    passo(erro='JSON hook "x" failed: exit status 1'),
    {"event": "step_update", "step_update": {"step_index": 9, "state": "DONE", "step_type": "subagent"}},
    {"event": "step_update", "step_update": {"step_index": 9, "state": "DONE",
        "step_type": "agent_response", "subagent_info": {}}},
])
def test_ferramenta_sem_a_recusa_descarta_a_resposta_e_bloqueia(ruim):
    client, falso = AIHubClient(), AgyFalso()
    with patch("subprocess.run", falso):
        liberar(client, falso)
        falso.texto = saida(ruim, resposta="nao pode aparecer")
        with pytest.raises(AIHubError, match="bloqueado por segurança"):
            client.enviar_prompt(CFG, "oi")
        falso.texto = saida(passo())
        with pytest.raises(AIHubError, match="bloqueado por segurança"):
            client.testar_conexao(CFG)


def test_ferramenta_recusada_pela_trava_nao_derruba_o_envio():
    client, falso = AIHubClient(), AgyFalso()
    with patch("subprocess.run", falso):
        liberar(client, falso)
        falso.texto = saida(passo(estado="ACTIVE", erro=None), passo(), resposta="segui sem ferramenta")
        assert client.enviar_prompt(CFG, "oi")["resposta"] == "segui sem ferramenta"


def test_violacao_com_codigo_de_erro_ainda_bloqueia():
    falso = AgyFalso(saida(passo(estado="DONE", erro=None), status="ERROR"), codigo=1)
    with patch("subprocess.run", falso), pytest.raises(AIHubError, match="bloqueado por segurança"):
        AIHubClient().testar_conexao(CFG)
    assert agy_seguro.estado.bloqueado


@pytest.mark.parametrize("falso", [
    AgyFalso("", codigo=2),
    AgyFalso(saida(init=False)),
    AgyFalso(saida(status="ERROR")),
])
def test_falha_vira_aviso_em_portugues_sem_texto_tecnico(falso):
    with patch("subprocess.run", falso), pytest.raises(AIHubError) as erro:
        AIHubClient().testar_conexao(CFG)
    assert "agy update" in str(erro.value) and "detalhe interno" not in str(erro.value)


def test_conexao_revisao_e_otimizacao_tambem_usam_a_trava():
    client, falso = AIHubClient(), AgyFalso()
    revisao = {"score_qualidade": 80, "pendencias": []}
    with patch("subprocess.run", falso):
        liberar(client, falso)
        client.revisar_com_ia(CFG, {"objetivo": "x"}, revisao)
        client.otimizar_prompt_com_ia(CFG, "prompt base")
    assert len(falso.chamadas) == 3
    for cmd, kw in falso.chamadas:
        assert cmd == [AGY[1], *agy_seguro.ARGS_AGY]
        assert ".agents" not in kw["input"] and kw["cwd"].endswith("trabalho")


def _criar_gancho(base: Path, conteudo: str, relativo="config/hooks.json"):
    arquivo = base / "gemini" / relativo
    arquivo.parent.mkdir(parents=True)
    arquivo.write_text(conteudo)


@pytest.mark.parametrize("relativo", ["config/hooks.json", "antigravity-cli/plugins/p/hooks.json"])
def test_ganchos_globais_exigem_aceite(isolado, relativo):
    _criar_gancho(isolado, '{"m": {"PreInvocation": [{"command": "x"}]}}', relativo)
    client, falso = AIHubClient(), AgyFalso()
    with patch("subprocess.run", falso):
        falso.texto = saida(passo())
        assert client.testar_conexao(CFG)["ganchos_globais"] is True
        falso.texto = saida(resposta="resposta final")
        for valor in (None, "true", False):
            with pytest.raises(AIHubError, match="ganchos globais"):
                client.enviar_prompt({**CFG, "aceito_ganchos": valor}, "oi")
        assert len(falso.chamadas) == 1
        out = client.enviar_prompt({**CFG, "aceito_ganchos": True}, "oi")
    assert out["resposta"] == "resposta final"


def test_ganchos_ilegiveis_contam_e_desligados_nao(isolado):
    assert agy_seguro.tem_ganchos_globais() is False
    _criar_gancho(isolado, "{quebrado")
    assert agy_seguro.tem_ganchos_globais() is True
    (isolado / "gemini" / "config" / "hooks.json").write_text('{"m": {"enabled": false, "command": "x"}}')
    assert agy_seguro.tem_ganchos_globais() is False


def test_rota_de_envio_repassa_o_aceite(isolado):
    _criar_gancho(isolado, '{"m": {"Stop": [{"command": "x"}]}}')
    falso, web = AgyFalso(saida(passo())), TestClient(main.app)
    with patch("subprocess.run", falso):
        assert web.post("/api/hub/testar", json=CFG).status_code == 200
        falso.texto = saida(resposta="resposta final")
        sem = web.post("/api/enviar-prompt", json={"prompt": "oi", "ai_config": CFG})
        com = web.post("/api/enviar-prompt",
                       json={"prompt": "oi", "ai_config": {**CFG, "aceito_ganchos": True}})
    assert sem.status_code == 400 and "ganchos globais" in sem.json()["detail"]
    assert com.status_code == 200 and com.json()["resposta"] == "resposta final"


def test_gemini_nao_e_usado_dentro_do_app(monkeypatch):
    monkeypatch.setattr(AIHubClient, "_resolve_local_binary",
                        staticmethod(lambda _p: ("gemini", "/usr/local/bin/gemini")))
    client = AIHubClient()
    with patch("subprocess.run") as run:
        for chamada in (lambda: client.testar_conexao(CFG), lambda: client.enviar_prompt(CFG, "oi")):
            with pytest.raises(AIHubError, match="Gemini CLI não é usado"):
                chamada()
    run.assert_not_called()


def test_tempo_esgotado_tambem_confere_o_que_ja_saiu():
    parcial = saida(passo(estado="DONE", erro=None)).encode()

    def estourar(cmd, **kw):
        if cmd[1:] == ["--version"]:
            return MagicMock(returncode=0, stdout="1.5.18", stderr="")
        raise subprocess.TimeoutExpired(cmd, 60, output=parcial)

    with patch("subprocess.run", estourar), pytest.raises(AIHubError, match="bloqueado por segurança"):
        AIHubClient().testar_conexao(CFG)
    assert agy_seguro.estado.bloqueado
