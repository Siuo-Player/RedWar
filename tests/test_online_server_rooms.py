from __future__ import annotations

import asyncio
import json
from pathlib import Path
import pytest
import websockets

from engine.pieces import Bone
from engine.ratings import LeaderboardManager
from online.server import app
from online.server.room import GameRoom, RoomManager


async def _recv_until_type(ws, target_type: str, timeout: float = 3.0) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        remaining = max(0.01, deadline - asyncio.get_running_loop().time())
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=remaining))
        if msg.get("tipo") == target_type:
            return msg
    raise TimeoutError(f"Did not receive message of type {target_type}")


def test_legacy_connection_flow():
    asyncio.run(_test_legacy_connection_flow())


async def _test_legacy_connection_flow():
    app.jogadores.clear()
    app.prontos.clear()
    app.sessao = None

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    ws_white = await websockets.connect(f"ws://127.0.0.1:{port}")
    setup_w = json.loads(await ws_white.recv())
    assert setup_w == {"tipo": "setup", "cor": "brancas"}

    ws_black = await websockets.connect(f"ws://127.0.0.1:{port}")
    setup_b = json.loads(await ws_black.recv())
    assert setup_b == {"tipo": "setup", "cor": "pretas"}

    await ws_white.send(json.dumps({"tipo": "pronto"}))
    await ws_black.send(json.dumps({"tipo": "pronto"}))

    start_w = await _recv_until_type(ws_white, "start_game")
    assert start_w["tipo"] == "start_game"

    state_w = await _recv_until_type(ws_white, "estado_jogo")
    assert state_w["dados"]["white_to_move"] is True

    await ws_white.close()
    await ws_black.close()
    server.close()
    await server.wait_closed()


def test_room_join_and_isolated_match(tmp_path: Path):
    asyncio.run(_test_room_join_and_isolated_match(tmp_path))


async def _test_room_join_and_isolated_match(tmp_path: Path):
    db_file = tmp_path / "ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    app.manager = RoomManager(leaderboard_manager=lb)

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    # Alice joins room "ROOM_A" as White
    ws_alice = await websockets.connect(f"ws://127.0.0.1:{port}")
    await ws_alice.send(json.dumps({
        "tipo": "join_room",
        "room_id": "ROOM_A",
        "player_id": "Alice",
        "time_control": "blitz_3_2"
    }))
    joined_a = await _recv_until_type(ws_alice, "room_joined")
    assert joined_a["cor"] == "brancas"
    assert joined_a["room_id"] == "ROOM_A"

    # Bob joins room "ROOM_A" as Black
    ws_bob = await websockets.connect(f"ws://127.0.0.1:{port}")
    await ws_bob.send(json.dumps({
        "tipo": "join_room",
        "room_id": "ROOM_A",
        "player_id": "Bob"
    }))
    joined_b = await _recv_until_type(ws_bob, "room_joined")
    assert joined_b["cor"] == "pretas"

    # Both ready up
    await ws_alice.send(json.dumps({"tipo": "pronto"}))
    await ws_bob.send(json.dumps({"tipo": "pronto"}))

    start_a = await _recv_until_type(ws_alice, "start_game")
    assert start_a["tipo"] == "start_game"

    room = app.manager.get_room("ROOM_A")
    assert room is not None
    assert room.is_started

    # Charlie connects as spectator to ROOM_A
    ws_charlie = await websockets.connect(f"ws://127.0.0.1:{port}")
    await ws_charlie.send(json.dumps({
        "tipo": "join_room",
        "room_id": "ROOM_A",
        "player_id": "Charlie",
        "role_preference": "espetador"
    }))
    joined_c = await _recv_until_type(ws_charlie, "room_joined")
    assert joined_c["cor"] == "espetador"

    # Place test pieces
    room.session.state.board[6][0] = Bone("brancas")
    room.session.state.board[1][0] = Bone("pretas")

    # Alice moves
    await ws_alice.send(json.dumps({
        "tipo": "acao",
        "type": "move",
        "start": (6, 0),
        "end": (5, 0)
    }))

    # Charlie receives update
    update_c = await _recv_until_type(ws_charlie, "estado_jogo")
    assert update_c["dados"]["white_to_move"] is False

    await ws_alice.close()
    await ws_bob.close()
    await ws_charlie.close()
    server.close()
    await server.wait_closed()
