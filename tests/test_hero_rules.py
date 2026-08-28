import pytest

from engine.pieces import FrostMage, obter_catalogo_pecas


def test_frostmage_has_two_square_diagonal_movement_and_no_basic_attack():
    mage = FrostMage("brancas")
    board = [[None for _ in range(8)] for _ in range(8)]
    effects = [[None for _ in range(8)] for _ in range(8)]

    assert set(mage.get_valid_moves(4, 4, board, effects)) == {
        (3, 3), (3, 5), (2, 2), (2, 6), (5, 3), (5, 5), (6, 2), (6, 6)
    }
    assert mage.get_valid_attacks(4, 4, board, effects) == []


def test_frostmage_nevada_uses_manhattan_range_three_and_has_no_usage_counter():
    mage = FrostMage("brancas")
    board = [[None for _ in range(8)] for _ in range(8)]
    effects = [[None for _ in range(8)] for _ in range(8)]

    from engine.pieces import Ranger
    board[1][4] = Ranger("pretas")
    board[4][7] = Ranger("pretas")
    board[0][0] = Ranger("pretas")

    targets = {spell["target"] for spell in mage.get_valid_spells(4, 4, board, effects)}
    assert (1, 4) in targets  # distance 3
    assert (4, 7) in targets  # distance 3
    assert (0, 0) not in targets  # distance 8
    assert not hasattr(mage, "spell_uses")
    assert not hasattr(mage, "spell_cooldown")


def test_draft_catalogue_allows_duplicate_hero_instances_by_cost_data():
    catalog = obter_catalogo_pecas()
    frost = next(item for item in catalog if item["name"] == "FrostMage")
    assert frost["cost"] == 5
    # There is intentionally no per-hero draft-copy limit in the catalogue contract.
    assert all("max_copies" not in item for item in catalog)
