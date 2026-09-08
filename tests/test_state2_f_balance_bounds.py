from tools.balance.auto_pricer import MAX_COST, MIN_COST, calcular_balanceamento


def _match(result: float) -> dict:
    return {
        "valid": True,
        "white_elo": 1000,
        "black_elo": 1000,
        "white_draft": {"Knight": 64},
        "black_draft": {},
        "result": result,
    }


def test_auto_pricer_never_proposes_cost_above_configured_maximum():
    report = calcular_balanceamento(
        {"matches": [_match(1.0)] * 100},
        {"Knight": {"cost": MAX_COST}},
    )
    change = report["changes"][0]
    assert change["old_cost"] == MAX_COST
    assert change["new_cost"] <= MAX_COST


def test_auto_pricer_never_proposes_cost_below_configured_minimum():
    report = calcular_balanceamento(
        {"matches": [_match(0.0)] * 100},
        {"Knight": {"cost": MIN_COST}},
    )
    change = report["changes"][0]
    assert change["old_cost"] == MIN_COST
    assert change["new_cost"] >= MIN_COST
