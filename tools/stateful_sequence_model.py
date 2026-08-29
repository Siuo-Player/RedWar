"""State-aware sequence generation for RedWar correctness experiments."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any, Iterable

from engine.config import LINHAS, COLUNAS


@dataclass(frozen=True)
class SequenceStep:
    index: int
    action: dict[str, Any]


def legal_actions(gs) -> list[dict[str, Any]]:
    """Enumerate actions using the existing GameState/piece semantics."""
    actions: list[dict[str, Any]] = []
    active_team = "brancas" if gs.white_to_move else "pretas"
    for r in range(LINHAS):
        for c in range(COLUNAS):
            piece = gs.board[r][c]
            if not piece or piece.team != active_team or not piece.can_act():
                continue
            for target in piece.get_valid_moves(r, c, gs.board, gs.tile_effects):
                actions.append({"type": "move", "start": (r, c), "end": tuple(target)})
            for target in piece.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                actions.append({"type": "attack", "start": (r, c), "end": tuple(target)})
            for target, info in piece.get_valid_stuns(r, c, gs.board, gs.tile_effects).items():
                if info and info.get("has_enemy"):
                    actions.append({
                        "type": "stun", "start": (r, c), "end": tuple(target),
                        "area": list(info.get("aoe", [])),
                    })
            for spawn in piece.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                actions.append({
                    "type": "spawn", "start": (r, c), "end": (spawn[0], spawn[1]),
                    "spawn_name": spawn[2],
                })
            for spell in piece.get_valid_spells(r, c, gs.board, gs.tile_effects):
                if isinstance(spell, dict):
                    name = spell.get("spell_type")
                    target = spell.get("target")
                    if name and target is not None:
                        actions.append({
                            "type": "spell", "start": (r, c), "end": tuple(target),
                            "spell_name": name,
                        })
                elif isinstance(spell, (tuple, list)) and len(spell) >= 3 and spell[2]:
                    actions.append({
                        "type": "spell", "start": (r, c), "end": (spell[0], spell[1]),
                        "spell_name": spell[2],
                    })
    return actions


def generate_legal_sequence(gs, seed: int, length: int = 32) -> list[dict[str, Any]]:
    """Generate a deterministic sequence by sampling only currently legal actions."""
    if length < 0:
        raise ValueError("length must be non-negative")
    rng = random.Random(seed)
    working = gs.fast_clone()
    sequence: list[dict[str, Any]] = []
    for _ in range(length):
        if working.game_over:
            break
        candidates = legal_actions(working)
        if not candidates:
            break
        action = rng.choice(candidates)
        sequence.append(action)
        working.execute_action(action)
    return sequence


def execute_with_trace(gs, sequence: Iterable[dict[str, Any]]) -> list[SequenceStep]:
    """Execute a sequence and retain its ordered semantic actions."""
    trace: list[SequenceStep] = []
    for index, action in enumerate(sequence):
        gs.execute_action(action)
        trace.append(SequenceStep(index, action.copy()))
    return trace


def first_divergence(expected: Iterable[str], actual: Iterable[str]) -> int | None:
    """Return the first differing representation or first length mismatch."""
    left, right = list(expected), list(actual)
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return index
    return min(len(left), len(right)) if len(left) != len(right) else None
