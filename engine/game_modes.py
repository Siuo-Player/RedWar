"""Game Modes and Chess.com-style Time Controls for RedWar.

Defines game mode configurations (Standard 8x8, Grand 10x10, Puzzles) and
clock management (Bullet, Blitz, Rapid, Classical with increments).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GameModeType(str, Enum):
    STANDARD_8X8 = "standard_8x8"
    GRAND_10X10 = "grand_10x10"
    BULLET = "bullet"
    BLITZ = "blitz"
    RAPID = "rapid"
    PUZZLE = "puzzle"
    SNAKE_DRAFT = "snake_draft"
    HAZARD_ARENA = "hazard_arena"


@dataclass(frozen=True)
class TimeControl:
    initial_seconds: float
    increment_seconds: float = 0.0

    @property
    def category(self) -> str:
        # Chess.com standard: total time = initial + 40 * increment
        total_estimated = self.initial_seconds + 40.0 * self.increment_seconds
        if total_estimated < 180.0:
            return "bullet"
        if total_estimated < 600.0:
            return "blitz"
        if total_estimated < 1800.0:
            return "rapid"
        return "classical"

    @classmethod
    def bullet_1_0(cls) -> TimeControl:
        return cls(initial_seconds=60.0, increment_seconds=0.0)

    @classmethod
    def blitz_3_2(cls) -> TimeControl:
        return cls(initial_seconds=180.0, increment_seconds=2.0)

    @classmethod
    def blitz_5_0(cls) -> TimeControl:
        return cls(initial_seconds=300.0, increment_seconds=0.0)

    @classmethod
    def rapid_10_0(cls) -> TimeControl:
        return cls(initial_seconds=600.0, increment_seconds=0.0)

    @classmethod
    def rapid_15_10(cls) -> TimeControl:
        return cls(initial_seconds=900.0, increment_seconds=10.0)

    @classmethod
    def classical_30_0(cls) -> TimeControl:
        return cls(initial_seconds=1800.0, increment_seconds=0.0)


class GameClock:
    """Tracks player time, decrements by elapsed ply duration, and applies increments."""

    def __init__(self, time_control: TimeControl):
        self.time_control = time_control
        self.white_time = time_control.initial_seconds
        self.black_time = time_control.initial_seconds

    def record_ply_time(self, white_to_move: bool, elapsed_seconds: float) -> None:
        if white_to_move:
            self.white_time = max(0.0, self.white_time - elapsed_seconds)
            if self.white_time > 0.0:
                self.white_time += self.time_control.increment_seconds
        else:
            self.black_time = max(0.0, self.black_time - elapsed_seconds)
            if self.black_time > 0.0:
                self.black_time += self.time_control.increment_seconds

    def is_flag_fallen(self, white_to_move: bool) -> bool:
        return self.white_time <= 0.0 if white_to_move else self.black_time <= 0.0

    def timeout_winner(self) -> str | None:
        if self.white_time <= 0.0 and self.black_time <= 0.0:
            return "Empate"
        if self.white_time <= 0.0:
            return "Pretas"
        if self.black_time <= 0.0:
            return "Brancas"
        return None


@dataclass
class GameMode:
    mode_type: GameModeType
    name: str
    board_rows: int = 8
    board_cols: int = 8
    draft_budget: int = 200
    max_twc: int = 50
    time_control: TimeControl = field(default_factory=TimeControl.rapid_10_0)

    def apply_to_game_state(self, state: Any) -> None:
        clock = GameClock(self.time_control)
        state.white_time = clock.white_time
        state.black_time = clock.black_time
        setattr(state, "clock", clock)
        setattr(state, "game_mode", self)
        setattr(state, "max_twc", self.max_twc)

    def create_game_state(self) -> Any:
        from engine.game_state import GameState
        state = GameState(
            time_limit_seconds=self.time_control.initial_seconds,
            rows=self.board_rows,
            cols=self.board_cols,
        )
        self.apply_to_game_state(state)
        return state

    @classmethod
    def standard_8x8(cls) -> GameMode:
        return get_preset_mode(GameModeType.STANDARD_8X8)

    @classmethod
    def grand_10x10(cls) -> GameMode:
        return get_preset_mode(GameModeType.GRAND_10X10)

    @classmethod
    def bullet(cls) -> GameMode:
        return get_preset_mode(GameModeType.BULLET)

    @classmethod
    def blitz(cls) -> GameMode:
        return get_preset_mode(GameModeType.BLITZ)

    @classmethod
    def rapid(cls) -> GameMode:
        return get_preset_mode(GameModeType.RAPID)

    @classmethod
    def puzzle(cls) -> GameMode:
        return get_preset_mode(GameModeType.PUZZLE)

    @classmethod
    def snake_draft(cls) -> GameMode:
        return get_preset_mode(GameModeType.SNAKE_DRAFT)

    @classmethod
    def hazard_arena(cls) -> GameMode:
        return get_preset_mode(GameModeType.HAZARD_ARENA)


_PRESETS: dict[GameModeType, GameMode] = {
    GameModeType.STANDARD_8X8: GameMode(
        mode_type=GameModeType.STANDARD_8X8,
        name="Padrão 8×8",
        board_rows=8,
        board_cols=8,
        draft_budget=200,
        max_twc=50,
        time_control=TimeControl.rapid_10_0(),
    ),
    GameModeType.GRAND_10X10: GameMode(
        mode_type=GameModeType.GRAND_10X10,
        name="Grand RedWar 10×10",
        board_rows=10,
        board_cols=10,
        draft_budget=300,
        max_twc=60,
        time_control=TimeControl.rapid_15_10(),
    ),
    GameModeType.BULLET: GameMode(
        mode_type=GameModeType.BULLET,
        name="Bullet 1+0",
        board_rows=8,
        board_cols=8,
        draft_budget=200,
        max_twc=50,
        time_control=TimeControl.bullet_1_0(),
    ),
    GameModeType.BLITZ: GameMode(
        mode_type=GameModeType.BLITZ,
        name="Blitz 3+2",
        board_rows=8,
        board_cols=8,
        draft_budget=200,
        max_twc=50,
        time_control=TimeControl.blitz_3_2(),
    ),
    GameModeType.RAPID: GameMode(
        mode_type=GameModeType.RAPID,
        name="Rápido 10+0",
        board_rows=8,
        board_cols=8,
        draft_budget=200,
        max_twc=50,
        time_control=TimeControl.rapid_10_0(),
    ),
    GameModeType.PUZZLE: GameMode(
        mode_type=GameModeType.PUZZLE,
        name="Táticas & Puzzles",
        board_rows=8,
        board_cols=8,
        draft_budget=0,
        max_twc=10,
        time_control=TimeControl(initial_seconds=300.0, increment_seconds=0.0),
    ),
    GameModeType.SNAKE_DRAFT: GameMode(
        mode_type=GameModeType.SNAKE_DRAFT,
        name="Tournament Snake Draft",
        board_rows=8,
        board_cols=8,
        draft_budget=200,
        max_twc=50,
        time_control=TimeControl.rapid_10_0(),
    ),
    GameModeType.HAZARD_ARENA: GameMode(
        mode_type=GameModeType.HAZARD_ARENA,
        name="Hazard Arena",
        board_rows=8,
        board_cols=8,
        draft_budget=200,
        max_twc=50,
        time_control=TimeControl.rapid_10_0(),
    ),
}


def get_preset_mode(mode_type: GameModeType) -> GameMode:
    """Retrieve a pre-configured, balanced GameMode instance."""
    if mode_type not in _PRESETS:
        raise ValueError(f"Unknown game mode type: {mode_type}")
    preset = _PRESETS[mode_type]
    # Return a shallow copy with fresh time control
    return GameMode(
        mode_type=preset.mode_type,
        name=preset.name,
        board_rows=preset.board_rows,
        board_cols=preset.board_cols,
        draft_budget=preset.draft_budget,
        max_twc=preset.max_twc,
        time_control=preset.time_control,
    )
