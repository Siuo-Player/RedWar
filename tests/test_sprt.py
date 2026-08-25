import math

import pytest

from tools.analytics.sprt import SPRTConfig, evaluate_sequence, log_likelihood_ratio, win_probability


def test_win_probability_is_symmetric_around_zero():
    assert win_probability(0.0) == pytest.approx(0.5)
    assert win_probability(100.0) > 0.5
    assert win_probability(-100.0) < 0.5
    assert win_probability(100.0) == pytest.approx(1.0 - win_probability(-100.0))


def test_sprt_boundaries_match_requested_error_rates():
    config = SPRTConfig(elo0=0.0, elo1=20.0, alpha=0.05, beta=0.05)
    assert config.upper == pytest.approx(math.log(19.0))
    assert config.lower == pytest.approx(math.log(0.05 / 0.95))


def test_sprt_accepts_h1_for_strong_wins():
    config = SPRTConfig(elo0=0.0, elo1=50.0, alpha=0.05, beta=0.05)
    result = evaluate_sequence(["win"] * 100, config)
    assert result.decision == "accept_h1"
    assert result.wins == result.games


def test_sprt_rejects_h1_for_strong_losses():
    config = SPRTConfig(elo0=0.0, elo1=50.0, alpha=0.05, beta=0.05)
    result = evaluate_sequence(["loss"] * 100, config)
    assert result.decision == "reject_h1"
    assert result.losses == result.games


def test_draws_are_explicit_and_neutral_when_fixed_draw_rate_is_shared():
    config = SPRTConfig(elo0=0.0, elo1=50.0, alpha=0.05, beta=0.05, draw_rate=0.2)
    assert log_likelihood_ratio("draw", config) == pytest.approx(0.0)
    result = evaluate_sequence(["draw"] * 20, config)
    assert result.decision == "continue"
    assert result.draws == 20


def test_invalid_outcome_is_rejected():
    with pytest.raises(ValueError):
        evaluate_sequence(["banana"], SPRTConfig())


def test_invalid_probabilities_are_rejected():
    with pytest.raises(ValueError):
        SPRTConfig(alpha=0.0)
    with pytest.raises(ValueError):
        SPRTConfig(beta=1.0)
    with pytest.raises(ValueError):
        SPRTConfig(draw_rate=1.0)
