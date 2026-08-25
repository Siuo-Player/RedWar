from tools.analytics.arena_tournament import summarize_pentanomial


def record(index, outcome, color, opening):
    return {
        "game_index": index,
        "pair_id": f"pair-{index // 2:06d}",
        "pair_member": index % 2,
        "challenger_color": color,
        "opening_index": opening,
        "outcome": outcome,
    }


def test_summary_uses_complete_inverted_colour_pairs():
    games = [
        record(0, "challenger", "white", 0),
        record(1, "baseline", "black", 0),
        record(2, "draw", "white", 1),
        record(3, "challenger", "black", 1),
    ]
    summary = summarize_pentanomial(games)
    assert summary["complete_pairs"] == 2
    assert summary["paired_games_used"] == 4
    assert summary["bins"] == {"DD_WL_LW": 2}
    assert summary["incomplete_pair_ids"] == []


def test_summary_rejects_same_opening_mismatch():
    games = [
        record(0, "challenger", "white", 0),
        record(1, "baseline", "black", 2),
    ]
    try:
        summarize_pentanomial(games)
    except ValueError as exc:
        assert "same opening" in str(exc)
    else:
        raise AssertionError("expected paired opening validation to fail")
