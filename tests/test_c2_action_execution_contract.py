import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _state_with_piece(name="Bone"):
    state = GameState()
    state.board[6][0] = criar_peca_por_nome(name, "brancas")
    state.compute_initial_hash()
    return state


def test_execute_action_accepts_canonical_game_action_and_matches_legacy_path():
    canonical_state = _state_with_piece()
    legacy_state = canonical_state.fast_clone()

    action = GameAction(ActionType.MOVE, (6, 0), (5, 0))
    canonical_state.execute_action(action)
    legacy_state.execute_action({"type": "move", "start": (6, 0), "end": (5, 0)})

    assert canonical_state.to_rwen() == legacy_state.to_rwen()
    assert canonical_state.get_state_hash() == legacy_state.get_state_hash()


def test_legal_shape_but_illegal_transition_rejects_before_state_mutation():
    state = _state_with_piece()
    before_rwen = state.to_rwen()
    before_hash = state.get_state_hash()

    invalid_transition = GameAction(ActionType.SPAWN, (6, 0), (6, 0), spawn_name="Bone")
    with pytest.raises(ValueError, match="SPAWN target square is occupied"):
        state.execute_action(invalid_transition)

    assert state.to_rwen() == before_rwen
    assert state.get_state_hash() == before_hash


def test_unknown_legacy_action_is_rejected_without_mutation():
    state = _state_with_piece()
    before_rwen = state.to_rwen()
    before_hash = state.get_state_hash()

    with pytest.raises(ValueError):
        state.execute_action({"type": "teleport", "start": (6, 0), "end": (5, 0)})

    assert state.to_rwen() == before_rwen
    assert state.get_state_hash() == before_hash


def test_action_contract_keeps_transition_authority_in_gamestate():
    state = _state_with_piece()
    action = GameAction(ActionType.MOVE, (6, 0), (5, 0))

    state.execute_action(action)

    assert state.board[6][0] is None
    assert state.board[5][0] is not None
    assert state.white_to_move is False
