import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PLAN = ROOT / "data" / "arena" / "strength" / "plans" / "2026-10-06-historical-bridge-v1.json"


def test_historical_bridge_dispatch_is_locked_to_the_predeclared_plan():
    workflow = (WORKFLOWS / "historical_bridge_dispatch.yml").read_text(encoding="utf-8")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))

    assert "run/historical-bridge-48dd4df-to-3826b3" in workflow
    assert "dispatch: predeclared historical bridge v1" in workflow
    assert "actions: write" in workflow
    assert "gh workflow run arena_experiments.yml" in workflow
    assert "48dd4df0f6809d072190291bceebb09ddfe52e5f" in workflow
    assert "3826b3bfe5c63102677f4a097163aeda4a03f83d" in workflow
    assert "-f games=100" in workflow
    assert "-f nodes=10000" in workflow

    assert plan["promotion_authority"] is False
    assert plan["baseline_ref"] == "48dd4df0f6809d072190291bceebb09ddfe52e5f"
    assert plan["challenger_ref"] == "3826b3bfe5c63102677f4a097163aeda4a03f83d"
    assert plan["rules_version"] == plan["baseline_ref"]
    assert plan["games"] == 100
    assert plan["node_budget"] == 10000
    assert plan["expected_complete_pairs"] == 50
    assert len(plan["opening_seeds"]) == 16
    assert len(set(plan["opening_seeds"])) == 16