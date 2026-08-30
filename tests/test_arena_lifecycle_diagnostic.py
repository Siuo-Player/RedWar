from tools.analytics.arena_lifecycle_diagnostic import compare_modes, parse_seeds, summarize


def test_parse_seeds_requires_exactly_16_unique_non_negative_values():
    assert parse_seeds(",".join(str(value) for value in range(16))) == tuple(range(16))

    for raw in ("1,2,3", ",".join(["1"] * 16), ",".join(str(value) for value in range(15)) + ",-1"):
        try:
            parse_seeds(raw)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid opening seed declaration was accepted")


def test_summarize_preserves_colour_and_total_outcomes():
    records = [
        {"outcome": "challenger", "challenger_color": "white"},
        {"outcome": "baseline", "challenger_color": "black"},
        {"outcome": "invalid", "challenger_color": "white"},
    ]
    summary = summarize(records)
    assert summary["games"] == 3
    assert summary["valid_games"] == 2
    assert summary["totals"] == {"challenger": 1, "baseline": 1, "invalid": 1}
    assert summary["challenger_outcomes_by_colour"]["white"]["challenger"] == 1
    assert summary["challenger_outcomes_by_colour"]["white"]["invalid"] == 1
    assert summary["challenger_outcomes_by_colour"]["black"]["baseline"] == 1


def test_compare_modes_reports_outcome_differences_without_calling_them_strength():
    persistent = summarize([
        {"outcome": "challenger", "challenger_color": "white"},
        {"outcome": "baseline", "challenger_color": "black"},
    ])
    fresh = summarize([
        {"outcome": "baseline", "challenger_color": "white"},
        {"outcome": "baseline", "challenger_color": "black"},
    ])
    comparison = compare_modes(persistent, fresh)
    assert comparison["outcome_delta"] == {"challenger": 1, "baseline": -1, "invalid": 0}
    assert comparison["persistent_colour_wins_difference"] == 1
    assert comparison["fresh_colour_wins_difference"] == 0
