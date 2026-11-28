"""Limite do corpo realmente recebido: vale mesmo quando o pedido não informa o tamanho."""

from __future__ import annotations

from starlette.responses import JSONResponse


class LimiteDoCorpo:
    """Lê o corpo em partes, para ao passar do limite e só então entrega o pedido ao app."""

    def __init__(self, app, limite: int) -> None:
        self.app = app
        self.limite = limite

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        corpo = bytearray()
        while True:
            mensagem = await receive()
            if mensagem["type"] != "http.request":
                return  # quem chamou desistiu antes de terminar de enviar
            corpo += mensagem.get("body", b"")
            if len(corpo) > self.limite:
                resposta = JSONResponse(status_code=413, content={"detail": "Requisição grande demais."})
                await resposta(scope, receive, send)
                return
            if not mensagem.get("more_body", False):
                break
        entregue = False

        async def repetir():
            nonlocal entregue
            if not entregue:
                entregue = True
                return {"type": "http.request", "body": bytes(corpo), "more_body": False}
            return await receive()

        await self.app(scope, repetir, send)
