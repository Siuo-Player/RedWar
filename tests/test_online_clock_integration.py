from __future__ import annotations

import asyncio
import json
import time
import pytest
import websockets

from engine.game_modes import TimeControl
from engine.pieces import Bone
from online.client.multiplayer_main import formatar_segundos
from online.network.client import NetworkClient
from online.server import app
from online.server.room import GameRoom



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


def test_clock_single_deduction_between_tick_and_action():
    """Verify that elapsed time is deducted only once per interval, eliminating double deduction."""
    room = GameRoom(room_id="ROOM_SINGLE_DEDUCT", time_control=TimeControl(initial_seconds=60.0, increment_seconds=0.0))
    room.session.state.board[6][0] = Bone("brancas")
    room.session.state.board[1][0] = Bone("pretas")
    room.add_player("alice", "brancas")
    room.add_player("bob", "pretas")
    room.start_game()

    initial_time = room.clock.white_time
    assert initial_time == 60.0

    # 1. Simulate 2.0s passing, ticked via background loop (room.tick_clock(2.0))
    room.tick_clock(2.0)
    assert room.clock.white_time == pytest.approx(58.0)

    # 2. Simulate another 1.5s passing before Alice submits her move.
    # Without fix, apply_action would deduct 3.5s (2.0 + 1.5), totaling 5.5s lost!
    # With fix, apply_action only deducts the residual 1.5s, totaling exactly 3.5s lost!
    room.last_move_timestamp = time.monotonic() - 1.5
    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    room.apply_action("alice", action)

    # Total elapsed was 2.0s + 1.5s = 3.5s. Alice's remaining time must be 56.5s!
    assert room.clock.white_time == pytest.approx(56.5)


def test_clock_tick_loop_no_argument_uses_room_timestamp():
    """Verify tick_clock() with no arguments deducts elapsed time based on room timestamp."""
    room = GameRoom(room_id="ROOM_NO_ARG_TICK", time_control=TimeControl(initial_seconds=60.0, increment_seconds=0.0))
    room.add_player("alice", "brancas")
    room.add_player("bob", "pretas")
    room.start_game()

    # Simulate 1.0s elapsed since game started
    room.last_move_timestamp = time.monotonic() - 1.0
    room.tick_clock()

    assert room.clock.white_time == pytest.approx(59.0, abs=0.05)


def test_clock_single_deduction_with_increment():
    """Verify single deduction behavior with time control increments."""
    room = GameRoom(room_id="ROOM_INCREMENT", time_control=TimeControl(initial_seconds=60.0, increment_seconds=2.0))
    room.session.state.board[6][0] = Bone("brancas")
    room.session.state.board[1][0] = Bone("pretas")
    room.add_player("alice", "brancas")
    room.add_player("bob", "pretas")
    room.start_game()

    # 3.0s elapsed via ticks
    room.tick_clock(3.0)
    assert room.clock.white_time == pytest.approx(57.0)

    # 1.0s residual before move
    room.last_move_timestamp = time.monotonic() - 1.0
    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    room.apply_action("alice", action)

    # Total time: 60.0 - 3.0 - 1.0 + 2.0 (increment) = 58.0s
    assert room.clock.white_time == pytest.approx(58.0)

