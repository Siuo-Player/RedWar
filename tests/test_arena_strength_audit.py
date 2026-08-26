import json

import pytest

from tools.analytics.arena_strength_audit import (
    audit_arena_results,
    build_independent_pair_units,
    load_arena_records,
)


METADATA = {
    "challenger_version": "c1",
    "baseline_version": "b1",
    "rules_version": "r1",
    "node_budget": 10_000,
    "games": 4,
    "opening_count": 2,
}


def game(index, outcome, valid=True, metadata=None):
    opening = index // 2
    experiment = dict(METADATA if metadata is None else metadata)
    return {
        "game_index": index,
        "pair_id": f"pair-{index // 2:06d}",
        "pair_member": index % 2,
        "challenger_color": "white" if index % 2 == 0 else "black",
        "baseline_color": "black" if index % 2 == 0 else "white",
        "opening_index": opening,
        "seed": 17000 + index,
        "outcome": outcome,
        "valid": valid,
        "termination_reason": "game_over" if valid else "max_plies_reached",
        "experiment": experiment,
    }


def write_jsonl(path, records):
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_build_independent_pair_units_keeps_pair_games_together():
    records = [
        game(0, "challenger"),
        game(1, "baseline"),
        game(2, "draw"),
        game(3, "baseline"),
    ]

    units, incomplete = build_independent_pair_units(records)

    assert incomplete == []
    assert [unit["unit_id"] for unit in units] == ["pair-000000", "pair-000001"]
    assert units[0]["outcomes"] == ["win", "loss"]
    assert units[1]["outcomes"] == ["draw", "loss"]


def test_incomplete_valid_pair_is_reported():
    metadata = dict(METADATA)
    metadata["games"] = 3
    records = [
        game(0, "challenger", metadata=metadata),
        game(1, "baseline", metadata=metadata),
        game(2, "draw", metadata=metadata),
    ]
    units, incomplete = build_independent_pair_units(records)

    assert len(units) == 1
    assert incomplete == ["pair-000001"]


def test_load_arena_records_validates_the_experiment(tmp_path):
    path = tmp_path / "arena.jsonl"
    write_jsonl(
        path,
        [game(0, "challenger"), game(1, "baseline"), game(2, "draw"), game(3, "baseline")],
    )

    records, metadata = load_arena_records(path)

    assert len(records) == 4
    assert metadata == METADATA


def test_audit_arena_results_is_descriptive_only(tmp_path):
    path = tmp_path / "arena.jsonl"
    write_jsonl(
        path,
        [game(0, "challenger"), game(1, "baseline"), game(2, "draw"), game(3, "baseline")],
    )

    result = audit_arena_results(path, bootstrap_samples=100, seed=7)

    assert result["pairs"] == 2
    assert result["status"] == "descriptive_empirical_audit_only"
    assert result["audit"]["audit_status"] == "descriptive_resampling_only"
    assert result["audit"]["units"] == 2


def test_audit_rejects_incomplete_valid_pair(tmp_path):
    metadata = dict(METADATA)
    metadata["games"] = 3
    path = tmp_path / "arena.jsonl"
    write_jsonl(
        path,
        [
            game(0, "challenger", metadata=metadata),
            game(1, "baseline", metadata=metadata),
            game(2, "draw", metadata=metadata),
        ],
    )

    with pytest.raises(ValueError, match="incomplete valid pairs"):
        audit_arena_results(path, bootstrap_samples=100)
