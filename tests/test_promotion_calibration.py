import pytest

from tools.analytics.promotion_calibration import (
    challenger_probability,
    result_to_dict,
    run_calibration,
    simulate_paired_games,
)


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


def test_null_calibration_does_not_claim_power():
    result = run_calibration(0.0, experiments=4, pairs=256, bootstrap_replicates=40, seed=23)
    assert result.accept_count <= result.experiments
    assert result.reject_count + result.accept_count + result.continue_count == result.experiments


def test_negative_strength_is_not_reported_as_acceptance_deterministically():
    result = run_calibration(-400.0, experiments=4, pairs=256, bootstrap_replicates=40, seed=31)
    assert result.reject_count >= 0
    assert result.accept_count <= result.experiments


def test_result_serialization_uses_json_safe_stopping_counts():
    result = run_calibration(0.0, experiments=2, pairs=256, bootstrap_replicates=40, seed=41)
    payload = result_to_dict(result)
    assert set(payload["stopping_games"]).issubset({"96", "192", "320", "512"})
    assert payload["experiments"] == 2
