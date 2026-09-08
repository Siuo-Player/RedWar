from __future__ import annotations

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.legal_actions import is_legal_action, legal_actions, to_legacy_dict, to_legacy_dicts
from engine.pieces import criar_peca_por_nome


def _state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    return state


def _put(state: GameState, row: int, col: int, name: str, team: str = "brancas", *, stun: int = 0) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    state.board[row][col] = piece


def test_legal_actions_is_canonical_and_deterministic():
    state = _state()
    _put(state, 6, 5, "Lich")
    _put(state, 4, 4, "Cleric")
    _put(state, 3, 3, "Templar", stun=2)
    _put(state, 1, 1, "Obelisk", "pretas")

    first = legal_actions(state)
    second = legal_actions(state)

    assert first == second
    assert first == tuple(sorted(first, key=lambda action: (
        action.type.value,
        action.start,
        action.end,
        action.spell_name or "",
        action.spawn_name or "",
        action.area,
    )))
    assert all(isinstance(action, GameAction) for action in first)
    assert any(action.type is ActionType.SPAWN for action in first)
    assert any(action.type is ActionType.SPELL and action.spell_name == "purify" for action in first)


def test_is_legal_action_and_legacy_boundary_share_exact_semantics():
    state = _state()
    _put(state, 6, 5, "Lich")
    actions = legal_actions(state)

    assert actions
    assert all(is_legal_action(state, action) for action in actions)
    assert all(to_legacy_dict(action) == action.to_dict() for action in actions)
    assert to_legacy_dicts(actions) == [action.to_dict() for action in actions]


def test_legal_actions_excludes_opponent_and_stunned_actors():
    state = _state()
    _put(state, 6, 5, "Lich", "brancas", stun=2)
    _put(state, 1, 1, "Lich", "pretas")

    assert legal_actions(state) == ()
