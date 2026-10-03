import asyncio

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


async def _exercise_authoritative_protocol() -> None:
    app.jogadores.clear()
    app.prontos.clear()
    app.sessao = None

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    clients = []
    try:
        port = server.sockets[0].getsockname()[1]
        branca = NetworkClient(host="127.0.0.1", port=port)
        preta = NetworkClient(host="127.0.0.1", port=port)
        clients.extend([branca, preta])

        await _wait_until(
            lambda: (
                branca.cor_atribuida == "brancas"
                and preta.cor_atribuida == "pretas"
                and branca.latest_state is not None
                and preta.latest_state is not None
            )
        )

        initial_state = branca.latest_state
        assert initial_state["white_to_move"] is True
        assert len(initial_state["board"]) == 8
        assert len(initial_state["board"][0]) == 8
        assert preta.latest_state == initial_state

        # A fixture with one legal piece for each side makes the protocol test
        # independent from future matchmaking/draft initialization.
        app.sessao.state.board[6][0] = Bone("brancas")
        app.sessao.state.board[1][0] = Bone("pretas")
        app.sessao.state.board[1][1] = Bone("pretas")
        await app._broadcast(app._mensagem_estado())

        await _wait_until(
            lambda: (
                branca.latest_state
                and branca.latest_state["board"][6][0]["team"] == "brancas"
                and preta.latest_state["board"][1][0]["team"] == "pretas"
            )
        )

        # The black client cannot play while white is the active side.
        preta.latest_error = None
        before = app.sessao.state.to_rwen()
        preta.enviar_acao((6, 0), (5, 0), action_type="move")
        await _wait_until(lambda: preta.latest_error is not None)
        assert "non-active player" in preta.latest_error
        assert app.sessao.state.to_rwen() == before

        # A legal-looking movement to an occupied square is rejected by the
        # authoritative legal-action resolver.
        branca.latest_error = None
        branca.enviar_acao((6, 0), (1, 0), action_type="move")
        await _wait_until(lambda: branca.latest_error is not None)
        assert "occupied" in branca.latest_error
        assert app.sessao.state.to_rwen() == before

        # The real NetworkClient protocol now reaches the authoritative
        # GameState and both clients receive the resulting state.
        branca.latest_error = None
        branca.enviar_acao((6, 0), (5, 0), action_type="move")
        await _wait_until(
            lambda: (
                branca.latest_state
                and preta.latest_state
                and branca.latest_state["white_to_move"] is False
                and preta.latest_state["white_to_move"] is False
                and branca.latest_state["board"][5][0]["team"] == "brancas"
                and branca.latest_state["board"][6][0] is None
                and preta.latest_state == branca.latest_state
            )
        )
        assert app.sessao.state.board[5][0].team == "brancas"
        assert app.sessao.state.board[6][0] is None
    finally:
        for client in clients:
            client.fechar()
        await asyncio.sleep(0.05)
        server.close()
        await server.wait_closed()
        app.jogadores.clear()
        app.prontos.clear()
        app.sessao = None


def test_websockets_17_server_handler_and_authoritative_client_protocol():
    asyncio.run(_exercise_authoritative_protocol())
