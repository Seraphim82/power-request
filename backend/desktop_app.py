"""Inicializador unificado do Power Request (sobe servidor local e abre o app)."""

from __future__ import annotations

import socket
import threading
import time
import urllib.request
import webbrowser

import uvicorn

import registro_local
from main import app


def find_free_port(preferred: int = 8765) -> int:
    """Usa a porta preferencial se estiver livre, ou escolhe uma porta local disponível."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_for_server(url: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def main() -> None:
    port = find_free_port(8765)
    app.state.porta = port  # a proteção de origem aceita só a porta em uso
    app.state.origens_dev = False  # no uso normal, a porta 5173 não é de confiança
    registro_local.ativar()
    url = f"http://127.0.0.1:{port}"

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    if wait_for_server(url):
        webbrowser.open(url)

    try:
        while thread.is_alive():
            thread.join(timeout=0.5)
    except KeyboardInterrupt:
        server.should_exit = True


if __name__ == "__main__":
    main()
