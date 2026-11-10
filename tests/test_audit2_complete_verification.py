from __future__ import annotations

import time
import pytest

from engine.actions import ActionType, GameAction
from engine.action_parser import ActionParser
from engine.game_modes import GameMode, GameModeType
from engine.game_state import GameState, coords_para_notacao
from engine.legal_actions import legal_actions
from engine.pieces import Bone, Dragoon, Obelisk, criar_peca_por_nome
from engine.ratings import LeaderboardManager
from online.server.room import GameRoom, RoomManager
from online.server.web_app import RedWarWebApp


def test_surrender_awards_clean_win_to_opponent_never_draw(tmp_path):
    """Verify Section 9.3: Surrender canonical action awards 1.0 to opponent and never draws."""
    lb_path = str(tmp_path / "ratings.json")
    lb = LeaderboardManager(storage_path=lb_path)
    manager = RoomManager(leaderboard_manager=lb)

    room = manager.create_room("ROOM_SURRENDER_TEST")
    room.add_player("alice")  # Brancas
    room.add_player("bob")    # Pretas
    room.start_game()

    # Alice is White to move and submits canonical surrender action
    surrender_action = {"type": "surrender"}
    room.apply_action("alice", surrender_action)

    assert room.is_finished
    assert room.winner == "pretas"
    assert room.termination_reason == "surrender"

    # Record match result into leaderboard
    manager.record_match_result(room)

    # Bob (pretas) must have won (1 win, 0 losses, score 1.0)
    # Alice (brancas) must have lost (0 wins, 1 loss, score 0.0)
    bob_prof = lb.get_profile("bob")
    alice_prof = lb.get_profile("alice")

    bob_stats = bob_prof.stats["standard_8x8"]
    alice_stats = alice_prof.stats["standard_8x8"]

    assert bob_stats["wins"] == 1
    assert bob_stats["losses"] == 0
    assert bob_stats["draws"] == 0
    assert bob_prof.get_rating("standard_8x8") > 1200

    assert alice_stats["wins"] == 0
    assert alice_stats["losses"] == 1
    assert alice_stats["draws"] == 0
    assert alice_prof.get_rating("standard_8x8") < 1200


def test_grand_10x10_grid_actions_and_movement():
    """Verify Section 5: Full 10x10 grid supports movement, attacks, legal actions, and notation."""
    gs = GameState(rows=10, cols=10)
    assert gs.rows == 10
    assert gs.cols == 10

    # Place a White Bone at (9, 0) and Black Bone at (8, 0)
    gs.board[9][0] = Bone("brancas")
    gs.board[8][0] = Bone("pretas")

    # Place a Dragoon at (9, 9)
    gs.board[9][9] = Dragoon("brancas")

    # Test coordinate validation: (9, 9) is valid on 10x10
    gs._validate_action_coordinates((9, 9), (7, 9))

    # Test coordinate validation outside: (10, 0) should raise
    with pytest.raises(ValueError, match="outside board"):
        gs._validate_action_coordinates((10, 0), (9, 0))

    # Test legal actions enumeration scans full 10x10
    actions = legal_actions(gs)
    assert len(actions) > 0

    # Check that Dragoon at (9, 9) has generated valid moves on the 10x10 board
    dragoon_actions = [a for a in actions if a.start == (9, 9)]
    assert len(dragoon_actions) > 0

    # Test notation formatting for rank 10
    assert coords_para_notacao(0, 9, rows=10) == "j10"
    assert coords_para_notacao(9, 0, rows=10) == "a1"

    # Test ActionParser supports 10x10
    coords = ActionParser.alg_to_coords("J10", total_linhas=10)
    assert coords == (0, 9)

    parsed = ActionParser.parse("MOVE J10 J8", max_rows=10, max_cols=10)
    assert parsed is not None
    assert parsed["origin"] == "J10"
    assert parsed["target"] == "J8"


def test_authoritative_clock_real_time_deduction():
    """Verify Section 8.2: Server deducts real-time elapsed seconds on moves and handles timeout."""
    room = GameRoom(room_id="ROOM_CLOCK_REALTIME")
    room.session.state.board[6][0] = Bone("brancas")
    room.session.state.board[1][0] = Bone("pretas")

    room.add_player("alice")
    room.add_player("bob")
    room.start_game()

    initial_time = room.clock.white_time

    # Simulate that Alice took 0.2 seconds before moving
    room.last_move_timestamp = time.monotonic() - 0.2

    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    room.apply_action("alice", action)

    # Alice's time must have decreased by ~0.2s and then gained increment (+0s in rapid 10+0)
    assert room.clock.white_time < initial_time
    assert room.clock.white_time == pytest.approx(initial_time - 0.2, abs=0.08)


def test_web_app_granular_csp_and_early_method_rejection():
    """Verify Section 4.4: Granular CSP and early 405 rejection for non-GET methods."""
    app = RedWarWebApp()
    resp = app.handle_request("POST", "/index.html", body="some_body")

    assert resp["status"] == 405
    csp = resp["headers"]["Content-Security-Policy"]
    assert "script-src 'self'" in csp
    assert "connect-src 'self'" in csp
    assert "default-src 'self'" in csp


def test_puzzle_endpoint_structure():
    """Verify puzzle bank schema integrity."""
    app = RedWarWebApp()
    resp = app.handle_request("GET", "/api/puzzles")

    assert resp["status"] == 200
    import json
    data = json.loads(resp["body"])
    assert "puzzles" in data
    assert len(data["puzzles"]) > 0

    for pz in data["puzzles"]:
        assert "puzzle_id" in pz
        assert "title" in pz
        assert "solution_moves" in pz
