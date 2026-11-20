from __future__ import annotations

import pytest

from engine.game_modes import (
    GameClock,
    GameMode,
    GameModeType,
    TimeControl,
    get_preset_mode,
)
from engine.game_state import GameState


def test_time_control_presets():
    """Verify standard Chess.com-style time control presets."""
    bullet = TimeControl.bullet_1_0()
    assert bullet.initial_seconds == 60.0
    assert bullet.increment_seconds == 0.0
    assert bullet.category == "bullet"

    blitz = TimeControl.blitz_3_2()
    assert blitz.initial_seconds == 180.0
    assert blitz.increment_seconds == 2.0
    assert blitz.category == "blitz"

    rapid = TimeControl.rapid_10_0()
    assert rapid.initial_seconds == 600.0
    assert rapid.increment_seconds == 0.0
    assert rapid.category == "rapid"


def test_game_clock_turn_decrement_and_increment():
    """Clock decrements by turn duration and adds increment upon completion."""
    tc = TimeControl(initial_seconds=180.0, increment_seconds=2.0)
    clock = GameClock(time_control=tc)

    assert clock.white_time == 180.0
    assert clock.black_time == 180.0

    # White takes 5 seconds to move
    clock.record_ply_time(white_to_move=True, elapsed_seconds=5.0)
    # 180.0 - 5.0 + 2.0 = 177.0
    assert clock.white_time == pytest.approx(177.0)
    assert clock.black_time == 180.0

    # Black takes 10 seconds to move
    clock.record_ply_time(white_to_move=False, elapsed_seconds=10.0)
    # 180.0 - 10.0 + 2.0 = 172.0
    assert clock.black_time == pytest.approx(172.0)
    assert clock.white_time == pytest.approx(177.0)


def test_game_clock_timeout_detection():
    """Timeout is detected when a player's remaining time hits zero."""
    tc = TimeControl(initial_seconds=10.0, increment_seconds=0.0)
    clock = GameClock(time_control=tc)

    # White takes 12 seconds on a 10s clock -> Flag falls!
    clock.record_ply_time(white_to_move=True, elapsed_seconds=12.0)
    assert clock.white_time <= 0.0
    assert clock.is_flag_fallen(white_to_move=True)
    assert not clock.is_flag_fallen(white_to_move=False)
    assert clock.timeout_winner() == "Pretas"


def test_game_mode_presets():
    """Preset game modes configure board dimensions, budgets, and rules."""
    standard = get_preset_mode(GameModeType.STANDARD_8X8)
    assert standard.board_rows == 8
    assert standard.board_cols == 8
    assert standard.draft_budget == 200
    assert standard.max_twc == 50

    grand = get_preset_mode(GameModeType.GRAND_10X10)
    assert grand.board_rows == 10
    assert grand.board_cols == 10
    assert grand.draft_budget == 300
    assert grand.max_twc == 60


def test_game_mode_applies_to_game_state():
    """A GameMode configures the state clock and limits upon initialization."""
    blitz_mode = get_preset_mode(GameModeType.BLITZ)
    state = GameState()
    blitz_mode.apply_to_game_state(state)

    assert state.white_time == 180.0
    assert state.black_time == 180.0
    assert hasattr(state, "clock")
    assert state.clock.time_control.increment_seconds == 2.0
