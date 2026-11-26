"""Fase 3: orçamento único no Sequenciar, limite informado e aviso de resposta cortada."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import ai_hub
import main
from ai_hub import AIHubClient, RespostaIA
from main import MARCA_RESPOSTA_CORTADA, app
from prompt_engine import PowerRequestEngine, ValidationError

client = TestClient(app, base_url="http://127.0.0.1:8765")
LIMITE = ai_hub.MAX_SEND_PROMPT_CHARS
BASE = "### Objetivo\nCriar painel de clientes"
CFG = {"provider": "claude_cli"}


def _rodadas(*tamanhos):
    """Cada resposta usa uma letra própria: A (mais antiga), B, C..."""
    return [{"pedido": "", "resposta": chr(65 + i) * t} for i, t in enumerate(tamanhos)]


def _montar(rodadas, base=BASE, novo="continue", **kw):
    return PowerRequestEngine().montar_continuacao(base, rodadas, novo, **kw)


@pytest.mark.parametrize("tamanhos", [(12_000,), (60_000, 60_000, 60_000), (5_000, 5_000, 5_000), (10_700, 100)])
def test_nunca_passa_do_limite_de_envio(tamanhos):
    assert len(_montar(_rodadas(*tamanhos))["prompt"]) <= LIMITE


def test_corta_as_antigas_primeiro_e_preserva_a_mais_recente():
    r = _montar(_rodadas(6_000, 6_000, 6_000))
    assert "C" * 6_000 in r["prompt"]
    assert "A" * 100 not in r["prompt"]
    assert r["rodadas_enviadas"] == 2 and r["rodadas_omitidas"] == 1
    assert r["rodadas_cortadas"] == [2]


def test_mais_recente_gigante_mantem_comeco_e_fim():
    resposta = "COMECO" + "x" * 30_000 + "FIM-DA-RESPOSTA"
    r = _montar([{"pedido": "", "resposta": resposta}])
    assert "COMECO" in r["prompt"] and "FIM-DA-RESPOSTA" in r["prompt"]
    assert "o meio foi retirado" in r["prompt"]
    assert r["rodadas_cortadas"] == [1]
    assert len(r["prompt"]) == LIMITE


def test_respostas_que_cabem_vao_inteiras():
    r = _montar(_rodadas(100, 200, 300))
    assert r["rodadas_enviadas"] == 3 and r["rodadas_cortadas"] == []


def test_pedido_original_grande_demais_explica_e_nao_corta():
    with pytest.raises(ValidationError, match="limite de envio"):
        _montar(_rodadas(5_000), base="b" * (LIMITE - 300))
    with pytest.raises(ValidationError, match="limite de envio"):
        _montar([], base="b" * LIMITE)


def test_numeracao_com_rodadas_nao_reenviadas():
    r = _montar(_rodadas(10, 10, 10), rodadas_anteriores=42)
    assert "[Rodada 45]" in r["prompt"] and "[Rodada 43]" in r["prompt"]
    assert "(3 de 45 rodadas)" in r["prompt"] and r["rodadas_omitidas"] == 42


def test_api_resposta_longa_nao_quebra_o_sequenciar(monkeypatch):
    vistos = []
    monkeypatch.setattr(AIHubClient, "call_llm", lambda self, c, s, u, **kw: vistos.append(u) or "ok")
    r = client.post("/api/sequenciar", json={
        "prompt_base": BASE, "ai_config": CFG, "novo_pedido": "continue",
        "rodadas": _rodadas(24_000, 24_000, 24_000), "rodadas_anteriores": 40})
    assert r.status_code == 200
    assert r.json()["rodadas_cortadas"] == [43] and r.json()["rodadas_omitidas"] == 42
    assert len(vistos[0]) <= LIMITE


def test_texto_no_limite_cabe_no_cli_local_junto_com_as_instrucoes():
    proc = MagicMock(returncode=0, stdout="ok", stderr="")
    prompt = _montar(_rodadas(30_000))["prompt"]
    assert len(prompt) == LIMITE
    with patch("ai_hub.shutil.which", return_value="/usr/bin/claude"), \
         patch("subprocess.run", return_value=proc) as run:
        AIHubClient().enviar_prompt(CFG, prompt)
    assert len(run.call_args.kwargs["input"]) <= ai_hub.MAX_CLI_PROMPT_CHARS


def test_health_informa_o_limite_de_envio():
    assert client.get("/api/health").json()["limite_envio"] == LIMITE


def _enviar_api(provider, corpo):
    resp = MagicMock()
    resp.read.return_value = json.dumps(corpo).encode()
    resp.__enter__.return_value = resp
    with patch("urllib.request.urlopen", return_value=resp):
        return AIHubClient().enviar_prompt({"provider": provider, "api_key": "chave12345678"}, "oi")


def _corpos(motivo_openai, motivo_claude, motivo_gemini, motivo_ollama):
    openai = {"choices": [{"message": {"content": "t"}, "finish_reason": motivo_openai}]}
    return [
        ("openai", openai),
        ("openrouter", openai),
        ("claude", {"content": [{"text": "t"}], "stop_reason": motivo_claude}),
        ("gemini", {"candidates": [{"content": {"parts": [{"text": "t"}]}, "finishReason": motivo_gemini}]}),
        ("ollama", {"message": {"content": "t"}, "done_reason": motivo_ollama}),
    ]


@pytest.mark.parametrize("provider,corpo", _corpos("length", "max_tokens", "MAX_TOKENS", "length"))
def test_detecta_corte_em_cada_provedor(provider, corpo):
    assert _enviar_api(provider, corpo)["cortada"] is True


@pytest.mark.parametrize("provider,corpo", _corpos("stop", "end_turn", "STOP", "stop"))
def test_resposta_completa_nao_e_marcada(provider, corpo):
    assert _enviar_api(provider, corpo)["cortada"] is False


@pytest.mark.parametrize("extra,cortada", [(0, False), (1, True)])
def test_detecta_corte_na_saida_do_cli(extra, cortada):
    proc = MagicMock(returncode=0, stdout="x" * (ai_hub.MAX_CLI_OUTPUT_CHARS + extra), stderr="")
    with patch("ai_hub.shutil.which", return_value="/usr/bin/claude"), \
         patch("subprocess.run", return_value=proc):
        out = AIHubClient().enviar_prompt(CFG, "oi")
    assert out["cortada"] is cortada
    assert len(out["resposta"]) == ai_hub.MAX_CLI_OUTPUT_CHARS


def test_marca_de_corte_fica_no_historico_nas_duas_rotas(monkeypatch):
    monkeypatch.setattr(AIHubClient, "call_llm", lambda *a, **k: RespostaIA("parcial", True))
    pid = main.history_store.salvar_pedido(
        categoria="web", objetivo="o", stack="s", entrada="e", saida="x", regras=["r"],
        tratamento_erros="", prompt_final=BASE, tokens_estimados=10, gerado_por="m")["id"]
    r1 = client.post("/api/enviar-prompt", json={"prompt": BASE, "ai_config": CFG, "pedido_id": pid})
    r2 = client.post("/api/sequenciar", json={
        "prompt_base": BASE, "pedido_id": pid, "ai_config": CFG,
        "rodadas": [{"pedido": "", "resposta": "parcial"}], "novo_pedido": "continue"})
    assert r1.json()["cortada"] is True and r2.json()["cortada"] is True
    assert r1.json()["resposta"] == "parcial"
    guardadas = main.history_store.listar_rodadas(pid)
    assert [g["resposta"] for g in guardadas] == ["parcial" + MARCA_RESPOSTA_CORTADA] * 2


def test_marca_da_tela_e_do_servidor_sao_iguais():
    from pathlib import Path
    ts = Path(__file__).resolve().parents[2] / "frontend" / "src" / "tamanhoEnvio.ts"
    assert MARCA_RESPOSTA_CORTADA.replace("\n", "\\n") in ts.read_text(encoding="utf-8")
