from __future__ import annotations

from pathlib import Path
import pytest

from engine.game_modes import GameMode, TimeControl
from engine.pieces import Bone
from engine.ratings import LeaderboardManager
from online.server.room import GameRoom, RoomManager


def test_room_creation_with_mode_and_clock():
    mode = GameMode.grand_10x10()
    tc = TimeControl.blitz_3_2()
    room = GameRoom(room_id="ROOM_GRAND", mode=mode, time_control=tc, rated=True)

    assert room.room_id == "ROOM_GRAND"
    assert room.mode.board_rows == 10
    assert room.mode.board_cols == 10
    assert room.clock.white_time == 180.0
    assert room.clock.black_time == 180.0
    assert room.clock.time_control.increment_seconds == 2.0
    assert not room.is_started
    assert not room.is_finished


def test_player_assignment_and_start():
    room = GameRoom(room_id="ROOM_TEST", time_control=TimeControl.bullet_1_0())
    
    role1 = room.add_player("alice")
    assert role1 == "brancas"
    assert room.white_player == "alice"

    role2 = room.add_player("bob")
    assert role2 == "pretas"
    assert room.black_player == "bob"

    room.start_game()
    assert room.is_started
    assert not room.is_finished

    # Third player becomes spectator
    role3 = room.add_player("charlie")
    assert role3 == "espetador"
    assert "charlie" in room.spectators


def test_action_execution_updates_clock_and_increments():
    room = GameRoom(room_id="ROOM_PLAY", time_control=TimeControl.blitz_3_2())
    room.session.state.board[6][0] = Bone("brancas")
    room.session.state.board[1][0] = Bone("pretas")

    room.add_player("alice")
    room.add_player("bob")
    room.start_game()

    initial_white_time = room.clock.white_time
    
    # Simulate 5 seconds elapsed on White's turn
    room.tick_clock(5.0)
    assert room.clock.white_time == pytest.approx(initial_white_time - 5.0)

    # White executes move from (6, 0) to (5, 0)
    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    room.apply_action("alice", action)

    # White gained increment (+2.0s)
    assert not room.session.state.white_to_move
    assert room.clock.white_time == pytest.approx(initial_white_time - 5.0 + 2.0)


def test_clock_flag_fall_triggers_timeout_loss():
    room = GameRoom(room_id="ROOM_TIMEOUT", time_control=TimeControl.bullet_1_0())
    room.add_player("alice")
    room.add_player("bob")
    room.start_game()

    # White has 60 seconds. Advance by 61 seconds.
    result = room.tick_clock(61.0)
    
    assert room.is_finished
    assert room.winner == "pretas"
    assert room.termination_reason == "flag_fall"
    assert result == "pretas"


def test_surrender_triggers_resignation_loss():
    room = GameRoom(room_id="ROOM_RESIGN")
    room.add_player("alice")
    room.add_player("bob")
    room.start_game()

    room.resign("alice")

    assert room.is_finished
    assert room.winner == "pretas"
    assert room.termination_reason == "resignation"


def test_match_end_updates_leaderboard_elo(tmp_path: Path):
    db_file = tmp_path / "test_ratings.json"
    leaderboard = LeaderboardManager(storage_path=str(db_file))
    manager = RoomManager(leaderboard_manager=leaderboard)

    room = manager.create_room(
        room_id="MATCH_001",
        time_control=TimeControl.blitz_3_2(),
        rated=True,
    )
    room.add_player("grandmaster_ana")
    room.add_player("challenger_bruno")
    room.start_game()

    # Ana wins by resignation
    room.resign("challenger_bruno")
    manager.record_match_result(room)

    p1 = leaderboard.get_or_create_profile("grandmaster_ana")
    p2 = leaderboard.get_or_create_profile("challenger_bruno")

    mode_name = room.mode.name
    # Winner gained ELO, loser lost ELO
    assert p1.get_rating(mode_name) > 1200
    assert p2.get_rating(mode_name) < 1200
    assert p1.get_wins(mode_name) == 1
