"""Independent legal-action reference for the A0 C3 gate.

This module intentionally does not call Piece.get_valid_* methods or Ares
move-generation/search code.  It implements small, explicit predicates from
the published RedWar rule model so that cross-implementation agreement can be
checked against a separate code path.
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
        return (
            self.action_type,
            self.start,
            self.end,
            self.spell_name,
            self.spawn_name,
        )


def canonical_actions(actions: list[OracleAction] | set[OracleAction]) -> tuple[tuple[Any, ...], ...]:
    return tuple(sorted(action.key() for action in actions))


def _inside(r: int, c: int) -> bool:
    return 0 <= r < ROWS and 0 <= c < COLS


def _piece(board: list[list[Any]], r: int, c: int) -> Any:
    return board[r][c]


def _effect_is_ice(tile_effects: list[list[Any]] | None, r: int, c: int) -> bool:
    if tile_effects is None:
        return False
    effect = tile_effects[r][c]
    return bool(effect and effect.get("type") == "ice")


def _team_name(piece: Any) -> str:
    return str(piece.team)


def _side_name(state: Any) -> str:
    return "brancas" if bool(state.white_to_move) else "pretas"


def _silenced(state: Any, row: int, col: int, team: str) -> bool:
    board = state.board
    for r in range(ROWS):
        for c in range(COLS):
            source = board[r][c]
            if source is None or source.name != "Inquisitor" or _team_name(source) == team:
                continue
            if getattr(source, "stun_timer", 0) != 0:
                continue
            if max(abs(row - r), abs(col - c)) <= 2:
                return True
    return False


def _ray_actions(
    *,
    state: Any,
    r: int,
    c: int,
    vectors: tuple[tuple[int, int], ...],
    max_steps: int,
    min_steps: int,
    action_type: str,
    spell_name: str | None = None,
) -> list[OracleAction]:
    board = state.board
    effects = state.tile_effects
    team = _team_name(board[r][c])
    out: list[OracleAction] = []
    for dr, dc in vectors:
        for step in range(1, max_steps + 1):
            nr, nc = r + dr * step, c + dc * step
            if not _inside(nr, nc) or _effect_is_ice(effects, nr, nc):
                break
            target = _piece(board, nr, nc)
            if target is None:
                continue
            if _team_name(target) != team and step >= min_steps and not _silenced(state, r, c, team):
                out.append(OracleAction(action_type, (r, c), (nr, nc), spell_name=spell_name))
            break
    return out


def _movement_actions(state: Any, r: int, c: int, piece: Any) -> list[OracleAction]:
    if getattr(piece, "stun_timer", 0) != 0:
        return []

    name = piece.name
    team = _team_name(piece)
    board = state.board
    effects = state.tile_effects

    if name in {"Obelisk", "StoneWall"}:
        vectors: tuple[tuple[int, int], ...] = ()
        max_steps = 0
        ghost = False
    elif name in {"Lich", "Cleric", "Pyromancer"}:
        vectors, max_steps, ghost = DIAGONAL, 1, False
    elif name in {"FrostMage"}:
        vectors, max_steps, ghost = DIAGONAL, 2, False
    elif name in {"Nightshade"}:
        vectors, max_steps, ghost = ORTHOGONAL, 4, True
    elif name in {"Bone", "Obelisk", "Sentry", "Ranger", "Templar", "Geomancer"}:
        vectors, max_steps, ghost = ORTHOGONAL, 1, False
    elif name in {"BoneLord", "Berserker", "Inquisitor"}:
        vectors, max_steps, ghost = ADJACENT, 1, False
    elif name in {"Phantom", "Trickster"}:
        vectors, max_steps, ghost = KNIGHT, 1, False
    elif name == "Ghoul":
        # Black moves in the positive row direction, white in the negative.
        raw = ((1, -1), (1, 0), (1, 1))
        vectors = tuple((-dr, dc) if team == "brancas" else (dr, dc) for dr, dc in raw)
        max_steps, ghost = 1, False
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

    name = piece.name
    if name in {"FrostMage", "Lich", "Cleric", "Trickster", "Geomancer", "Pyromancer", "Dragoon", "Inquisitor", "BoneLord", "Phantom", "Sentry", "Ranger"}:
        spell_attacks = {
            "Phantom": (KNIGHT, 1, "spectral_strike"),
            "Sentry": (ORTHOGONAL, 8, "sentinel_shot"),
            "Ranger": (ORTHOGONAL, 8, "aimed_shot"),
            "BoneLord": (((-1, -1), (-1, 1), (-2, -2), (-2, 2)), 1, "bone_v"),
        }
        spec = spell_attacks.get(name)
        if spec is not None:
            vectors, max_steps, spell = spec
            min_steps = 2 if name == "Ranger" else 1
            return _ray_actions(
                state=state,
                r=r,
                c=c,
                vectors=tuple(vectors),
                max_steps=max_steps,
                min_steps=min_steps,
                action_type="SPELL",
                spell_name=spell,
            )
        return []

    if name == "Ghoul":
        raw = ((1, -1), (1, 0), (1, 1))
        vectors = tuple((-dr, dc) if piece.team == "brancas" else (dr, dc) for dr, dc in raw)
        return _ray_actions(state=state, r=r, c=c, vectors=vectors, max_steps=1, min_steps=1, action_type="ATTACK")

    geometry = {
        "Bone": (ORTHOGONAL, 1),
        "Obelisk": (ORTHOGONAL, 1),
        "Templar": (ORTHOGONAL, 1),
        "Berserker": (ADJACENT, 1),
        "Inquisitor": (ADJACENT, 1),
        "Nightshade": (ORTHOGONAL, 1),
    }
    spec = geometry.get(name)
    if spec is None:
        return []
    vectors, max_steps = spec
    return _ray_actions(state=state, r=r, c=c, vectors=tuple(vectors), max_steps=max_steps, min_steps=1, action_type="ATTACK")


def _spell_actions(state: Any, r: int, c: int, piece: Any) -> list[OracleAction]:
    if getattr(piece, "stun_timer", 0) != 0 or _silenced(state, r, c, _team_name(piece)):
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
                if dr == 0 and dc == 0 or abs(dr) + abs(dc) > 3:
                    continue
                fr, fc = r + dr, c + dc
                if not _inside(fr, fc) or _effect_is_ice(effects, fr, fc):
                    continue
                out.append(OracleAction("SPELL", (r, c), (fr, fc), spell_name="nevada"))

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
                if _inside(nr, nc) and (nr, nc) != (r, c) and board[nr][nc] is not None and board[nr][nc].team == piece.team:
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
        max_jump = 2
        for dr, dc in (*ORTHOGONAL, *DIAGONAL):
            for step in range(2, max_jump + 1):
                nr, nc = r + dr * step, c + dc * step
                if not _inside(nr, nc) or _effect_is_ice(effects, nr, nc):
                    break
                target = board[nr][nc]
                if target is None:
                    out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="jump"))
                else:
                    if target.team != piece.team:
                        out.append(OracleAction("SPELL", (r, c), (nr, nc), spell_name="jump"))
                    break

    return out


def legal_actions(state: Any) -> tuple[tuple[Any, ...], ...]:
    """Return a canonical independent action set for a RedWar GameState-like object."""
    team = _side_name(state)
    actions: list[OracleAction] = []
    for r in range(ROWS):
        for c in range(COLS):
            piece = state.board[r][c]
            if piece is None or _team_name(piece) != team or getattr(piece, "stun_timer", 0) != 0:
                continue
            actions.extend(_movement_actions(state, r, c, piece))
            actions.extend(_attack_actions(state, r, c, piece))
            actions.extend(_spell_actions(state, r, c, piece))
    return canonical_actions(actions)
