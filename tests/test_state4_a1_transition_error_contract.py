from __future__ import annotations

import pytest

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _state(source_name: str = "Lich") -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    state.board[4][4] = criar_peca_por_nome(source_name, "brancas")
    state.compute_initial_hash()
    return state


def _assert_rejected_without_mutation(state: GameState, action: dict, message: str) -> None:
    before = state.to_rwen()
    with pytest.raises(ValueError, match=message):
        state.execute_action(action)
    assert state.to_rwen() == before


def test_occupied_spawn_keeps_domain_error_and_does_not_mutate() -> None:
    state = _state("Lich")
    state.board[5][4] = criar_peca_por_nome("Bone", "brancas")
    _assert_rejected_without_mutation(
        state,
        {"type": "spawn", "start": (4, 4), "end": (5, 4), "spawn_name": "Ghoul"},
        "SPAWN target square is occupied",
    )


def test_silenced_declared_spell_keeps_domain_error_and_does_not_mutate() -> None:
    state = _state("FrostMage")
    state.board[4][6] = criar_peca_por_nome("Inquisitor", "pretas")
    _assert_rejected_without_mutation(
        state,
        {"type": "spell", "start": (4, 4), "end": (4, 5), "spell_name": "nevada"},
        "SPELL is blocked by Inquisitor silence",
    )


def test_unknown_spell_is_rejected_without_mutation() -> None:
    state = _state("FrostMage")
    _assert_rejected_without_mutation(
        state,
        {"type": "spell", "start": (4, 4), "end": (4, 5), "spell_name": "not_a_spell"},
        "illegal action",
    )
