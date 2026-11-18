"""Testes severos da ponte local CLI (Claude e Antigravity) contra command injection e falhas."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ai_hub import AIHubClient, AIHubError, AIHubSecurityError


def test_cli_local_bloqueia_caminho_customizado_em_base_url():
    client = AIHubClient()
    with pytest.raises(AIHubSecurityError):
        client.validate_config({"provider": "claude_cli", "base_url": "/bin/sh"})


def test_cli_local_aceita_claude_e_antigravity_sem_chave_api():
    client = AIHubClient()
    c1 = client.validate_config({"provider": "claude_cli", "alias": "Claude do Mac"})
    c2 = client.validate_config({"provider": "antigravity_cli", "alias": "Antigravity do Mac"})
    assert c1["provider"] == "claude_cli" and c1["api_key"] == ""
    assert c2["provider"] == "antigravity_cli" and c2["api_key"] == ""


def test_cli_local_passa_ataque_shell_apenas_por_stdin_com_shell_false():
    client = AIHubClient()
    mock_proc = MagicMock(returncode=0, stdout="OK", stderr="")

    with patch.object(AIHubClient, "_resolve_local_binary", return_value=("claude", "/opt/homebrew/bin/claude")), \
         patch("subprocess.run", return_value=mock_proc) as mock_run:
        out = client.call_llm(
            {"provider": "claude_cli", "alias": "Claude"},
            "Responda OK",
            "; rm -rf / && $(cat /etc/passwd) --dangerously-skip-permissions",
        )

    assert out == "OK"
    args, kwargs = mock_run.call_args
    assert args[0] == ["/opt/homebrew/bin/claude", "-p"]
    assert kwargs["shell"] is False
    assert "; rm -rf /" in kwargs["input"]
    assert all("rm" not in a and "dangerously" not in a for a in args[0])


def test_cli_local_bloqueia_null_byte():
    client = AIHubClient()
    with patch.object(AIHubClient, "_resolve_local_binary", return_value=("agy", "/opt/homebrew/bin/agy")):
        with pytest.raises(AIHubSecurityError, match="byte nulo"):
            client.call_llm({"provider": "antigravity_cli"}, "sys", "ola\x00mundo")


def test_cli_local_bloqueia_prompt_gigante():
    client = AIHubClient()
    with patch.object(AIHubClient, "_resolve_local_binary", return_value=("agy", "/opt/homebrew/bin/agy")):
        with pytest.raises(AIHubSecurityError, match="limite de segurança"):
            client.call_llm({"provider": "antigravity_cli"}, "sys", "A" * 15000)


def test_cli_local_informa_erro_claro_quando_nao_instalado():
    client = AIHubClient()
    with patch.object(AIHubClient, "_resolve_local_binary", return_value=(None, None)):
        with pytest.raises(AIHubError, match="não foi encontrado"):
            client.call_llm({"provider": "antigravity_cli"}, "sys", "teste")


def test_cli_local_trata_timeout_e_erro_de_login():
    client = AIHubClient()
    with patch.object(AIHubClient, "_resolve_local_binary", return_value=("claude", "/opt/homebrew/bin/claude")), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=60)):
        with pytest.raises(AIHubError, match="Tempo esgotado"):
            client.call_llm({"provider": "claude_cli", "alias": "Claude"}, "sys", "teste")

    mock_fail = MagicMock(returncode=1, stdout="", stderr="Please login first")
    with patch.object(AIHubClient, "_resolve_local_binary", return_value=("claude", "/opt/homebrew/bin/claude")), \
         patch("subprocess.run", return_value=mock_fail):
        with pytest.raises(AIHubError, match="Please login first"):
            client.call_llm({"provider": "claude_cli", "alias": "Claude"}, "sys", "teste")


def test_detectar_ferramentas_locais_identifica_claude_e_agy():
    client = AIHubClient()
    fake_which = lambda name, path=None: f"/opt/homebrew/bin/{name}" if name in {"claude", "agy"} else None
    with patch("shutil.which", side_effect=fake_which):
        det = client.detectar_ferramentas_locais()
    assert det["claude_cli"]["disponivel"] is True
    assert det["claude_cli"]["comando_detectado"] == "claude"
    assert det["antigravity_cli"]["disponivel"] is True
    assert det["antigravity_cli"]["comando_detectado"] == "agy"
    assert det["ollama"]["disponivel"] is False
