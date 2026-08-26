from tools.analytics import holdout_arena


def test_holdout_summary_contains_identity_and_balanced_colours(monkeypatch):
    class FakeBot:
        def __init__(self, *args, **kwargs):
            pass

        def __del__(self):
            pass

    def fake_match(_white, _black, opening_index, opening_seed=None):
        assert opening_seed in [17001, 17003, 17011, 17021, 17027, 17033, 17041, 17047]
        return {
            "winner": "Brancas" if opening_index % 2 == 0 else "Pretas",
            "seed": opening_seed,
            "opening_index": opening_index,
            "initial_rwen": "root",
            "final_rwen": "final",
            "plies": 4,
        }

    monkeypatch.setattr(holdout_arena, "CppEngineBot", FakeBot)
    monkeypatch.setattr(holdout_arena, "run_headless_match", fake_match)

    summary = holdout_arena.run_holdout("challenger", "baseline", 100)

    assert summary["mode"] == "protected_holdout"
    assert summary["holdout_set_id"] == "ares-holdout-v1"
    assert len(summary["holdout_set_sha256"]) == 64
    assert summary["cases"] == 8
    assert summary["wins_challenger"] == 8
    assert summary["wins_baseline"] == 0
    assert summary["draws"] == 0
