import json
from pathlib import Path


LEDGER = Path("data/arena/strength/historical-real-arena-edges-v1.json")


def test_historical_real_arena_ledger_is_fail_closed():
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "redwar-historical-real-arena-edges-v1"
    assert payload["promotion_authority"] is False

    controls = [e for e in payload["edges"] if e["comparison_type"] == "A/A control"]
    assert len(controls) == 1
    assert controls[0]["graph_eligible"] is False

    version_edges = [e for e in payload["edges"] if e["graph_eligible"] is True]
    assert len(version_edges) == 1

    edge = version_edges[0]
    assert edge["challenger_version"]
    assert edge["baseline_version"]
    assert edge["rules_version"]
    assert edge["games"] == 512
    assert edge["complete_pairs"] == 256
    assert edge["challenger_wins"] == 265
    assert edge["baseline_wins"] == 247
    assert edge["draws"] == 0
    assert edge["invalid_games"] == 0
    assert edge["node_budget"] == 10_000
    assert edge["workflow_run_id"] == 35027785973
    assert edge["artifact_id"] == 10420239661

    assert edge["promotion_decision"] == "reject"
    assert edge["promotion_authority_used"] is True
    assert edge["gate_stages"][-1]["lower_bound_elo"] < 0

    graph = payload["current_graph_status"]
    assert graph["connected_components"] == 1
    assert graph["version_edges"] == 1
    assert graph["acceptance_met"] is False
    assert graph["remaining_gap"].startswith("at least one additional provenance-compatible")


def test_promotion_507_stage_records_account_for_final_budget():
    edge = next(
        e for e in json.loads(LEDGER.read_text(encoding="utf-8"))["edges"]
        if e["edge_id"] == "ares-promotion-507-512"
    )
    assert sum(stage["games"] for stage in edge["stage_files"]) == 512
    assert edge["stage_files"][0]["game_index_range"] == [0, 95]
    assert edge["stage_files"][-1]["game_index_range"] == [320, 511]
