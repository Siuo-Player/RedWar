from types import SimpleNamespace

from tools.replay.hover_visuals import _active_silence_cells


class Piece:
    def __init__(self, name, team="brancas", can_act=True):
        self.name = name
        self.team = team
        self._can_act = can_act

    def can_act(self):
        return self._can_act


def board():
    return [[None for _ in range(8)] for _ in range(8)]


def test_active_inquisitor_marks_its_full_silence_area():
    gs = SimpleNamespace(board=board())
    gs.board[0][0] = Piece("Inquisitor", "pretas")

    cells = _active_silence_cells(gs)

    assert (0, 0) in cells
    assert (2, 2) in cells
    assert (2, 3) not in cells


def test_stunned_inquisitor_does_not_mark_silence_area():
    gs = SimpleNamespace(board=board())
    gs.board[3][3] = Piece("Inquisitor", "pretas", can_act=False)

    assert _active_silence_cells(gs) == set()


def test_multiple_active_inquisitors_union_their_areas():
    gs = SimpleNamespace(board=board())
    gs.board[0][0] = Piece("Inquisitor", "pretas")
    gs.board[7][7] = Piece("Inquisitor", "pretas")

    cells = _active_silence_cells(gs)

    assert (1, 1) in cells
    assert (6, 6) in cells
    assert (3, 3) not in cells
