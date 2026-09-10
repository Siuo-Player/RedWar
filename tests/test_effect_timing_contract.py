from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _put(gs, row, col, name, team):
    piece = criar_peca_por_nome(name, team)
    assert piece is not None
    gs.board[row][col] = piece
    return piece


def _move(gs, start, end):
    gs.make_action(start, end, "move", affected_area=[])


def test_effect_timer_ticks_only_when_owner_becomes_active():
    gs = GameState()
    _put(gs, 7, 0, "Phantom", "brancas")
    _put(gs, 0, 7, "Phantom", "pretas")
    gs.tile_effects[3][3] = {"type": "fire", "timer": 3, "team": "brancas"}
    gs.compute_initial_hash()

    _move(gs, (7, 0), (6, 0))
    assert gs.white_to_move is False
    assert gs.tile_effects[3][3]["timer"] == 3

    _move(gs, (0, 7), (1, 7))
    assert gs.white_to_move is True
    assert gs.tile_effects[3][3]["timer"] == 2

    _move(gs, (6, 0), (7, 0))
    assert gs.white_to_move is False
    assert gs.tile_effects[3][3]["timer"] == 2

    _move(gs, (1, 7), (0, 7))
    assert gs.white_to_move is True
    assert gs.tile_effects[3][3]["timer"] == 1

    _move(gs, (7, 0), (6, 0))
    assert gs.white_to_move is False
    assert gs.tile_effects[3][3]["timer"] == 1

    _move(gs, (0, 7), (1, 7))
    assert gs.white_to_move is True
    assert gs.tile_effects[3][3] is None
