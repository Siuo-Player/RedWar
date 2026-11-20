from __future__ import annotations

import json
from pathlib import Path
import pytest

from tools.balance.contextual_balance_lab import (
    calculate_hero_efficiency,
    suggest_integer_price_adjustments,
    audit_first_player_advantage,
    MatchupRecord,
    CompositionMatchupRunner,
)


def test_hero_efficiency_calculation():
    """Efficiency accounts for lethal kills, stuns inflicted, and hero cost."""
    # High-cost hero (cost 30) with 2 kills and 1 stun
    eff_high = calculate_hero_efficiency(kills=2, stuns=1, cost=30)
    # Low-cost hero (cost 10) with 2 kills and 1 stun
    eff_low = calculate_hero_efficiency(kills=2, stuns=1, cost=10)

    # Lower-cost hero achieving identical impact has higher cost-efficiency
    assert eff_low > eff_high
    assert eff_high == pytest.approx((2 * 2.0 + 1 * 1.0) / 30.0)
    assert eff_low == pytest.approx((2 * 2.0 + 1 * 1.0) / 10.0)


def test_integer_price_adjustments_bounded():
    """Adjustments are coarse-to-fine integer interventions bounded by MIN_COST and MAX_COST."""
    stats = {
        "FrostMage": {"win_rate": 0.72, "games": 50, "current_cost": 25},
        "Bone": {"win_rate": 0.30, "games": 50, "current_cost": 8},
        "Templar": {"win_rate": 0.51, "games": 50, "current_cost": 15},
        "MinHero": {"win_rate": 0.20, "games": 50, "current_cost": 5},
    }

    adjustments = suggest_integer_price_adjustments(stats, min_cost=5, max_cost=200)

    # Overperforming FrostMage should increase in cost
    assert adjustments["FrostMage"]["adjustment"] > 0
    assert adjustments["FrostMage"]["new_cost"] == 26 or adjustments["FrostMage"]["new_cost"] == 27
    assert isinstance(adjustments["FrostMage"]["new_cost"], int)

    # Underperforming Bone should decrease in cost
    assert adjustments["Bone"]["adjustment"] < 0
    assert adjustments["Bone"]["new_cost"] in (6, 7)
    assert isinstance(adjustments["Bone"]["new_cost"], int)

    # Balanced Templar has 0 adjustment
    assert adjustments["Templar"]["adjustment"] == 0
    assert adjustments["Templar"]["new_cost"] == 15

    # MinHero cannot drop below MIN_COST (5)
    assert adjustments["MinHero"]["new_cost"] == 5


def test_audit_first_player_advantage():
    """First-player advantage must be explicitly calculated across paired games."""
    records = [
        MatchupRecord(game_id="1", white_comp="A", black_comp="B", winner="white", plies=20, seed=42),
        MatchupRecord(game_id="2", white_comp="B", black_comp="A", winner="white", plies=25, seed=42),
        MatchupRecord(game_id="3", white_comp="A", black_comp="B", winner="black", plies=30, seed=43),
        MatchupRecord(game_id="4", white_comp="B", black_comp="A", winner="white", plies=22, seed=43),
    ]

    audit = audit_first_player_advantage(records)

    assert audit["total_games"] == 4
    assert audit["white_wins"] == 3
    assert audit["black_wins"] == 1
    assert audit["white_win_rate"] == 0.75
    assert audit["first_player_advantage_delta"] == pytest.approx(0.50)


def test_runner_preserves_pair_provenance(tmp_path: Path):
    """The runner executes paired matches and saves structured reports."""
    runner = CompositionMatchupRunner(nodes=50)
    report_file = tmp_path / "balance_report.json"

    comp_a = ["Templar", "Ranger"]
    comp_b = ["FrostMage", "Bone"]

    result = runner.run_paired_matchup(comp_a, comp_b, seed=123, pairs=1)

    assert len(result.records) == 2, "1 pair must produce exactly 2 paired games (colors swapped)"
    # Game 1: comp_a is white, comp_b is black
    assert result.records[0].white_comp == comp_a
    assert result.records[0].black_comp == comp_b
    # Game 2: comp_b is white, comp_a is black
    assert result.records[1].white_comp == comp_b
    assert result.records[1].black_comp == comp_a
    # Both share the same seed
    assert result.records[0].seed == 123
    assert result.records[1].seed == 123

    runner.export_report(result, report_file)
    assert report_file.is_file()
    data = json.loads(report_file.read_text(encoding="utf-8"))
    assert "records" in data
    assert "provenance" in data
