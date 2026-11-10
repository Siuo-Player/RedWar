from __future__ import annotations

import asyncio
import json
from pathlib import Path
import pytest
import websockets

from engine.ratings import LeaderboardManager
from online.server import app
from online.server.room import RoomManager


async def _recv_type(ws, expected_type, timeout=3.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        remaining = max(0.01, deadline - asyncio.get_running_loop().time())
        try:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=remaining))
            if msg.get("tipo") == expected_type:
                return msg
        except asyncio.TimeoutError:
            break
    raise AssertionError(f"Expected message type '{expected_type}' was not received within timeout")


@pytest.mark.anyio
async def test_full_web_multiplayer_e2e_lifecycle(tmp_path: Path):
    """Verify Section 1 & Section 3: End-to-end WebSocket multiplayer handshake, move, and ELO scoring."""
    db_file = tmp_path / "e2e_ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    app.manager = RoomManager(leaderboard_manager=lb)

    server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    url = f"ws://127.0.0.1:{port}"

    try:
        # 1. Alice connects and joins room
        alice_ws = await websockets.connect(url)
        _ = await alice_ws.recv()  # legacy setup greeting

        await alice_ws.send(json.dumps({
            "tipo": "join_room",
            "room_id": "ROOM_E2E_MATCH",
            "player_id": "alice",
            "role_preference": "brancas",
            "time_control": "rapid_10_0",
            "mode": "standard_8x8",
        }))
        alice_joined = json.loads(await alice_ws.recv())
        assert alice_joined["tipo"] == "room_joined"
        assert alice_joined["cor"] == "brancas"
        alice_token = alice_joined["reconnect_token"]
        assert alice_token is not None

        # 2. Bob connects and joins room
        bob_ws = await websockets.connect(url)
        _ = await bob_ws.recv()  # legacy setup greeting

        await bob_ws.send(json.dumps({
            "tipo": "join_room",
            "room_id": "ROOM_E2E_MATCH",
            "player_id": "bob",
            "role_preference": "pretas",
            "time_control": "rapid_10_0",
            "mode": "standard_8x8",
        }))
        bob_joined = json.loads(await bob_ws.recv())
        assert bob_joined["tipo"] == "room_joined"
        assert bob_joined["cor"] == "pretas"
        bob_token = bob_joined["reconnect_token"]
        assert bob_token is not None

        # 3. Both send ready handshake
        await alice_ws.send(json.dumps({"tipo": "pronto"}))
        await bob_ws.send(json.dumps({"tipo": "pronto"}))

        # 4. Both receive start_game and initial populated board
        alice_start = await _recv_type(alice_ws, "start_game")
        bob_start = await _recv_type(bob_ws, "start_game")
        assert alice_start["tipo"] == "start_game"
        assert bob_start["tipo"] == "start_game"

        alice_state = await _recv_type(alice_ws, "estado_jogo")
        bob_state = await _recv_type(bob_ws, "estado_jogo")
        assert alice_state["dados"]["white_to_move"] is True
        assert bob_state["dados"]["white_to_move"] is True

        # Invariant: Initial board must NOT be empty (contains standard Dragoon, Bones, etc.)
        board = alice_state["dados"]["board"]
        assert board[7][0]["name"] == "Dragoon"
        assert board[7][0]["team"] == "brancas"
        assert board[6][0]["name"] == "Bone"
        assert board[0][0]["name"] == "Dragoon"
        assert board[0][0]["team"] == "pretas"

        # 5. Alice makes a legal opening move (Bone from (6, 0) to (5, 0))
        await alice_ws.send(json.dumps({
            "tipo": "acao",
            "type": "move",
            "start": [6, 0],
            "end": [5, 0],
        }))

        # Both receive updated estado_jogo with the piece moved
        alice_move_state = await _recv_type(alice_ws, "estado_jogo")
        bob_move_state = await _recv_type(bob_ws, "estado_jogo")
        assert alice_move_state["dados"]["board"][6][0] is None
        assert alice_move_state["dados"]["board"][5][0]["name"] == "Bone"
        assert alice_move_state["dados"]["white_to_move"] is False
        assert bob_move_state["dados"]["board"][5][0]["name"] == "Bone"
        assert bob_move_state["dados"]["white_to_move"] is False

        # 6. Bob resigns
        await bob_ws.send(json.dumps({"tipo": "resign"}))
        game_over_alice = await _recv_type(alice_ws, "game_over")
        assert game_over_alice["reason"] == "resignation"
        assert game_over_alice["room"]["winner"] == "brancas"
        assert game_over_alice["room"]["is_finished"] is True

        # 7. Verify ELO scoring
        alice_prof = lb.get_profile("alice")
        bob_prof = lb.get_profile("bob")
        assert alice_prof.stats["standard_8x8"]["wins"] == 1
        assert alice_prof.get_rating("standard_8x8") > 1200
        assert bob_prof.stats["standard_8x8"]["losses"] == 1
        assert bob_prof.get_rating("standard_8x8") < 1200

        # 8. Test reconnection with cryptographic token
        await bob_ws.close()
        bob_reconnect_ws = await websockets.connect(url)
        _ = await bob_reconnect_ws.recv()  # greeting

        await bob_reconnect_ws.send(json.dumps({
            "tipo": "reconnect",
            "room_id": "ROOM_E2E_MATCH",
            "token": bob_token,
        }))
        reconnect_msg = await _recv_type(bob_reconnect_ws, "reconnect_success")
        assert reconnect_msg["cor"] == "pretas"
        assert reconnect_msg["player_id"] == "bob"

        await alice_ws.close()
        await bob_reconnect_ws.close()

    finally:
        server.close()
        await server.wait_closed()


def test_responsive_css_selectors_match_html():
    """Verify Section 3: CSS media queries match actual HTML element IDs and classes."""
    css_path = Path("deploy/web/styles.css")
    css_content = css_path.read_text(encoding="utf-8")

    # Mismatched legacy selectors must NOT appear in responsive rules
    assert ".app-container" not in css_content
    assert "#gameCanvas" not in css_content
    assert ".nav-tabs" not in css_content

    # Canonical HTML tags and classes must be present
    assert "main {" in css_content or "main," in css_content or "main\n" in css_content
    assert "#gameBoard" in css_content
    assert ".board-container" in css_content
    assert ".nav-links" in css_content
