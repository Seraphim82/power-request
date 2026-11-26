"""Chamada segura ao Antigravity (agy): pedido pela entrada padrão e ferramentas travadas.

O agy não tem uma opção testada para desligar as ferramentas. A proteção é um gancho
PreToolUse, criado numa pasta temporária, que recusa toda ferramenta. O app só usa o agy
depois de provar que o gancho está valendo na versão instalada, e descarta a resposta se
alguma ferramenta aparecer sem a recusa. Essa segunda conferência só detecta: não desfaz.

Os ganchos globais do próprio agy rodam por fora desta trava e podem registrar o conteúdo.
"""

from __future__ import annotations

import json
import secrets
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

MARCA_RECUSA = "Ferramentas bloqueadas pelo Power Request."
ERRO_DO_GANCHO = f"denied by pre-tool hook: {MARCA_RECUSA}"
ARGS_AGY = ["--input-format", "stream-json", "--output-format", "stream-json"]
# Passos que não são ferramenta. Qualquer outro tipo é tratado como ferramenta.
PASSOS_SEM_FERRAMENTA = {"user_input", "agent_response", "system_message"}

SCRIPT_GANCHO = (
    "import json\n"
    f'print(json.dumps({{"decision": "deny", "reason": {MARCA_RECUSA!r}}}))\n'
)

AVISO_FALHA = (
    "O Antigravity não respondeu como esperado. No Terminal, rode agy e confira o login. "
    "Se estiver certo, rode agy update e use Testar Conexão de novo."
)
AVISO_SEM_PROVA = (
    "Antes de usar o Antigravity, clique em Testar Conexão no Hub de IAs. "
    "O teste confere se as ferramentas estão travadas."
)
AVISO_BLOQUEADO = (
    "Antigravity bloqueado por segurança: uma ferramenta apareceu sem ser recusada pela trava, "
    "e a ação pode ter acontecido. A resposta foi descartada. Não use até a trava ser revisada."
)
AVISO_GANCHOS = (
    "Há ganchos globais ligados ao Antigravity, e o que você mandar pode ser guardado por eles. "
    "No Hub de IAs, marque que está ciente para liberar o envio."
)


class AgyFalha(Exception):
    """Falha com mensagem pronta para a tela."""


class _Estado:
    def __init__(self) -> None:
        self.provado: tuple[str, str] | None = None  # (caminho do programa, versão)
        self.bloqueado = False


estado = _Estado()


def pasta_gemini() -> Path:
    return Path.home() / ".gemini"


def _tem_comando(no: Any) -> bool:
    if isinstance(no, dict):
        if no.get("enabled") is False:
            return False
        return "command" in no or any(_tem_comando(v) for v in no.values())
    if isinstance(no, list):
        return any(_tem_comando(v) for v in no)
    return False


def tem_ganchos_globais() -> bool:
    """True se houver gancho global ou de plugin. Arquivo ilegível conta como existente."""
    base = pasta_gemini()
    arquivos = [base / "config" / "hooks.json"]
    for raiz in (base / "config" / "plugins", base / "antigravity-cli" / "plugins"):
        arquivos += sorted(raiz.glob("*/hooks.json"))
    for arquivo in arquivos:
        try:
            if not arquivo.exists():
                continue
            if _tem_comando(json.loads(arquivo.read_text(encoding="utf-8"))):
                return True
        except (OSError, ValueError):
            return True
    return False


def _preparar_trava(raiz: Path) -> Path:
    """Cria a pasta de trabalho com o gancho. O script do gancho fica fora dela."""
    trabalho = raiz / "trabalho"
    agentes = trabalho / ".agents"
    agentes.mkdir(parents=True)
    gancho = raiz / "gancho.py"
    gancho.write_text(SCRIPT_GANCHO, encoding="utf-8")
    comando = shlex.join([sys.executable, str(gancho)])
    config = {
        "trava-power-request": {
            "PreToolUse": [
                {"matcher": "*", "hooks": [{"type": "command", "command": comando, "timeout": 20}]}
            ]
        }
    }
    (agentes / "hooks.json").write_text(json.dumps(config), encoding="utf-8")
    return trabalho


def analisar_saida(saida: str) -> dict[str, Any]:
    """Lê o stream-json e confere se toda ferramenta foi recusada pela nossa trava."""
    iniciou = False
    resultado: dict[str, Any] = {}
    ferramentas: dict[tuple[str, str], tuple[str, str]] = {}
    for numero, linha in enumerate(saida.splitlines()):
        try:
            evento = json.loads(linha)
        except ValueError:
            continue
        if not isinstance(evento, dict):
            continue
        tipo = evento.get("event")
        if tipo == "init":
            iniciou = True
        elif tipo == "result" and isinstance(evento.get("result"), dict):
            resultado = evento["result"]
        elif tipo == "step_update":
            passo = evento.get("step_update")
            if not isinstance(passo, dict):
                passo = {}
            sem_ferramenta = (
                passo.get("step_type") in PASSOS_SEM_FERRAMENTA
                and not any(k in passo for k in ("tool_name", "tool_info", "subagent_info"))
            )
            if sem_ferramenta:
                continue
            chave = (str(passo.get("conversation_id")), str(passo.get("step_index", f"l{numero}")))
            info = passo.get("tool_info")
            erro = info.get("error") if isinstance(info, dict) else None
            mensagem = str(erro.get("message", "")) if isinstance(erro, dict) else ""
            # Vale o último estado de cada passo.
            ferramentas[chave] = (str(passo.get("state", "")), mensagem)

    recusadas = sum(
        1 for situacao, msg in ferramentas.values() if situacao == "ERROR" and ERRO_DO_GANCHO in msg
    )
    resposta = resultado.get("response")
    return {
        "iniciou": iniciou,
        "sucesso": resultado.get("status") == "SUCCESS",
        "resposta": resposta.strip() if isinstance(resposta, str) else "",
        "recusadas": recusadas,
        "violacao": recusadas != len(ferramentas),
    }


def _bloquear() -> None:
    estado.bloqueado = True
    estado.provado = None
    raise AgyFalha(AVISO_BLOQUEADO)


def _rodar(binario: str, texto: str, limite: int, env: dict[str, str]) -> tuple[dict[str, Any], str]:
    """Executa o agy numa pasta nova, com a trava. O texto vai só pela entrada padrão."""
    linha = json.dumps({"event": "user", "message": {"content": texto}})
    with tempfile.TemporaryDirectory(prefix="power-request-agy-") as pasta:
        trabalho = _preparar_trava(Path(pasta).resolve())
        try:
            proc = subprocess.run(
                [binario, *ARGS_AGY],
                input=linha + "\n",
                capture_output=True,
                text=True,
                timeout=limite,
                shell=False,
                env=env,
                cwd=str(trabalho),
            )
        except subprocess.TimeoutExpired as exc:
            # O que saiu antes do estouro também é conferido.
            parcial = exc.stdout or ""
            if isinstance(parcial, bytes):
                parcial = parcial.decode("utf-8", errors="replace")
            if analisar_saida(parcial)["violacao"]:
                _bloquear()
            raise AgyFalha(
                f"Tempo esgotado ({limite}s) aguardando o Antigravity. Tente de novo."
            ) from None
        except OSError:
            raise AgyFalha(AVISO_FALHA) from None

    saida = proc.stdout or ""
    analise = analisar_saida(saida)
    # A violação é conferida antes de qualquer outra falha, para nunca passar despercebida.
    if analise["violacao"]:
        _bloquear()
    if proc.returncode != 0 or not analise["iniciou"] or not analise["sucesso"]:
        raise AgyFalha(AVISO_FALHA)
    return analise, saida


def versao(binario: str, env: dict[str, str]) -> str:
    try:
        proc = subprocess.run(
            [binario, "--version"], capture_output=True, text=True, timeout=30, shell=False, env=env
        )
    except (OSError, subprocess.SubprocessError):
        raise AgyFalha(AVISO_FALHA) from None
    texto = (proc.stdout or "").strip()
    if proc.returncode != 0 or not texto:
        raise AgyFalha(AVISO_FALHA)
    return texto[:100]


def provar_trava(binario: str, limite: int, env: dict[str, str]) -> None:
    """Pede a leitura de um arquivo falso e só aprova se a nossa trava recusar."""
    if estado.bloqueado:
        raise AgyFalha(AVISO_BLOQUEADO)
    estado.provado = None
    versao_atual = versao(binario, env)
    segredo = "FALSO-" + secrets.token_hex(8)
    with tempfile.TemporaryDirectory(prefix="power-request-prova-") as pasta:
        arquivo = Path(pasta).resolve() / "arquivo-falso.txt"
        arquivo.write_text(segredo + "\n", encoding="utf-8")
        pedido = (
            "Teste autorizado com arquivo falso. Use sua ferramenta de leitura para abrir o "
            f"arquivo {arquivo} e responda com o conteúdo. Se for bloqueado, não tente outro "
            "caminho. Não faça mais nada."
        )
        analise, saida = _rodar(binario, pedido, limite, env)
    if segredo in saida:
        _bloquear()
    if analise["recusadas"] < 1:
        raise AgyFalha(
            "Não consegui confirmar que as ferramentas estão travadas, então o Antigravity "
            "continua desativado. Use Testar Conexão de novo."
        )
    estado.provado = (binario, versao_atual)


def enviar(binario: str, texto: str, limite: int, env: dict[str, str]) -> str:
    """Envia o texto, exigindo trava já provada para o programa e a versão atuais."""
    if estado.bloqueado:
        raise AgyFalha(AVISO_BLOQUEADO)
    if estado.provado is None or estado.provado != (binario, versao(binario, env)):
        raise AgyFalha(AVISO_SEM_PROVA)
    analise, _ = _rodar(binario, texto, limite, env)
    if not analise["resposta"]:
        raise AgyFalha("O Antigravity não retornou texto na resposta.")
    return analise["resposta"]
