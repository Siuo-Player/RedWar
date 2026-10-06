import json
from pathlib import Path


LEDGER = Path("data/arena/strength/historical-real-arena-edges-v1.json")


def test_historical_real_arena_ledger_is_fail_closed():
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "redwar-historical-real-arena-edges-v1"
    assert payload["promotion_authority"] is False

    edges = payload["edges"]
    compatible = [edge for edge in edges if edge["status"] == "compatible_real_edge"]
    assert len(compatible) == 2

    for edge in compatible:
        assert edge["challenger_version"]
        assert edge["baseline_version"]
        assert edge["rules_version"]
        assert edge["games"] > 0
        assert edge["complete_pairs"] * 2 == edge["games"]
        assert edge["draws"] == 0
        assert edge["invalid_games"] == 0
        assert edge["node_budget"] == 10_000
        assert edge["workflow_run_id"] > 0
        assert edge["artifact_id"] > 0

    promotion = next(edge for edge in compatible if edge["edge_id"] == "ares-promotion-507-512")
    assert promotion["promotion_decision"] == "reject"
    assert promotion["promotion_authority_used"] is True
    assert promotion["games"] == 512
    assert promotion["complete_pairs"] == 256
    assert promotion["challenger_wins"] == 265
    assert promotion["baseline_wins"] == 247
    assert promotion["gate_stages"][-1]["lower_bound_elo"] < 0

    graph = payload["current_graph_status"]
    assert graph["connected_components"] == 2
    assert graph["acceptance_met"] is False
    assert graph["components"] == [
        [
            "37b94d51b810b7ef698139f896afd30eee50fa5a",
            "f6a1ee4beb160ee4e23e7e044fba0f78aa5961ac",
        ],
        [
            "48dd4df0f6809d072190291bceebb09ddfe52e5f",
            "bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613",
        ],
    ]


def test_promotion_507_stage_records_account_for_final_budget():
    edge = next(
        edge for edge in json.loads(LEDGER.read_text(encoding="utf-8"))["edges"]
        if edge["edge_id"] == "ares-promotion-507-512"
    )
    assert sum(stage["games"] for stage in edge["stage_files"]) == 512
    assert edge["stage_files"][0]["game_index_range"] == [0, 95]
    assert edge["stage_files"][-1]["game_index_range"] == [320, 511]
