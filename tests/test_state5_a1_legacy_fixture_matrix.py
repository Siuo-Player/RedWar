from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine.actions import GameAction, normalize_action
from engine.game_state import GameState
from engine.legal_actions import legal_actions, resolve_legal_action
from engine.pieces import criar_peca_por_nome


@dataclass(frozen=True)
class LegacyFixture:
    hero: str
    action: dict
    enemy: tuple[int, int] | None = None
    allied: tuple[int, int] | None = None
    stun_allied: bool = False


def _state(fixture: LegacyFixture) -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    state.board[4][4] = criar_peca_por_nome(fixture.hero, "brancas")

    if fixture.enemy is not None:
        state.board[fixture.enemy[0]][fixture.enemy[1]] = criar_peca_por_nome("Bone", "pretas")
    if fixture.allied is not None:
        ally = criar_peca_por_nome("Bone", "brancas")
        if fixture.stun_allied:
            ally.stun_timer = 1
        state.board[fixture.allied[0]][fixture.allied[1]] = ally

    state.compute_initial_hash()
    return state


FIXTURES = (
    LegacyFixture("Phantom", {"type": "spell", "start": (4, 4), "end": (2, 5), "spell_name": "spectral_strike"}, enemy=(2, 5)),
    LegacyFixture("Sentry", {"type": "spell", "start": (4, 4), "end": (4, 5), "spell_name": "sentinel_shot"}, enemy=(4, 5)),
    LegacyFixture("Ranger", {"type": "spell", "start": (4, 4), "end": (4, 6), "spell_name": "aimed_shot"}, enemy=(4, 6)),
    LegacyFixture("BoneLord", {"type": "spell", "start": (4, 4), "end": (3, 3), "spell_name": "bone_v"}, enemy=(3, 3)),
    LegacyFixture("FrostMage", {"type": "spell", "start": (4, 4), "end": (4, 6), "spell_name": "nevada"}, enemy=(3, 6)),
    LegacyFixture("Lich", {"type": "spawn", "start": (4, 4), "end": (3, 3), "spawn_name": "Ghoul"}),
    LegacyFixture("Pyromancer", {"type": "spell", "start": (4, 4), "end": (4, 6), "spell_name": "ignite"}, enemy=(4, 6)),
    LegacyFixture("Dragoon", {"type": "spell", "start": (4, 4), "end": (4, 6), "spell_name": "jump"}, allied=(4, 5)),
    LegacyFixture("Cleric", {"type": "spell", "start": (4, 4), "end": (4, 6), "spell_name": "purify"}, allied=(4, 6), stun_allied=True),
    LegacyFixture("Trickster", {"type": "spell", "start": (4, 4), "end": (4, 6), "spell_name": "swap"}, allied=(4, 6)),
    LegacyFixture("Geomancer", {"type": "spell", "start": (4, 4), "end": (4, 5), "spell_name": "barricade"}),
)


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda fixture: fixture.hero)
def test_legacy_fixture_resolves_to_an_enumerated_canonical_action(fixture: LegacyFixture) -> None:
    state = _state(fixture)
    normalized = normalize_action(fixture.action)
    resolved = resolve_legal_action(state, normalized)

    assert isinstance(resolved, GameAction)
    assert resolved in set(legal_actions(state))
    assert resolved.type.value == fixture.action["type"]
    assert resolved.start == fixture.action["start"]
    assert resolved.end == fixture.action["end"]
    if "spell_name" in fixture.action:
        assert resolved.spell_name == fixture.action["spell_name"]
    if "spawn_name" in fixture.action:
        assert resolved.spawn_name == fixture.action["spawn_name"]

    clone = state.fast_clone()
    clone.execute_action(fixture.action)
