from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Mapping
from unittest.mock import MagicMock

import pytest

from engine.game_modes import GameClock, GameMode, TimeControl
from engine.pieces import Bone
from online.server.app import _clock_tick_loop
from online.server.room import GameRoom, RoomManager, setup_standard_board


def _setup_test_room(initial_seconds: float = 60.0, increment_seconds: float = 0.0) -> GameRoom:
    """Helper to initialize a started 2-player room with standard board."""
    tc = TimeControl(initial_seconds=initial_seconds, increment_seconds=increment_seconds)
    room = GameRoom(room_id="TEST_ADVERSARIAL_ROOM", time_control=tc)
    room.add_player("player_white", "brancas")
    room.add_player("player_black", "pretas")
    room.start_game()
    return room


def _make_dummy_move(room: GameRoom, team: str) -> dict[str, Any]:
    """Find a valid pawn advance or piece move for the specified team."""
    state = room.session.state
    rows = getattr(state, "rows", len(state.board))
    cols = getattr(state, "cols", len(state.board[0]))
    for r in range(rows):
        for c in range(cols):
            p = state.board[r][c]
            if p and p.team == team and getattr(p, "stun_timer", 0) == 0:
                moves = p.get_valid_moves(r, c, state.board, state.tile_effects)
                if moves:
                    return {"type": "move", "start": (r, c), "end": moves[0]}
    # If no move found, return surrender to finish cleanly
    return {"type": "surrender"}


def test_clock_telescoping_single_deduction_invariant():
    """Mathematical Invariant: Over any sequence of N interleaved ticks and moves,

    total deducted elapsed time across both players must equal total wall clock time
    (accounting for increments). Double deduction would cause deducted time >> wall time.
    """
    room = _setup_test_room(initial_seconds=300.0, increment_seconds=2.0)
    base_monotonic = time.monotonic()
    room.last_move_timestamp = base_monotonic

    white_accumulated_time = 0.0
    black_accumulated_time = 0.0
    white_moves_count = 0
    black_moves_count = 0

    current_sim_time = base_monotonic
    random.seed(42)

    # Simulate 30 events: randomly choosing between background tick and player move
    for step in range(30):
        if room.is_finished:
            break

        # Advance simulated time between 0.06s and 1.80s (above 0.05 threshold to test exact deductions)
        delta = random.uniform(0.06, 1.80)
        current_sim_time += delta
        room.last_move_timestamp = current_sim_time - delta

        active_is_white = room.session.state.white_to_move
        if active_is_white:
            white_accumulated_time += delta
        else:
            black_accumulated_time += delta

        # Choose event: 50% chance tick, 50% chance move
        event_type = random.choice(["tick", "move"])

        if event_type == "tick":
            # Simulate background tick with no arguments (uses room monotonic clock)
            # We monkeypatch time.monotonic to return current_sim_time
            orig_monotonic = time.monotonic
            try:
                time.monotonic = lambda: current_sim_time
                room.tick_clock()
            finally:
                time.monotonic = orig_monotonic
        else:
            # Player move
            player = "player_white" if active_is_white else "player_black"
            team = "brancas" if active_is_white else "pretas"
            action = _make_dummy_move(room, team)
            if active_is_white:
                white_moves_count += 1
            else:
                black_moves_count += 1

            orig_monotonic = time.monotonic
            try:
                time.monotonic = lambda: current_sim_time
                room.apply_action(player, action)
            finally:
                time.monotonic = orig_monotonic

    expected_white = 300.0 - white_accumulated_time + (white_moves_count * 2.0)
    expected_black = 300.0 - black_accumulated_time + (black_moves_count * 2.0)

    # Double deduction in pre-fix code would have deducted white_accumulated_time * 2
    # Verify that single deduction holds with float precision
    assert room.clock.white_time == pytest.approx(expected_white, abs=0.01), (
        f"White clock mismatch! Expected {expected_white:.3f}, got {room.clock.white_time:.3f}. "
        f"Double deduction detected if actual is much lower than expected."
    )
    assert room.clock.black_time == pytest.approx(expected_black, abs=0.01), (
        f"Black clock mismatch! Expected {expected_black:.3f}, got {room.clock.black_time:.3f}."
    )


def test_rapid_moves_sub_50ms_latency_grace():
    """Verify that rapid moves (<50ms) benefit from network jitter grace without drifting

    or double-deducting subsequent turns.
    """
    room = _setup_test_room(initial_seconds=60.0, increment_seconds=0.0)
    initial_white = room.clock.white_time

    # Player white moves with delta = 0.02s (< 0.05s)
    sim_time = time.monotonic()
    room.last_move_timestamp = sim_time - 0.02

    orig_monotonic = time.monotonic
    try:
        time.monotonic = lambda: sim_time
        action = _make_dummy_move(room, "brancas")
        room.apply_action("player_white", action)
    finally:
        time.monotonic = orig_monotonic

    # White took < 50ms: clock unchanged (latency forgiveness)
    assert room.clock.white_time == pytest.approx(initial_white)

    # Turn passes to black. Black thinks for 1.20s (> 50ms)
    sim_time += 1.20
    room.last_move_timestamp = sim_time - 1.20
    initial_black = room.clock.black_time

    orig_monotonic = time.monotonic
    try:
        time.monotonic = lambda: sim_time
        action = _make_dummy_move(room, "pretas")
        room.apply_action("player_black", action)
    finally:
        time.monotonic = orig_monotonic

    # Black lost exactly 1.20s; White's prior 0.02s was NOT charged to Black!
    assert room.clock.black_time == pytest.approx(initial_black - 1.20, abs=0.01)


def test_zero_interval_deduction():
    """Verify multiple ticks and moves with zero interval (0.0s elapsed) produce zero deduction."""
    room = _setup_test_room(initial_seconds=60.0, increment_seconds=0.0)

    # 1. Ticking with 0.0 elapsed
    room.tick_clock(0.0)
    assert room.clock.white_time == pytest.approx(60.0)

    # 2. Ticking with None argument when now == last_move_timestamp
    now = time.monotonic()
    room.last_move_timestamp = now
    orig_monotonic = time.monotonic
    try:
        time.monotonic = lambda: now
        room.tick_clock()
        assert room.clock.white_time == pytest.approx(60.0)

        # 3. Action at exactly now == last_move_timestamp
        action = _make_dummy_move(room, "brancas")
        room.apply_action("player_white", action)
        assert room.clock.white_time == pytest.approx(60.0)
    finally:
        time.monotonic = orig_monotonic


def test_flag_fall_via_tick_terminates_and_locks_match():
    """Verify that when clock expires during tick_clock, flag fall triggers cleanly,

    sets winner, and rejects future actions and ticks.
    """
    room = _setup_test_room(initial_seconds=5.0, increment_seconds=0.0)
    assert not room.is_finished

    # Simulate 6.0s elapsed (exceeding initial 5.0s)
    winner = room.tick_clock(6.0)

    assert winner == "pretas"
    assert room.is_finished is True
    assert room.termination_reason == "flag_fall"
    assert room.winner == "pretas"
    assert room.clock.white_time == 0.0

    # Additional ticks do nothing
    extra = room.tick_clock(1.0)
    assert extra is None
    assert room.clock.white_time == 0.0

    # Move attempt after flag fall raises ValueError
    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    with pytest.raises(ValueError, match="match is already finished"):
        room.apply_action("player_white", action)


def test_flag_fall_via_apply_action_terminates_cleanly():
    """Verify that when a player moves after their clock already expired, the action

    is intercepted as flag fall without raising unhandled exceptions or modifying the board.
    """
    room = _setup_test_room(initial_seconds=2.0, increment_seconds=0.0)
    pawn_start = (room.session.state.rows - 2, 0)
    pawn_end = (room.session.state.rows - 3, 0)

    # Player took 4.0s before submitting move (clock had 2.0s)
    sim_time = time.monotonic()
    room.last_move_timestamp = sim_time - 4.0

    orig_monotonic = time.monotonic
    try:
        time.monotonic = lambda: sim_time
        action = {"type": "move", "start": pawn_start, "end": pawn_end}
        result = room.apply_action("player_white", action)
    finally:
        time.monotonic = orig_monotonic

    assert room.is_finished is True
    assert room.termination_reason == "flag_fall"
    assert room.winner == "pretas"
    assert room.clock.white_time == 0.0

    # Board was NOT modified by the flagged move
    assert room.session.state.board[pawn_end[0]][pawn_end[1]] is None
    assert room.session.state.board[pawn_start[0]][pawn_start[1]] is not None


def test_background_clock_tick_loop_integration():
    """Stress test the real async _clock_tick_loop from app.py:

    Ensure it periodically ticks active rooms, terminates flag falls,
    and broadcasts game_over cleanly without crashing.
    """
    async def _run():
        room_manager = RoomManager()
        room1 = room_manager.create_room("ROOM_ASYNC_1", time_control=TimeControl(initial_seconds=1.0))
        room1.add_player("alice", "brancas")
        room1.add_player("bob", "pretas")
        room1.start_game()

        room2 = room_manager.create_room("ROOM_ASYNC_2", time_control=TimeControl(initial_seconds=10.0))
        room2.add_player("carol", "brancas")
        room2.add_player("dave", "pretas")
        room2.start_game()

        # Start background clock tick loop
        tick_task = asyncio.create_task(_clock_tick_loop(room_manager))

        try:
            # Let tick loop run for 2.2 seconds
            await asyncio.sleep(2.2)

            # room1 initial_seconds was 1.0s, so it should have flagged fall and terminated
            assert room1.is_finished is True
            assert room1.termination_reason == "flag_fall"
            assert room1.winner == "pretas"

            # room2 initial_seconds was 10.0s, so it should still be active with deducted time
            assert room2.is_finished is False
            assert room2.clock.white_time < 10.0
            assert room2.clock.white_time > 6.0
        finally:
            tick_task.cancel()
            try:
                await tick_task
            except asyncio.CancelledError:
                pass

    asyncio.run(_run())
