import pytest

from tools.balance.auto_pricer import (
    MIN_SAMPLES_FOR_ADJUSTMENT,
    calcular_balanceamento,
    calcular_win_esperada,
)


def test_expected_win_probability_is_symmetric():
    a = calcular_win_esperada(1500, 1700)
    b = calcular_win_esperada(1700, 1500)

    assert 0.0 < a < 0.5 < b < 1.0
    assert a + b == pytest.approx(1.0)


def test_expected_win_probability_handles_extreme_elos_without_overflow():
    assert calcular_win_esperada(-10**12, 10**12) == 0.0
    assert calcular_win_esperada(10**12, -10**12) == 1.0


def test_expected_win_probability_handles_extreme_finite_float_elos_without_overflow():
    assert calcular_win_esperada(-1e308, 1e308) == 0.0
    assert calcular_win_esperada(1e308, -1e308) == 1.0


def test_expected_win_probability_rejects_non_finite_elos():
    with pytest.raises(ValueError):
        calcular_win_esperada(float("inf"), 1500)

    with pytest.raises(ValueError):
        calcular_win_esperada(1500, float("nan"))


def test_balance_calculation_does_not_mutate_hero_config():
    stats = {
        "matches": [
            {
                "valid": True,
                "white_elo": 1000,
                "black_elo": 1000,
                "white_draft": {"Knight": 1},
                "black_draft": {},
                "result": 1.0,
            }
        ]
    }
    heroes = {"Knight": {"cost": 50}}

    report = calcular_balanceamento(stats, heroes)

    assert heroes == {"Knight": {"cost": 50}}
    assert report["valid_matches"] == 1
    assert report["changes"][0]["old_cost"] == 50
    assert report["method"] == "elo_adjusted_occurrence_heuristic"
    assert report["interpretation"] == "diagnostic_pricing_heuristic_not_causal_power_estimate"


def test_balance_rejects_unbounded_draft_quantity():
    stats = {
        "matches": [
            {
                "valid": True,
                "white_elo": 1000,
                "black_elo": 1000,
                "white_draft": {"Knight": 10**100},
                "black_draft": {},
                "result": 1.0,
            }
        ]
    }
    heroes = {"Knight": {"cost": 50}}

    with pytest.raises(ValueError, match="Quantidade fora de gama"):
        calcular_balanceamento(stats, heroes)


def test_balance_rejects_non_integer_draft_quantity():
    stats = {
        "matches": [
            {
                "valid": True,
                "white_elo": 1000,
                "black_elo": 1000,
                "white_draft": {"Knight": 1.5},
                "black_draft": {},
                "result": 1.0,
            }
        ]
    }
    heroes = {"Knight": {"cost": 50}}

    with pytest.raises(ValueError, match="Quantidade inválida"):
        calcular_balanceamento(stats, heroes)


def test_balance_does_not_adjust_below_minimum_sample_size():
    matches = [
        {
            "valid": True,
            "white_elo": 1000,
            "black_elo": 1000,
            "white_draft": {"Knight": 1},
            "black_draft": {},
            "result": 1.0,
        }
        for _ in range(MIN_SAMPLES_FOR_ADJUSTMENT - 1)
    ]
    report = calcular_balanceamento({"matches": matches}, {"Knight": {"cost": 50}})
    change = report["changes"][0]
    assert change["samples"] == MIN_SAMPLES_FOR_ADJUSTMENT - 1
    assert change["eligible_for_adjustment"] is False
    assert change["new_cost"] == 50
    assert change["changed"] is False


def test_balance_rejects_missing_validity_provenance():
    stats = {
        "matches": [
            {
                "white_elo": 1000,
                "black_elo": 1000,
                "white_draft": {"Knight": 1},
                "black_draft": {},
                "result": 1.0,
            }
        ]
    }
    with pytest.raises(ValueError, match="proveniência explícita"):
        calcular_balanceamento(stats, {"Knight": {"cost": 50}})


def test_balance_reports_invalid_match_provenance():
    stats = {
        "matches": [
            {
                "valid": True,
                "white_elo": 1000,
                "black_elo": 1000,
                "white_draft": {"Knight": 1},
                "black_draft": {},
                "result": 1.0,
            },
            {
                "valid": False,
                "failure_reason": "engine_crash",
                "white_elo": 1000,
                "black_elo": 1000,
                "white_draft": {},
                "black_draft": {"Knight": 1},
                "result": 0.0,
            },
        ]
    }
    report = calcular_balanceamento(stats, {"Knight": {"cost": 50}})
    assert report["invalid_matches"] == 1
    assert report["invalid_provenance"] == {"engine_crash": 1}
