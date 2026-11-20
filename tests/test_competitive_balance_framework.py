# tests/test_competitive_balance_framework.py
"""
Test Suite for Competitive Game Balance Framework & Positional Analytics Engine.
Validates mathematical balance attribution, spatial win-rate differentials,
pairwise synergies, counter-matchups, and Riot-style classification.
"""
import pytest
from tools.analytics.competitive_balance_framework import CompetitiveBalanceEngine


def test_record_match_accumulates_draft_and_win_counts():
    engine = CompetitiveBalanceEngine()
    engine.record_match(
        white_roster=["Paladin", "Valkyrie", "Arcanist"],
        black_roster=["Duelist", "Warden", "Marksman"],
        winner_side="white",
        white_move_positions={"Valkyrie": [(3, 3), (3, 4)]},
        black_move_positions={"Marksman": [(1, 2)]},
    )

    assert engine.total_matches == 1
    assert engine.hero_draft_counts["Valkyrie"] == 1
    assert engine.hero_wins["Valkyrie"] == 1
    assert engine.hero_draft_counts["Marksman"] == 1
    assert engine.hero_wins["Marksman"] == 0

    metrics_valk = engine.compute_hero_metrics("Valkyrie", cost=22)
    assert metrics_valk.win_rate == 1.0
    assert metrics_valk.presence_rate == 1.0

    metrics_marks = engine.compute_hero_metrics("Marksman", cost=28)
    assert metrics_marks.win_rate == 0.0


def test_pairwise_synergy_and_counter_computation():
    engine = CompetitiveBalanceEngine()
    # Team 1: Valkyrie + Arcanist wins 3 games together
    for _ in range(3):
        engine.record_match(
            white_roster=["Valkyrie", "Arcanist"],
            black_roster=["Inquisitor", "Berserker"],
            winner_side="white",
        )
    # 4 games where Arcanist loses without Valkyrie against Inquisitor
    for _ in range(4):
        engine.record_match(
            white_roster=["Arcanist", "Duelist"],
            black_roster=["Inquisitor", "Berserker"],
            winner_side="black",
        )

    metrics = engine.compute_hero_metrics("Valkyrie", cost=22)
    assert len(metrics.top_synergies) > 0
    ally, syn_delta = metrics.top_synergies[0]
    assert ally == "Arcanist"
    assert syn_delta > 0.0

    # Inquisitor faced Arcanist and won once
    metrics_arc = engine.compute_hero_metrics("Arcanist", cost=23)
    assert any(adv == "Inquisitor" for adv, _ in metrics_arc.top_counters)


def test_spatial_tile_winrate_differential_and_power_tiles():
    engine = CompetitiveBalanceEngine(grid_size=8)
    # Valkyrie visits (3, 3) and always wins
    for _ in range(4):
        engine.record_match(
            white_roster=["Valkyrie"],
            black_roster=["Warden"],
            winner_side="white",
            white_move_positions={"Valkyrie": [(3, 3)]},
        )
    # Valkyrie visits (0, 0) and loses twice
    for _ in range(2):
        engine.record_match(
            white_roster=["Valkyrie"],
            black_roster=["Warden"],
            winner_side="black",
            white_move_positions={"Valkyrie": [(0, 0)]},
        )

    metrics = engine.compute_hero_metrics("Valkyrie", cost=22)
    assert len(metrics.power_tiles) == 3
    # Top power tile should be (3, 3) with positive delta
    best_r, best_c, best_delta = metrics.power_tiles[0]
    assert (best_r, best_c) == (3, 3)
    assert best_delta > 0.0


def test_riot_framework_classification_thresholds():
    engine = CompetitiveBalanceEngine()
    # 10 matches, hero A wins 9 (90% WR, high presence -> STRONG_FOR_COST)
    for _ in range(9):
        engine.record_match(white_roster=["HeroOP"], black_roster=["HeroUP"], winner_side="white")
    engine.record_match(white_roster=["HeroOP"], black_roster=["HeroUP"], winner_side="black")

    metrics_op = engine.compute_hero_metrics("HeroOP", cost=15)
    assert metrics_op.riot_balance_status == "STRONG_FOR_COST"

    metrics_up = engine.compute_hero_metrics("HeroUP", cost=60)
    assert metrics_up.riot_balance_status == "OVERPRICED"


def test_benchmark_dataset_generation_covers_all_30_heroes():
    from engine.pieces import carregar_heroes
    hero_dict = carregar_heroes()
    assert len(hero_dict) >= 30

    costs = {name: data.get("cost", 30) for name, data in hero_dict.items()}
    engine = CompetitiveBalanceEngine()
    dataset = engine.generate_balanced_benchmark_dataset(costs)

    assert len(dataset) >= 30
    for name in ("Valkyrie", "Arcanist", "Duelist", "Warden", "Illusionist", "Marksman"):
        assert name in dataset
        entry = dataset[name]
        assert "winRate" in entry
        assert "presenceRate" in entry
        assert "efficiency" in entry
        assert "powerTiles" in entry
        assert "topSynergies" in entry
        assert "topCounters" in entry
