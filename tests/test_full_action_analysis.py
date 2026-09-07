from __future__ import annotations

import importlib
import sys
import types

from engine.game_state import GameState
from engine.legal_actions import is_legal_action, legal_actions
from engine.pieces import Bone, Lich, Pyromancer


def _load_analysis_module(monkeypatch):
    evaluator = types.ModuleType("ai.evaluator")
    evaluator.avaliador_mestre = lambda _state: 0
    monkeypatch.setitem(sys.modules, "ai.evaluator", evaluator)
    sys.modules.pop("ai.search", None)
    return importlib.import_module("ai.search")


def test_engine_legal_action_adapter_covers_all_implemented_action_kinds():
    state = GameState()
    state.board[4][4] = Pyromancer("brancas")
    state.board[6][3] = Bone("brancas")
    state.board[3][4] = Bone("pretas")
    state.board[5][4] = Bone("pretas")

    actions = legal_actions(state)
    kinds = {action.type.value for action in actions}

    assert {"move", "attack", "spell"}.issubset(kinds)
    assert all(is_legal_action(state, action) for action in actions)


def test_engine_legal_action_adapter_includes_spawn_and_stun_shape():
    spawn_state = GameState()
    spawn_state.board[4][4] = Lich("brancas")
    spawn_actions = legal_actions(spawn_state)
    assert any(
        action.type.value == "spawn" and action.spawn_name == "Ghoul"
        for action in spawn_actions
    )

    class StunPiece:
        team = "brancas"
        name = "TestStunner"

        def can_act(self):
            return True

        def get_valid_moves(self, *args):
            return []

        def get_valid_attacks(self, *args):
            return []

        def get_valid_spawns(self, *args):
            return []

        def get_valid_spells(self, *args):
            return []

        def get_valid_stuns(self, *args):
            return {(4, 4): {"has_enemy": True, "aoe": [(4, 4), (4, 5)]}}

    stun_state = GameState()
    stun_state.board[3][3] = StunPiece()
    stun_actions = legal_actions(stun_state)
    assert any(
        action.type.value == "stun"
        and action.end == (4, 4)
        and action.area == ((4, 4), (4, 5))
        for action in stun_actions
    )


def test_python_analysis_uses_complete_canonical_action_space(monkeypatch):
    search = _load_analysis_module(monkeypatch)
    state = GameState()
    state.board[4][4] = Lich("brancas")
    state.board[3][3] = Bone("pretas")

    expected = [action.to_dict() for action in legal_actions(state)]
    actual = search.get_all_moves_for_analysis(state)
    assert actual == expected


def test_analysis_ties_are_deterministic(monkeypatch):
    search = _load_analysis_module(monkeypatch)
    state = GameState()
    state.board[4][4] = Bone("brancas")
    state.board[6][6] = Bone("pretas")

    _, first = next(search.analisar_posicao_continuamente(state, max_depth=1))
    _, second = next(search.analisar_posicao_continuamente(state, max_depth=1))
    assert first == second
