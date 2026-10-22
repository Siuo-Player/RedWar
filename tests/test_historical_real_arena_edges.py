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
    assert "lifecycle-neutral" in bridge["interpretation"]
    assert "population-identical" in bridge["interpretation"]
    dataset_path = Path(bridge["dataset_path"])
    audit_path = Path(bridge["audit_path"])
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert dataset["manifest"]["canonical_sha256"] == bridge["dataset_canonical_sha256"]
    assert dataset["manifest"]["source_artifact"]["raw_sha256"] == bridge["source_raw_sha256"]
    assert audit["source_dataset_canonical_sha256"] == bridge["dataset_canonical_sha256"]
    assert audit["status"] == "descriptive_empirical_audit_only"

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


def test_bridge_opening_cluster_sensitivity_is_reproducible():
    """Opening-cluster resampling is a caveated sensitivity, not a calibrated CI."""
    from collections import defaultdict
    import math
    import random

    dataset_path = Path("data/arena/strength/2026-10-20-historical-bridge-100.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    by_seed = defaultdict(list)
    for game in dataset["games"]:
        if game["valid"]:
            by_seed[game["seed"]].append(game["outcome"] == "challenger")

    seeds = dataset["manifest"]["experiment"]["opening_seeds"]
    assert len(seeds) == 16
    assert len(by_seed) == 16
    assert sorted(len(by_seed[seed]) for seed in seeds) == [6] * 14 + [8] * 2
    seed_rates = [sum(by_seed[seed]) / len(by_seed[seed]) for seed in seeds]
    assert math.isclose(sum(seed_rates) / len(seed_rates), 0.5390625)

    # Fixed-opening-cluster sensitivity; nearest-rank percentiles are explicit.
    rng = random.Random(0)
    samples = sorted(
        sum(seed_rates[rng.randrange(len(seed_rates))] for _ in seed_rates) / len(seed_rates)
        for _ in range(20_000)
    )
    lower, median, upper = samples[499], samples[9_999], samples[19_499]
    assert math.isclose(lower, 0.4270833333333333)
    assert math.isclose(median, 0.5390625)
    assert math.isclose(upper, 0.6432291666666666)
    # Repeated fixed seeds and persistent process state still limit inference.
