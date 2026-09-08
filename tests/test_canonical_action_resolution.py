from __future__ import annotations

import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.legal_actions import legal_actions, resolve_legal_action
from engine.pieces import criar_peca_por_nome


def _state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    return state


def _put(state: GameState, row: int, col: int, name: str, team: str = "brancas") -> None:
    state.board[row][col] = criar_peca_por_nome(name, team)


def test_resolve_legal_action_returns_exact_canonical_action_for_each_supported_type():
    move_state = _state()
    _put(move_state, 6, 0, "Bone")

    attack_state = _state()
    _put(attack_state, 6, 0, "Bone")
    _put(attack_state, 5, 0, "Bone", "pretas")

    spawn_state = _state()
    _put(spawn_state, 6, 5, "Lich")

    spell_state = _state()
    _put(spell_state, 6, 5, "Cleric")
    _put(spell_state, 5, 5, "Bone")
    spell_state.board[5][5].stun_timer = 1

    cases = (
        (move_state, ActionType.MOVE),
        (attack_state, ActionType.ATTACK),
        (spawn_state, ActionType.SPAWN),
        (spell_state, ActionType.SPELL),
    )

    for state, expected_type in cases:
        actions = legal_actions(state)
        matching = tuple(action for action in actions if action.type is expected_type)
        assert matching, f"missing canonical {expected_type.value} action"
        for action in matching:
            assert resolve_legal_action(state, action) == action


def test_resolve_legal_action_expands_legacy_stun_without_aoe_to_unique_canonical_value():
    class StunPiece:
        name = "TestStunner"
        team = "brancas"
        stun_timer = 0

        def can_act(self):
            return True

        def get_valid_moves(self, *args):
            return []

        def get_valid_attacks(self, *args):
            return []

        def get_valid_stuns(self, *args):
            return {(4, 4): {"has_enemy": True, "aoe": [(4, 4), (4, 5)]}}

        def get_valid_spawns(self, *args):
            return []

        def get_valid_spells(self, *args):
            return []

    state = _state()
    state.board[3][3] = StunPiece()

    canonical = GameAction(
        ActionType.STUN,
        (3, 3),
        (4, 4),
        area=((4, 4), (4, 5)),
    )
    legacy = GameAction(ActionType.STUN, (3, 3), (4, 4))

    assert canonical in legal_actions(state)
    assert resolve_legal_action(state, canonical) == canonical
    assert resolve_legal_action(state, legacy) == canonical


def test_resolve_legal_action_rejects_currently_illegal_action_without_mutating_state():
    state = _state()
    _put(state, 6, 0, "Bone")
    before = state.to_rwen()
    action = GameAction(ActionType.MOVE, (6, 0), (0, 0))

    with pytest.raises(ValueError, match="illegal action"):
        resolve_legal_action(state, action)

    assert state.to_rwen() == before
