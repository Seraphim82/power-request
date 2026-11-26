"""Envio automático (experimental): abre o site da IA, cola o prompt e dá Enter.

Hoje só o macOS tem estratégia (AppleScript via ``osascript``). Para Windows (PowerShell/SendKeys)
e Linux (xdotool, só X11) basta registrar uma função nova em ``ESTRATEGIAS``; sistema sem
estratégia devolve ``sem_suporte`` (usar copiar e colar), sem quebrar nada.

Segurança:
- o prompt nunca entra em script nem em comando de shell: vai pela área de transferência
  (``pbcopy``) ou, quando curto e o site aceita, como parâmetro codificado de URL passado em
  ``argv`` (sem shell);
- os scripts AppleScript são textos fixos; só valores validados (navegador da lista fechada,
  URL https do perfil) chegam a eles, por argumento;
- o endereço de cada site vem de ``perfis_sites.json`` e é validado (https, domínio coerente).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import quote, urlparse

from ai_hub import AIHubError, AIHubSecurityError

PERFIS_ARQUIVO = Path(__file__).resolve().parent / "perfis_sites.json"
MAX_PROMPT_CHARS = 100_000
MAX_ESPERA_MS = 30_000
MAX_PARAMETRO_URL = 14_000
NAVEGADORES = ("Safari", "Google Chrome")  # o primeiro instalado vira o "automático"
STATUS_CONFIRMADO = "confirmado"
STATUS_NAO_CONFIRMADO = "nao_confirmado"
STATUS_SEM_PERMISSAO = "sem_permissao"
STATUS_SEM_SUPORTE = "sem_suporte"

MSG_PLANO_B = "Não consegui confirmar o envio. O texto está copiado, é só colar e enviar."
MSG_SEM_PERMISSAO = (
    "O macOS bloqueou o controle do teclado. Em Ajustes do Sistema > Privacidade e Segurança > "
    "Acessibilidade, autorize o app (Power Request ou o Terminal). O texto está copiado: "
    "é só colar e enviar."
)
MSG_SEM_AUTOMACAO = (
    "O macOS não deixou o Terminal controlar o {navegador}. Em Ajustes do Sistema > Privacidade e "
    "Segurança > System & App Protection Override > Terminal, deixe o {navegador} como Always Allow. "
    "O texto está copiado: é só colar e enviar."
)
MSG_SEM_SUPORTE = "O envio automático ainda não funciona neste sistema. Use copiar e colar."

_em_execucao = threading.Lock()

MSG_ABA_ERRADA = (
    "Parei antes de colar: a aba da frente não era a página esperada do {nome}. Nada foi digitado. "
    "O texto está copiado: é só colar e enviar."
)
MSG_ABA_MUDOU = (
    "Parei antes do Enter: a aba da frente mudou depois de colar. Confira onde o texto foi colado "
    "antes de enviar. O texto continua copiado."
)
_ERRO_ANTES_DE_COLAR = "PR_ABA_ERRADA"
_ERRO_ANTES_DO_ENTER = "PR_ABA_MUDOU"
VARIAVEL_DESTINO = "PR_DESTINO"

# Como cada navegador informa o endereço da aba da frente.
_ABA_DA_FRENTE = {
    "Google Chrome": "URL of active tab of front window",
    "Safari": "URL of current tab of front window",
}

# Textos fixos: nada do usuário é concatenado aqui. Os valores chegam por argv, e o endereço
# esperado (do perfil validado, nunca do prompt) por variável de ambiente. A conferência fica
# dentro do próprio script para ficar o mais perto possível de cada tecla.
_MODELO_TECLAS = """
on abaCerta(destino)
    if destino is "" then return false
    tell application "System Events" to set naFrente to name of first application process whose frontmost is true
    if naFrente is not "__NAVEGADOR__" then return false
    tell application "__NAVEGADOR__" to set endereco to __ABA__
    if endereco is destino then return true
    if endereco starts with (destino & "?") then return true
    if endereco starts with (destino & "#") then return true
    return false
end abaCerta

on run argv
    set navegador to item 1 of argv
    set colar to item 2 of argv
    set pausaMs to (item 3 of argv) as integer
    set destino to system attribute "PR_DESTINO"
    tell application navegador to activate
    delay 0.6
    if colar is "sim" then
        if not abaCerta(destino) then error "PR_ABA_ERRADA"
        tell application "System Events" to keystroke "v" using command down
        delay (pausaMs / 1000)
        if not abaCerta(destino) then error "PR_ABA_MUDOU"
    else
        if not abaCerta(destino) then error "PR_ABA_ERRADA"
    end if
    tell application "System Events" to key code 36
end run
"""
# Um texto fixo por navegador: o AppleScript precisa do nome literal para entender "URL of ...".
_SCRIPTS_TECLAS = {
    nome: _MODELO_TECLAS.replace("__NAVEGADOR__", nome).replace("__ABA__", aba)
    for nome, aba in _ABA_DA_FRENTE.items()
}
_SCRIPT_TECLA_INOFENSIVA = 'tell application "System Events" to key code 56'  # só a tecla Shift
_SCRIPTS_URL = {
    "Google Chrome": 'tell application "Google Chrome" to return URL of active tab of front window',
    "Safari": 'tell application "Safari" to return URL of current tab of front window',
}


# --------------------------------------------------------------------------- perfis


def _host_ok(url: str, dominio: str) -> bool:
    partes = urlparse(url)
    host = (partes.hostname or "").lower()
    return partes.scheme == "https" and (host == dominio or host.endswith("." + dominio))


def _inteiro(valor: Any, nome: str, minimo: int, maximo: int) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise AIHubError(f"Perfil de site inválido: '{nome}' deve ser um número entre {minimo} e {maximo}.")
    return valor


def _validar_perfil(chave: str, bruto: Any) -> dict[str, Any]:
    if not isinstance(bruto, dict):
        raise AIHubError(f"Perfil de site inválido: {chave}.")
    for campo in ("nome", "dominio", "url_nova", "url_conversa_prefixo"):
        if not isinstance(bruto.get(campo), str) or not bruto[campo].strip():
            raise AIHubError(f"Perfil de site inválido ({chave}): falta '{campo}'.")
    dominio = bruto["dominio"].strip().lower()
    for campo in ("url_nova", "url_conversa_prefixo"):
        if not _host_ok(bruto[campo], dominio):
            raise AIHubError(f"Perfil de site inválido ({chave}): '{campo}' precisa ser https de {dominio}.")
    parametro = bruto.get("parametro_texto")
    if parametro is not None and (not isinstance(parametro, str) or not parametro.isalnum()):
        raise AIHubError(f"Perfil de site inválido ({chave}): 'parametro_texto' inválido.")
    return {
        "nome": bruto["nome"].strip(),
        "dominio": dominio,
        "url_nova": bruto["url_nova"],
        "url_conversa_prefixo": bruto["url_conversa_prefixo"],
        "parametro_texto": parametro,
        "validado_no_mac": bruto.get("validado_no_mac") is True,
        "limite_parametro": _inteiro(bruto.get("limite_parametro", 0), "limite_parametro", 0, MAX_PARAMETRO_URL),
        "espera_carregar_ms": _inteiro(bruto.get("espera_carregar_ms", 4000), "espera_carregar_ms", 0, MAX_ESPERA_MS),
        "espera_apos_colar_ms": _inteiro(bruto.get("espera_apos_colar_ms", 1000), "espera_apos_colar_ms", 0, MAX_ESPERA_MS),
        "espera_confirmar_ms": _inteiro(bruto.get("espera_confirmar_ms", 8000), "espera_confirmar_ms", 0, MAX_ESPERA_MS),
    }


def carregar_perfis(arquivo: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    try:
        bruto = json.loads((arquivo or PERFIS_ARQUIVO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise AIHubError("Não foi possível ler os perfis dos sites.") from None
    if not isinstance(bruto, dict):
        raise AIHubError("Perfis dos sites em formato inválido.")
    return {str(chave): _validar_perfil(str(chave), valor) for chave, valor in bruto.items()}


def perfis_para_ui() -> dict[str, Any]:
    perfis = carregar_perfis()
    return {
        "suportado": sys.platform in ESTRATEGIAS,
        "perfis": [{"chave": c, "nome": p["nome"]} for c, p in perfis.items()],
        "nao_validados": [c for c, p in perfis.items() if not p["validado_no_mac"]],
        "navegadores": list(NAVEGADORES),
    }


# --------------------------------------------------------------------------- macOS


def _osascript(
    script: str, *args: str, timeout: int = 25, destino: Optional[str] = None
) -> subprocess.CompletedProcess:
    extra = {"env": {**os.environ, VARIAVEL_DESTINO: destino}} if destino else {}
    return subprocess.run(
        ["osascript", "-e", script, *args],
        capture_output=True, text=True, timeout=timeout, shell=False, check=False, **extra,
    )


def _sem_permissao(resultado: subprocess.CompletedProcess) -> bool:
    erro = (resultado.stderr or "").lower()
    return resultado.returncode != 0 and (
        "1002" in erro or "not allowed to send keystrokes" in erro or "não tem permissão" in erro
        or "not allowed assistive" in erro or "(-25211)" in erro
    )


def _sem_automacao(resultado: subprocess.CompletedProcess) -> bool:
    """Erro -1743: o macOS não autorizou controlar o app (permissão de Automação)."""
    erro = (resultado.stderr or "").lower()
    return resultado.returncode != 0 and ("-1743" in erro or "not authorized to send apple events" in erro)


def _resumo_erro(resultado: subprocess.CompletedProcess) -> str:
    """Última linha do erro do osascript, curta e sem quebras (os argumentos nunca levam o prompt)."""
    linhas = [l for l in (resultado.stderr or "").strip().splitlines() if l.strip()]
    return " ".join(linhas[-1].split())[:160] if linhas else ""


def _navegador_valido(navegador: Optional[str]) -> str:
    if navegador is None:
        for candidato in NAVEGADORES:
            if _navegador_instalado(candidato):
                return candidato
        raise AIHubError("Nenhum navegador compatível (Chrome ou Safari) foi encontrado.")
    if navegador not in NAVEGADORES:
        raise AIHubError("Navegador não suportado. Use Google Chrome ou Safari.")
    return navegador


def _navegador_instalado(navegador: str) -> bool:
    try:
        return subprocess.run(
            ["open", "-Ra", navegador], capture_output=True, timeout=10, shell=False, check=False
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _copiar(texto: str) -> None:
    try:
        subprocess.run(["pbcopy"], input=texto, text=True, timeout=10, shell=False, check=True)
    except (OSError, subprocess.SubprocessError):
        raise AIHubError("Não foi possível copiar o prompt para a área de transferência.") from None


def _ler_url_atual(navegador: str) -> str:
    try:
        r = _osascript(_SCRIPTS_URL[navegador], timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def _enviar_macos(texto: str, perfil: dict[str, Any], navegador: str) -> dict[str, Any]:
    _copiar(texto)  # sempre: é o plano B se algo falhar
    parametro = perfil["parametro_texto"]
    via_url = bool(parametro) and len(texto) <= perfil["limite_parametro"]
    destino = perfil["url_nova"]
    if via_url:
        destino = f"{destino}?{parametro}={quote(texto, safe='')}"
        if len(destino) > MAX_PARAMETRO_URL + 200:
            via_url = False
            destino = perfil["url_nova"]
    try:
        subprocess.run(["open", "-a", navegador, destino], timeout=15, shell=False, check=True)
    except (OSError, subprocess.SubprocessError):
        raise AIHubError(f"Não foi possível abrir o {navegador}.") from None

    time.sleep(perfil["espera_carregar_ms"] / 1000)
    try:
        r = _osascript(
            _SCRIPTS_TECLAS[navegador],
            navegador, "nao" if via_url else "sim", str(perfil["espera_apos_colar_ms"]),
            destino=perfil["url_nova"],
        )
    except subprocess.TimeoutExpired:
        return {
            "status": STATUS_NAO_CONFIRMADO,
            "mensagem": f"{MSG_PLANO_B} (O {navegador} não respondeu a tempo; pode haver uma janela do macOS esperando permissão.)",
        }
    except (OSError, subprocess.SubprocessError):
        return {"status": STATUS_NAO_CONFIRMADO, "mensagem": MSG_PLANO_B}
    if r.returncode != 0 and _ERRO_ANTES_DE_COLAR in (r.stderr or ""):
        # com o texto no link nada é colado, mas o Enter também não sai
        return {"status": STATUS_NAO_CONFIRMADO, "mensagem": MSG_ABA_ERRADA.format(nome=perfil["nome"])}
    if r.returncode != 0 and _ERRO_ANTES_DO_ENTER in (r.stderr or ""):
        return {"status": STATUS_NAO_CONFIRMADO, "mensagem": MSG_ABA_MUDOU}
    if _sem_permissao(r):
        return {"status": STATUS_SEM_PERMISSAO, "mensagem": MSG_SEM_PERMISSAO}
    if _sem_automacao(r):
        return {"status": STATUS_SEM_PERMISSAO, "mensagem": MSG_SEM_AUTOMACAO.format(navegador=navegador)}
    if r.returncode != 0:
        detalhe = _resumo_erro(r)
        mensagem = f"{MSG_PLANO_B} (Detalhe técnico: {detalhe})" if detalhe else MSG_PLANO_B
        return {"status": STATUS_NAO_CONFIRMADO, "mensagem": mensagem}

    # Conferência: se o endereço da aba virou o de uma conversa, o envio aconteceu.
    prazo = time.monotonic() + perfil["espera_confirmar_ms"] / 1000
    while True:
        if _ler_url_atual(navegador).startswith(perfil["url_conversa_prefixo"]):
            return {"status": STATUS_CONFIRMADO, "mensagem": f"Enviado para o {perfil['nome']}."}
        if time.monotonic() >= prazo:
            return {"status": STATUS_NAO_CONFIRMADO, "mensagem": MSG_PLANO_B}
        time.sleep(0.5)


ESTRATEGIAS: dict[str, Callable[[str, dict[str, Any], str], dict[str, Any]]] = {"darwin": _enviar_macos}


# --------------------------------------------------------------------------- API pública


def enviar_automatico(
    texto: str, ia: str, navegador: Optional[str] = None, *, aviso_aceito: bool = False
) -> dict[str, Any]:
    if not aviso_aceito:
        raise AIHubError("Confirme o aviso do envio automático antes de continuar.")
    texto = (texto or "").strip()
    if not texto:
        raise AIHubError("Não há prompt para enviar.")
    if len(texto) > MAX_PROMPT_CHARS:
        raise AIHubError(f"O prompt tem mais de {MAX_PROMPT_CHARS} caracteres.")
    if "\x00" in texto:
        raise AIHubSecurityError("Entrada contém byte nulo não permitido.")
    perfil = carregar_perfis().get(ia)
    if perfil is None:
        raise AIHubError("Ainda não há perfil de envio automático para essa IA.")
    estrategia = ESTRATEGIAS.get(sys.platform)
    if estrategia is None:
        return {"status": STATUS_SEM_SUPORTE, "mensagem": MSG_SEM_SUPORTE}
    escolhido = _navegador_valido(navegador)
    if not _em_execucao.acquire(blocking=False):
        raise AIHubError("Já há um envio automático em andamento.")
    try:
        return estrategia(texto, perfil, escolhido)
    finally:
        _em_execucao.release()


def testar_automacao(navegador: Optional[str] = None) -> dict[str, Any]:
    """Confere o que dá para conferir sem enviar nada (só aperta a tecla Shift)."""
    itens: list[dict[str, Any]] = []
    if sys.platform not in ESTRATEGIAS:
        itens.append({"item": "Sistema", "ok": False, "detalhe": MSG_SEM_SUPORTE})
        return {"ok": False, "itens": itens}
    itens.append({"item": "Sistema", "ok": True, "detalhe": "macOS"})
    nav = _navegador_valido(navegador)
    itens.append({"item": "Navegador", "ok": True, "detalhe": nav})
    try:
        r = _osascript(_SCRIPT_TECLA_INOFENSIVA, timeout=15)
        ok = r.returncode == 0
        detalhe = "Permissão de Acessibilidade concedida." if ok else (
            MSG_SEM_PERMISSAO if _sem_permissao(r) else "O macOS não executou o teste de teclado."
        )
    except (OSError, subprocess.SubprocessError):
        ok, detalhe = False, "O macOS não executou o teste de teclado."
    itens.append({"item": "Controle do teclado", "ok": ok, "detalhe": detalhe})
    return {"ok": all(i["ok"] for i in itens), "itens": itens}
