from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.legal_actions import legal_actions, resolve_legal_action
from engine.pieces import HERO_DEFS, criar_peca_por_nome


@dataclass(frozen=True)
class FixtureVariant:
    name: str
    enemy_positions: tuple[tuple[int, int], ...] = ()
    allied_positions: tuple[tuple[int, int], ...] = ()
    stunned_allies: tuple[tuple[int, int], ...] = ()


def _state(hero_name: str, fixture: FixtureVariant) -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.tile_effects = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    state.state_history = {}
    state.board[4][4] = criar_peca_por_nome(hero_name, "brancas")

    for row, col in fixture.enemy_positions:
        state.board[row][col] = criar_peca_por_nome("Bone", "pretas")
    for row, col in fixture.allied_positions:
        ally = criar_peca_por_nome("Templar", "brancas")
        if (row, col) in fixture.stunned_allies:
            ally.stun_timer = 1
        state.board[row][col] = ally

    state.compute_initial_hash()
    return state


FIXTURES = (
    FixtureVariant("empty"),
    FixtureVariant(
        "enemy-pressure",
        enemy_positions=((2, 4), (4, 6), (3, 3)),
    ),
    FixtureVariant(
        "ally-pressure",
        allied_positions=((3, 3), (4, 5), (5, 5)),
    ),
    FixtureVariant(
        "mixed-pressure",
        enemy_positions=((2, 4), (4, 6), (3, 3)),
        allied_positions=((4, 5), (5, 5)),
        stunned_allies=((4, 5),),
    ),
)


def _generator_actions(state: GameState, hero_name: str) -> tuple[GameAction, ...]:
    piece = state.board[4][4]
    assert piece is not None and piece.name == hero_name
    generated: set[GameAction] = set()

    for end in piece.get_valid_moves(4, 4, state.board, state.tile_effects):
        generated.add(GameAction(ActionType.MOVE, (4, 4), tuple(end)))

    for end in piece.get_valid_attacks(4, 4, state.board, state.tile_effects):
        generated.add(GameAction(ActionType.ATTACK, (4, 4), tuple(end)))

    for end, info in piece.get_valid_stuns(4, 4, state.board, state.tile_effects).items():
        if info and info.get("has_enemy"):
            area = tuple(tuple(position) for position in info.get("aoe", ()))
            generated.add(GameAction(ActionType.STUN, (4, 4), tuple(end), area=area))

    for row, col, spawn_name in piece.get_valid_spawns(4, 4, state.board, state.tile_effects):
        generated.add(
            GameAction(
                ActionType.SPAWN,
                (4, 4),
                (int(row), int(col)),
                spawn_name=str(spawn_name),
            )
        )

    for spell in piece.get_valid_spells(4, 4, state.board, state.tile_effects):
        if isinstance(spell, dict):
            target = spell.get("target")
            spell_name = spell.get("spell_type")
        else:
            target = spell[0:2]
            spell_name = (
                spell[2]
                if len(spell) >= 3
                else ("jump" if piece.name == "Dragoon" and len(spell) == 2 else None)
            )
        if target is not None and spell_name:
            generated.add(
                GameAction(
                    ActionType.SPELL,
                    (4, 4),
                    tuple(target),
                    spell_name=str(spell_name),
                )
            )

    return tuple(sorted(generated, key=lambda action: action.to_dict().__repr__()))


def _legacy_without_optional_stun_area(action: GameAction) -> dict:
    payload = action.to_dict()
    payload.pop("area", None)
    return payload


@pytest.mark.parametrize("hero_name", tuple(HERO_DEFS))
@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda fixture: fixture.name)
def test_every_piece_generated_action_crosses_canonical_legacy_boundary(
    hero_name: str,
    fixture: FixtureVariant,
) -> None:
    """Piece rule generators must be fully representable by the canonical action space."""
    state = _state(hero_name, fixture)
    generated = _generator_actions(state, hero_name)
    canonical = set(legal_actions(state))

    for action in generated:
        assert action in canonical, (
            f"{hero_name}/{fixture.name}: generator action missing from canonical action space: "
            f"{action.to_dict()}"
        )

        resolved = resolve_legal_action(state, action.to_dict())
        assert resolved == action

        clone = state.fast_clone()
        clone.execute_action(action.to_dict())

        if action.type is ActionType.STUN and action.area:
            legacy_stun = _legacy_without_optional_stun_area(action)
            assert resolve_legal_action(state, legacy_stun) == action


@pytest.mark.parametrize("hero_name", tuple(HERO_DEFS))
@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda fixture: fixture.name)
def test_canonical_action_projection_matches_direct_piece_generators(
    hero_name: str,
    fixture: FixtureVariant,
) -> None:
    """The adapter must neither lose nor invent actions relative to piece generators."""
    state = _state(hero_name, fixture)
    generated = set(_generator_actions(state, hero_name))
    canonical = set(legal_actions(state))

    assert canonical == generated, (
        f"{hero_name}/{fixture.name}: canonical projection differs from direct generators\n"
        f"Generator-only: {sorted(a.to_dict().__repr__() for a in generated - canonical)}\n"
        f"Canonical-only: {sorted(a.to_dict().__repr__() for a in canonical - generated)}"
    )
