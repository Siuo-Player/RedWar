import pytest

from tools.analytics.historical_rating_calibration import Comparison, fit_global_rating


def test_anchor_is_zero_and_extreme_matchup_stays_finite():
    result = fit_global_rating(
        [Comparison("V1", "V0", 100)],
        anchor="V0",
    )
    assert result.converged
    assert result.ratings["V0"] == 0.0
    assert result.ratings["V1"] > 0.0
    assert result.ratings["V1"] < float("inf")
    assert result.standard_errors["V1"] > 0.0


def test_global_fit_does_not_sum_chain_deltas():
    result = fit_global_rating(
        [
            Comparison("V1", "V0", 80),
            Comparison("V0", "V1", 20),
            Comparison("V2", "V1", 80),
            Comparison("V1", "V2", 20),
            Comparison("V2", "V0", 50),
            Comparison("V0", "V2", 50),
        ],
        anchor="V0",
    )
    assert result.converged
    assert result.ratings["V0"] == 0.0
    assert abs(result.ratings["V2"]) < 150.0
    assert abs(result.ratings["V2"] - result.ratings["V1"]) < 200.0


def test_direct_comparison_can_pull_a_chain_estimate_back_toward_anchor():
    without_direct = fit_global_rating(
        [
            Comparison("V1", "V0", 90),
            Comparison("V0", "V1", 10),
            Comparison("V2", "V1", 90),
            Comparison("V1", "V2", 10),
        ],
        anchor="V0",
    )
    with_direct = fit_global_rating(
        [
            Comparison("V1", "V0", 90),
            Comparison("V0", "V1", 10),
            Comparison("V2", "V1", 90),
            Comparison("V1", "V2", 10),
            Comparison("V2", "V0", 50),
            Comparison("V0", "V2", 50),
        ],
        anchor="V0",
    )
    assert with_direct.converged
    assert abs(with_direct.ratings["V2"]) < abs(without_direct.ratings["V2"])


def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError, match="at least one comparison"):
        fit_global_rating([], anchor="V0")
    with pytest.raises(ValueError, match="prior_sigma"):
        fit_global_rating([Comparison("V1", "V0", 1)], anchor="V0", prior_sigma=0)
    with pytest.raises(ValueError, match="games"):
        fit_global_rating([Comparison("V1", "V0", 0)], anchor="V0")
