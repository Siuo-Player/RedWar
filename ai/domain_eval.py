# ai/domain_eval.py
"""
Domain-Specific Evaluation Engine for RedWar (Ares AI Core).
Adapts Stockfish-style minimax evaluation specifically to RedWar mechanics:
2-Stun survival horizons, emergent mechanics synergies, and lethal terrain knockback physics.
"""
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

        # 2. Domain-Specific: 2-Stun Horizon Evaluation
        # If an enemy has stun_timer > 0 and is in striking distance of an ally,
        # that piece is facing immediate permanent death.
        for e_r, e_c, enemy in enemies:
            e_stun = getattr(enemy, "stun_timer", 0)
            if e_stun > 0:
                # Enemy is stunned: can an ally reach it this turn?
                for a_r, a_c, ally in allies:
                    dist = max(abs(a_r - e_r), abs(a_c - e_c))
                    if dist <= 3:  # Reachable range
                        # Impending elimination bonus proportional to piece value
                        score += float(getattr(enemy, "cost", 50)) * 1.6
                        break
            else:
                # Normal enemy: slight threat if ally is near
                for a_r, a_c, ally in allies:
                    dist = max(abs(a_r - e_r), abs(a_c - e_c))
                    if dist <= 1:
                        score += 10.0
                        break

        # 3. Defensive: Check if allies are stunned and exposed to enemy lethal follow-up
        for a_r, a_c, ally in allies:
            a_stun = getattr(ally, "stun_timer", 0)
            if a_stun > 0:
                for e_r, e_c, enemy in enemies:
                    dist = max(abs(a_r - e_r), abs(a_c - e_c))
                    if dist <= 3:
                        score -= float(getattr(ally, "cost", 50)) * 1.6
                        break

        # 4. Emergent Mechanics Synergies
        detected_synergies = self.matrix.detect_spatial_synergies(state, team)
        for syn in detected_synergies:
            score += syn.value

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
