from engine.game_state import GameState
from engine.pieces import FrostMage, Inquisitor, Bone


def empty_board():
    return [[None for _ in range(8)] for _ in range(8)]


def empty_effects():
    return [[None for _ in range(8)] for _ in range(8)]


def test_nevada_allows_empty_centers_with_manhattan_range_three():
    mage = FrostMage("brancas")
    board = empty_board()
    effects = empty_effects()

    targets = {entry["target"] for entry in mage.get_valid_spells(4, 4, board, effects)}

    assert (4, 4) not in targets
    assert (1, 4) in targets
    assert (4, 1) in targets
    assert (2, 5) in targets
    assert (0, 0) not in targets


def test_nevada_rejects_ice_centers_but_other_centers_remain_available():
    mage = FrostMage("brancas")
    board = empty_board()
    effects = empty_effects()
    effects[5][4] = {"type": "ice", "timer": 3, "team": "brancas"}

    targets = {entry["target"] for entry in mage.get_valid_spells(4, 4, board, effects)}

    assert (5, 4) not in targets
    assert (4, 5) in targets


def test_nevada_is_blocked_by_opposing_inquisitor_silence():
    mage = FrostMage("brancas")
    inquisitor = Inquisitor("pretas")
    board = empty_board()
    effects = empty_effects()
    board[2][4] = inquisitor

    assert mage.get_valid_spells(4, 4, board, effects) == []


def test_stunned_inquisitor_does_not_project_silence():
    mage = FrostMage("brancas")
    inquisitor = Inquisitor("pretas")
    inquisitor.stun_timer = 2
    board = empty_board()
    effects = empty_effects()
    board[2][4] = inquisitor

    targets = {entry["target"] for entry in mage.get_valid_spells(4, 4, board, effects)}

    assert (4, 4) not in targets
    assert (4, 3) in targets


def test_nevada_can_be_cast_again_on_a_different_center_without_cooldown():
    gs = GameState()
    mage = FrostMage("brancas")
    gs.board[4][4] = mage
    gs.board[0][0] = Bone("pretas")

    gs.make_action((4, 4), (1, 4), action_type="spell", spell_name="nevada")
    first_ice = gs.tile_effects[1][4]
    assert first_ice and first_ice["type"] == "ice"

    gs.white_to_move = True
    gs.make_action((4, 4), (2, 4), action_type="spell", spell_name="nevada")

    assert gs.tile_effects[2][4]
    assert gs.tile_effects[2][4]["type"] == "ice"
