from tools.analytics.arena_tournament import _strength_from_games, summarize_experiment_balance, summarize_pentanomial


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


def test_invalid_games_are_excluded_from_strength_rating():
    games = [
        game("challenger", valid=True, index=0),
        game("invalid", valid=False, color="black", index=1),
    ]

    challenger, baseline, delta, _ = _strength_from_games(games)

    assert challenger > baseline
    assert delta > 0


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
    assert summary["incomplete_pair_ids"] == []
