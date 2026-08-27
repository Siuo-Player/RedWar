import pytest

from tools.analytics.strength_matchup_context import (
    analyze_matchup_context,
    detect_intransitive_cycles,
    summarize_matchups,
)


def game(challenger, baseline, outcome, opening=0, valid=True, node_budget=10_000, rules="r1"):
    return {
        "valid": valid,
        "outcome": outcome,
        "opening_index": opening,
        "experiment": {
            "challenger_version": challenger,
            "baseline_version": baseline,
            "node_budget": node_budget,
            "rules_version": rules,
        },
    }


def test_summarize_matchups_preserves_direction_and_context():
    summaries = summarize_matchups(
        [
            game("A", "B", "challenger", opening=1),
            game("A", "B", "baseline", opening=1),
            game("A", "B", "draw", opening=1),
            game("B", "A", "challenger", opening=1),
            game("A", "B", "challenger", opening=2),
            game("A", "B", "challenger", opening=2, valid=False),
        ],
        context_fields=("opening_index",),
    )

    assert len(summaries) == 3
    first = next(
        item
        for item in summaries
        if item["challenger"] == "A"
        and item["baseline"] == "B"
        and item["context"]["opening_index"] == 1
    )
    assert first["games"] == 3
    assert first["challenger_wins"] == 1
    assert first["baseline_wins"] == 1
    assert first["draws"] == 1
    assert first["challenger_score_rate"] == pytest.approx(0.5)
    assert first["context"]["node_budget"] == 10_000
    assert first["context"]["rules_version"] == "r1"


def test_different_budgets_are_not_pooled():
    summaries = summarize_matchups(
        [
            game("A", "B", "challenger", node_budget=10_000),
            game("A", "B", "baseline", node_budget=10_000),
            game("A", "B", "challenger", node_budget=20_000),
            game("A", "B", "baseline", node_budget=20_000),
        ]
    )

    assert len(summaries) == 2
    assert {item["context"]["node_budget"] for item in summaries} == {10_000, 20_000}


def test_detects_three_way_intransitivity():
    summaries = [
        {"challenger": "A", "baseline": "B", "context": {}, "games": 4, "challenger_score_rate": 0.75},
        {"challenger": "B", "baseline": "C", "context": {}, "games": 4, "challenger_score_rate": 0.75},
        {"challenger": "C", "baseline": "A", "context": {}, "games": 4, "challenger_score_rate": 0.75},
    ]

    cycles = detect_intransitive_cycles(summaries, min_games=4)

    assert len(cycles) == 1
    assert cycles[0]["players"] == ["A", "B", "C"]
    assert cycles[0]["interpretation"] == "descriptive_intransitive_cycle"


def test_does_not_mix_contexts_to_create_a_cycle():
    summaries = [
        {"challenger": "A", "baseline": "B", "context": {"opening_index": 1}, "games": 4, "challenger_score_rate": 0.75},
        {"challenger": "B", "baseline": "C", "context": {"opening_index": 2}, "games": 4, "challenger_score_rate": 0.75},
        {"challenger": "C", "baseline": "A", "context": {"opening_index": 1}, "games": 4, "challenger_score_rate": 0.75},
    ]

    assert detect_intransitive_cycles(summaries, min_games=4) == []


def test_analysis_marks_result_as_descriptive_only():
    result = analyze_matchup_context(
        [
            game("A", "B", "challenger", opening=0),
            game("A", "B", "baseline", opening=0),
            game("A", "B", "challenger", opening=0),
            game("A", "B", "baseline", opening=0),
        ],
        min_games=4,
    )

    assert result["status"] == "descriptive_matchup_analysis_only"
    assert result["context_fields"] == ["opening_index"]
    assert result["control_fields"] == ["rules_version", "node_budget"]
    assert result["intransitive_cycles"] == []
