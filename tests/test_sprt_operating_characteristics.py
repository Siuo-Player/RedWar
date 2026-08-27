import pytest

from tools.analytics.sprt import SPRTConfig
from tools.analytics.sprt_operating_characteristics import (
    run_standard_suite,
    simulate_operating_characteristics,
)


def test_operating_characteristics_are_deterministic():
    config = SPRTConfig(elo0=0.0, elo1=50.0, alpha=0.05, beta=0.05)

    first = run_standard_suite(config, trials=200, max_games=500, seed=123)
    second = run_standard_suite(config, trials=200, max_games=500, seed=123)

    assert first == second
    assert first["schema_version"] == "redwar-sprt-operating-characteristics-v1"
    assert first["null"]["trials"] == 200
    assert first["known_positive"]["trials"] == 200


def test_known_null_and_positive_effect_have_expected_error_direction():
    config = SPRTConfig(elo0=0.0, elo1=50.0, alpha=0.05, beta=0.05)
    result = run_standard_suite(config, trials=2000, max_games=1000, seed=17)

    null = result["null"]
    positive = result["known_positive"]

    assert null["false_positive_rate"] is not None
    assert positive["false_negative_rate"] is not None
    assert 0.0 <= null["false_positive_rate"] <= 1.0
    assert 0.0 <= positive["false_negative_rate"] <= 1.0
    assert null["false_positive_rate"] < 0.12
    assert positive["false_negative_rate"] < 0.12
    assert null["stopping_rate"] > 0.8
    assert positive["stopping_rate"] > 0.8


def test_draw_generating_process_is_recorded_without_claiming_evidence():
    config = SPRTConfig(elo0=0.0, elo1=50.0, alpha=0.05, beta=0.05, draw_rate=0.25)
    result = simulate_operating_characteristics(
        config,
        true_elo_delta=0.0,
        trials=200,
        max_games=200,
        seed=9,
        true_draw_rate=0.25,
    )

    assert result.true_draw_rate == pytest.approx(0.25)
    assert result.mean_draws > 0.0
    assert result.false_positive_rate is not None


def test_invalid_simulation_parameters_are_rejected():
    config = SPRTConfig()
    with pytest.raises(ValueError):
        simulate_operating_characteristics(config, true_elo_delta=0.0, trials=0)
    with pytest.raises(ValueError):
        simulate_operating_characteristics(config, true_elo_delta=0.0, max_games=0)
    with pytest.raises(ValueError):
        simulate_operating_characteristics(config, true_elo_delta=0.0, true_draw_rate=1.0)
