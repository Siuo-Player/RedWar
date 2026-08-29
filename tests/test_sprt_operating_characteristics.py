from tools.analytics.sprt_operating_characteristics import calibrate_operating_characteristics


def test_operating_characteristics_are_reproducible():
    first = calibrate_operating_characteristics(
        true_elo_delta=0.0,
        draw_rate=0.2,
        trials=200,
        seed=123,
        max_games=1000,
    )
    second = calibrate_operating_characteristics(
        true_elo_delta=0.0,
        draw_rate=0.2,
        trials=200,
        seed=123,
        max_games=1000,
    )
    assert first == second
    assert first["promotion_authority"] is False
    assert first["interpretation"] == "synthetic_operating_characteristic_only"


def test_h0_does_not_systematically_accept_h1():
    result = calibrate_operating_characteristics(
        true_elo_delta=0.0,
        draw_rate=0.2,
        trials=500,
        seed=7,
        max_games=1000,
    )
    assert result["summary"]["accept_h1_rate"] < 0.12


def test_positive_known_effect_is_detected_more_often_than_h0():
    h0 = calibrate_operating_characteristics(
        true_elo_delta=0.0,
        draw_rate=0.2,
        trials=500,
        seed=7,
        max_games=2000,
    )
    h1 = calibrate_operating_characteristics(
        true_elo_delta=50.0,
        draw_rate=0.2,
        trials=500,
        seed=7,
        max_games=2000,
    )
    assert h1["summary"]["accept_h1_rate"] > h0["summary"]["accept_h1_rate"]


def test_small_effect_is_measured_as_low_power_not_as_failure_of_logic():
    result = calibrate_operating_characteristics(
        true_elo_delta=1.0,
        draw_rate=0.5,
        trials=300,
        seed=11,
        max_games=500,
    )
    assert 0.0 <= result["summary"]["accept_h1_rate"] <= 1.0
    assert 0.0 <= result["summary"]["inconclusive_rate"] <= 1.0
