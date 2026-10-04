import asyncio
import json

import websockets

from engine.pieces import Bone
from online.network.client import NetworkClient
from online.server import app


async def _wait_until(predicate, timeout=3.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition was not reached before timeout")


async def _recv_type(websocket, expected_type, timeout=3.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        remaining = max(0.01, deadline - asyncio.get_running_loop().time())
        message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=remaining))
        if message.get("tipo") == expected_type:
            return message
    raise AssertionError(f"message type {expected_type!r} was not received")


async def _exercise_authoritative_protocol() -> None:
    app.jogadores.clear()
    app.prontos.clear()
    app.sessao = None

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    branca = NetworkClient(host="127.0.0.1", port=server.sockets[0].getsockname()[1])
    preta = None

    try:
        await _wait_until(lambda: branca.cor_atribuida == "brancas")

        preta = await websockets.connect(
            f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        )
        setup = json.loads(await asyncio.wait_for(preta.recv(), timeout=2))
        assert setup == {"tipo": "setup", "cor": "pretas"}

        await preta.send(json.dumps({"tipo": "pronto"}))

        start = await _recv_type(preta, "start_game")
        assert start == {"tipo": "start_game"}

        initial = await _recv_type(preta, "estado_jogo")
        assert initial["dados"]["white_to_move"] is True
        assert len(initial["dados"]["board"]) == 8
        assert len(initial["dados"]["board"][0]) == 8

        await _wait_until(
            lambda: (
                isinstance(branca.latest_state, dict)
                and branca.latest_state["white_to_move"] is True
            )
        )
        assert branca.latest_state == initial["dados"]

        app.sessao.state.board[6][0] = Bone("brancas")
        app.sessao.state.board[1][0] = Bone("pretas")
        app.sessao.state.board[1][1] = Bone("pretas")
        await app._broadcast(app._mensagem_estado())

        fixture_state = await _recv_type(preta, "estado_jogo")
        await _wait_until(
            lambda: (
                isinstance(branca.latest_state, dict)
                and isinstance(branca.latest_state["board"][6][0], dict)
                and branca.latest_state["board"][6][0]["team"] == "brancas"
                and isinstance(branca.latest_state["board"][1][0], dict)
                and branca.latest_state["board"][1][0]["team"] == "pretas"
            )
        )
        assert fixture_state["dados"] == branca.latest_state

        before = app.sessao.state.to_rwen()
        await preta.send(
            json.dumps(
                {
                    "tipo": "acao",
                    "type": "move",
                    "start": [6, 0],
                    "end": [5, 0],
                }
            )
        )
        black_error = await _recv_type(preta, "erro")
        assert "non-active player" in black_error["mensagem"]
        assert app.sessao.state.to_rwen() == before

        branca.latest_error = None
        branca.enviar_acao((6, 0), (1, 0), action_type="move")
        await _wait_until(
            lambda: (
                branca.latest_error is not None
                and "occupied" in branca.latest_error
            )
        )
        assert app.sessao.state.to_rwen() == before

        branca.latest_error = None
        branca.enviar_acao((6, 0), (5, 0), action_type="move")
        updated = await _recv_type(preta, "estado_jogo")
        await _wait_until(
            lambda: (
                isinstance(branca.latest_state, dict)
                and branca.latest_state["white_to_move"] is False
                and branca.latest_state["board"][5][0]["team"] == "brancas"
                and branca.latest_state["board"][6][0] is None
            )
        )

        assert updated["dados"] == branca.latest_state
        assert app.sessao.state.board[5][0].team == "brancas"
        assert app.sessao.state.board[6][0] is None
    finally:
        if preta is not None:
            await preta.close()
        branca.fechar()
        await asyncio.sleep(0.05)
        server.close()
        await server.wait_closed()
        app.jogadores.clear()
        app.prontos.clear()
        app.sessao = None


def test_websockets_17_server_handler_and_authoritative_client_protocol():
    asyncio.run(_exercise_authoritative_protocol())
