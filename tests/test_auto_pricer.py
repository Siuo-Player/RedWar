import pytest

from tools.balance.auto_pricer import calcular_balanceamento, calcular_win_esperada


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
