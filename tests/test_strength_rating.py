from tools.analytics.strength_rating import MatchResult, Rating, compare, estimate, expected_score


def test_expected_score_is_symmetric():
    assert expected_score(1500, 1500) == 0.5
    assert expected_score(1700, 1500) > 0.5
    assert expected_score(1500, 1700) < 0.5


def test_identical_result_stream_preserves_zero_sum_rating():
    initial = {"A": Rating(), "B": Rating()}
    ratings = estimate(
        initial,
        [MatchResult("A", "B", "win"), MatchResult("A", "B", "loss")],
    )
    assert ratings["A"].value + ratings["B"].value == 3000.0
    assert ratings["A"].value != 1500.0
    assert ratings["B"].value != 1500.0
    assert ratings["A"].games == 2
    assert ratings["B"].games == 2


def test_draw_has_no_rating_delta_when_equal():
    initial = {"A": Rating(), "B": Rating()}
    ratings = estimate(initial, [MatchResult("A", "B", "draw")])
    assert ratings["A"].value == ratings["B"].value == 1500.0


def test_uncertainty_decreases_but_has_floor():
    initial = {"A": Rating(), "B": Rating()}
    ratings = estimate(
        initial,
        [MatchResult("A", "B", "win")] * 1000,
    )
    assert ratings["A"].uncertainty < 350.0
    assert ratings["A"].uncertainty >= 20.0
    assert ratings["B"].uncertainty >= 20.0


def test_relative_estimate_exposes_delta_and_interval():
    estimate_result = compare(Rating(1520, 100, 30**2), Rating(1500, 100, 30**2))
    assert estimate_result.delta == 20
    assert estimate_result.lower_95 < 20 < estimate_result.upper_95
    assert estimate_result.delta_uncertainty > 0


def test_relative_estimate_labels_interval_as_engineering_proxy():
    estimate_result = compare(Rating(1520, 100, 30**2), Rating(1500, 100, 30**2))
    assert estimate_result.interval_type == "engineering_uncertainty_proxy_v1"
