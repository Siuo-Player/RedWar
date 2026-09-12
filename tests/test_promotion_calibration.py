import pytest

from tools.analytics.promotion_calibration import (
    challenger_probability,
    result_to_dict,
    run_calibration,
    simulate_paired_games,
)
from tools.analytics.strength_statistics import BootstrapInterval, evaluate_promotion


def test_challenger_probability_matches_binary_bradley_terry():
    assert challenger_probability(0.0) == pytest.approx(0.5)
    assert challenger_probability(400.0) == pytest.approx(10.0 / 11.0)
    assert challenger_probability(-400.0) == pytest.approx(1.0 / 11.0)


def test_simulation_is_binary_and_colour_inverted():
    games = simulate_paired_games(0.0, pairs=4, seed=11)
    assert len(games) == 8
    assert {game.outcome for game in games} <= {"challenger", "baseline"}
    for pair_index in range(4):
        pair = games[pair_index * 2 : pair_index * 2 + 2]
        assert pair[0].opening_seed == pair[1].opening_seed
        assert (pair[0].challenger_colour, pair[1].challenger_colour) == ("white", "black")


def test_calibration_is_deterministic_for_fixed_seed():
    first = run_calibration(0.0, experiments=8, pairs=256, bootstrap_replicates=40, seed=17)
    second = run_calibration(0.0, experiments=8, pairs=256, bootstrap_replicates=40, seed=17)
    assert first == second


def test_null_false_accept_rate_is_controlled():
    result = run_calibration(0.0, experiments=40, pairs=256, bootstrap_replicates=100, seed=23)

    # Calibration sanity check only. This does not define a minimum practical Elo
    # improvement: the production rule is simply lower_bound_elo > 0.
    assert result.accept_rate <= 0.10
    assert result.accept_count + result.reject_count + result.continue_count == result.experiments


def test_calibration_detects_a_clear_positive_signal():
    result = run_calibration(200.0, experiments=40, pairs=256, bootstrap_replicates=100, seed=31)

    # A large synthetic signal should be detected reliably, but +200 Elo is NOT
    # the production promotion threshold.
    assert result.accept_rate >= 0.80
    assert result.reject_count + result.accept_count + result.continue_count == result.experiments


def test_calibration_rejects_a_clear_negative_signal():
    result = run_calibration(-200.0, experiments=40, pairs=256, bootstrap_replicates=100, seed=41)

    # A clearly weaker challenger should be rejected reliably at the hard budget.
    assert result.reject_rate >= 0.80
    assert result.reject_count + result.accept_count + result.continue_count == result.experiments


def test_positive_lower_bound_is_sufficient_regardless_of_effect_size():
    games = simulate_paired_games(0.0, pairs=256, seed=71)

    # The important contract is that +2 Elo in the lower bound accepts even when
    # the point estimate is only +9.
    import tools.analytics.strength_statistics as strength_statistics

    original = strength_statistics.paired_bootstrap_delta
    try:
        strength_statistics.paired_bootstrap_delta = lambda *args, **kwargs: BootstrapInterval(
            lower=2.0,
            median=9.0,
            upper=16.0,
            confidence=0.975,
            replicates=kwargs.get("replicates", 100),
            cluster_count=256,
        )
        decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=72)
    finally:
        strength_statistics.paired_bootstrap_delta = original

    assert decision.decision == "accept"
    assert decision.lower_bound_elo == pytest.approx(2.0)


def test_non_positive_lower_bound_does_not_accept():
    games = simulate_paired_games(0.0, pairs=256, seed=73)

    import tools.analytics.strength_statistics as strength_statistics

    original = strength_statistics.paired_bootstrap_delta
    try:
        strength_statistics.paired_bootstrap_delta = lambda *args, **kwargs: BootstrapInterval(
            lower=0.0,
            median=9.0,
            upper=18.0,
            confidence=0.975,
            replicates=kwargs.get("replicates", 100),
            cluster_count=256,
        )
        decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=74)
    finally:
        strength_statistics.paired_bootstrap_delta = original

    assert decision.decision != "accept"


def test_result_serialization_uses_json_safe_stopping_counts():
    result = run_calibration(0.0, experiments=2, pairs=256, bootstrap_replicates=40, seed=51)
    payload = result_to_dict(result)
    assert set(payload["stopping_games"]).issubset({"96", "192", "320", "512"})
    assert payload["experiments"] == 2
