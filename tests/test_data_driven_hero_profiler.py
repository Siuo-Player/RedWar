# tests/test_data_driven_hero_profiler.py
"""
Test suite for data-driven Hero Profiling and Football-Style Analytics in RedWar.
Verifies that hero attributes, square heatmaps, game phase curves, and multi-class
classifications are derived empirically from simulation tracking data, not hardcoded.
"""
import pytest
from tools.analytics.hero_data_profiler import (
    HeroDataProfiler,
    MatchEvent,
    HeroDataProfile,
    HeroRadarMetrics,
)


def test_profiler_ingests_match_events():
    profiler = HeroDataProfiler()

    # Simulate tracking events for Paladin
    events = [
        MatchEvent(hero_name="Paladin", team="brancas", turn=3, pos=(3, 3), action="move"),
        MatchEvent(hero_name="Paladin", team="brancas", turn=4, pos=(3, 4), action="attack_stun", target_hero="Dragoon"),
        MatchEvent(hero_name="Paladin", team="brancas", turn=5, pos=(3, 4), action="defend_zone", squares_controlled=5),
        MatchEvent(hero_name="Paladin", team="brancas", turn=15, pos=(3, 5), action="game_end", won=True),
    ]
    for ev in events:
        profiler.record_event(ev)

    profile = profiler.compute_profile("Paladin")
    assert profile.hero_name == "Paladin"
    assert profile.total_games_observed >= 1
    assert profile.win_rate > 0.0


def test_heatmap_generation():
    profiler = HeroDataProfiler()
    
    # Hero predominantly played in the center (3, 3) and (4, 4)
    for _ in range(10):
        profiler.record_event(MatchEvent(hero_name="Paladin", team="brancas", turn=5, pos=(3, 3), action="move", won=True))
        profiler.record_event(MatchEvent(hero_name="Paladin", team="brancas", turn=6, pos=(4, 4), action="move", won=True))
    
    heatmap = profiler.get_square_heatmap("Paladin", grid_size=8)
    assert len(heatmap) == 8
    assert len(heatmap[0]) == 8
    assert heatmap[3][3] > heatmap[0][0]
    assert heatmap[4][4] > heatmap[7][7]


def test_phase_of_game_valuation():
    profiler = HeroDataProfiler()

    # Shadowblade scoring high in endgame (>turn 20)
    for _ in range(5):
        profiler.record_event(MatchEvent(hero_name="Shadowblade", team="brancas", turn=22, action="attack_kill", target_hero="Paladin", won=True))
    # Ranger scoring high in opening (<turn 10)
    for _ in range(5):
        profiler.record_event(MatchEvent(hero_name="Ranger", team="brancas", turn=4, action="attack_stun", target_hero="BoneLord", won=True))

    profile_shadow = profiler.compute_profile("Shadowblade")
    profile_ranger = profiler.compute_profile("Ranger")

    assert profile_shadow.endgame_rating > profile_shadow.opening_rating
    assert profile_ranger.opening_rating > profile_ranger.endgame_rating


def test_radar_metrics_and_multi_class_derivation():
    profiler = HeroDataProfiler()

    # Generate synthetic matches showing Paladin acting as high zone control and survivability
    for t in range(1, 25):
        profiler.record_event(MatchEvent(
            hero_name="Paladin", team="brancas", turn=t, pos=(3, 3),
            action="defend_zone", squares_controlled=6, won=True
        ))
    
    profile = profiler.compute_profile("Paladin")
    radar = profile.radar_metrics

    assert isinstance(radar, HeroRadarMetrics)
    assert 0.0 <= radar.zone_control <= 100.0
    assert 0.0 <= radar.survivability <= 100.0

    # Multi-class tagging should derive Vanguard based on high zone control & survivability
    classes = profile.derived_classes
    assert any("Vanguard" in c or "Tanque" in c for c in classes)


def test_cost_efficiency_calculation():
    profiler = HeroDataProfiler()
    # High impact hero with cost 55
    for _ in range(10):
        profiler.record_event(MatchEvent(hero_name="Paladin", team="brancas", turn=8, action="attack_stun", won=True))

    profile = profiler.compute_profile("Paladin", base_cost=55)
    assert profile.cost_efficiency_ratio > 0.0
    assert profile.cost_recommendation in ["balanced", "increase_cost", "decrease_cost"]
