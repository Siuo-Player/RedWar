"""Independent legal-action reference for the A0 C3 gate.

This module intentionally does not call Piece.get_valid_* methods or Ares
move-generation/search code. It uses explicit, small predicates so that
cross-implementation agreement is not based on calling the implementation
under test.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ROWS = COLS = 8

ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
ADJACENT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
KNIGHT = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))


@dataclass(frozen=True, slots=True)
class OracleAction:
    action_type: str
    start: tuple[int, int]
    end: tuple[int, int]
    spell_name: str | None = None
    spawn_name: str | None = None

    def key(self) -> tuple[Any, ...]:
        return (self.action_type, self.start, self.end, self.spell_name, self.spawn_name)


def canonical_actions(actions: list[OracleAction] | set[OracleAction]) -> tuple[tuple[Any, ...], ...]:
    """Canonical semantic action set: deterministic ordering + deduplication."""
    return tuple(sorted({action.key() for action in actions}))


def _inside(r: int, c: int) -> bool:
    return 0 <= r < ROWS and 0 <= c < COLS


def _effect_is_ice(tile_effects: list[list[Any]] | None, r: int, c: int) -> bool:
    if tile_effects is None:
        return False
    effect = tile_effects[r][c]
    return bool(effect and effect.get("type") == "ice")


def _team(piece: Any) -> str:
    return str(piece.team)


def _side_name(state: Any) -> str:
    return "brancas" if bool(state.white_to_move) else "pretas"


def _silenced(state: Any, row: int, col: int, team: str) -> bool:
    for r in range(ROWS):
        for c in range(COLS):
            source = state.board[r][c]
            if source is None or source.name != "Inquisitor" or _team(source) == team:
                continue
            if getattr(source, "stun_timer", 0) != 0:
                continue
            if max(abs(row - r), abs(col - c)) <= 2:
                return True
    return False


def _ray_actions(state: Any, r: int, c: int, vectors: tuple[tuple[int, int], ...], max_steps: int,
                 min_steps: int, action_type: str, spell_name: str | None = None) -> list[OracleAction]:
    board = state.board
    effects = state.tile_effects
    team = _team(board[r][c])
    out: list[OracleAction] = []
    silenced = action_type == "SPELL" and _silenced(state, r, c, team)
    if silenced:
        return out
    for dr, dc in vectors:
        for step in range(1, max_steps + 1):
            nr, nc = r + dr * step, c + dc * step
            if not _inside(nr, nc) or _effect_is_ice(effects, nr, nc):
                break
            target = board[nr][nc]
            if target is None:
                continue
            if _team(target) != team and step >= min_steps:
                out.append(OracleAction(action_type, (r, c), (nr, nc), spell_name=spell_name))
            break
    return out


def _movement_actions(state: Any, r: int, c: int, piece: Any) -> list[OracleAction]:
    board = state.board
    effects = state.tile_effects
    team = _team(piece)
    name = piece.name
    if name in {"Obelisk", "StoneWall"}:
        vectors, max_steps, ghost = (), 0, False
    elif name in {"Lich", "Cleric", "Pyromancer"}:
        vectors, max_steps, ghost = DIAGONAL, 1, False
    elif name == "FrostMage":
        vectors, max_steps, ghost = DIAGONAL, 2, False
    elif name == "Nightshade":
        vectors, max_steps, ghost = ORTHOGONAL, 4, True
    elif name in {"Bone", "Sentry", "Ranger", "Templar", "Geomancer"}:
        vectors, max_steps, ghost = ORTHOGONAL, 1, False
    elif name in {"BoneLord", "Berserker", "Inquisitor"}:
        vectors, max_steps, ghost = ADJACENT, 1, False
    elif name in {"Phantom", "Trickster"}:
        vectors, max_steps, ghost = KNIGHT, 1, False
    elif name == "Ghoul":
        raw = ((1, -1), (1, 0), (1, 1))
        vectors, max_steps, ghost = tuple((-dr, dc) if team == "brancas" else (dr, dc) for dr, dc in raw), 1, False
    elif name == "Dragoon":
        vectors, max_steps, ghost = ORTHOGONAL, 1, False
    else:
        vectors, max_steps, ghost = (), 0, False

    out: list[OracleAction] = []
    for dr, dc in vectors:
        for step in range(1, max_steps + 1):
            nr, nc = r + dr * step, c + dc * step
            if not _inside(nr, nc) or _effect_is_ice(effects, nr, nc):
                break
            if board[nr][nc] is not None:
                if ghost:
                    continue
                break
            out.append(OracleAction("MOVE", (r, c), (nr, nc)))
    return out


def _attack_actions(state: Any, r: int, c: int, piece: Any) -> list[OracleAction]:
    if getattr(piece, "stun_timer", 0) != 0:
        return []
    spell_attacks = {
        "Phantom": (KNIGHT, 1, 1, "spectral_strike"),
        "Sentry": (ORTHOGONAL, 8, 1, "sentinel_shot"),
        "Ranger": (ORTHOGONAL, 8, 2, "aimed_shot"),
        "BoneLord": (((-1, -1), (-1, 1), (-2, -2), (-2, 2)), 1, 1, "bone_v"),
    }
    if piece.name in spell_attacks:
        vectors, max_steps, min_steps, spell = spell_attacks[piece.name]
        return _ray_actions(state, r, c, tuple(vectors), max_steps, min_steps, "SPELL", spell)

    if piece.name == "Ghoul":
        raw = ((1, -1), (1, 0), (1, 1))
        vectors = tuple((-dr, dc) if piece.team == "brancas" else (dr, dc) for dr, dc in raw)
        return _ray_actions(state, r, c, vectors, 1, 1, "ATTACK")

    geometry = {
        "Bone": (ORTHOGONAL, 1),
        "Obelisk": (ORTHOGONAL, 1),
        "Templar": (ORTHOGONAL, 1),
        "Berserker": (ADJACENT, 1),
        "Dragoon": (ORTHOGONAL, 1),
        "Inquisitor": (ADJACENT, 1),
        "Nightshade": (ORTHOGONAL, 1),
    }
    spec = geometry.get(piece.name)
    if spec is None:
        return []
    vectors, max_steps = spec
    return _ray_actions(state, r, c, tuple(vectors), max_steps, 1, "ATTACK")


def _spell_actions(state: Any, r: int, c: int, piece: Any) -> list[OracleAction]:
    if getattr(piece, "stun_timer", 0) != 0 or _silenced(state, r, c, _team(piece)):
        return []
    board = state.board
    effects = state.tile_effects
    name = piece.name
    out: list[OracleAction] = []

    if name == "Lich" and getattr(piece, "spawn_cooldown", 0) == 0:
        direction = -1 if piece.team == "brancas" else 1
        for dc in (-1, 0, 1):
            nr, nc = r + direction, c + dc
            if _inside(nr, nc) and board[nr][nc] is None and not _effect_is_ice(effects, nr, nc):
                out.append(OracleAction("SPAWN", (r, c), (nr, nc), spawn_name="Ghoul"))

    elif name == "FrostMage":
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if (dr == 0 and dc == 0) or abs(dr) + abs(dc) > 3:
                    continue
                nr, nc = r + dr, c + dc
                if _inside(nr, nc) and not _effect_is_ice(effects, nr, nc):
                    out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="nevada"))

    elif name == "Cleric":
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if not _inside(nr, nc):
                    continue
                target = board[nr][nc]
                if target is not None and target.team == piece.team and getattr(target, "stun_timer", 0) > 0:
                    out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="purify"))

    elif name == "Trickster":
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nr, nc = r + dr, c + dc
                if _inside(nr, nc) and (nr, nc) != (r, c):
                    target = board[nr][nc]
                    if target is not None and target.team == piece.team:
                        out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="swap"))

    elif name == "Geomancer":
        for dr, dc in ADJACENT:
            nr, nc = r + dr, c + dc
            if _inside(nr, nc) and board[nr][nc] is None:
                out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="barricade"))

    elif name == "Pyromancer":
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not _inside(nr, nc):
                    continue
                target = board[nr][nc]
                if target is None or target.team != piece.team:
                    out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="ignite"))

    elif name == "Dragoon":
        for dr, dc in (*ORTHOGONAL, *DIAGONAL):
            nr, nc = r + dr * 2, c + dc * 2
            if not _inside(nr, nc) or _effect_is_ice(effects, nr, nc):
                continue
            target = board[nr][nc]
            if target is None or target.team != piece.team:
                out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="jump"))

    return out


def legal_actions(state: Any) -> tuple[tuple[Any, ...], ...]:
    """Return canonical legal actions for a GameState-like object."""
    team = _side_name(state)
    actions: list[OracleAction] = []
    for r in range(ROWS):
        for c in range(COLS):
            piece = state.board[r][c]
            if piece is None or _team(piece) != team or getattr(piece, "stun_timer", 0) != 0:
                continue
            actions.extend(_movement_actions(state, r, c, piece))
            actions.extend(_attack_actions(state, r, c, piece))
            actions.extend(_spell_actions(state, r, c, piece))
    return canonical_actions(actions)
