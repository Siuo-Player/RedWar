import json

import pytest

from tools.analytics.real_arena_strength_report import analyze_real_arena


def legacy_game(index, outcome):
    return {
        "game_index": index,
        "pair_id": f"pair-{index // 2:06d}",
        "pair_member": index % 2,
        "challenger_color": "white" if index % 2 == 0 else "black",
        "baseline_color": "black" if index % 2 == 0 else "white",
        "experiment": {
            "challenger_version": "c1",
            "baseline_version": "b1",
            "rules_version": "r1",
            "node_budget": 10_000,
            "games": 4,
            "opening_count": 2,
        },
        "outcome": outcome,
        "opening_index": index // 2,
        "seed": 100 + index // 2,
    }


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_legacy_artifact_requires_explicit_opt_in(tmp_path):
    path = tmp_path / "legacy.jsonl"
    write_jsonl(
        path,
        [
            legacy_game(0, "challenger"),
            legacy_game(1, "baseline"),
            legacy_game(2, "challenger"),
            legacy_game(3, "baseline"),
        ],
    )

    with pytest.raises(ValueError, match="legacy per-game schema"):
        analyze_real_arena(path, bootstrap_samples=100)


def test_legacy_report_is_explicitly_descriptive(tmp_path):
    path = tmp_path / "legacy.jsonl"
    write_jsonl(
        path,
        [
            legacy_game(0, "challenger"),
            legacy_game(1, "baseline"),
            legacy_game(2, "challenger"),
            legacy_game(3, "challenger"),
        ],
    )

    result = analyze_real_arena(path, allow_legacy=True, bootstrap_samples=200, seed=7, sprt_elo1=(5.0, 100.0))

    assert result["status"] == "legacy_real_arena_descriptive_calibration"
    assert result["validation"]["validation_status"] == "legacy_structural_audit_only"
    assert result["promotion_decision"] == "not_evaluated"
    assert result["calibration"]["wins"] == 3
    assert result["calibration"]["losses"] == 1
    assert {item["decision"] for item in result["sprt"]} <= {"continue", "accept_h1", "reject_h1"}


def test_legacy_report_preserves_missing_schema_fields(tmp_path):
    path = tmp_path / "legacy.jsonl"
    write_jsonl(
        path,
        [
            legacy_game(0, "challenger"),
            legacy_game(1, "baseline"),
            legacy_game(2, "baseline"),
            legacy_game(3, "challenger"),
        ],
    )

    result = analyze_real_arena(path, allow_legacy=True, bootstrap_samples=100)

    assert "valid" in result["validation"]["missing_current_game_fields"]
    assert "termination_reason" in result["validation"]["missing_current_game_fields"]


def test_legacy_pair_bootstrap_uses_complete_pairs(tmp_path):
    path = tmp_path / "legacy.jsonl"
    write_jsonl(
        path,
        [
            legacy_game(0, "challenger"),
            legacy_game(1, "baseline"),
            legacy_game(2, "challenger"),
            legacy_game(3, "baseline"),
        ],
    )

    result = analyze_real_arena(path, allow_legacy=True, bootstrap_samples=200, seed=0)

    assert result["paired_bootstrap"]["units"] == 2
    assert result["paired_bootstrap"]["audit_status"].startswith("descriptive_paired_resampling_only")
