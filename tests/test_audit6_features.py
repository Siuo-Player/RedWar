# tests/test_audit6_features.py
"""Comprehensive verification of RedWar Audit 6 requirements:
1. Late-joining spectator receives immediate authoritative game state and board.
2. Reconnection closes and invalidates the previous active WebSocket session.
3. Disconnected spectators are removed from room tracking without resource leaks.
4. Full multiplayer move history and action synchronization in AuthoritativeSession.
5. Authoritative state payload preserves tile effects, lifespan, and cooldowns.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import time
import pytest
import websockets

from engine.game_state import GameState
from engine.pieces import Bone, FrostMage, Geomancer, Lich
from engine.ratings import LeaderboardManager
from online.server import app
from online.server.authority import AuthoritativeSession
from online.server.room import RoomManager


async def _recv_until_type(ws, target_type: str, timeout: float = 3.0) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout - (time.time() - start))
            data = json.loads(msg)
            if data.get("tipo") == target_type:
                return data
        except asyncio.TimeoutError:
            break
    raise AssertionError(f"Timeout waiting for message tipo='{target_type}'")


def test_authority_move_history_and_state_payload():
    """Verify AuthoritativeSession records move_history and actions_history."""
    state = GameState()
    state.board[6][0] = Bone("brancas")
    state.board[1][0] = Bone("pretas")
    session = AuthoritativeSession(state)

    assert session.move_history == []
    assert session.actions_history == []
    assert session.last_move is None

    # White moves
    session.apply_action("brancas", {"type": "move", "start": (6, 0), "end": (5, 0)})
    assert len(session.move_history) == 1
    assert len(session.actions_history) == 1
    assert "a2-a3" in session.move_history[0].lower()
    assert session.last_action == {"start": (6, 0), "end": (5, 0), "type": "move", "spell_name": None, "spawn_name": None}

    # Black moves
    session.apply_action("pretas", {"type": "move", "start": (1, 0), "end": (2, 0)})
    assert len(session.move_history) == 2
    assert len(session.actions_history) == 2

    payload = session.state_payload()
    assert payload["move_history"] == session.move_history
    assert payload["actions_history"] == session.actions_history
    assert payload["last_move"] == session.last_move
    assert payload["last_action"] == session.last_action


def test_tile_effects_and_lifespan_in_state_payload():
    """Verify state_payload accurately captures tile_effects and piece lifespan."""
    state = GameState()
    state.board[6][2] = FrostMage("brancas")
    state.board[4][2] = Bone("pretas")
    session = AuthoritativeSession(state)

    # FrostMage casts Nevada
    session.apply_action("brancas", {"type": "spell", "start": (6, 2), "end": (4, 2), "spell_name": "nevada"})
    payload = session.state_payload()

    # Ice tile effect should be present
    assert payload["tile_effects"][4][2] is not None
    assert payload["tile_effects"][4][2]["type"] == "ice"

    # Bone at (4,2) was stunned
    assert payload["board"][4][2]["stun_timer"] >= 1

    # Now test Geomancer barricade creates StoneWall with lifespan
    state2 = GameState()
    state2.board[6][4] = Geomancer("brancas")
    session2 = AuthoritativeSession(state2)
    session2.apply_action("brancas", {"type": "spell", "start": (6, 4), "end": (5, 4), "spell_name": "barricade"})
    payload2 = session2.state_payload()
    wall = payload2["board"][5][4]
    assert wall is not None
    assert wall["name"] == "StoneWall"
    assert wall["lifespan"] == 3


def test_spectator_late_join_receives_immediate_board_state(tmp_path: Path):
    """Verify that a late-joining spectator immediately receives the active game state."""
    asyncio.run(_test_spectator_late_join_receives_immediate_board_state(tmp_path))


async def _test_spectator_late_join_receives_immediate_board_state(tmp_path: Path):
    db_file = tmp_path / "ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    app.manager = RoomManager(leaderboard_manager=lb)

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    try:
        # White joins
        ws_white = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws_white.send(json.dumps({"tipo": "join_room", "room_id": "LATE_JOIN_ROOM", "player_id": "P_White"}))
        await _recv_until_type(ws_white, "room_joined")

        # Black joins
        ws_black = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws_black.send(json.dumps({"tipo": "join_room", "room_id": "LATE_JOIN_ROOM", "player_id": "P_Black"}))
        await _recv_until_type(ws_black, "room_joined")

        # Both ready
        await ws_white.send(json.dumps({"tipo": "pronto"}))
        await ws_black.send(json.dumps({"tipo": "pronto"}))
        await _recv_until_type(ws_white, "start_game")

        room = app.manager.get_room("LATE_JOIN_ROOM")
        assert room.is_started

        # White makes a move
        room.session.state.board[6][0] = Bone("brancas")
        room.session.state.board[1][0] = Bone("pretas")
        await ws_white.send(json.dumps({"tipo": "acao", "type": "move", "start": (6, 0), "end": (5, 0)}))
        await _recv_until_type(ws_white, "estado_jogo")

        # Now spectator joins late into in-progress game
        ws_spec = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws_spec.send(json.dumps({
            "tipo": "join_room",
            "room_id": "LATE_JOIN_ROOM",
            "player_id": "Spectator_Bob",
            "role_preference": "espetador"
        }))

        # 1. room_joined payload must contain non-null estado_jogo
        joined = await _recv_until_type(ws_spec, "room_joined")
        assert joined["cor"] == "espetador"
        assert joined["estado_jogo"] is not None
        assert joined["estado_jogo"]["white_to_move"] is False

        # 2. Spectator immediately receives direct estado_jogo message
        state_msg = await _recv_until_type(ws_spec, "estado_jogo")
        assert state_msg["dados"]["white_to_move"] is False
        assert state_msg["dados"]["board"][5][0]["name"] == "Bone"

        await ws_white.close()
        await ws_black.close()
        await ws_spec.close()
    finally:
        server.close()
        await server.wait_closed()


def test_reconnect_closes_and_invalidates_old_websocket(tmp_path: Path):
    """Verify that reconnect closes previous WebSocket and updates authority to new socket."""
    asyncio.run(_test_reconnect_closes_and_invalidates_old_websocket(tmp_path))


async def _test_reconnect_closes_and_invalidates_old_websocket(tmp_path: Path):
    db_file = tmp_path / "ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    app.manager = RoomManager(leaderboard_manager=lb)

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    try:
        # White joins on socket 1
        ws1_white = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws1_white.send(json.dumps({"tipo": "join_room", "room_id": "RECON_ROOM", "player_id": "Alice"}))
        joined = await _recv_until_type(ws1_white, "room_joined")
        token = joined["reconnect_token"]
        assert token is not None

        # Black joins
        ws_black = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws_black.send(json.dumps({"tipo": "join_room", "room_id": "RECON_ROOM", "player_id": "Bob"}))
        await _recv_until_type(ws_black, "room_joined")

        # Ready up
        await ws1_white.send(json.dumps({"tipo": "pronto"}))
        await ws_black.send(json.dumps({"tipo": "pronto"}))
        await _recv_until_type(ws1_white, "start_game")

        # Alice reconnects via new socket 2
        ws2_white = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws2_white.send(json.dumps({
            "tipo": "reconnect",
            "room_id": "RECON_ROOM",
            "token": token
        }))

        recon_success = await _recv_until_type(ws2_white, "reconnect_success")
        assert recon_success["cor"] == "brancas"
        assert recon_success["player_id"] == "Alice"

        # Verify old socket 1 is closed
        with pytest.raises(websockets.exceptions.ConnectionClosed):
            while True:
                await asyncio.wait_for(ws1_white.recv(), timeout=2.0)
        assert ws1_white.close_code is not None

        await ws2_white.close()
        await ws_black.close()
    finally:
        server.close()
        await server.wait_closed()


def test_disconnected_spectator_cleaned_up(tmp_path: Path):
    """Verify that a disconnected spectator is removed from room.spectators."""
    asyncio.run(_test_disconnected_spectator_cleaned_up(tmp_path))


async def _test_disconnected_spectator_cleaned_up(tmp_path: Path):
    db_file = tmp_path / "ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    app.manager = RoomManager(leaderboard_manager=lb)

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    try:
        room_id = "SPEC_CLEAN_ROOM"
        ws_spec = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws_spec.send(json.dumps({
            "tipo": "join_room",
            "room_id": room_id,
            "player_id": "Spec_Dave",
            "role_preference": "espetador"
        }))
        await _recv_until_type(ws_spec, "room_joined")

        room = app.manager.get_room(room_id)
        assert room is not None
        assert "Spec_Dave" in room.spectators
        assert room.spectator_count == 1

        # Spectator disconnects
        await ws_spec.close()
        await asyncio.sleep(0.1)

        assert "Spec_Dave" not in room.spectators
        assert room.spectator_count == 0
    finally:
        server.close()
        await server.wait_closed()
