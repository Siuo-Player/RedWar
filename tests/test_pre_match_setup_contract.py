import pytest

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from engine.setup import validate_complete_pre_match_setup, validate_pre_match_setup


def _place(board, row, col, name, team):
    piece = criar_peca_por_nome(name, team)
    assert piece is not None
    board[row][col] = piece
    return piece


def test_valid_setup_allows_duplicate_draftable_heroes():
    gs = GameState()
    for col in range(8):
        _place(gs.board, 7, col, "Phantom", "brancas")
        _place(gs.board, 0, col, "Phantom", "pretas")

    costs = validate_complete_pre_match_setup(gs.board)

    assert costs["brancas"] == 40
    assert costs["pretas"] == 40


def test_setup_rejects_budget_overflow():
    gs = GameState()
    for col in range(8):
        _place(gs.board, 7, col, "Obelisk", "brancas")

    with pytest.raises(ValueError, match="exceeds budget"):
        validate_pre_match_setup(gs.board, "brancas")


def test_setup_rejects_piece_outside_home_rows():
    gs = GameState()
    _place(gs.board, 5, 0, "Phantom", "brancas")

    with pytest.raises(ValueError, match="outside home rows"):
        validate_pre_match_setup(gs.board, "brancas")


def test_setup_rejects_non_draftable_spawn_only_unit():
    gs = GameState()
    _place(gs.board, 7, 0, "Ghoul", "brancas")

    with pytest.raises(ValueError, match="Non-draftable"):
        validate_pre_match_setup(gs.board, "brancas")


def test_setup_rejects_wrong_side_placement_when_validating_that_side():
    gs = GameState()
    _place(gs.board, 7, 0, "Phantom", "pretas")

    with pytest.raises(ValueError, match="outside home rows"):
        validate_pre_match_setup(gs.board, "pretas")


def test_runtime_spawn_units_are_not_restricted_by_draft_contract_after_setup():
    gs = GameState()
    _place(gs.board, 7, 0, "Phantom", "brancas")
    _place(gs.board, 0, 0, "Phantom", "pretas")
    validate_complete_pre_match_setup(gs.board)

    gs.board[6][0] = criar_peca_por_nome("Ghoul", "brancas")
    assert gs.board[6][0] is not None
    assert gs.board[6][0].draftable is False
