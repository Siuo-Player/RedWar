from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _state_with_two_mobile_sides():
    state = GameState()
    state.board[6][0] = criar_peca_por_nome("Geomancer", "brancas")
    state.board[1][0] = criar_peca_por_nome("Cleric", "pretas")
    state.compute_initial_hash()
    return state


def test_check_game_over_is_idempotent_for_same_position():
    state = _state_with_two_mobile_sides()
    current_hash = state.get_state_hash()
    state.state_history = {current_hash: 2}

    state.check_game_over()
    assert state.game_over is True
    assert state.state_history[current_hash] == 3

    state.check_game_over()
    assert state.state_history[current_hash] == 3


def test_real_reobservation_after_different_position_increments_history():
    state = _state_with_two_mobile_sides()
    initial_hash = state.get_state_hash()

    state.check_game_over()
    assert state.state_history[initial_hash] == 1

    state.white_to_move = not state.white_to_move
    state._hash_valid = False
    different_hash = state.get_state_hash()
    assert different_hash != initial_hash
    state.check_game_over()
    assert state.state_history[different_hash] == 1

    state.white_to_move = not state.white_to_move
    state._hash_valid = False
    assert state.get_state_hash() == initial_hash
    state.check_game_over()
    assert state.state_history[initial_hash] == 2


def test_fast_clone_preserves_last_history_observation_marker():
    state = _state_with_two_mobile_sides()
    current_hash = state.get_state_hash()
    state.check_game_over()

    clone = state.fast_clone()
    clone.check_game_over()

    assert state.state_history[current_hash] == 1
    assert clone.state_history[current_hash] == 1
