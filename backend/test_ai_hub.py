"""Suíte severa de segurança, sabotagem e resiliência para o Hub de IAs."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from ai_hub import (
    AIHubClient,
    AIHubError,
    AIHubSecurityError,
    exchange_openrouter_oauth_code,
)


def test_hub_rejeita_provedor_desconhecido():
    client = AIHubClient()
    with pytest.raises(AIHubSecurityError):
        client.validate_config({"provider": "provedor_falso", "api_key": "sk-123456789"})


def test_hub_rejeita_chave_vazia_para_provedor_nuvem():
    client = AIHubClient()
    with pytest.raises(AIHubError, match="chave API"):
        client.validate_config({"provider": "openrouter", "api_key": "   "})


def test_hub_bloqueia_header_injection_na_chave_api():
    client = AIHubClient()
    with pytest.raises(AIHubSecurityError):
        client.validate_config({"provider": "openai", "api_key": "sk-123\r\nX-Evil: 1"})


def test_hub_bloqueia_path_traversal_no_modelo():
    client = AIHubClient()
    with pytest.raises(AIHubSecurityError):
        client.validate_config(
            {"provider": "gemini", "api_key": "AIzaTeste123456", "model": "../../etc/passwd"}
        )


@pytest.mark.parametrize(
    "url_maliciosa",
    [
        "http://169.254.169.254/latest/meta-data",
        "https://site-malicioso.com",
        "file:///etc/passwd",
        "http://10.0.0.1:11434",
    ],
)
def test_hub_bloqueia_ssrf_no_ollama(url_maliciosa):
    client = AIHubClient()
    with pytest.raises(AIHubSecurityError, match="SSRF"):
        client.validate_config({"provider": "ollama", "base_url": url_maliciosa})


def test_hub_permite_ollama_local_sem_chave():
    client = AIHubClient()
    cfg = client.validate_config({"provider": "ollama", "base_url": "http://localhost:11434/"})
    assert cfg["base_url"] == "http://localhost:11434"
    assert cfg["api_key"] == ""


def test_hub_gemini_envia_chave_no_header_nunca_na_url():
    client = AIHubClient()
    cfg = client.validate_config(
        {"provider": "gemini", "api_key": "AIzaSegredo99999", "model": "gemini-2.5-flash"}
    )
    req = client._build_request(cfg, "sys", "usr")
    assert "AIzaSegredo99999" not in req.full_url
    assert req.get_header("X-goog-api-key") == "AIzaSegredo99999"


def test_hub_nunca_vaza_chave_em_erro_http():
    client = AIHubClient()
    segredo = "sk-segredo-ultra-confidencial-98765"
    erro_http = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=io.BytesIO(f"Invalid key: {segredo}".encode("utf-8")),
    )
    with patch("urllib.request.urlopen", side_effect=erro_http):
        with pytest.raises(AIHubError) as exc_info:
            client.call_llm({"provider": "openai", "api_key": segredo}, "sys", "usr")
    assert segredo not in str(exc_info.value)
    assert "[CHAVE_OCULTA]" in str(exc_info.value)


def test_hub_revisao_parseia_json_dentro_de_markdown():
    client = AIHubClient()
    fake_body = {
        "choices": [
            {
                "message": {
                    "content": '```json\n{"score_qualidade": 88, "pendencias": ["Definir limite de mensagens por minuto"], "dica_extra": "Use webhooks assíncronos."}\n```'
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_body).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = client.revisar_com_ia(
            {"provider": "openrouter", "api_key": "sk-or-v1-teste123", "alias": "Meu OpenRouter"},
            {"objetivo": "Bot de WhatsApp"},
            {"aprovado": True, "score_qualidade": 100, "pendencias": []},
        )
    assert res["aprovado"] is False
    assert res["score_qualidade"] == 88
    assert "Definir limite de mensagens por minuto" in res["pendencias"]
    assert "webhooks" in res["dica_extra"]
    assert "Meu OpenRouter" in res["revisado_por"]


def test_hub_mascara_chaves_corretamente():
    assert AIHubClient.mask_secret("sk-or-v1-abcdef123456") == "sk-o...3456"
    assert AIHubClient.mask_secret("curta") == "****"
    assert AIHubClient.mask_secret("") == ""


def test_oauth_exchange_bloqueia_codigo_invalido():
    for ruim in ["", "curto", "codigo com espaco", "../../etc/passwd"]:
        with pytest.raises(AIHubSecurityError):
            exchange_openrouter_oauth_code(ruim, "verifier_valido_12345678")


def test_oauth_exchange_bloqueia_verifier_invalido():
    with pytest.raises(AIHubSecurityError):
        exchange_openrouter_oauth_code("codigo_valido_12345678", "curto")


def test_oauth_exchange_sucesso_retorna_credencial():
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"key": "sk-or-v1-oauth-ok-999"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = exchange_openrouter_oauth_code("codigo_valido_12345678", "verifier_valido_12345678")
    assert res["api_key"] == "sk-or-v1-oauth-ok-999"


def test_oauth_exchange_trata_erro_http():
    erro = urllib.error.HTTPError(
        url="https://openrouter.ai/api/v1/auth/keys",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=io.BytesIO(b"code expired"),
    )
    with patch("urllib.request.urlopen", side_effect=erro):
        with pytest.raises(AIHubError, match="Autorização recusada"):
            exchange_openrouter_oauth_code("codigo_valido_12345678", "verifier_valido_12345678")
