# ai/domain_eval.py
"""
Domain-Specific Evaluation Engine for RedWar (Ares AI Core).
Adapts Stockfish-style minimax evaluation specifically to RedWar mechanics:
2-Stun survival horizons with distance lethality gradients, emergent mechanics synergies,
and lethal terrain knockback physics.
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Optional
from engine.game_state import GameState
from engine.hero_matrix import HeroMatrix


class RedWarDomainEvaluator:
    """
    Evaluator that replaces generic chess heuristics with RedWar's domain-specific
    mechanics: stun-to-death windows, spatial combos, and hazard lethality.
    """
    def __init__(self):
        self.matrix = HeroMatrix()

    def evaluate(self, state: GameState, team: str) -> float:
        """
        Evaluate position for 'team' in centipawns.
        Positive value favors 'team'.
        """
        enemy_team = "pretas" if team == "brancas" else "brancas"
        score = 0.0

        allies = []
        enemies = []
        for r in range(len(state.board)):
            for c in range(len(state.board[0])):
                p = state.board[r][c]
                if p:
                    if p.team == team:
                        allies.append((r, c, p))
                    else:
                        enemies.append((r, c, p))

        # 1. Base Material Score
        ally_material = sum(getattr(p, "cost", 50) for _, _, p in allies)
        enemy_material = sum(getattr(p, "cost", 50) for _, _, p in enemies)
        score += float(ally_material - enemy_material)

        # 2. Domain-Specific: 2-Stun Horizon Evaluation with Distance Lethality Gradient
        # If an enemy has stun_timer > 0 and is in striking distance of an ally,
        # that piece faces imminent permanent elimination.
        for e_r, e_c, enemy in enemies:
            e_stun = getattr(enemy, "stun_timer", 0)
            e_cost = float(getattr(enemy, "cost", 50))
            if e_stun > 0:
                # Enemy is stunned: can an ally reach and execute it?
                min_ally_dist = 99
                for a_r, a_c, _ in allies:
                    d = max(abs(a_r - e_r), abs(a_c - e_c))
                    if d < min_ally_dist:
                        min_ally_dist = d
                if min_ally_dist <= 3:
                    # Chebyshev distance gradient: dist=1 -> 0.6375, dist=2 -> 0.425, dist=3 -> 0.25
                    lethality_weight = max(0.25, (4 - min_ally_dist) / 4.0 * 0.85)
                    score += e_cost * lethality_weight
            else:
                # Un-stunned enemy: tactical proximity pressure
                for a_r, a_c, _ in allies:
                    dist = max(abs(a_r - e_r), abs(a_c - e_c))
                    if dist <= 1:
                        score += 2.0
                        break

        # 3. Defensive: Check if allies are stunned and exposed to enemy lethal execution
        for a_r, a_c, ally in allies:
            a_stun = getattr(ally, "stun_timer", 0)
            a_cost = float(getattr(ally, "cost", 50))
            if a_stun > 0:
                min_enemy_dist = 99
                for e_r, e_c, _ in enemies:
                    d = max(abs(a_r - e_r), abs(a_c - e_c))
                    if d < min_enemy_dist:
                        min_enemy_dist = d
                if min_enemy_dist <= 3:
                    # dist=1 -> 0.675, dist=2 -> 0.450, dist=3 -> 0.300
                    vulnerability_weight = max(0.30, (4 - min_enemy_dist) / 4.0 * 0.90)
                    score -= a_cost * vulnerability_weight

        # 4. Emergent Mechanics Synergies
        detected_synergies = self.matrix.detect_spatial_synergies(state, team)
        for syn in detected_synergies:
            score += syn.value

        # 5. Positional Spatial Dominance & Center Control
        for r, c, ally in allies:
            dist = abs(r - 3.5) + abs(c - 3.5)
            score += max(0.0, (7.0 - dist) * 1.5)
        for r, c, enemy in enemies:
            dist = abs(r - 3.5) + abs(c - 3.5)
            score -= max(0.0, (7.0 - dist) * 1.5)

        return score

    def evaluate_hazard_opportunities(
        self,
        state: GameState,
        hazards: Dict[str, List[Tuple[int, int]]],
        team: str
    ) -> float:
        """
        Evaluate offensive knockback-to-lava opportunities and defensive hazard avoidance.
        """
        offensive_push = self.matrix.evaluate_push_hazard_threat(state, hazards, team)
        enemy_team = "pretas" if team == "brancas" else "brancas"
        defensive_danger = self.matrix.evaluate_push_hazard_threat(state, hazards, enemy_team)
        return offensive_push - defensive_danger
