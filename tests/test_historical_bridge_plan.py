import json
from pathlib import Path


PLAN = Path("data/arena/strength/plans/2026-10-06-historical-bridge-v1.json")


def test_historical_bridge_plan_is_fixed_and_non_authoritative():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))

    assert plan["schema_version"] == "redwar-historical-bridge-plan-v1"
    assert plan["status"] == "predeclared_manual_execution"
    assert plan["promotion_authority"] is False
    assert plan["workflow"] == ".github/workflows/arena_experiments.yml"
    assert plan["mode"] == "experiment"

    assert plan["baseline_ref"] == "48dd4df0f6809d072190291bceebb09ddfe52e5f"
    assert plan["challenger_ref"] == "3826b3bfe5c63102677f4a097163aeda4a03f83d"
    assert plan["rules_version"] == plan["baseline_ref"]

    assert plan["node_budget"] == 10_000
    assert plan["games"] == 100
    assert plan["expected_complete_pairs"] == 50
    assert plan["opening_count"] == 16
    assert len(plan["opening_seeds"]) == 16
    assert len(set(plan["opening_seeds"])) == 16

    assert plan["selection_policy"] == "paired-fixed-openings"
    assert plan["controller_population"] == "Ares-historical-version-to-version"
    assert plan["skill_context"] == "fixed-node-budget-10k"
    assert plan["colour_policy"] == "alternating_per_game"
    assert plan["pairing_policy"] == "adjacent-games-same-opening-with-inverted-challenger-colour"

    planned = plan["expected_graph_effect"]["planned_edge"]
    assert planned == [plan["baseline_ref"], plan["challenger_ref"]]

    existing = plan["expected_graph_effect"]["existing_edge"]
    assert len(existing) == 2
    assert existing[0] == plan["baseline_ref"]
    assert existing[1] == "bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613"

    assert "cannot promote" in plan["rationale"]["authority_boundary"]
