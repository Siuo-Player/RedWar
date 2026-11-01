import math

import pytest

from tools.analytics.arena_tournament import (
    _aggregate_elo_equivalent_from_games,
    _sequential_rating_diagnostic_from_games,
    summarize_experiment_balance,
    summarize_pentanomial,
)


def game(outcome, valid=True, color="white", opening=0, index=0):
    return {
        "game_index": index,
        "pair_id": f"pair-{index // 2:06d}",
        "pair_member": index % 2,
        "challenger_color": color,
        "opening_index": opening,
        "seed": 17000 + opening,
        "outcome": outcome,
        "valid": valid,
        "failure_reason": None if valid else "max_plies_reached",
    }


def test_invalid_games_are_excluded_from_sequential_rating_diagnostic():
    games = [
        game("challenger", valid=True, index=0),
        game("invalid", valid=False, color="black", index=1),
    ]

    challenger, baseline, delta, _ = _sequential_rating_diagnostic_from_games(games)

    assert challenger > baseline
    assert delta > 0


def test_aggregate_elo_equivalent_is_order_invariant_for_the_same_outcomes():
    outcomes = ["challenger"] * 54 + ["baseline"] * 46
    stored_order = [game(outcome, index=index) for index, outcome in enumerate(outcomes)]
    reversed_order = list(reversed(stored_order))

    first_score, first_delta, first_games = _aggregate_elo_equivalent_from_games(stored_order)
    second_score, second_delta, second_games = _aggregate_elo_equivalent_from_games(reversed_order)

    assert first_games == second_games == 100
    assert first_score == second_score == pytest.approx(0.54)
    assert first_delta == second_delta == pytest.approx(400.0 * math.log10(54 / 46))
    assert first_delta > 0


def test_sequential_rating_remains_explicitly_order_dependent_diagnostic():
    wins_first = [game(outcome, index=index) for index, outcome in enumerate(["challenger"] * 4 + ["baseline"] * 2)]
    losses_first = list(reversed(wins_first))

    _, _, wins_first_delta, _ = _sequential_rating_diagnostic_from_games(wins_first)
    _, _, losses_first_delta, _ = _sequential_rating_diagnostic_from_games(losses_first)

    assert wins_first_delta != losses_first_delta


def test_invalid_games_are_excluded_from_balance_audit():
    balance = summarize_experiment_balance([
        game("challenger", valid=True, color="white", index=0),
        game("invalid", valid=False, color="black", index=1),
    ])

    assert balance["valid_games"] == 1
    assert balance["challenger_games_by_colour"] == {"white": 1}


def test_invalid_games_break_pair_completeness_instead_of_becoming_draws():
    summary = summarize_pentanomial([
        game("challenger", valid=True, color="white", index=0),
        game("invalid", valid=False, color="black", index=1),
    ])

    assert summary["paired_games_used"] == 0
    assert summary["complete_pairs"] == 0
    assert summary["incomplete_pair_ids"] == ["pair-000000"]
