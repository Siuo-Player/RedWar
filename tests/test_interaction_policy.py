from __future__ import annotations

from types import SimpleNamespace

from tools.replay.interaction import actions_for_destination, needs_offensive_target_confirmation


class FakePiece:
    def __init__(self):
        self.team = "brancas"

    def get_valid_moves(self, *args):
        return [(3, 4)]

    def get_valid_attacks(self, *args):
        return [(3, 4)]

    def get_valid_stuns(self, *args):
        return {}

    def get_valid_spawns(self, *args):
        return []

    def get_valid_spells(self, *args):
        return [{"target": (3, 4), "spell_type": "nevada"}]


def _board():
    return [[None for _ in range(8)] for _ in range(8)]


def test_destination_keeps_all_legal_action_interpretations():
    piece = FakePiece()
    gs = SimpleNamespace(board=_board(), tile_effects=_board())
    gs.board[4][4] = piece

    actions = actions_for_destination(gs, 4, 4, 3, 4)
    assert [action["type"] for action in actions] == ["move", "attack", "spell"]


def test_friendly_destination_is_still_a_legal_spell_target_for_resolution():
    piece = FakePiece()
    gs = SimpleNamespace(board=_board(), tile_effects=_board())
    gs.board[4][4] = piece
    gs.board[3][4] = SimpleNamespace(team="brancas")

    actions = actions_for_destination(gs, 4, 4, 3, 4)
    assert any(action["type"] == "spell" for action in actions)


def test_offensive_spell_against_ally_requires_confirmation():
    gs = SimpleNamespace(board=_board())
    caster = SimpleNamespace(team="brancas")
    gs.board[4][4] = caster
    gs.board[3][4] = SimpleNamespace(team="brancas")
    action = {
        "type": "spell",
        "spell_name": "nevada",
        "start": (4, 4),
        "end": (3, 4),
    }
    assert needs_offensive_target_confirmation(gs, action) is True


def test_support_spell_against_ally_does_not_require_confirmation():
    gs = SimpleNamespace(board=_board())
    caster = SimpleNamespace(team="brancas")
    gs.board[4][4] = caster
    gs.board[3][4] = SimpleNamespace(team="brancas")
    action = {
        "type": "spell",
        "spell_name": "purify",
        "start": (4, 4),
        "end": (3, 4),
    }
    assert needs_offensive_target_confirmation(gs, action) is False
