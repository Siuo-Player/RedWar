import json
from pathlib import Path


LEDGER = Path("data/arena/strength/historical-real-arena-edges-v1.json")


def _components(edges):
    graph = {}
    for edge in edges:
        if not edge["graph_eligible"]:
            continue
        a = edge["baseline_version"]
        b = edge["challenger_version"]
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)

    components = []
    unseen = set(graph)
    while unseen:
        root = min(unseen)
        stack = [root]
        component = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            unseen.discard(node)
            stack.extend(graph[node] - component)
        components.append(sorted(component))
    return sorted(components)


def test_historical_real_arena_ledger_is_fail_closed():
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "redwar-historical-real-arena-edges-v1"
    assert payload["promotion_authority"] is False

    controls = [e for e in payload["edges"] if e["comparison_type"] == "A/A control"]
    assert len(controls) == 1
    assert controls[0]["graph_eligible"] is False

    version_edges = [e for e in payload["edges"] if e["graph_eligible"] is True]
    assert len(version_edges) == 2

    promotion = next(e for e in version_edges if e["edge_id"] == "ares-promotion-507-512")
    assert promotion["status"] == "compatible_real_edge"
    assert promotion["challenger_version"] == "bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613"
    assert promotion["baseline_version"] == "48dd4df0f6809d072190291bceebb09ddfe52e5f"
    assert promotion["rules_version"] == promotion["challenger_version"]
    assert promotion["games"] == 512
    assert promotion["complete_pairs"] == 256
    assert promotion["challenger_wins"] == 265
    assert promotion["baseline_wins"] == 247
    assert promotion["draws"] == 0
    assert promotion["invalid_games"] == 0
    assert promotion["node_budget"] == 10_000
    assert promotion["source_workflow_run_id"] == 35027785973
    assert promotion["source_artifact_id"] == 10420239661
    assert promotion["promotion_decision"] == "reject"
    assert promotion["promotion_authority_used"] is True
    assert promotion["gate_stages"][-1]["lower_bound_elo"] < 0

    bridge = next(e for e in version_edges if e["edge_id"] == "historical-bridge-2026-10-08-100")
    assert bridge["status"] == "compatible_real_edge"
    assert bridge["challenger_version"] == "3826b3bfe5c63102677f4a097163aeda4a03f83d"
    assert bridge["baseline_version"] == "48dd4df0f6809d072190291bceebb09ddfe52e5f"
    assert bridge["rules_version"] == bridge["baseline_version"]
    assert bridge["games"] == 100
    assert bridge["complete_pairs"] == 50
    assert bridge["challenger_wins"] == 54
    assert bridge["baseline_wins"] == 46
    assert bridge["draws"] == 0
    assert bridge["invalid_games"] == 0
    assert bridge["node_budget"] == 10_000
    assert bridge["source_workflow_run_id"] == 37858487666
    assert bridge["source_artifact_id"] == 11584718698
    assert bridge["source_artifact_digest"] == "sha256:164b0a332d1a5ad66303ff2053b8386bbbc70de6eedbc880c6d0b7bc0d5a5da8"
    assert bridge["raw_sha256"] == "249a5dc14e551c8cc24406d1ed712f54693b5e00f9d20fd4dc20b26ba53e0bc2"
    assert bridge["pair_bins"] == {"WW": 10, "split": 34, "LL": 6}
    assert bridge["diagnostic_flags"] == {
        "colour_imbalance": False,
        "opening_imbalance": True,
        "seed_reuse": True,
    }
    assert bridge["promotion_decision"] == "not_evaluated"
    assert bridge["promotion_authority_used"] is False
    assert "not a strength claim" in bridge["interpretation"]

    graph = payload["current_graph_status"]
    components = _components(payload["edges"])
    assert graph["components"] == components
    assert graph["connected_components"] == 1
    assert graph["version_edges"] == 2
    assert graph["acceptance_met"] is True
    assert graph["compatible_nodes"] == [
        "3826b3bfe5c63102677f4a097163aeda4a03f83d",
        "48dd4df0f6809d072190291bceebb09ddfe52e5f",
        "bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613",
    ]
    assert graph["remaining_gap"].startswith("Minimum connected multi-edge historical graph established")


def test_promotion_507_stage_records_account_for_final_budget():
    edge = next(
        e for e in json.loads(LEDGER.read_text(encoding="utf-8"))["edges"]
        if e["edge_id"] == "ares-promotion-507-512"
    )
    assert sum(stage["games"] for stage in edge["stage_files"]) == 512
    assert edge["stage_files"][0]["game_index_range"] == [0, 95]
    assert edge["stage_files"][-1]["game_index_range"] == [320, 511]
