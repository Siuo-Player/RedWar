"""Opening book heuristics and master setup repertoire for Ares AI in RedWar.

Provides instant book evaluation during early plies (turn_count <= 4) to preserve
clock budget for complex middlegame and endgame tactical complications.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from engine.legal_actions import legal_actions, to_legacy_dicts


def get_opening_move(state: Any, team: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Probe the opening book for a principled development move.

    Returns a legal action dict if an opening rule matches, else None.
    """
    if len(getattr(state, "move_log", [])) > 8:
        return None

    if team is None:
        team = "brancas" if getattr(state, "white_to_move", True) else "pretas"

    actions = to_legacy_dicts(legal_actions(state))
    if not actions:
        return None

    # Check for direct tactical opportunities first (e.g. free capture/kill in opening)
    for act in actions:
        m_type = str(act.get("type", "")).lower()
        if m_type in ("attack", "stun"):
            end = act.get("end")
            if end:
                target = state.board[end[0]][end[1]]
                if target and target.stun_timer > 0:
                    # Immediate lethal 2-hit stun kill takes precedence even in book
                    return act

    # Score opening development moves
    # Principles:
    # 1. Advance toward central files and ranks (rows 3, 4, cols 2, 3, 4, 5)
    # 2. Advance mobile flankers and controllers (Valkyrie, Duelist, Arcanist, Marksman, Warden, Illusionist)
    # 3. Avoid moving same piece twice unnecessarily
    # 4. Do not move vulnerable spawners into direct enemy melee lines
    scored_moves: list[tuple[float, dict[str, Any]]] = []

    for act in actions:
        start = act.get("start")
        end = act.get("end")
        if not start or not end:
            continue

        piece = state.board[start[0]][start[1]]
        if not piece or piece.team != team:
            continue

        score = 0.0
        sr, sc = start
        er, ec = end

        # Center control bonus (distance to center 3.5, 3.5)
        dist_before = abs(sr - 3.5) + abs(sc - 3.5)
        dist_after = abs(er - 3.5) + abs(ec - 3.5)
        center_progress = dist_before - dist_after
        score += center_progress * 15.0

        # Development of backline pieces forward
        if team == "brancas":
            forward_progress = sr - er  # Moving up rows 7 -> 6 -> 5 ...
        else:
            forward_progress = er - sr  # Moving down rows 0 -> 1 -> 2 ...
        score += forward_progress * 10.0

        # Vanguard & high-tempo hero preferences
        hero_name = piece.name
        if hero_name in ("Valkyrie", "Duelist", "Arcanist", "Warden", "Paladin", "Ranger", "Marksman", "Illusionist"):
            score += 25.0
        elif hero_name in ("BoneLord", "Lich", "Inquisitor"):
            # High-value casters prefer staying shielded initially
            score += 5.0

        # Hero-specific strategic development for new 30-hero roster
        if hero_name == "Illusionist" and er in (2, 3, 4, 5):
            score += 10.0
        elif hero_name == "Marksman" and (er in (2, 3, 4, 5) or ec in (2, 3, 4, 5)):
            score += 10.0

        # Small tie-breaking jitter for repertoire diversity
        score += random.uniform(0.0, 3.0)

        scored_moves.append((score, act))

    if not scored_moves:
        return None

    scored_moves.sort(key=lambda item: item[0], reverse=True)
    best_candidate = scored_moves[0]
    if best_candidate[0] > 10.0:
        return best_candidate[1]

    return None
