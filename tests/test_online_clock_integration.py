from __future__ import annotations

import asyncio
import json
import pytest
import websockets

from online.client.multiplayer_main import formatar_segundos
from online.network.client import NetworkClient
from online.server import app


def test_formatar_segundos():
    assert formatar_segundos(600) == "10:00"
    assert formatar_segundos(182) == "03:02"
    assert formatar_segundos(5) == "00:05"
    assert formatar_segundos(0) == "00:00"
    assert formatar_segundos(-3) == "00:00"


def test_network_client_receives_room_and_clock():
    asyncio.run(_test_network_client_receives_room_and_clock())


async def _test_network_client_receives_room_and_clock():
    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    client1 = NetworkClient(host="127.0.0.1", port=port, room_id="TEST_CLOCK_ROOM", player_id="p1")
    client2 = NetworkClient(host="127.0.0.1", port=port, room_id="TEST_CLOCK_ROOM", player_id="p2")

    try:
        # Wait until both connected and assigned roles
        for _ in range(50):
            if client1.cor_atribuida and client2.cor_atribuida:
                break
            await asyncio.sleep(0.05)

        assert client1.cor_atribuida in ("brancas", "pretas")
        assert client2.cor_atribuida in ("brancas", "pretas")
        assert client1.cor_atribuida != client2.cor_atribuida

        # Wait for start_game and initial room state
        for _ in range(50):
            if client1.latest_room and client1.latest_clock:
                break
            await asyncio.sleep(0.05)

        assert client1.latest_room is not None
        assert client1.latest_clock is not None
        assert client1.latest_clock["white_time"] > 0
        assert client1.latest_clock["black_time"] > 0
    finally:
        client1.fechar()
        client2.fechar()
        server.close()
        await server.wait_closed()
