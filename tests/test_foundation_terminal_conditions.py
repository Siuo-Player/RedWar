from engine.game_state import GameState
from engine.pieces import Pyromancer, criar_peca_por_nome


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



def test_material_tiebreak_ignores_temporary_summons():
    state = GameState()
    state.board[0][0] = criar_peca_por_nome("Templar", "brancas")  # 15
    temporary_bone = criar_peca_por_nome("Bone", "brancas")  # 8
    temporary_bone.lifespan = 5
    state.board[0][1] = temporary_bone
    state.board[7][7] = criar_peca_por_nome("Geomancer", "pretas")  # 21
    state.turns_without_capture = 50

    state.check_game_over()

    assert state.game_over is True
    assert state.winner == "Desempate por Material (21 vs 15) - Pretas Vencem no Desempate"


def test_equal_material_tiebreak_currently_awards_black():
    state = GameState()
    state.board[0][0] = criar_peca_por_nome("Templar", "brancas")  # 15
    state.board[7][7] = criar_peca_por_nome("Templar", "pretas")  # 15
    state.turns_without_capture = 50

    state.check_game_over()

    assert state.game_over is True
    assert state.winner == "Desempate por Material (15 vs 15) - Pretas Vencem no Desempate"
