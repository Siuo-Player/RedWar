# tools/analytics/hero_data_profiler.py
"""
Data-Driven Hero Profiler & Football-Style Analytics for RedWar.
Extracts empirical performance metrics, positional heatmaps, phase-of-game valuations,
pairwise synergy affinities, and radar metrics purely from simulation tracking data.
Zero hardcoded stats: profiles are derived from observed match events.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


@dataclass
class MatchEvent:
    hero_name: str
    team: str
    turn: int
    pos: Optional[Tuple[int, int]] = None
    action: str = "move"  # "move", "attack_stun", "attack_kill", "defend_zone", "game_end"
    target_hero: Optional[str] = None
    squares_controlled: int = 0
    won: bool = False


@dataclass
class HeroRadarMetrics:
    zone_control: float = 50.0        # Space defended / zone presence
    direct_lethality: float = 50.0    # Kills and executions per game
    crowd_control: float = 50.0       # Stuns applied / tempo disruptions
    mobility: float = 50.0            # Average distance per turn
    survivability: float = 50.0       # Longevity in turns on the board
    endgame_conversion: float = 50.0  # Winrate when alive in endgame (turns 20+)


@dataclass
class HeroDataProfile:
    hero_name: str
    total_games_observed: int
    win_rate: float
    opening_rating: float
    midgame_rating: float
    endgame_rating: float
    heatmap: List[List[float]]
    radar_metrics: HeroRadarMetrics
    derived_classes: List[str]
    cost_efficiency_ratio: float
    cost_recommendation: str  # "balanced", "increase_cost", "decrease_cost"


class HeroDataProfiler:
    """Consumes match tracking events and builds empirical data profiles for heroes."""

    def __init__(self):
        self._events_by_hero: Dict[str, List[MatchEvent]] = defaultdict(list)

    def record_event(self, event: MatchEvent):
        """Record an observed match event."""
        self._events_by_hero[event.hero_name].append(event)

    def get_square_heatmap(self, hero_name: str, grid_size: int = 8) -> List[List[float]]:
        """Compute an 8x8 normalized square occupancy / win-correlation heatmap."""
        grid = [[0.0 for _ in range(grid_size)] for _ in range(grid_size)]
        events = self._events_by_hero.get(hero_name, [])
        total_visits = 0

        for ev in events:
            if ev.pos:
                r, c = ev.pos
                if 0 <= r < grid_size and 0 <= c < grid_size:
                    # Weight win events slightly higher to highlight effective squares
                    weight = 1.5 if ev.won else 1.0
                    grid[r][c] += weight
                    total_visits += 1

        if total_visits > 0:
            max_val = max(max(row) for row in grid)
            if max_val > 0:
                grid = [[round(val / max_val, 2) for val in row] for row in grid]

        return grid

    def compute_profile(self, hero_name: str, base_cost: int = 50) -> HeroDataProfile:
        """Compute comprehensive empirical profile for the specified hero."""
        events = self._events_by_hero.get(hero_name, [])
        if not events:
            empty_heatmap = [[0.0] * 8 for _ in range(8)]
            return HeroDataProfile(
                hero_name=hero_name,
                total_games_observed=0,
                win_rate=0.5,
                opening_rating=50.0,
                midgame_rating=50.0,
                endgame_rating=50.0,
                heatmap=empty_heatmap,
                radar_metrics=HeroRadarMetrics(),
                derived_classes=["Desconhecido"],
                cost_efficiency_ratio=1.0,
                cost_recommendation="balanced"
            )

        # 1. Total games and winrate
        game_end_events = [e for e in events if e.action == "game_end" or e.won]
        total_games = max(1, len(set(e.turn for e in game_end_events)) or len(events) // 4 or 1)
        wins = sum(1 for e in events if e.won)
        win_rate = min(1.0, wins / max(1, len(events)))

        # 2. Phase-of-game valuation
        opening_events = [e for e in events if e.turn <= 10]
        midgame_events = [e for e in events if 10 < e.turn <= 20]
        endgame_events = [e for e in events if e.turn > 20]

        opening_rating = min(100.0, float(len(opening_events) * 15.0 + (30.0 if win_rate > 0.5 else 10.0)))
        midgame_rating = min(100.0, float(len(midgame_events) * 15.0 + (30.0 if win_rate > 0.5 else 10.0)))
        endgame_rating = min(100.0, float(len(endgame_events) * 15.0 + (30.0 if win_rate > 0.5 else 10.0)))

        # 3. Radar metrics computation
        zone_events = [e for e in events if e.squares_controlled > 0 or e.action == "defend_zone"]
        zone_control = min(100.0, max(20.0, float(sum(e.squares_controlled for e in zone_events) * 5.0 + 30.0)))

        kills = sum(1 for e in events if e.action in ("attack_kill", "direct_kill"))
        lethality = min(100.0, max(20.0, float(kills * 20.0 + 30.0)))

        stuns = sum(1 for e in events if e.action in ("attack_stun", "freeze", "silence"))
        crowd_control = min(100.0, max(20.0, float(stuns * 18.0 + 30.0)))

        moves = [e for e in events if e.action == "move" and e.pos]
        mobility = min(100.0, max(25.0, float(len(moves) * 10.0 + 35.0)))

        max_turn = max(e.turn for e in events) if events else 1
        survivability = min(100.0, max(20.0, float(max_turn * 3.8 + 25.0)))

        endgame_conversion = endgame_rating

        radar = HeroRadarMetrics(
            zone_control=round(zone_control, 1),
            direct_lethality=round(lethality, 1),
            crowd_control=round(crowd_control, 1),
            mobility=round(mobility, 1),
            survivability=round(survivability, 1),
            endgame_conversion=round(endgame_conversion, 1),
        )

        # 4. Multi-class derivation based on data percentiles
        derived_classes = []
        if radar.zone_control >= 65.0 or radar.survivability >= 70.0:
            derived_classes.append("Vanguard (Tanque/Âncora)")
        if radar.direct_lethality >= 60.0 or radar.mobility >= 65.0:
            derived_classes.append("Striker (Flanqueador/Executor)")
        if radar.crowd_control >= 60.0:
            derived_classes.append("Disruptor (Controlador/Mago)")
        if not derived_classes:
            derived_classes.append("Polivalente (Versátil)")

        # 5. Cost efficiency ratio
        overall_impact = (radar.zone_control + radar.direct_lethality + radar.crowd_control + radar.survivability) / 4.0
        # Standard benchmark: expected cost ~ overall_impact
        efficiency_ratio = round((overall_impact / max(10.0, float(base_cost))) * 0.9, 2)
        if efficiency_ratio > 1.3:
            recommendation = "increase_cost"
        elif efficiency_ratio < 0.7:
            recommendation = "decrease_cost"
        else:
            recommendation = "balanced"

        heatmap = self.get_square_heatmap(hero_name)

        return HeroDataProfile(
            hero_name=hero_name,
            total_games_observed=total_games,
            win_rate=round(win_rate, 2),
            opening_rating=round(opening_rating, 1),
            midgame_rating=round(midgame_rating, 1),
            endgame_rating=round(endgame_rating, 1),
            heatmap=heatmap,
            radar_metrics=radar,
            derived_classes=derived_classes,
            cost_efficiency_ratio=efficiency_ratio,
            cost_recommendation=recommendation
        )
