# tests/test_ares_sprt_and_profiles.py
"""
Test suite for Stockfish-inspired SPRT (Sequential Probability Ratio Test)
and mode-specialized Ares AI profiles.
"""
import pytest
from ai.sprt import SPRTConfig, SPRTStatus, SPRTTracker, calculate_elo_difference
from ai.profiles import (
    AresProfileRegistry,
    StandardAresProfile,
    GrandAresProfile,
    DraftAresProfile,
    HazardAresProfile,
)
from engine.game_state import GameState
from engine.pieces import Dragoon, FrostMage, Paladin, Shadowblade, Stormcaller


def test_sprt_thresholds_and_bounds():
    config = SPRTConfig(elo0=0.0, elo1=5.0, alpha=0.05, beta=0.05)
    tracker = SPRTTracker(config)

    # Thresholds: ln(19) ~ 2.9444, ln(1/19) ~ -2.9444
    assert tracker.upper_bound > 2.9
    assert tracker.lower_bound < -2.9
    assert tracker.status == SPRTStatus.CONTINUE
    assert tracker.llr == pytest.approx(0.0)


def test_sprt_h1_accepted_on_consecutive_wins():
    config = SPRTConfig(elo0=0.0, elo1=5.0, alpha=0.05, beta=0.05)
    tracker = SPRTTracker(config)

    # Adding a dominant series of wins for candidate
    for _ in range(40):
        tracker.add_result(win=1, loss=0, draw=0)
        if tracker.status == SPRTStatus.H1_ACCEPTED:
            break

    assert tracker.status == SPRTStatus.H1_ACCEPTED
    assert tracker.llr >= tracker.upper_bound
    elo_diff, ci = tracker.estimate_elo()
    assert elo_diff > 0


def test_sprt_h0_accepted_on_consecutive_losses():
    config = SPRTConfig(elo0=0.0, elo1=5.0, alpha=0.05, beta=0.05)
    tracker = SPRTTracker(config)

    # Adding a dominant series of losses for candidate
    for _ in range(40):
        tracker.add_result(win=0, loss=1, draw=0)
        if tracker.status == SPRTStatus.H0_ACCEPTED:
            break

    assert tracker.status == SPRTStatus.H0_ACCEPTED
    assert tracker.llr <= tracker.lower_bound
    elo_diff, ci = tracker.estimate_elo()
    assert elo_diff < 0


def test_calculate_elo_from_score():
    # 50% score = 0 Elo difference
    assert calculate_elo_difference(0.5) == pytest.approx(0.0, abs=0.1)
    # >50% score = positive Elo
    assert calculate_elo_difference(0.65) > 50.0
    # <50% score = negative Elo
    assert calculate_elo_difference(0.35) < -50.0


def test_mode_specialized_profiles_registered():
    registry = AresProfileRegistry()
    assert "standard_8x8" in registry.available_profiles()
    assert "grand_10x10" in registry.available_profiles()
    assert "snake_draft" in registry.available_profiles()
    assert "hazard_arena" in registry.available_profiles()


def test_profile_evaluations():
    registry = AresProfileRegistry()
    standard_profile = registry.get("standard_8x8")
    grand_profile = registry.get("grand_10x10")
    hazard_profile = registry.get("hazard_arena")

    state = GameState()
    # Profiles should provide mode-tuned evaluation weights
    eval_std = standard_profile.evaluate(state)
    eval_grand = grand_profile.evaluate(state)
    eval_hazard = hazard_profile.evaluate(state)

    assert isinstance(eval_std, float)
    assert isinstance(eval_grand, float)
    assert isinstance(eval_hazard, float)

    # Check search parameters tailored for each mode
    params_std = standard_profile.get_search_params()
    params_grand = grand_profile.get_search_params()
    assert "depth_extension" in params_std
    assert "territory_weight" in params_grand
    assert params_grand["territory_weight"] > params_std.get("territory_weight", 0.0)


def test_hazard_profile_penalizes_lava_proximity():
    hazard_profile = HazardAresProfile()
    state = GameState()
    # Add a white Paladin
    paladin = Paladin("brancas")
    state.board[2][2] = paladin
    # Simulate hazard at (2, 3)
    hazards = {"lava": [(2, 3)]}
    score_near_lava = hazard_profile.evaluate_hazards(state, hazards, "brancas")

    # Away from lava
    hazards_far = {"lava": [(7, 7)]}
    score_far_lava = hazard_profile.evaluate_hazards(state, hazards_far, "brancas")

    # Being right next to lethal lava should have a lower safety evaluation
    assert score_near_lava < score_far_lava
