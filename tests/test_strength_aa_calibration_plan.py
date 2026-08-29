import json
from pathlib import Path


PLAN = Path("data/arena/strength/plans/2026-08-29-aa-calibration-v1.json")


def test_aa_plan_is_balanced_and_non_promotional():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["promotion_authority"] is False
    assert plan["experimental_unit"] == "paired-opening-seed"
    assert plan["requirements"]["balanced_colours"] is True
    assert plan["requirements"]["paired_reversal"] is True
    run = plan["conditions"][0]
    assert run["role"] == "calibration"
    assert run["challenger_version"] == "SELF"
    assert run["baseline_version"] == "SELF"
    assert run["expected_direction"] == "neutral"
    assert len(run["opening_seeds"]) == 16
    assert run["node_budget"] > 0
