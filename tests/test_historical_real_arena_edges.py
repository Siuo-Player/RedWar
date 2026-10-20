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

    edge = version_edges[0]
    assert edge["status"] == "compatible_real_edge"
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
    assert edge["source_workflow_run_id"] == 35027785973
    assert edge["source_artifact_id"] == 10420239661

    assert edge["promotion_decision"] == "reject"
    assert edge["promotion_authority_used"] is True
    assert edge["gate_stages"][-1]["lower_bound_elo"] < 0

    bridge = next(e for e in version_edges if e["edge_id"] == "ares-historical-bridge-597-100")
    assert bridge["status"] == "compatible_real_edge"
    assert bridge["baseline_version"] == "48dd4df0f6809d072190291bceebb09ddfe52e5f"
    assert bridge["challenger_version"] == "3826b3bfe5c63102677f4a097163aeda4a03f83d"
    assert bridge["rules_version"] == bridge["baseline_version"]
    assert bridge["games"] == 100
    assert bridge["complete_pairs"] == 50
    assert bridge["challenger_wins"] == 54
    assert bridge["baseline_wins"] == 46
    assert bridge["draws"] == 0
    assert bridge["invalid_games"] == 0
    assert bridge["node_budget"] == 10_000
    assert bridge["source_workflow_run_id"] == 37858487666
    assert bridge["source_commit"] == "0eccfa8d0f68af488cce87b6191af26e3b0961a9"
    assert bridge["source_artifact_id"] == 11584718698
    assert bridge["source_artifact_digest"] == "sha256:164b0a332d1a5ad66303ff2053b8386bbbc70de6eedbc880c6d0b7bc0d5a5da8"
    assert bridge["source_raw_sha256"] == "249a5dc14e551c8cc24406d1ed712f54693b5e00f9d20fd4dc20b26ba53e0bc2"
    assert bridge["promotion_authority_used"] is False
    assert bridge["promotion_decision"] == "not_authorized"
    assert bridge["pair_bins"] == {"WW": 10, "DD_WL_LW": 34, "LL": 6}
    assert bridge["lifecycle_context"]
    assert bridge["population_context"]
    assert "not lifecycle-neutral" in bridge["interpretation"]

    graph = payload["current_graph_status"]
    components = _components(payload["edges"])
    assert graph["components"] == components
    assert graph["connected_components"] == len(components)
    assert graph["version_edges"] == len(version_edges) == 2
    assert graph["acceptance_met"] is True
    assert graph["remaining_gap"].startswith("The descriptive graph is connected")
    assert graph["connected_components"] == 1


def test_promotion_507_stage_records_account_for_final_budget():
    edge = next(
        e for e in json.loads(LEDGER.read_text(encoding="utf-8"))["edges"]
        if e["edge_id"] == "ares-promotion-507-512"
    )
    assert sum(stage["games"] for stage in edge["stage_files"]) == 512
    assert edge["stage_files"][0]["game_index_range"] == [0, 95]
    assert edge["stage_files"][-1]["game_index_range"] == [320, 511]
