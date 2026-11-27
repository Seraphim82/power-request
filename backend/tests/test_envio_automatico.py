"""Testes do envio automático (experimental): perfis, segurança dos comandos e conferência."""
import json
import subprocess
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import envio_automatico as ea
import main
from ai_hub import AIHubError, AIHubSecurityError

PROMPT = "### Objetivo\nCriar algo; `rm -rf ~` $(whoami) \"aspas\" 'simples' && echo x\n"
client = TestClient(main.app)


class Ambiente:
    """Simula macOS: registra cada comando e responde a URL da aba conforme o cenário."""

    def __init__(self, urls=("https://claude.ai/new",), teclas_rc=0, teclas_erro=""):
        self.chamadas = []
        self.urls = list(urls)
        self.teclas_rc = teclas_rc
        self.teclas_erro = teclas_erro

    def run(self, cmd, **kw):
        self.chamadas.append((cmd, kw))
        if cmd[0] == "osascript":
            if "return URL" in cmd[2]:
                url = self.urls.pop(0) if len(self.urls) > 1 else self.urls[0]
                return subprocess.CompletedProcess(cmd, 0, stdout=url + "\n", stderr="")
            return subprocess.CompletedProcess(cmd, self.teclas_rc, stdout="", stderr=self.teclas_erro)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    def comandos(self, nome):
        return [c for c, _ in self.chamadas if c[0] == nome]


@pytest.fixture
def mac(monkeypatch):
    monkeypatch.setattr(ea.sys, "platform", "darwin")
    monkeypatch.setattr(ea.time, "sleep", lambda s: None)
    # monotonic avança 1s por chamada: o prazo de confirmação sempre termina
    relogio = iter(range(0, 10_000))
    monkeypatch.setattr(ea.time, "monotonic", lambda: float(next(relogio)))


def _enviar(amb, texto=PROMPT, ia="claude", navegador="Google Chrome"):
    with patch("envio_automatico.subprocess.run", side_effect=amb.run):
        return ea.enviar_automatico(texto, ia, navegador, aviso_aceito=True)


# ------------------------------------------------------------------ perfis


def test_perfil_do_claude_carrega_e_e_valido():
    p = ea.carregar_perfis()["claude"]
    assert p["dominio"] == "claude.ai" and p["url_nova"].startswith("https://claude.ai/")
    assert p["url_conversa_prefixo"] == "https://claude.ai/chat/"


@pytest.mark.parametrize(
    "mudanca",
    [
        {"url_nova": "http://claude.ai/new"},
        {"url_nova": "https://claude.ai.evil.com/new"},
        {"url_conversa_prefixo": "https://outro.com/chat/"},
        {"parametro_texto": "q&x=1"},
        {"espera_carregar_ms": 999_999},
        {"espera_confirmar_ms": "8"},
        {"limite_parametro": 50_000},
    ],
)
def test_perfil_invalido_e_rejeitado(tmp_path, mudanca):
    base = json.loads(ea.PERFIS_ARQUIVO.read_text())["claude"] | mudanca
    arq = tmp_path / "p.json"
    arq.write_text(json.dumps({"claude": base}))
    with pytest.raises(AIHubError):
        ea.carregar_perfis(arq)


def test_arquivo_de_perfis_ausente_da_erro_amigavel(tmp_path):
    with pytest.raises(AIHubError):
        ea.carregar_perfis(tmp_path / "nao-existe.json")


# ------------------------------------------------------------------ validações


def test_exige_aviso_aceito():
    with pytest.raises(AIHubError):
        ea.enviar_automatico("oi", "claude")


@pytest.mark.parametrize("texto", ["", "   \n"])
def test_prompt_vazio_e_rejeitado(texto):
    with pytest.raises(AIHubError):
        ea.enviar_automatico(texto, "claude", aviso_aceito=True)


def test_byte_nulo_e_barrado():
    with pytest.raises(AIHubSecurityError):
        ea.enviar_automatico("a\x00b", "claude", aviso_aceito=True)


def test_prompt_gigante_e_rejeitado():
    with pytest.raises(AIHubError):
        ea.enviar_automatico("a" * (ea.MAX_PROMPT_CHARS + 1), "claude", aviso_aceito=True)


def test_ia_sem_perfil_e_rejeitada():
    with pytest.raises(AIHubError):
        ea.enviar_automatico("oi", "ia-inexistente", aviso_aceito=True)


def test_sistema_sem_suporte_nao_quebra(monkeypatch):
    monkeypatch.setattr(ea.sys, "platform", "linux")
    out = ea.enviar_automatico("oi", "claude", aviso_aceito=True)
    assert out["status"] == ea.STATUS_SEM_SUPORTE and "copiar e colar" in out["mensagem"]


def test_navegador_fora_da_lista_e_rejeitado(mac):
    with pytest.raises(AIHubError):
        _enviar(Ambiente(), navegador="Firefox; rm -rf ~")


# ------------------------------------------------------------------ macOS


def test_prompt_nunca_vai_em_script_nem_em_comando_de_shell(mac):
    amb = Ambiente(urls=["https://claude.ai/chat/abc"])
    longo = PROMPT * 600  # passa do limite da URL: usa área de transferência + ⌘V
    _enviar(amb, longo)
    for cmd, kw in amb.chamadas:
        assert kw.get("shell") is False or "shell" not in kw
        assert all("rm -rf" not in parte and "whoami" not in parte for parte in cmd)
    assert amb.chamadas[0][0] == ["pbcopy"] and amb.chamadas[0][1]["input"] == longo.strip()


def test_perfil_claude_padrao_cola_com_comando_v_e_nao_usa_url(mac):
    amb = Ambiente(urls=["https://claude.ai/chat/abc"])
    out = _enviar(amb)
    assert amb.comandos("open")[0][3] == "https://claude.ai/new"
    teclas = [c for c in amb.comandos("osascript") if "keystroke" in c[2]][0]
    assert teclas[3:] == ["Google Chrome", "sim", "1200"]
    assert out["status"] == ea.STATUS_CONFIRMADO


def test_prompt_curto_vai_na_url_codificada_e_so_aperta_enter(mac, monkeypatch):
    # perfil hipotético de um site que aceita ?q= e envia sozinho
    perfil = ea.carregar_perfis()["claude"] | {"parametro_texto": "q", "limite_parametro": 12000}
    monkeypatch.setattr(ea, "carregar_perfis", lambda arquivo=None: {"claude": perfil})
    amb = Ambiente(urls=["https://claude.ai/chat/abc"])
    out = _enviar(amb)
    abrir = amb.comandos("open")[0]
    assert abrir[:3] == ["open", "-a", "Google Chrome"]
    assert abrir[3].startswith("https://claude.ai/new?q=") and "%60rm%20-rf%20~%60" in abrir[3]
    assert " " not in abrir[3] and "`" not in abrir[3]
    teclas = [c for c in amb.comandos("osascript") if "keystroke" in c[2]][0]
    assert teclas[3:] == ["Google Chrome", "nao", "1200"]
    assert out["status"] == ea.STATUS_CONFIRMADO


def test_prompt_longo_abre_pagina_limpa_e_cola(mac, monkeypatch):
    perfil = ea.carregar_perfis()["claude"] | {"parametro_texto": "q", "limite_parametro": 12000}
    monkeypatch.setattr(ea, "carregar_perfis", lambda arquivo=None: {"claude": perfil})
    amb = Ambiente(urls=["https://claude.ai/chat/abc"])
    _enviar(amb, "palavra " * 3000)
    assert amb.comandos("open")[0][3] == "https://claude.ai/new"
    teclas = [c for c in amb.comandos("osascript") if "keystroke" in c[2]][0]
    assert teclas[4] == "sim"


def test_confirmado_quando_a_aba_vira_conversa(mac):
    amb = Ambiente(urls=["https://claude.ai/new", "https://claude.ai/chat/123"])
    out = _enviar(amb)
    assert out["status"] == ea.STATUS_CONFIRMADO


def test_plano_b_quando_a_aba_continua_em_conversa_nova(mac):
    out = _enviar(Ambiente(urls=["https://claude.ai/new"]))
    assert out["status"] == ea.STATUS_NAO_CONFIRMADO
    assert out["mensagem"] == ea.MSG_PLANO_B


def test_sem_permissao_de_acessibilidade(mac):
    amb = Ambiente(teclas_rc=1, teclas_erro="execution error: ... não tem permissão para enviar teclas. (1002)")
    out = _enviar(amb)
    assert out["status"] == ea.STATUS_SEM_PERMISSAO and "Acessibilidade" in out["mensagem"]


def test_erro_generico_do_osascript_cai_no_plano_b(mac):
    out = _enviar(Ambiente(teclas_rc=1, teclas_erro="algo estranho"))
    assert out["status"] == ea.STATUS_NAO_CONFIRMADO


def test_sem_permissao_de_automacao_do_navegador_diz_qual(mac):
    amb = Ambiente(teclas_rc=1, teclas_erro="execution error: Not authorized to send Apple events to Google Chrome. (-1743)")
    out = _enviar(amb, navegador="Google Chrome")
    assert out["status"] == ea.STATUS_SEM_PERMISSAO
    assert "Google Chrome" in out["mensagem"] and "Always Allow" in out["mensagem"]


def test_erro_desconhecido_mostra_detalhe_tecnico_sem_vazar_o_prompt(mac):
    amb = Ambiente(teclas_rc=1, teclas_erro="linha 1\n  36:47: execution error:   algo   estranho (-9999)  ")
    out = _enviar(amb)
    assert out["status"] == ea.STATUS_NAO_CONFIRMADO
    assert "algo estranho (-9999)" in out["mensagem"] and "rm -rf" not in out["mensagem"]


def test_osascript_que_nao_responde_explica_possivel_janela_pendente(mac):
    amb = Ambiente()
    original = amb.run

    def run(cmd, **kw):
        if cmd[0] == "osascript" and "keystroke" in cmd[2]:
            raise subprocess.TimeoutExpired(cmd, 25)
        return original(cmd, **kw)

    amb.run = run
    out = _enviar(amb)
    assert out["status"] == ea.STATUS_NAO_CONFIRMADO and "não respondeu" in out["mensagem"]


def test_falha_ao_ler_url_nao_quebra(mac):
    amb = Ambiente()
    original = amb.run

    def run(cmd, **kw):
        if cmd[0] == "osascript" and "return URL" in cmd[2]:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="sem automação")
        return original(cmd, **kw)

    amb.run = run
    assert _enviar(amb)["status"] == ea.STATUS_NAO_CONFIRMADO


def test_so_um_envio_automatico_por_vez(mac):
    assert ea._em_execucao.acquire(blocking=False)
    try:
        with pytest.raises(AIHubError):
            _enviar(Ambiente())
    finally:
        ea._em_execucao.release()


def test_trava_e_liberada_mesmo_com_erro(mac):
    def explode(cmd, **kw):
        raise OSError("boom")

    with patch("envio_automatico.subprocess.run", side_effect=explode):
        with pytest.raises(AIHubError):
            ea.enviar_automatico("oi", "claude", "Safari", aviso_aceito=True)
    assert ea._em_execucao.acquire(blocking=False)
    ea._em_execucao.release()


# ------------------------------------------------------------------ testar automação


def test_testar_automacao_ok(mac):
    with patch("envio_automatico.subprocess.run", side_effect=Ambiente().run):
        out = ea.testar_automacao("Safari")
    assert out["ok"] and [i["item"] for i in out["itens"]] == ["Sistema", "Navegador", "Controle do teclado"]


def test_testar_automacao_sem_permissao(mac):
    amb = Ambiente(teclas_rc=1, teclas_erro="(1002)")
    with patch("envio_automatico.subprocess.run", side_effect=amb.run):
        out = ea.testar_automacao("Safari")
    assert not out["ok"] and "Acessibilidade" in out["itens"][-1]["detalhe"]


def test_testar_automacao_em_outro_sistema(monkeypatch):
    monkeypatch.setattr(ea.sys, "platform", "win32")
    assert ea.testar_automacao()["ok"] is False


# ------------------------------------------------------------------ API


def test_api_lista_perfis():
    r = client.get("/api/envio-automatico/perfis")
    assert r.status_code == 200
    assert {"chave": "claude", "nome": "Claude"} in r.json()["perfis"]


def test_api_sem_aviso_aceito_da_400():
    r = client.post("/api/envio-automatico", json={"prompt": "oi", "ia": "claude"})
    assert r.status_code == 400


def test_api_envia_e_devolve_status(monkeypatch):
    monkeypatch.setattr(ea.sys, "platform", "linux")
    r = client.post("/api/envio-automatico", json={"prompt": "oi", "ia": "claude", "aviso_aceito": True})
    assert r.status_code == 200 and r.json()["status"] == ea.STATUS_SEM_SUPORTE


def test_api_testar(monkeypatch):
    monkeypatch.setattr(ea.sys, "platform", "linux")
    r = client.post("/api/envio-automatico/testar", json={})
    assert r.status_code == 200 and r.json()["ok"] is False
