from __future__ import annotations

import pytest

from engine.game_modes import GameMode, GameModeType
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def test_game_state_supports_10x10_grid():
    gs = GameState(rows=10, cols=10)
    assert len(gs.board) == 10
    assert len(gs.board[0]) == 10
    assert len(gs.tile_effects) == 10
    assert len(gs.tile_effects[0]) == 10


def test_grand_10x10_game_mode_initializes_state():
    mode = GameMode.grand_10x10()
    assert mode.mode_type == GameModeType.GRAND_10X10
    assert mode.board_rows == 10
    assert mode.board_cols == 10

    gs = mode.create_game_state()
    assert len(gs.board) == 10
    assert len(gs.board[0]) == 10
    assert gs.game_mode == mode


def test_grand_10x10_hash_and_clone():
    gs = GameState(rows=10, cols=10)
    gs.board[0][0] = criar_peca_por_nome("Obelisk", "pretas")
    gs.board[9][9] = criar_peca_por_nome("Obelisk", "brancas")

    initial_hash = gs.compute_initial_hash()
    assert initial_hash != 0

    clone = gs.fast_clone()
    assert len(clone.board) == 10
    assert len(clone.board[0]) == 10
    assert clone.get_state_hash() == initial_hash
    assert clone.board[0][0].name == "Obelisk"
    assert clone.board[9][9].name == "Obelisk"
