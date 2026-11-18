"""Testes do envio via Terminal (macOS): segurança do script, pasta e modos de cada IA."""
import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import ai_hub
import main
from ai_hub import AIHubError, AIHubSecurityError, AIHubClient

PROMPT = "### Objetivo\nCriar algo; `rm -rf ~` $(whoami) \"aspas\" 'simples' && echo x\n"
client = TestClient(main.app)


@pytest.fixture
def casa(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path.resolve()))
    monkeypatch.setattr(ai_hub.sys, "platform", "darwin")
    monkeypatch.setattr(
        AIHubClient, "_resolve_local_binary",
        staticmethod(lambda provider: ("claude" if provider == "claude_cli" else "agy", f"/usr/local/bin/{'claude' if provider == 'claude_cli' else 'agy'}")),
    )
    return tmp_path.resolve()


def _abrir(provider="claude_cli", pasta="proj", prompt=PROMPT):
    chamadas = []

    def falso(cmd, **kw):
        chamadas.append((cmd, kw))
        if cmd[0] == "open":
            chamadas.append(("script", Path(cmd[-1]).read_text()))
            chamadas.append(("modo", oct(stat.S_IMODE(os.stat(cmd[-1]).st_mode))))
            chamadas.append(("prompt_txt", Path(cmd[-1]).with_name("prompt.txt")))
        return None

    with patch("ai_hub.subprocess.run", side_effect=falso):
        out = AIHubClient().abrir_no_terminal({"provider": provider}, prompt, pasta)
    return out, chamadas


def test_claude_recebe_prompt_por_arquivo_e_nunca_no_script(casa):
    out, ch = _abrir()
    script = dict((c[0], c[1]) for c in ch if c[0] in ("script", "modo", "prompt_txt"))
    assert out["aberto"] and out["modo"] == "argumento"
    assert PROMPT.strip() not in script["script"] and "rm -rf ~" not in script["script"]
    assert "whoami" not in script["script"]
    assert script["prompt_txt"].read_text() == PROMPT.strip()
    assert 'exec /usr/local/bin/claude "$PROMPT"' in script["script"]
    assert script["modo"] == "0o700"
    assert stat.S_IMODE(os.stat(script["prompt_txt"]).st_mode) == 0o600
    assert (casa / "proj").is_dir() and f"cd {casa / 'proj'}" in script["script"]
    assert ["open", "-a", "Terminal"] == [c for c in ch if c[0] and isinstance(c[0], list)][-1][0][:3]
    import shutil; shutil.rmtree(script["prompt_txt"].parent)


def test_antigravity_copia_para_area_de_transferencia(casa):
    out, ch = _abrir("antigravity_cli")
    assert out["modo"] == "area_de_transferencia"
    pb = [c for c in ch if isinstance(c[0], list) and c[0][0] == "pbcopy"][0]
    assert pb[1]["input"] == PROMPT.strip() and pb[1].get("shell") is False
    script = [c[1] for c in ch if c[0] == "script"][0]
    assert "PROMPT" not in script and "exec /usr/local/bin/agy" in script
    import shutil; shutil.rmtree(Path([c[1] for c in ch if c[0] == "prompt_txt"][0]).parent)


@pytest.mark.parametrize("pasta", ["/etc", "../fora", "~", ".", ".ssh/x", "Library/app", "Desktop/.oculta", "a\nb", ""])
def test_pastas_perigosas_sao_recusadas(casa, pasta):
    with pytest.raises(AIHubError):
        AIHubClient.validar_pasta_terminal(pasta)


def test_pasta_com_link_simbolico_para_fora_e_recusada(casa, tmp_path_factory):
    fora = tmp_path_factory.mktemp("fora")
    (casa / "atalho").symlink_to(fora)
    with pytest.raises(AIHubSecurityError):
        AIHubClient.validar_pasta_terminal("atalho")


def test_pasta_valida_e_criada_dentro_da_home(casa):
    p = AIHubClient.validar_pasta_terminal("Desktop/meu projeto")
    assert p == casa / "Desktop" / "meu projeto" and p.is_dir()


def test_provedor_de_nuvem_e_recusado(casa):
    with pytest.raises(AIHubError):
        AIHubClient().abrir_no_terminal({"provider": "openrouter", "api_key": "sk-x" * 10}, PROMPT, "p")


def test_so_macos(monkeypatch):
    monkeypatch.setattr(ai_hub.sys, "platform", "linux")
    with pytest.raises(AIHubError, match="macOS"):
        AIHubClient().abrir_no_terminal({"provider": "claude_cli"}, PROMPT, "p")


def test_prompt_vazio_ou_gigante(casa):
    for texto in ("", "   ", "x" * (ai_hub.MAX_TERMINAL_PROMPT_CHARS + 1)):
        with pytest.raises(AIHubError):
            AIHubClient().abrir_no_terminal({"provider": "claude_cli"}, texto, "p")


def test_falha_ao_abrir_limpa_arquivos_temporarios(casa):
    import subprocess, tempfile
    antes = set(Path(tempfile.gettempdir()).glob("power-request-term-*"))
    with patch("ai_hub.subprocess.run", side_effect=subprocess.CalledProcessError(1, "open")):
        with pytest.raises(AIHubError):
            AIHubClient().abrir_no_terminal({"provider": "claude_cli"}, PROMPT, "p")
    assert set(Path(tempfile.gettempdir()).glob("power-request-term-*")) == antes


def test_endpoint_e_protecoes(casa):
    corpo = {"prompt": PROMPT, "pasta": "proj", "ai_config": {"provider": "claude_cli"}}
    with patch.object(AIHubClient, "abrir_no_terminal", return_value={"aberto": True, "modo": "argumento", "pasta": "x", "alias": "a", "provider": "claude_cli"}) as m:
        assert client.post("/api/abrir-terminal", json=corpo).status_code == 200
        assert client.post("/api/abrir-terminal", json=corpo, headers={"Origin": "https://evil.com"}).status_code == 403
        assert client.post("/api/abrir-terminal", json=corpo, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert m.call_count == 1
    assert client.post("/api/abrir-terminal", json={**corpo, "pasta": "../x"}).status_code in (400, 403)


def test_script_gerado_entrega_prompt_intacto_e_apaga_temporarios(casa, tmp_path):
    """Executa de verdade o .command com um 'claude' falso que grava o argumento recebido."""
    import subprocess as sp
    saida = tmp_path / "recebido.txt"
    falso = tmp_path / "claude"
    falso.write_text(f'#!/bin/bash\nprintf %s "$1" > {saida}\npwd > {saida}.cwd\n')
    falso.chmod(0o755)
    real_run = sp.run

    def executa(cmd, **kw):
        if cmd[0] == "open":
            return real_run(["/bin/bash", cmd[-1]], check=True, timeout=20)
    with patch.object(AIHubClient, "_resolve_local_binary", staticmethod(lambda p: ("claude", str(falso)))), \
         patch("ai_hub.subprocess.run", side_effect=executa):
        AIHubClient().abrir_no_terminal({"provider": "claude_cli"}, PROMPT, "Desktop/x")
    assert saida.read_text() == PROMPT.strip()
    assert Path(str(saida) + ".cwd").read_text().strip() == str((casa / "Desktop" / "x").resolve())
    import tempfile
    assert not list(Path(tempfile.gettempdir()).glob("power-request-term-*"))
