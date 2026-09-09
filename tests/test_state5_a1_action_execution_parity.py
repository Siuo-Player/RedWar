from __future__ import annotations

import pytest

from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.pieces import HERO_DEFS, criar_peca_por_nome


@pytest.mark.parametrize("hero_name", tuple(HERO_DEFS))
def test_every_canonical_action_round_trips_through_legacy_execute(hero_name: str) -> None:
    """Every enumerated action must be executable through the legacy boundary."""
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    state.board[4][4] = criar_peca_por_nome(hero_name, "brancas")
    state.board[4][6] = criar_peca_por_nome("Bone", "pretas")
    state.board[3][3] = criar_peca_por_nome("Bone", "brancas")
    state.compute_initial_hash()

    actions = legal_actions(state)
    for action in actions:
        clone = state.fast_clone()
        clone.execute_action(action.to_dict())
