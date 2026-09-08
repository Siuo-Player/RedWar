import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.pieces import Bone, criar_peca_por_nome


def _state_with_piece(name="Bone"):
    state = GameState()
    state.board[6][0] = criar_peca_por_nome(name, "brancas")
    state.compute_initial_hash()
    return state


def test_execute_action_rejects_structurally_valid_but_illegal_move_before_mutation():
    state = _state_with_piece()
    before = state.to_rwen()
    before_hash = state.get_state_hash()

    illegal = GameAction(ActionType.MOVE, (6, 0), (6, 1))
    with pytest.raises(ValueError, match="illegal action"):
        state.execute_action(illegal)

    assert state.to_rwen() == before
    assert state.get_state_hash() == before_hash


def test_execute_action_rejects_equivalent_illegal_legacy_mapping():
    state = _state_with_piece()
    before = state.to_rwen()
    before_hash = state.get_state_hash()

    with pytest.raises(ValueError, match="illegal action"):
        state.execute_action({"type": "move", "start": [6, 0], "end": [6, 1]})

    assert state.to_rwen() == before
    assert state.get_state_hash() == before_hash


def test_execute_action_accepts_a_canonical_legal_move():
    state = _state_with_piece()
    action = GameAction(ActionType.MOVE, (6, 0), (5, 0))

    state.execute_action(action)

    assert state.board[6][0] is None
    assert state.board[5][0] is not None
    assert state.board[5][0].name == "Bone"
