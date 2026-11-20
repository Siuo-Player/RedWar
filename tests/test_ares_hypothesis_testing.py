# tests/test_ares_hypothesis_testing.py
"""
Test Suite for Ares Hypothesis-Driven Engine Evolution & Elo Testing Framework.
Verifies Stockfish-adapted Bradley-Terry formulas, mirror-pair duel execution,
Wald SPRT boundaries, and anti-involution promotion decisions.
"""
import json
from pathlib import Path
import pytest

from ai.ares_hypothesis_testing import (
    AresHypothesisTester,
    Hypothesis,
    HypothesisTestResult,
)
from ai.sprt import SPRTConfig, calculate_elo_difference


def test_hypothesis_record_creation_and_attributes():
    hypo = Hypothesis(
        id="H-20261108-01",
        title="Tactical Stun Quiescence Extension",
        bottleneck="Delayed lethality execution on stunned targets beyond 2 steps",
        proposed_heuristic="Prioritize MVV-LVA lethal spell strikes inside quiescence search",
        baseline_version="ares-2.0-baseline",
        candidate_version="ares-2.0-challenger-mvv-qs",
        target_elo_gain=10.0,
    )
    assert hypo.id == "H-20261108-01"
    assert hypo.target_elo_gain == 10.0
    assert len(hypo.created_at) > 0


def test_bradley_terry_elo_calculation_and_symmetry():
    # 50% win rate must yield exactly 0 Elo
    assert round(calculate_elo_difference(0.50), 1) == 0.0

    # Symmetry: score S vs (1 - S)
    elo_60 = calculate_elo_difference(0.60)
    elo_40 = calculate_elo_difference(0.40)
    assert elo_60 > 0.0
    assert elo_40 < 0.0
    assert round(elo_60 + elo_40, 3) == 0.0

    # 75% win rate in Bradley-Terry is ~ +190.8 Elo
    elo_75 = calculate_elo_difference(0.75)
    assert 185.0 < elo_75 < 195.0


def test_sprt_tracker_promotes_upon_significant_superiority():
    tester = AresHypothesisTester(SPRTConfig(elo0=0.0, elo1=30.0))
    hypo = Hypothesis(
        id="H-TEST-PROMO",
        title="Superior Candidate Test",
        bottleneck="Suboptimal move ordering",
        proposed_heuristic="PV bonus +2M",
        baseline_version="v1",
        candidate_version="v2",
    )

    from ai.sprt import SPRTTracker, SPRTStatus
    tracker = SPRTTracker(SPRTConfig(elo0=0.0, elo1=30.0))
    status = tracker.add_result(win=45, loss=5, draw=0)

    delta_elo, margin = tracker.estimate_elo()
    assert delta_elo > 0.0
    assert status == SPRTStatus.H1_ACCEPTED


def test_sprt_tracker_rejects_upon_inferiority_or_null_gain():
    tester = AresHypothesisTester(SPRTConfig(elo0=0.0, elo1=30.0))
    hypo = Hypothesis(
        id="H-TEST-REJECT",
        title="Inferior Candidate Test",
        bottleneck="Excessive pruning",
        proposed_heuristic="Aggressive NMP without guards",
        baseline_version="v1",
        candidate_version="v2",
    )

    from ai.sprt import SPRTTracker, SPRTStatus
    tracker = SPRTTracker(SPRTConfig(elo0=0.0, elo1=30.0))
    status = tracker.add_result(win=5, loss=45, draw=0)

    delta_elo, margin = tracker.estimate_elo()
    assert delta_elo < 0.0
    assert status == SPRTStatus.H0_ACCEPTED


def test_mirror_pair_duel_execution_with_deterministic_mock_bots(tmp_path):
    hypo = Hypothesis(
        id="H-TEST-MIRROR",
        title="Mirror Pair Execution Test",
        bottleneck="Color bias check",
        proposed_heuristic="Symmetric paired testing",
        baseline_version="base",
        candidate_version="cand",
    )

    # Create two simple bots that pick legal actions
    from ai.ares2 import AresEngine
    class DeterministicTestBot:
        def __init__(self, name="TestBot", depth=1):
            self.engine = AresEngine()
            self.depth = depth
            self.nome = name

        def play(self, gs):
            return self.engine.choose_best_move(gs, max_depth=self.depth, time_limit=0.1)

    challenger = DeterministicTestBot("Cand", depth=1)
    baseline = DeterministicTestBot("Base", depth=1)

    tester = AresHypothesisTester()
    # Run a small duel of 2 pairs (4 games total)
    result = tester.run_hypothesis_duel(
        hypothesis=hypo,
        challenger_bot=challenger,
        baseline_bot=baseline,
        num_pairs=2,
        opening_seeds=[42, 43],
        early_stopping=False,
    )

    assert result.pairs_played == 2
    assert result.total_games == 4
    assert result.challenger_wins + result.baseline_wins + result.draws == 4

    # Check mirror pair symmetry: in each pair, challenger played once as White and once as Black
    for p in result.pair_outcomes:
        assert p["game1"]["challenger_color"] == "white"
        assert p["game2"]["challenger_color"] == "black"

    # Verify Markdown report formatting
    md = tester.format_markdown_report(result)
    assert "# Relatório de Teste de Hipótese Ares AI" in md
    assert hypo.id in md
    assert "Margem de Erro (95% CI)" in md

    # Verify JSON persistence
    json_path = tmp_path / "hypothesis_report.json"
    tester.save_report_json(result, json_path)
    assert json_path.exists()
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["hypothesis"]["id"] == hypo.id
    assert "delta_elo" in data


def test_multitier_3sigma_promotion_gate():
    """Verify that multi-tier estimation calculates both 1.96-sigma and 3.0-sigma."""
    from ai.sprt import SPRTTracker, SPRTConfig
    tracker = SPRTTracker(SPRTConfig(elo0=0.0, elo1=10.0))
    tracker.add_result(win=35, loss=5, draw=0)

    multitier = tracker.estimate_elo_multitier()
    delta_elo = multitier["delta_elo"]
    margin_95 = multitier["margin_95"]
    margin_3sigma = multitier["margin_3sigma"]

    assert delta_elo > 0.0
    ratio = margin_3sigma / margin_95
    assert 1.45 <= ratio <= 1.60
    assert multitier["ci_3sigma"][0] < multitier["ci_95"][0]
    assert multitier["ci_3sigma"][1] > multitier["ci_95"][1]
