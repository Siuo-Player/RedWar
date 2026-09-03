from __future__ import annotations

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tools.analytics.legal_action_oracle import canonical_actions, legal_actions


def _state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    return state


def _put(state: GameState, row: int, col: int, name: str, team: str = "brancas"):
    state.board[row][col] = criar_peca_por_nome(name, team)
    return state.board[row][col]


def _action(action_type, start, end, spell=None, spawn=None):
    return (action_type, start, end, spell, spawn)


def test_oracle_lich_covers_move_and_spawn_without_piece_generators():
    state = _state()
    _put(state, 6, 5, "Lich")

    actions = set(legal_actions(state))

    assert _action("MOVE", (6, 5), (5, 4)) in actions
    assert _action("MOVE", (6, 5), (5, 6)) in actions
    assert _action("SPAWN", (6, 5), (5, 4), spawn="Ghoul") in actions
    assert _action("SPAWN", (6, 5), (5, 5), spawn="Ghoul") in actions
    assert _action("SPAWN", (6, 5), (5, 6), spawn="Ghoul") in actions


def test_oracle_ranger_requires_enemy_and_minimum_range_for_aimed_shot():
    state = _state()
    _put(state, 4, 4, "Ranger")
    _put(state, 4, 6, "Obelisk", "pretas")

    actions = set(legal_actions(state))

    assert _action("SPELL", (4, 4), (4, 6), "aimed_shot") in actions
    assert _action("SPELL", (4, 4), (4, 5), "aimed_shot") not in actions


def test_oracle_ranger_does_not_fire_through_nearest_enemy():
    state = _state()
    _put(state, 4, 4, "Ranger")
    _put(state, 4, 5, "Obelisk", "pretas")
    _put(state, 4, 6, "Obelisk", "pretas")

    actions = set(legal_actions(state))

    assert _action("SPELL", (4, 4), (4, 5), "aimed_shot") not in actions
    assert _action("SPELL", (4, 4), (4, 6), "aimed_shot") not in actions


def test_oracle_inquisitor_silences_enemy_spells_but_not_movement():
    state = _state()
    _put(state, 4, 4, "Inquisitor", "pretas")
    _put(state, 4, 6, "Geomancer", "brancas")

    actions = set(legal_actions(state))

    assert _action("MOVE", (4, 6), (3, 6)) in actions
    assert not any(
        action[0] == "SPELL" and action[1] == (4, 6)
        for action in actions
    )


def test_oracle_frostmage_uses_manhattan_three_spell_envelope():
    state = _state()
    _put(state, 4, 4, "FrostMage")

    actions = set(legal_actions(state))

    assert _action("SPELL", (4, 4), (1, 4), "nevada") in actions
    assert _action("SPELL", (4, 4), (2, 5), "nevada") in actions
    assert _action("SPELL", (4, 4), (0, 0), "nevada") not in actions
    assert _action("SPELL", (4, 4), (4, 4), "nevada") not in actions


def test_oracle_canonicalization_ignores_generation_order_and_deduplicates():
    a = _action("MOVE", (4, 4), (3, 4))
    b = _action("SPELL", (4, 4), (2, 4), "nevada")
    assert canonical_actions([
        type("A", (), {"key": lambda self: a})(),
        type("B", (), {"key": lambda self: b})(),
    ]) == canonical_actions([
        type("B", (), {"key": lambda self: b})(),
        type("A", (), {"key": lambda self: a})(),
        type("A", (), {"key": lambda self: a})(),
    ])
