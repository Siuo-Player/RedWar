"""Authoritative Python action-space adapter for the RedWar engine.

This module is the single engine-facing place that turns the piece-level legal
move generators into canonical ``GameAction`` values. It deliberately does
not duplicate hero rules: piece implementations remain the rule primitives.
"""
from __future__ import annotations

from typing import Any

from engine.actions import ActionType, GameAction, normalize_action
from engine.config import COLUNAS, LINHAS


def legal_actions(gs: Any) -> tuple[GameAction, ...]:
    """Return all legal actions for the side to move in deterministic order."""
    current_team = "brancas" if gs.white_to_move else "pretas"
    actions: set[GameAction] = set()
    for r in range(LINHAS):
        for c in range(COLUNAS):
            piece = gs.board[r][c]
            if piece is None or piece.team != current_team or not piece.can_act():
                continue
            for end in piece.get_valid_moves(r, c, gs.board, gs.tile_effects):
                actions.add(GameAction(ActionType.MOVE, (r, c), tuple(end)))
            for end in piece.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                actions.add(GameAction(ActionType.ATTACK, (r, c), tuple(end)))
            for end, info in piece.get_valid_stuns(r, c, gs.board, gs.tile_effects).items():
                if not info or not info.get("has_enemy"):
                    continue
                area = tuple(tuple(position) for position in info.get("aoe", ()))
                actions.add(GameAction(ActionType.STUN, (r, c), tuple(end), area=area))
            for spawn_r, spawn_c, spawn_name in piece.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                actions.add(GameAction(ActionType.SPAWN, (r, c), (int(spawn_r), int(spawn_c)), spawn_name=str(spawn_name)))
            for spell in piece.get_valid_spells(r, c, gs.board, gs.tile_effects):
                if isinstance(spell, dict):
                    target = spell.get("target")
                    spell_name = spell.get("spell_type")
                else:
                    target = spell[0:2]
                    spell_name = spell[2] if len(spell) >= 3 else (
                        "jump" if piece.name == "Dragoon" and len(spell) == 2 else None
                    )
                if target is None or not spell_name:
                    continue
                actions.add(GameAction(ActionType.SPELL, (r, c), tuple(target), spell_name=str(spell_name)))
    return tuple(sorted(actions, key=_action_key))


def _declared_spell_names(gs: Any, piece: Any) -> set[str]:
    """Return spells owned by a hero from the canonical hero configuration."""
    from engine.pieces import HERO_DEFS

    definition = HERO_DEFS.get(piece.name, {}) or {}
    names = {str(name).lower() for name in definition.get("spells", []) if name}
    attack = (definition.get("behavior") or {}).get("attack") or {}
    if attack.get("attack_action") == "spell" and attack.get("spell_name"):
        names.add(str(attack["spell_name"]).lower())
    return names


def resolve_legal_action(gs: Any, action: GameAction) -> GameAction:
    """Resolve an input to a canonical execution representation."""
    normalized = normalize_action(action)
    available = legal_actions(gs)
    if normalized in available:
        return normalized

    if normalized.type is ActionType.STUN and not normalized.area:
        compatible = tuple(
            candidate for candidate in available
            if candidate.type is ActionType.STUN
            and candidate.start == normalized.start
            and candidate.end == normalized.end
            and candidate.spawn_name == normalized.spawn_name
            and candidate.spell_name == normalized.spell_name
        )
        if len(compatible) == 1:
            return compatible[0]

    if normalized.type is ActionType.SPELL:
        start_row, start_col = normalized.start
        piece = gs.board[start_row][start_col]
        current_team = "brancas" if gs.white_to_move else "pretas"
        spell_name = (normalized.spell_name or "").lower()
        if piece is None or piece.team != current_team or spell_name not in _declared_spell_names(gs, piece):
            raise ValueError(f"illegal action for current position: {normalized.to_dict()}")

    validator = getattr(gs, "_validate_transition", None)
    if validator is not None:
        try:
            validator(
                normalized.start,
                normalized.end,
                normalized.type.value,
                affected_area=list(normalized.area),
                spawn_name=normalized.spawn_name,
                spell_name=normalized.spell_name,
            )
        except ValueError:
            return normalized

    raise ValueError(f"illegal action for current position: {normalized.to_dict()}")


def is_legal_action(gs: Any, action: GameAction) -> bool:
    """Return whether ``action`` is present in the authoritative action space."""
    if not isinstance(action, GameAction):
        raise TypeError("action must be a GameAction")
    return action in set(legal_actions(gs))


def to_legacy_dict(action: GameAction) -> dict[str, Any]:
    """Cross the canonical-to-legacy boundary explicitly at integration edges."""
    if not isinstance(action, GameAction):
        raise TypeError("action must be a GameAction")
    return action.to_dict()


def to_legacy_dicts(actions: tuple[GameAction, ...] | list[GameAction]) -> list[dict[str, Any]]:
    """Convert a canonical action collection without changing its ordering."""
    return [to_legacy_dict(action) for action in actions]


def _action_key(action: GameAction) -> tuple[Any, ...]:
    """Stable ordering key independent of object identity or hash randomization."""
    return (action.type.value, action.start, action.end, action.spell_name or "", action.spawn_name or "", action.area)
