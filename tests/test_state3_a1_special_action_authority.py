from __future__ import annotations

import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.legal_actions import resolve_legal_action
from engine.pieces import criar_peca_por_nome


def _state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    return state


def test_unauthorized_spell_cannot_bypass_piece_action_space() -> None:
    state = _state()
    state.board[6][0] = criar_peca_por_nome("Bone", "brancas")
    state.compute_initial_hash()
    action = GameAction(ActionType.SPELL, (6, 0), (5, 0), spell_name="nevada")
    before = state.to_rwen()

    with pytest.raises(ValueError, match="illegal action"):
        resolve_legal_action(state, action)

    assert state.to_rwen() == before


def test_unauthorized_spell_cannot_execute_via_execute_action() -> None:
    state = _state()
    state.board[6][0] = criar_peca_por_nome("Bone", "brancas")
    state.compute_initial_hash()
    action = GameAction(ActionType.SPELL, (6, 0), (5, 0), spell_name="nevada")
    before = state.to_rwen()

    with pytest.raises(ValueError, match=r"Unknown or undeclared spell for Bone: nevada"):
        state.execute_action(action)

    assert state.to_rwen() == before
