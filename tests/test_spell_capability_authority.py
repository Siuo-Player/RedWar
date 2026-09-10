import copy

import pytest

from engine.actions import GameAction, ActionType
from engine.game_state import GameState
from engine.legal_actions import resolve_legal_action
from engine.pieces import HERO_DEFS, criar_peca_por_nome


def test_attack_action_spell_must_also_be_declared_as_hero_spell(monkeypatch):
    original = copy.deepcopy(HERO_DEFS["Ranger"])
    patched = copy.deepcopy(original)
    patched["spells"] = []
    patched.setdefault("behavior", {}).setdefault("attack", {})
    patched["behavior"]["attack"]["attack_action"] = "spell"
    patched["behavior"]["attack"]["spell_name"] = "aimed_shot"
    monkeypatch.setitem(HERO_DEFS, "Ranger", patched)

    gs = GameState()
    ranger = criar_peca_por_nome("Ranger", "brancas")
    target = criar_peca_por_nome("Bone", "pretas")
    gs.board[4][4] = ranger
    gs.board[4][6] = target

    action = GameAction(
        ActionType.SPELL,
        (4, 4),
        (4, 6),
        spell_name="aimed_shot",
    )

    with pytest.raises(ValueError, match="illegal action for current position"):
        resolve_legal_action(gs, action)
