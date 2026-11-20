from __future__ import annotations

import pytest

from engine.game_state import GameState
from engine.hazards import HazardArena, HazardType
from engine.pieces import Paladin


def test_hazard_arena_blocks_movement():
    arena = HazardArena(rows=8, cols=8)
    arena.add_hazard(3, 3, HazardType.BARRIER)

    assert arena.is_blocked(3, 3) is True
    assert arena.is_move_allowed((2, 3), (3, 3)) is False
    assert arena.is_blocked(3, 4) is False
    assert arena.is_move_allowed((2, 4), (3, 4)) is True


def test_hazard_arena_lava_incinerates_landing_piece():
    state = GameState()
    arena = HazardArena(rows=8, cols=8)
    arena.add_hazard(4, 4, HazardType.LAVA)

    # Place a pawn on (4, 4)
    pawn = Paladin("brancas")
    state.board[4][4] = pawn

    effect = arena.trigger_square_effect(state, 4, 4)
    assert effect == "lava_incineration"
    assert state.board[4][4] is None  # Incinerated!


def test_hazard_arena_healing_spring_cleanses():
    state = GameState()
    arena = HazardArena(rows=8, cols=8)
    arena.add_hazard(4, 3, HazardType.HEALING_SPRING)

    pawn = Paladin("brancas")
    pawn.stun_timer = 2
    state.board[4][3] = pawn

    effect = arena.trigger_square_effect(state, 4, 3)
    assert effect == "cleansed_and_healed"
    assert pawn.stun_timer == 0


def test_hazard_arena_symmetrical_generation():
    arena = HazardArena.generate_symmetrical_arena(rows=8, cols=8, num_pairs=3, seed=42)
    assert len(arena.hazards) == 6  # 3 pairs

    for (r, c), h_type in arena.hazards.items():
        sym_r = 7 - r
        sym_c = 7 - c
        assert (sym_r, sym_c) in arena.hazards
        assert arena.hazards[(sym_r, sym_c)] == h_type
        # Assert base ranks 0, 1, 6, 7 are never blocked to preserve standard setups
        assert r not in (0, 1, 6, 7)
