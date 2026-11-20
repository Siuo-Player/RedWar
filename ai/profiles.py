# ai/profiles.py
"""
Mode-specialized Ares AI Engine Profiles for RedWar.
Each profile tailors evaluation weights, tactical heuristics,
and search parameters to the specific rules and geometry of each game mode.
"""
from typing import Dict, Any, List, Optional
from engine.game_state import GameState


class AresProfile:
    """Base class for all mode-specialized Ares AI profiles."""
    name: str = "base"

    def evaluate(self, state: GameState) -> float:
        """Evaluate position from white's perspective in centipawns."""
        white_val = sum(p.cost for row in state.board for p in row if p and p.team == "brancas")
        black_val = sum(p.cost for row in state.board for p in row if p and p.team == "pretas")
        return float(white_val - black_val)

    def get_search_params(self) -> Dict[str, Any]:
        """Return search parameters for this profile."""
        return {
            "depth_extension": 1,
            "territory_weight": 0.05,
            "tactical_aggression": 1.0,
        }


class StandardAresProfile(AresProfile):
    """
    Optimized for Standard 8×8 mode.
    Focuses on quick tempo, rapid piece development, and decisive 2-stun executions.
    """
    name = "standard_8x8"

    def evaluate(self, state: GameState) -> float:
        score = super().evaluate(state)
        # Bonus for central control on 8x8
        for r in range(2, 6):
            for c in range(2, 6):
                p = state.board[r][c]
                if p:
                    mult = 1.0 if p.team == "brancas" else -1.0
                    score += mult * 4.0
        return score

    def get_search_params(self) -> Dict[str, Any]:
        return {
            "depth_extension": 1,
            "territory_weight": 0.05,
            "tactical_aggression": 1.2,
            "killer_slots": 2,
        }


class GrandAresProfile(AresProfile):
    """
    Optimized for Grand 10×10 mode.
    Prioritizes territorial expansion, long-range sniper lanes, and multi-unit coordination.
    """
    name = "grand_10x10"

    def evaluate(self, state: GameState) -> float:
        score = super().evaluate(state)
        # Broad territorial spread and flank mobility
        for r in range(len(state.board)):
            for c in range(len(state.board[0])):
                p = state.board[r][c]
                if p:
                    mult = 1.0 if p.team == "brancas" else -1.0
                    # On 10x10, advancement across rows is heavily rewarded
                    advancement = (9 - r) if p.team == "brancas" else r
                    score += mult * (advancement * 1.5)
        return score

    def get_search_params(self) -> Dict[str, Any]:
        return {
            "depth_extension": 2,
            "territory_weight": 0.18,
            "tactical_aggression": 0.95,
            "killer_slots": 2,
        }


class DraftAresProfile(AresProfile):
    """
    Optimized for Tournament Snake Draft mode.
    Evaluates hero team synergies, counter-picks, and role balance (tanks, mages, flankers).
    """
    name = "snake_draft"

    def evaluate(self, state: GameState) -> float:
        score = super().evaluate(state)
        # Synergy bonuses
        white_heroes = {p.__class__.__name__ for row in state.board for p in row if p and p.team == "brancas"}
        black_heroes = {p.__class__.__name__ for row in state.board for p in row if p and p.team == "pretas"}

        # Synergies: FrostMage + Dragoon (freeze + execute)
        if "FrostMage" in white_heroes and "Dragoon" in white_heroes:
            score += 15.0
        if "FrostMage" in black_heroes and "Dragoon" in black_heroes:
            score -= 15.0

        # Synergies: Paladin + Stormcaller (frontline + rear artillery)
        if "Paladin" in white_heroes and "Stormcaller" in white_heroes:
            score += 12.0
        if "Paladin" in black_heroes and "Stormcaller" in black_heroes:
            score -= 12.0

        return score

    def get_search_params(self) -> Dict[str, Any]:
        return {
            "depth_extension": 1,
            "territory_weight": 0.08,
            "tactical_aggression": 1.1,
            "synergy_multiplier": 1.25,
            "killer_slots": 2,
        }


class HazardAresProfile(AresProfile):
    """
    Optimized for Hazard Arena mode.
    Understands dynamic terrain: avoids ending turns next to lava,
    aims to push enemy pieces into lethal zones, and controls healing springs.
    """
    name = "hazard_arena"

    def evaluate(self, state: GameState) -> float:
        return super().evaluate(state)

    def evaluate_hazards(self, state: GameState, hazards: Dict[str, List[tuple]], team: str) -> float:
        """
        Evaluate positional safety and leverage against hazards.
        """
        score = 0.0
        lava_tiles = set(hazards.get("lava", []))
        spring_tiles = set(hazards.get("healing_spring", []))

        for r in range(len(state.board)):
            for c in range(len(state.board[0])):
                p = state.board[r][c]
                if not p:
                    continue
                mult = 1.0 if p.team == team else -1.0

                # Check proximity to lava
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    adj = (r + dr, c + dc)
                    if adj in lava_tiles:
                        # Serious danger penalty
                        score -= mult * 25.0

                # Check healing spring occupancy
                if (r, c) in spring_tiles:
                    score += mult * 18.0

        return score

    def get_search_params(self) -> Dict[str, Any]:
        return {
            "depth_extension": 1,
            "territory_weight": 0.06,
            "tactical_aggression": 1.3,
            "hazard_safety_margin": 30.0,
            "killer_slots": 2,
        }


class AresProfileRegistry:
    """Registry providing the tailored Ares AI profile for any given game mode."""
    def __init__(self):
        self._profiles: Dict[str, AresProfile] = {
            "standard_8x8": StandardAresProfile(),
            "grand_10x10": GrandAresProfile(),
            "snake_draft": DraftAresProfile(),
            "hazard_arena": HazardAresProfile(),
        }

    def available_profiles(self) -> List[str]:
        return list(self._profiles.keys())

    def get(self, mode_name: str) -> AresProfile:
        return self._profiles.get(mode_name, self._profiles["standard_8x8"])
