import copy

import pytest

from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.pieces import HERO_DEFS, criar_peca_por_nome


def test_no_legal_action_termination_uses_canonical_action_space(monkeypatch):
    original = copy.deepcopy(HERO_DEFS["Ranger"])
    patched = copy.deepcopy(original)
    patched["spells"] = []
    monkeypatch.setitem(HERO_DEFS, "Ranger", patched)

    gs = GameState()
    gs.board[4][4] = criar_peca_por_nome("Ranger", "brancas")
    gs.board[4][6] = criar_peca_por_nome("Bone", "pretas")

    assert legal_actions(gs) == ()
    gs.check_game_over()
    assert gs.game_over is True
    assert "Oponente Bloqueado" in gs.winner


def test_valid_no_action_state_still_terminates():
    gs = GameState()
    gs.board[0][0] = criar_peca_por_nome("Obelisk", "brancas")
    gs.board[7][7] = criar_peca_por_nome("Obelisk", "pretas")
    for col in range(1, 8):
        gs.board[0][col] = criar_peca_por_nome("StoneWall", "brancas")
    assert legal_actions(gs) == ()
    gs.check_game_over()
    assert gs.game_over is True
    assert "Oponente Bloqueado" in gs.winner
