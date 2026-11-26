"""Fase 4: origem exata, filtro sem falso positivo, log sem dados sensíveis e permissões."""
import os
import stat

import pytest
from fastapi.testclient import TestClient

import main
import registro_local
from history_store import HistoryStore
from prompt_engine import PowerRequestEngine, SecurityError

client = TestClient(main.app)
CORPO = {"intencao": "Quero um site simples"}


def _post(origem, base="http://testserver"):
    c = TestClient(main.app, base_url=base)
    return c.post("/api/analisar-intencao", json=CORPO, headers={"Origin": origem}).status_code


# ------------------------------------------------------------------ origem


@pytest.mark.parametrize(
    "origem",
    [
        "http://127.0.0.1:3000", "http://localhost:8000", "http://localhost", "http://127.0.0.1",
        "https://127.0.0.1:8765", "http://localhost:5174", "http://127.0.0.1:87650",
        "http://127.0.0.1:8765.evil.com", "http://evil.com@127.0.0.1:8765", "null", "",
    ],
)
def test_outra_porta_protocolo_ou_formato_e_recusado(origem):
    assert _post(origem) == 403


@pytest.mark.parametrize(
    "origem",
    ["http://127.0.0.1:8765", "http://localhost:8765", "http://localhost:5173", "http://127.0.0.1:5173"],
)
def test_origem_do_app_e_do_vite_passam(origem):
    assert _post(origem) == 200


def test_porta_alternativa_do_app_passa_e_a_padrao_deixa_de_valer(monkeypatch):
    monkeypatch.setattr(main.app.state, "porta", 50123, raising=False)
    assert _post("http://127.0.0.1:50123", base="http://127.0.0.1:50123") == 200
    assert _post("http://127.0.0.1:8765", base="http://127.0.0.1:50123") == 403


def test_mesma_origem_do_servidor_passa_em_qualquer_porta():
    assert _post("http://127.0.0.1:8000", base="http://127.0.0.1:8000") == 200


# ------------------------------------------------------------------ filtro


@pytest.mark.parametrize(
    "texto",
    [
        "Linguagem JavaScript: Node",
        "JavaScript: Node (Express) com banco SQLite",
        "Stack em JavaScript : React",
        "Sei pouco de JavaScript:\nexplique o passo a passo",
    ],
)
def test_texto_comum_com_javascript_passa(texto):
    assert PowerRequestEngine()._sanitizar_e_validar_seguranca(texto, "stack")


@pytest.mark.parametrize(
    "ataque",
    [
        "javascript:alert(1)", "JAVASCRIPT:void(0)", "javascript :alert(1)",
        "javascript: alert(1)", "javascript:\n  document.cookie", "javascript: window.location='x'",
        "javascript:%61lert(1)", "javascript://x%0Aalert(1)",
    ],
)
def test_endereco_javascript_continua_bloqueado(ataque):
    with pytest.raises(SecurityError):
        PowerRequestEngine()._sanitizar_e_validar_seguranca(ataque, "objetivo")


# ------------------------------------------------------------------ log


@pytest.fixture
def log(tmp_path):
    pasta = tmp_path / "log"
    assert registro_local.ativar(pasta)
    yield pasta / "power_request.log"
    registro_local.desativar()


def test_falha_deixa_rastro_sem_dados_enviados(log):
    r = client.post("/api/analisar-intencao", json={"intencao": "SEGREDO123 javascript:alert(1)"})
    assert r.status_code == 403
    texto = log.read_text()
    assert "rota=/api/analisar-intencao codigo=403 tipo=SecurityError" in texto
    assert "SEGREDO123" not in texto and "alert" not in texto


def test_log_nao_grava_endereco_real_busca_nem_origem(log):
    client.delete("/api/historico/987654?q=SEGREDO123")
    client.get("/caminho-SEGREDO123")
    client.post("/api/analisar-intencao", json=CORPO, headers={"Origin": "http://SEGREDO123.test"})
    texto = log.read_text()
    assert "rota=/api/historico/{pedido_id} codigo=404" in texto
    assert "codigo=403" in texto
    assert "SEGREDO123" not in texto and "987654" not in texto


def test_erro_inesperado_grava_so_o_tipo(log, monkeypatch):
    def explode(_):
        raise RuntimeError("chave sk-SEGREDO123")

    monkeypatch.setattr(main.engine, "analisar_intencao", explode)
    with pytest.raises(RuntimeError):
        client.post("/api/analisar-intencao", json=CORPO)
    texto = log.read_text()
    assert "codigo=500 tipo=RuntimeError" in texto and "SEGREDO123" not in texto


def test_envio_automatico_nao_confirmado_deixa_rastro_sem_o_prompt(log, monkeypatch):
    monkeypatch.setattr(
        main.envio_automatico, "enviar_automatico",
        lambda *a, **k: {"status": "nao_confirmado", "mensagem": "x"},
    )
    client.post("/api/envio-automatico", json={"prompt": "SEGREDO123", "ia": "claude", "aviso_aceito": True})
    texto = log.read_text()
    assert "tipo=envio_nao_confirmado" in texto and "SEGREDO123" not in texto


def test_sucesso_nao_vai_para_o_log(log):
    client.get("/api/health")
    assert log.read_text() == ""


def _modo(caminho):
    return stat.S_IMODE(os.stat(caminho).st_mode)


def test_log_e_pasta_ficam_privados_e_o_tamanho_e_limitado(log):
    for _ in range(3000):
        registro_local.registrar_falha("POST", "/api/x", 400, "ValidationError")
    antigo = log.with_name(log.name + ".1")
    assert _modo(log.parent) == 0o700 and _modo(log) == 0o600 and _modo(antigo) == 0o600
    assert log.stat().st_size <= registro_local.MAX_BYTES
    assert len(list(log.parent.iterdir())) == 2


# ------------------------------------------------------------------ permissões do banco


def test_pasta_padrao_antiga_e_banco_antigo_sao_ajustados(tmp_path, monkeypatch):
    pasta = tmp_path / ".power_request"
    pasta.mkdir()
    (pasta / "history.db").touch()
    os.chmod(pasta, 0o755)
    os.chmod(pasta / "history.db", 0o644)
    monkeypatch.setattr("history_store.Path.home", lambda: tmp_path)
    HistoryStore()
    assert _modo(pasta) == 0o700 and _modo(pasta / "history.db") == 0o600


def test_banco_novo_nasce_privado_e_pasta_alheia_nao_muda(tmp_path):
    nova = tmp_path / "nova"
    HistoryStore(nova / "h.db")
    assert _modo(nova) == 0o700 and _modo(nova / "h.db") == 0o600
    alheia = tmp_path / "alheia"
    alheia.mkdir()
    os.chmod(alheia, 0o755)
    HistoryStore(alheia / "h.db")
    assert _modo(alheia) == 0o755 and _modo(alheia / "h.db") == 0o600


# ------------------------------------------------------------------ envio automático: conferir a aba
# Simulação: o AppleScript não roda aqui. Os testes conferem o script e a reação do app.

import subprocess  # noqa: E402
from unittest.mock import patch  # noqa: E402

import envio_automatico as ea  # noqa: E402


@pytest.mark.parametrize("navegador", ea.NAVEGADORES)
def test_toda_tecla_do_script_vem_depois_de_conferir_a_aba(navegador):
    script = ea._SCRIPTS_TECLAS[navegador]
    corpo = script[script.index("on run argv"):]
    colar = corpo.index('keystroke "v"')
    enter = corpo.index("key code 36")
    assert corpo.index("if not abaCerta(destino)") < colar
    assert colar < corpo.index('error "PR_ABA_MUDOU"') < enter
    senao = corpo[corpo.index("    else\n"):enter]  # caminho sem colar também confere
    assert "if not abaCerta(destino)" in senao
    assert script.count("keystroke") == 1 and script.count("key code 36") == 1
    assert f'if naFrente is not "{navegador}" then return false' in script
    assert "__" not in script


def _rodar(monkeypatch, erro):
    monkeypatch.setattr(ea.sys, "platform", "darwin")
    monkeypatch.setattr(ea.time, "sleep", lambda s: None)
    chamadas = []

    def run(cmd, **kw):
        chamadas.append((cmd, kw))
        teclas = cmd[0] == "osascript" and "keystroke" in cmd[2]
        return subprocess.CompletedProcess(cmd, 1 if teclas else 0, stdout="", stderr=erro if teclas else "")

    with patch("envio_automatico.subprocess.run", side_effect=run):
        saida = ea.enviar_automatico("SEGREDO123", "claude", "Safari", aviso_aceito=True)
    return saida, chamadas


@pytest.mark.parametrize(
    "codigo,trecho", [("PR_ABA_ERRADA", "Nada foi digitado"), ("PR_ABA_MUDOU", "antes do Enter")]
)
def test_aba_errada_para_explica_e_nao_tenta_confirmar(monkeypatch, codigo, trecho):
    saida, chamadas = _rodar(monkeypatch, f"execution error: {codigo} (-2700)")
    assert saida["status"] == ea.STATUS_NAO_CONFIRMADO and trecho in saida["mensagem"]
    assert "osascript" == chamadas[-1][0][0] and "keystroke" in chamadas[-1][0][2]


def test_endereco_esperado_vem_do_perfil_e_o_prompt_nao_vai_ao_script(monkeypatch):
    _, chamadas = _rodar(monkeypatch, "PR_ABA_ERRADA")
    cmd, kw = chamadas[-1]
    assert kw["env"][ea.VARIAVEL_DESTINO] == "https://claude.ai/new"
    assert all("SEGREDO123" not in p for p in cmd)
    assert all("SEGREDO123" not in v for v in kw["env"].values())
