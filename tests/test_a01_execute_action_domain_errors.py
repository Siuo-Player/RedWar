from __future__ import annotations

import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _empty_state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    return state


def _put(state: GameState, row: int, col: int, name: str, team: str = "brancas") -> None:
    state.board[row][col] = criar_peca_por_nome(name, team)


def _snapshot(state: GameState) -> tuple:
    return (
        state.to_rwen(),
        state.get_state_hash(),
        tuple(tuple(row) for row in state.board),
        tuple(tuple(row) for row in state.tile_effects),
        tuple(state.move_log),
        dict(state.last_move) if state.last_move is not None else None,
        dict(state.state_history),
        state._last_history_hash,
        state.white_to_move,
        state.game_over,
        state.winner,
    )


@pytest.mark.parametrize(
    ("action", "message"),
    [
        (
            GameAction(ActionType.SPAWN, (4, 4), (4, 4), spawn_name="Bone"),
            "SPAWN target square is occupied",
        ),
        (
            GameAction(ActionType.SPELL, (4, 4), (4, 4), spell_name="not_a_spell"),
            "Unknown spell: not_a_spell",
        ),
    ],
)
def test_execute_action_preserves_transition_error_contract(action: GameAction, message: str):
    state = _empty_state()
    _put(state, 4, 4, "BoneLord")
    before = _snapshot(state)

    with pytest.raises(ValueError, match=message):
        state.execute_action(action)

    assert _snapshot(state) == before


def test_execute_action_preserves_inquisitor_silence_error_contract():
    state = _empty_state()
    _put(state, 4, 4, "Cleric")
    _put(state, 4, 6, "Inquisitor", "pretas")
    before = _snapshot(state)

    action = GameAction(ActionType.SPELL, (4, 4), (3, 3), spell_name="purify")
    with pytest.raises(ValueError, match="SPELL is blocked by Inquisitor silence"):
        state.execute_action(action)

    assert _snapshot(state) == before


def test_execute_action_rejects_canonical_membership_gap_after_domain_validation():
    state = _empty_state()
    _put(state, 4, 4, "Lich")
    before = _snapshot(state)

    action = GameAction(ActionType.SPAWN, (4, 4), (4, 5), spawn_name="Ghoul")
    with pytest.raises(ValueError, match="illegal action"):
        state.execute_action(action)

    assert _snapshot(state) == before


def test_execute_action_rejects_nonexistent_source_with_domain_error():
    state = _empty_state()
    before = _snapshot(state)

    action = GameAction(ActionType.MOVE, (4, 4), (4, 5))
    with pytest.raises(ValueError, match="No piece at source square"):
        state.execute_action(action)

    assert _snapshot(state) == before
