import asyncio
import json

import websockets

from online.server import app


async def _exercise_server() -> None:
    app.jogadores.clear()
    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    try:
        port = server.sockets[0].getsockname()[1]
        async with websockets.connect(f"ws://127.0.0.1:{port}") as websocket:
            setup = json.loads(await asyncio.wait_for(websocket.recv(), timeout=2))
            assert setup == {"tipo": "setup", "cor": "brancas"}
            await websocket.send(json.dumps({"tipo": "acao_agnostica", "acao": "MOVE A2 A4"}))
    finally:
        server.close()
        await server.wait_closed()
        app.jogadores.clear()


def test_websockets_17_server_handler_and_client_handshake():
    asyncio.run(_exercise_server())
