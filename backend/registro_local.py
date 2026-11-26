"""Log local curto de falhas, para sobrar rastro quando algo dá errado.

Guarda só data, método, rota (o modelo, sem valores), código e tipo do erro. Nunca grava
mensagem de erro, corpo, parâmetros, prompt, resposta ou chave.
Só funciona depois de ``ativar()`` (chamado ao abrir o app): os testes não escrevem no log real.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

MAX_BYTES = 100_000
COPIAS = 1
_logger = logging.getLogger("power_request.falhas")
_logger.propagate = False
_logger.addHandler(logging.NullHandler())


class _ArquivoPrivado(RotatingFileHandler):
    """Todo arquivo do log, inclusive o criado na rotação, fica com 600."""

    def _open(self):
        os.close(os.open(self.baseFilename, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600))
        os.chmod(self.baseFilename, 0o600)
        return super()._open()

    def handleError(self, record):  # disco cheio etc.: o log nunca derruba nem polui o app
        pass


def desativar() -> None:
    for h in list(_logger.handlers):
        if isinstance(h, _ArquivoPrivado):
            _logger.removeHandler(h)
            h.close()


def ativar(pasta: Optional[Path] = None) -> bool:
    destino = pasta or Path.home() / ".power_request"
    desativar()
    try:
        destino.mkdir(mode=0o700, parents=True, exist_ok=True)
        if pasta is None:
            os.chmod(destino, 0o700)
        arquivo = destino / "power_request.log"
        handler = _ArquivoPrivado(arquivo, maxBytes=MAX_BYTES, backupCount=COPIAS, encoding="utf-8")
        antigo = Path(f"{arquivo}.1")
        if antigo.exists():
            os.chmod(antigo, 0o600)
    except OSError:
        return False
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    return True


def _limpo(valor: object) -> str:
    return "".join(c for c in str(valor) if c.isalnum() or c in "_-/{}.")[:80] or "-"


def registrar_falha(metodo: str, rota: str, codigo: object, tipo: str) -> None:
    _logger.info(
        "metodo=%s rota=%s codigo=%s tipo=%s",
        _limpo(metodo), _limpo(rota), _limpo(codigo), _limpo(tipo),
    )
