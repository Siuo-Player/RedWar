from engine.game_state import GameState
from engine.pieces import Pyromancer


def _put(state, row, col, team="brancas"):
    state.board[row][col] = Pyromancer(team)


def test_check_game_over_annihilation():
    state = GameState()
    _put(state, 0, 0, "pretas")

    state.check_game_over()

    assert state.game_over is True
    assert state.winner == "Aniquilação (Pretas Vencem)"


def test_check_game_over_50_turn_no_capture_uses_material():
    state = GameState()
    _put(state, 0, 0, "brancas")
    _put(state, 7, 7, "pretas")
    state.turns_without_capture = 50

    state.check_game_over()

    assert state.game_over is True
    assert state.winner.startswith("Desempate por Material")


def test_check_game_over_third_repetition_uses_material():
    state = GameState()
    _put(state, 0, 0, "brancas")
    _put(state, 7, 7, "pretas")
    state.compute_initial_hash()
    state.state_history[state.current_hash] = 2

    state.check_game_over()

    assert state.game_over is True
    assert state.winner.startswith("Desempate por Material")
