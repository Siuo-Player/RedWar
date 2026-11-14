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


def test_full_web_multiplayer_e2e_lifecycle(tmp_path: Path):
    """Verify Section 1 & Section 3: End-to-end WebSocket multiplayer handshake, move, and ELO scoring."""
    async def _run():
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

    asyncio.run(_run())


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


def test_room_manager_cleanup_preserves_finished_rooms_during_rematch():
    """Verify that cleanup_stale_rooms retains finished rooms during rematch window

    and does not prune rooms when subsequent create_room() calls are made.
    """
    rm = RoomManager()
    room = rm.create_room("ROOM_FINISHED_GRACE")
    room.white_player = "alice"
    room.black_player = "bob"
    room.start_game()
    room.resign("bob")
    assert room.is_finished is True
    assert room.finished_timestamp is not None

    # 1. Immediate create_room call must NOT prune the just-finished room
    second_room = rm.create_room("ROOM_SECOND")
    second_room.white_player = "charlie"
    assert rm.get_room("ROOM_FINISHED_GRACE") is not None, "Finished room was improperly pruned on create_room!"

    # 2. Cleanup with default grace period (300s) must retain room
    pruned = rm.cleanup_stale_rooms(finished_retention_seconds=300.0)
    assert pruned == 0
    assert rm.get_room("ROOM_FINISHED_GRACE") is not None

    # 3. If a rematch is proposed, room must be preserved even if retention period passes
    room.propose_rematch("alice")
    assert room.rematch_pending is True
    # Simulate finished_timestamp far in the past
    room.finished_timestamp = 1000.0
    pruned_with_pending_rematch = rm.cleanup_stale_rooms(max_idle_seconds=1800.0, finished_retention_seconds=10.0)
    assert pruned_with_pending_rematch == 0
    assert rm.get_room("ROOM_FINISHED_GRACE") is not None

    # 4. If rematch proposals are cleared and retention period has elapsed, room is pruned
    room.rematch_proposals.clear()
    pruned_after_expiry = rm.cleanup_stale_rooms(max_idle_seconds=1800.0, finished_retention_seconds=10.0)
    assert pruned_after_expiry == 1
    assert rm.get_room("ROOM_FINISHED_GRACE") is None


def test_web_multiplayer_rematch_color_swap_e2e(tmp_path: Path):
    """Verify end-to-end rematch flow with seat swapping, token rotation, and move gating."""
    async def _run():
        db_file = tmp_path / "rematch_ratings.json"
        lb = LeaderboardManager(storage_path=str(db_file))
        app.manager = RoomManager(leaderboard_manager=lb)

        server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        url = f"ws://127.0.0.1:{port}"

        try:
            # Game 1: Alice = White, Bob = Black
            alice_ws = await websockets.connect(url)
            _ = await alice_ws.recv()  # greeting
            await alice_ws.send(json.dumps({
                "tipo": "join_room",
                "room_id": "REMATCH_TEST_ROOM",
                "player_id": "alice",
                "role_preference": "brancas",
            }))
            alice_join = json.loads(await alice_ws.recv())
            assert alice_join["cor"] == "brancas"
            alice_token_g1 = alice_join["reconnect_token"]

            bob_ws = await websockets.connect(url)
            _ = await bob_ws.recv()  # greeting
            await bob_ws.send(json.dumps({
                "tipo": "join_room",
                "room_id": "REMATCH_TEST_ROOM",
                "player_id": "bob",
                "role_preference": "pretas",
            }))
            bob_join = json.loads(await bob_ws.recv())
            assert bob_join["cor"] == "pretas"
            bob_token_g1 = bob_join["reconnect_token"]

            await alice_ws.send(json.dumps({"tipo": "pronto"}))
            await bob_ws.send(json.dumps({"tipo": "pronto"}))

            _ = await _recv_type(alice_ws, "start_game")
            _ = await _recv_type(bob_ws, "start_game")
            _ = await _recv_type(alice_ws, "estado_jogo")
            _ = await _recv_type(bob_ws, "estado_jogo")

            # Alice moves, then Bob resigns
            await alice_ws.send(json.dumps({
                "tipo": "acao",
                "type": "move",
                "start": [6, 0],
                "end": [5, 0],
            }))
            _ = await _recv_type(alice_ws, "estado_jogo")
            _ = await _recv_type(bob_ws, "estado_jogo")

            await bob_ws.send(json.dumps({"tipo": "resign"}))
            _ = await _recv_type(alice_ws, "game_over")
            _ = await _recv_type(bob_ws, "game_over")

            # Rematch Phase: Alice proposes rematch
            await alice_ws.send(json.dumps({"tipo": "rematch"}))
            alice_proposal = await _recv_type(alice_ws, "rematch_proposal")
            assert alice_proposal["tipo"] == "rematch_proposal"

            # Bob accepts rematch
            await bob_ws.send(json.dumps({"tipo": "rematch"}))

            # Both receive rematch_update with swapped colors and new tokens!
            alice_rematch = await _recv_type(alice_ws, "rematch_update")
            bob_rematch = await _recv_type(bob_ws, "rematch_update")

            assert alice_rematch["cor"] == "pretas", f"Alice should now be black, got {alice_rematch['cor']}"
            assert bob_rematch["cor"] == "brancas", f"Bob should now be white, got {bob_rematch['cor']}"

            alice_token_g2 = alice_rematch["reconnect_token"]
            bob_token_g2 = bob_rematch["reconnect_token"]

            # Both receive start_game for Game 2
            _ = await _recv_type(alice_ws, "start_game")
            _ = await _recv_type(bob_ws, "start_game")
            alice_g2_state = await _recv_type(alice_ws, "estado_jogo")
            bob_g2_state = await _recv_type(bob_ws, "estado_jogo")

            assert alice_g2_state["dados"]["white_to_move"] is True
            assert bob_g2_state["dados"]["white_to_move"] is True

            # Bob is now White and plays the opening move!
            await bob_ws.send(json.dumps({
                "tipo": "acao",
                "type": "move",
                "start": [6, 0],
                "end": [5, 0],
            }))

            alice_after_bob = await _recv_type(alice_ws, "estado_jogo")
            bob_after_bob = await _recv_type(bob_ws, "estado_jogo")
            assert alice_after_bob["dados"]["white_to_move"] is False
            assert bob_after_bob["dados"]["white_to_move"] is False

            # Alice is now Black and plays response move!
            await alice_ws.send(json.dumps({
                "tipo": "acao",
                "type": "move",
                "start": [1, 0],
                "end": [2, 0],
            }))

            alice_after_alice = await _recv_type(alice_ws, "estado_jogo")
            bob_after_alice = await _recv_type(bob_ws, "estado_jogo")
            assert alice_after_alice["dados"]["white_to_move"] is True
            assert bob_after_alice["dados"]["white_to_move"] is True

            # Alice resigns Game 2
            await alice_ws.send(json.dumps({"tipo": "resign"}))
            _ = await _recv_type(alice_ws, "game_over")
            _ = await _recv_type(bob_ws, "game_over")

            # Check leaderboard: 1 win and 1 loss for each
            alice_prof = lb.get_profile("alice")
            bob_prof = lb.get_profile("bob")
            assert alice_prof.stats["standard_8x8"]["wins"] == 1
            assert alice_prof.stats["standard_8x8"]["losses"] == 1
            assert bob_prof.stats["standard_8x8"]["wins"] == 1
            assert bob_prof.stats["standard_8x8"]["losses"] == 1

            # Test reconnection in Game 2 with new tokens
            await alice_ws.close()
            alice_rec_ws = await websockets.connect(url)
            _ = await alice_rec_ws.recv()
            await alice_rec_ws.send(json.dumps({
                "tipo": "reconnect",
                "room_id": "REMATCH_TEST_ROOM",
                "token": alice_token_g2,
            }))
            rec_msg = await _recv_type(alice_rec_ws, "reconnect_success")
            assert rec_msg["cor"] == "pretas"
            assert rec_msg["player_id"] == "alice"

            await alice_rec_ws.close()
            await bob_ws.close()

        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(_run())


def test_room_manager_all_termination_pathways_and_retention_lifecycle():
    """Systematically verify all 8 termination and retention conditions in RoomManager."""
    import time
    from engine.pieces import criar_peca_por_nome

    rm = RoomManager()

    # 1. Termination Pathway: Resignation
    r_resign = rm.create_room("ROOM_TERM_RESIGN")
    r_resign.white_player = "alice"
    r_resign.black_player = "bob"
    r_resign.start_game()
    r_resign.resign("alice")
    assert r_resign.is_finished is True
    assert r_resign.finished_timestamp is not None
    assert r_resign.winner == "pretas"
    assert r_resign.termination_reason == "resignation"

    # 2. Termination Pathway: Flag Fall
    r_flag = rm.create_room("ROOM_TERM_FLAG")
    r_flag.white_player = "alice"
    r_flag.black_player = "bob"
    r_flag.start_game()
    winner_flag = r_flag.tick_clock(elapsed_seconds=r_flag.clock.white_time + 10.0)
    assert r_flag.is_finished is True
    assert r_flag.finished_timestamp is not None
    assert r_flag.termination_reason == "flag_fall"
    assert r_flag.winner == "pretas"
    assert winner_flag == "pretas"

    # 3. Termination Pathway: Elimination Game Over
    r_elim = rm.create_room("ROOM_TERM_ELIM")
    r_elim.white_player = "alice"
    r_elim.black_player = "bob"
    r_elim.start_game()
    state_elim = r_elim.session.state
    for r in range(len(state_elim.board)):
        for c in range(len(state_elim.board[0])):
            state_elim.board[r][c] = None
    state_elim.board[4][4] = criar_peca_por_nome("Paladin", "brancas")
    state_elim.board[4][5] = criar_peca_por_nome("Bone", "pretas")
    state_elim.board[4][5].stun_timer = 2  # Stunned target -> lethal kill on 2nd hit
    r_elim.apply_action("alice", {
        "type": "attack",
        "start": [4, 4],
        "end": [4, 5],
    })
    assert r_elim.is_finished is True
    assert r_elim.finished_timestamp is not None
    assert r_elim.termination_reason == "elimination"
    assert r_elim.winner == "brancas"

    # 4. Termination Pathway: Turn Limit
    r_turn = rm.create_room("ROOM_TERM_TURN_LIMIT")
    r_turn.white_player = "alice"
    r_turn.black_player = "bob"
    r_turn.start_game()
    state_turn = r_turn.session.state
    state_turn.turns_without_capture = state_turn.max_twc - 1
    r_turn.apply_action("alice", {
        "type": "move",
        "start": [6, 0],
        "end": [5, 0],
    })
    assert r_turn.is_finished is True
    assert r_turn.finished_timestamp is not None
    assert r_turn.termination_reason == "turn_limit"

    # 5. Retention Lifecycle: Active Rematch Proposal retains room beyond 300s grace period
    r_rematch = rm.create_room("ROOM_REMATCH_LIFECYCLE")
    r_rematch.white_player = "alice"
    r_rematch.black_player = "bob"
    r_rematch.start_game()
    r_rematch.resign("bob")
    assert r_rematch.is_finished is True

    r_rematch.propose_rematch("alice")
    assert r_rematch.rematch_pending is True
    r_rematch.finished_timestamp = time.time() - 600.0
    r_rematch.last_activity_timestamp = time.time() - 100.0

    pruned = rm.cleanup_stale_rooms(finished_retention_seconds=300.0, max_idle_seconds=1800.0)
    assert rm.get_room("ROOM_REMATCH_LIFECYCLE") is not None, "Room with pending rematch proposal must NOT be pruned"

    # 6. Retention Lifecycle: Abandoned rematch proposal pruned after max_idle_seconds
    r_rematch.last_activity_timestamp = time.time() - 2000.0  # idle > 1800.0
    pruned_abandoned = rm.cleanup_stale_rooms(finished_retention_seconds=300.0, max_idle_seconds=1800.0)
    assert rm.get_room("ROOM_REMATCH_LIFECYCLE") is None, "Abandoned rematch past max_idle_seconds must be pruned"

    # 7. Rematch Acceptance: Resets is_finished=False and finished_timestamp=None
    r_accept = rm.create_room("ROOM_REMATCH_ACCEPT")
    r_accept.white_player = "alice"
    r_accept.black_player = "bob"
    r_accept.start_game()
    r_accept.resign("bob")
    assert r_accept.is_finished is True
    assert r_accept.finished_timestamp is not None

    r_accept.propose_rematch("alice")
    accepted = r_accept.propose_rematch("bob")
    assert accepted is True
    assert r_accept.is_finished is False
    assert r_accept.finished_timestamp is None
    assert r_accept.is_started is True
    assert r_accept.white_player == "bob"
    assert r_accept.black_player == "alice"

    # 8. Normal Finished Room: Pruned after 300s retention grace period when no rematch pending
    r_stale = rm.create_room("ROOM_EXPIRED_NO_REMATCH")
    r_stale.white_player = "alice"
    r_stale.black_player = "bob"
    r_stale.start_game()
    r_stale.resign("alice")
    assert len(r_stale.rematch_proposals) == 0

    # Before 300s: not pruned
    r_stale.finished_timestamp = time.time() - 150.0
    rm.cleanup_stale_rooms(finished_retention_seconds=300.0, max_idle_seconds=1800.0)
    assert rm.get_room("ROOM_EXPIRED_NO_REMATCH") is not None

    # After 300s: pruned
    r_stale.finished_timestamp = time.time() - 350.0
    rm.cleanup_stale_rooms(finished_retention_seconds=300.0, max_idle_seconds=1800.0)
    assert rm.get_room("ROOM_EXPIRED_NO_REMATCH") is None


