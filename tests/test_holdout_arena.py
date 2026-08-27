from tools.analytics import holdout_arena

HOLDOUT_SEEDS = [17001, 17003, 17011, 17021, 17027, 17033, 17041, 17047]


def test_holdout_summary_preserves_cases_and_colour_pairs(monkeypatch):
    class FakeBot:
        def __init__(self, *args, **kwargs):
            pass

        def __del__(self):
            pass

    calls = []

    def fake_match(_white, _black, opening_index, opening_seed=None):
        assert opening_seed in HOLDOUT_SEEDS
        calls.append((opening_index, opening_seed))
        return {
            "winner": "Brancas",
            "seed": opening_seed,
            "opening_index": opening_index,
            "initial_rwen": "root",
            "final_rwen": "final",
            "plies": 4,
            "valid": True,
            "termination_reason": "game_over",
            "failure_reason": None,
        }

    monkeypatch.setattr(holdout_arena, "CppEngineBot", FakeBot)
    monkeypatch.setattr(holdout_arena, "run_headless_match", fake_match)

    summary = holdout_arena.run_holdout("challenger", "baseline", 100)

    assert summary["mode"] == "protected_holdout"
    assert summary["holdout_set_id"] == "ares-holdout-v1"
    assert len(summary["holdout_set_sha256"]) == 64
    assert summary["cases"] == 8
    assert summary["games"] == 16
    assert summary["complete_pairs"] == 8
    assert summary["wins_challenger"] == 4
    assert summary["wins_baseline"] == 4
    assert summary["draws"] == 0
    assert summary["invalid_games"] == 0

    for index in range(8):
        first, second = summary["games_detail"][index * 2:index * 2 + 2]
        assert first["pair_id"] == second["pair_id"]
        assert first["holdout_case"] == second["holdout_case"]
        assert first["opening_index"] == second["opening_index"]
        assert first["seed"] == second["seed"]
        assert first["challenger_color"] != second["challenger_color"]
        assert first["pair_member"] == 0
        assert second["pair_member"] == 1
        assert calls[index * 2] == calls[index * 2 + 1]


def test_holdout_keeps_explicit_case_identity_and_provenance(monkeypatch):
    class FakeBot:
        def __init__(self, *args, **kwargs):
            pass

        def __del__(self):
            pass

    def fake_match(_white, _black, opening_index, opening_seed=None):
        return {
            "winner": "Brancas",
            "seed": opening_seed,
            "opening_index": opening_index,
            "initial_rwen": "root",
            "final_rwen": "final",
            "plies": 4,
        }

    monkeypatch.setattr(holdout_arena, "CppEngineBot", FakeBot)
    monkeypatch.setattr(holdout_arena, "run_headless_match", fake_match)

    summary = holdout_arena.run_holdout(
        "challenger",
        "baseline",
        10000,
        challenger_version="challenger-sha",
        baseline_version="baseline-sha",
        rules_version="rules-sha",
    )
    case_ids = [game["holdout_case"] for game in summary["games_detail"]]
    assert case_ids == [f"holdout-00{i}" for i in range(1, 9) for _ in (0, 1)]
    assert summary["experiment"]["challenger_version"] == "challenger-sha"
    assert summary["experiment"]["baseline_version"] == "baseline-sha"
    assert summary["experiment"]["rules_version"] == "rules-sha"
    assert summary["experiment"]["node_budget"] == 10000
