import json
from pathlib import Path

from tools.analytics.strength_calibration_protocol import validate_calibration_plan

PLAN = Path("data/arena/strength/plans/2026-08-29-aa-calibration-v1.json")


def test_aa_plan_is_protocol_v3_and_non_promotional():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    audit = validate_calibration_plan(plan)

    assert plan["promotion_authority"] is False
    assert audit["schema_version"] == "redwar-strength-calibration-protocol-v3"
    assert audit["calibration_run_count"] == 2
    assert audit["holdout_run_count"] == 1
    assert audit["context_variation"]["distinct_calibration_contexts"] == 2

    runs = plan["runs"]
    assert runs[0]["role"] == "calibration"
    assert runs[1]["role"] == "calibration"
    assert runs[0]["challenger_version"] == runs[0]["baseline_version"] == "SELF"
    assert runs[1]["challenger_version"] == runs[1]["baseline_version"] == "SELF"
    assert runs[2]["role"] == "holdout"
    assert runs[2]["holdout"] is True
    assert runs[2]["execution_ready"] is False
    assert all(len(run["opening_seeds"]) == 16 for run in runs)
    assert all(run["node_budget"] > 0 for run in runs)
