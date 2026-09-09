from __future__ import annotations

import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.legal_actions import legal_actions, resolve_legal_action
from engine.pieces import criar_peca_por_nome


def _state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    return state


def test_valid_transition_domain_does_not_override_missing_canonical_spawn_membership():
    state = _state()
    state.board[6][5] = criar_peca_por_nome("Lich", "brancas")

    # Empty destination and a syntactically valid spawn name satisfy the
    # transition validator, but the Lich generator is the authority for which
    # spawn squares/names are actually legal.
    action = GameAction(
        ActionType.SPAWN,
        (6, 5),
        (4, 5),
        spawn_name="Ghoul",
    )

    assert action not in legal_actions(state)
    before = state.to_rwen()
    with pytest.raises(ValueError, match="illegal action"):
        resolve_legal_action(state, action)
    assert state.to_rwen() == before


def test_valid_transition_domain_does_not_override_missing_canonical_stun_membership():
    state = _state()
    state.board[4][4] = criar_peca_por_nome("Bone", "brancas")
    state.board[2][4] = criar_peca_por_nome("Bone", "pretas")

    # The transition validator can validate a non-empty affected area, but the
    # action-space adapter must still reject STUN when no piece-level legal STUN
    # generator produced that action.
    action = GameAction(
        ActionType.STUN,
        (4, 4),
        (2, 4),
        area=((2, 4),),
    )

    assert action not in legal_actions(state)
    before = state.to_rwen()
    with pytest.raises(ValueError, match="illegal action"):
        resolve_legal_action(state, action)
    assert state.to_rwen() == before
