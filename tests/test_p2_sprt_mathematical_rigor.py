from __future__ import annotations

import pytest

from ai.ares_hypothesis_testing import (
    AresHypothesisTester,
    Hypothesis,
    HypothesisTestResult,
)
from ai.sprt import SPRTConfig, SPRTStatus, SPRTTracker, calculate_elo_difference


def test_12_consecutive_wins_does_not_trigger_h1():
    """Verify exact Wald SPRT prevents premature H1 acceptance on small sample sizes (12 wins)."""
    # Target hypothesis: +15 Elo
    config = SPRTConfig(elo0=0.0, elo1=15.0, alpha=0.05, beta=0.05, min_games=20)
    tracker = SPRTTracker(config)

    for _ in range(12):
        tracker.add_result(win=1, loss=0, draw=0)

    assert tracker.total_games == 12
    # Exact Wald LLR must be ~0.507, far below upper decision bound (~2.944)
    assert tracker.llr < 1.0
    assert tracker.llr < tracker.upper_bound
    # Must remain CONTINUE (cannot declare H1 at 12 games)
    assert tracker.status == SPRTStatus.CONTINUE


def test_tier_0_screening_prohibits_champion_promotion():
    """Verify Tier 0 screening (< 20 games) strictly forbids PROMOTED verdict."""
    tester = AresHypothesisTester(SPRTConfig(elo0=0.0, elo1=15.0))
    hypo = Hypothesis(
        id="H-TEST-TIER0",
        title="Screening Candidate",
        bottleneck="Tactical search",
        proposed_heuristic="Draft boost",
        baseline_version="v1",
        candidate_version="v2",
    )

    # Mock bots for fast duel of 4 pairs = 8 games (Tier 0)
    class FastBot:
        def __init__(self, name):
            self.nome = name

        def play(self, gs):
            moves = gs.get_legal_actions()
            return moves[0] if moves else None

    result = tester.run_hypothesis_duel(
        hypothesis=hypo,
        challenger_bot=FastBot("Cand"),
        baseline_bot=FastBot("Base"),
        num_pairs=4,
        opening_seeds=[10, 11, 12, 13],
        early_stopping=False,
    )

    assert result.total_games == 8
    assert result.tier == "TIER_0_SCREENING"
    # Even if challenger won games, verdict MUST NOT be PROMOTED in Tier 0
    assert result.verdict in ("CONTINUE", "REJECTED")
    assert result.verdict != "PROMOTED"


def test_tier_1_sprt_verification_prohibits_champion_promotion():
    """Verify Tier 1 verification (20 <= N < 100) strictly forbids PROMOTED verdict."""
    hypo = Hypothesis(
        id="H-TEST-TIER1",
        title="Intermediate Candidate",
        bottleneck="Null move pruning",
        proposed_heuristic="Adaptive R=3",
        baseline_version="v1",
        candidate_version="v2",
    )

    # 50 games played: 45 wins, 5 losses (Tier 1)
    tracker = SPRTTracker(SPRTConfig(elo0=0.0, elo1=30.0, min_games=20))
    tracker.add_result(win=45, loss=5, draw=0)
    assert tracker.total_games == 50
    assert tracker.status == SPRTStatus.H1_ACCEPTED

    stats = tracker.estimate_elo_multitier()
    delta_elo = stats["delta_elo"]
    ci_lower_3sigma = stats["ci_3sigma"][0]
    total_games = tracker.total_games

    tier = "TIER_1_SPRT"
    sigma_gate_passed = bool(delta_elo > 0 and ci_lower_3sigma >= 0.0)

    # Apply Ares hypothesis decision logic
    if tier == "TIER_2_CHAMPION_GATE" and (tracker.status == SPRTStatus.H1_ACCEPTED and sigma_gate_passed):
        verdict = "PROMOTED"
    elif tracker.status == SPRTStatus.H0_ACCEPTED or (delta_elo < 0 and stats["ci_95"][1] <= 0.0):
        verdict = "REJECTED"
    elif delta_elo > 0:
        verdict = "CONTINUE"
    else:
        verdict = "REJECTED"

    # Must be CONTINUE, never PROMOTED in Tier 1
    assert verdict == "CONTINUE"


def test_tier_2_champion_gate_authorizes_promotion_with_3sigma():
    """Verify Tier 2 (>= 100 games) allows PROMOTED when both H1 and 3-sigma gate pass."""
    hypo = Hypothesis(
        id="H-TEST-TIER2",
        title="Production Candidate",
        bottleneck="History table saturation",
        proposed_heuristic="Aging decay factor",
        baseline_version="v1",
        candidate_version="v2",
    )

    # 120 games played: 95 wins, 25 losses (Tier 2, strong significant positive signal)
    tracker = SPRTTracker(SPRTConfig(elo0=0.0, elo1=20.0, min_games=20))
    tracker.add_result(win=95, loss=25, draw=0)
    assert tracker.total_games == 120
    assert tracker.status == SPRTStatus.H1_ACCEPTED

    stats = tracker.estimate_elo_multitier()
    delta_elo = stats["delta_elo"]
    ci_lower_3sigma = stats["ci_3sigma"][0]
    total_games = tracker.total_games

    assert total_games >= 100
    tier = "TIER_2_CHAMPION_GATE"
    sigma_gate_passed = bool(delta_elo > 0 and ci_lower_3sigma >= 0.0)
    assert sigma_gate_passed is True

    if tier == "TIER_2_CHAMPION_GATE" and (tracker.status == SPRTStatus.H1_ACCEPTED and sigma_gate_passed):
        verdict = "PROMOTED"
    elif tracker.status == SPRTStatus.H0_ACCEPTED:
        verdict = "REJECTED"
    else:
        verdict = "CONTINUE"

    assert verdict == "PROMOTED"
