import json

from tools.analytics.strength_context_artifacts import enrich_arena_summary


def record(index, outcome, colour, opening, seed, valid=True):
    return {
        "game_index": index,
        "outcome": outcome,
        "challenger_color": colour,
        "opening_index": opening,
        "seed": seed,
        "valid": valid,
    }


def test_enrich_arena_summary_attaches_context_without_changing_strength_fields(tmp_path):
    results = tmp_path / "arena.jsonl"
    summary = tmp_path / "arena.jsonl.summary.json"
    records = [
        record(0, "challenger", "white", 0, 101),
        record(1, "baseline", "black", 0, 211),
        record(2, "draw", "white", 1, 307),
        record(3, "challenger", "black", 1, 401),
    ]
    results.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
    summary.write_text(json.dumps({"rating_delta": 12.5, "promoted": False}), encoding="utf-8")

    payload = enrich_arena_summary(results, summary)

    assert payload["rating_delta"] == 12.5
    assert payload["promoted"] is False
    assert payload["strength_context_diagnostics"]["valid_games"] == 4
    assert payload["strength_context_diagnostics"]["flags"] == {
        "colour_imbalance": False,
        "opening_imbalance": False,
        "seed_reuse": False,
    }
    persisted = json.loads(summary.read_text(encoding="utf-8"))
    assert persisted == payload


def test_enrich_arena_summary_ignores_invalid_games(tmp_path):
    results = tmp_path / "arena.jsonl"
    summary = tmp_path / "arena.jsonl.summary.json"
    records = [
        record(0, "challenger", "white", 0, 101),
        record(1, "invalid", "black", 0, 211, valid=False),
    ]
    results.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
    summary.write_text(json.dumps({"games": 2}), encoding="utf-8")

    payload = enrich_arena_summary(results, summary)

    assert payload["games"] == 2
    assert payload["strength_context_diagnostics"]["valid_games"] == 1
