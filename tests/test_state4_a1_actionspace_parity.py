from __future__ import annotations

from engine.game_state import GameState
from engine.legal_actions import legal_actions as engine_legal_actions
from engine.pieces import criar_peca_por_nome
from tools.analytics.legal_action_oracle import legal_actions as oracle_legal_actions


def _state(name: str, source: tuple[int, int], target: tuple[int, int] | None = None) -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    state.board[source[0]][source[1]] = criar_peca_por_nome(name, "brancas")
    if target is not None:
        state.board[target[0]][target[1]] = criar_peca_por_nome("Bone", "pretas")
    state.compute_initial_hash()
    return state


def _engine_semantics(state: GameState) -> set[tuple]:
    return {
        (action.type.value.upper(), action.start, action.end, action.spell_name, action.spawn_name)
        for action in engine_legal_actions(state)
    }


def test_representative_special_action_space_matches_independent_oracle() -> None:
    cases = {
        "Ranger": _state("Ranger", (6, 0), (4, 0)),
        "Sentry": _state("Sentry", (6, 2), (1, 2)),
        "Phantom": _state("Phantom", (5, 5), (3, 4)),
        "BoneLord": _state("BoneLord", (4, 4), (3, 3)),
        "Lich": _state("Lich", (6, 3)),
        "FrostMage": _state("FrostMage", (6, 3), (4, 3)),
        "Cleric": _state("Cleric", (6, 3)),
        "Trickster": _state("Trickster", (6, 3)),
        "Geomancer": _state("Geomancer", (6, 3)),
        "Pyromancer": _state("Pyromancer", (6, 3), (5, 3)),
        "Dragoon": _state("Dragoon", (6, 3)),
    }

    mismatches = []
    for name, state in cases.items():
        engine_set = _engine_semantics(state)
        oracle_set = set(oracle_legal_actions(state))
        if engine_set != oracle_set:
            mismatches.append({
                "piece": name,
                "engine_only": sorted(engine_set - oracle_set),
                "oracle_only": sorted(oracle_set - engine_set),
            })

    assert not mismatches, mismatches
