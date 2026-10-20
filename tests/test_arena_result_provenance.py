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
    assert summary["incomplete_pair_ids"] == ["pair-000000"]



def test_experiment_mode_cannot_promote_with_zero_threshold():
    from tools.analytics.arena_tournament import _promotion_decision

    assert not _promotion_decision(
        wins_challenger=54,
        wins_baseline=46,
        invalid_games=0,
        win_threshold=0,
        promotion_authority=False,
    )


def test_authoritative_promotion_gate_keeps_existing_margin_semantics():
    from tools.analytics.arena_tournament import _promotion_decision

    assert _promotion_decision(60, 50, 0, 10, True)
    assert not _promotion_decision(59, 50, 0, 10, True)
    assert not _promotion_decision(60, 50, 1, 10, True)


def test_non_authoritative_experiment_does_not_promote_even_with_wins():
    from tools.analytics.arena_tournament import _promotion_decision

    assert not _promotion_decision(100, 0, 0, 0, False)



def test_aggregate_score_elo_equivalent_is_order_invariant():
    from tools.analytics.arena_tournament import _aggregate_score_elo_equivalent

    first_order = [
        game("challenger", index=0),
        game("challenger", index=1),
        game("baseline", index=2),
        game("baseline", index=3),
    ]
    second_order = [
        game("challenger", index=0),
        game("baseline", index=1),
        game("challenger", index=2),
        game("baseline", index=3),
    ]

    assert _aggregate_score_elo_equivalent(first_order) == _aggregate_score_elo_equivalent(second_order)
    assert _aggregate_score_elo_equivalent(first_order) == 0.0


def test_sequential_elo_diagnostic_is_explicitly_order_dependent():
    first_order = [
        game("challenger", index=0),
        game("challenger", index=1),
        game("baseline", index=2),
        game("baseline", index=3),
    ]
    second_order = [
        game("challenger", index=0),
        game("baseline", index=1),
        game("challenger", index=2),
        game("baseline", index=3),
    ]

    assert _strength_from_games(first_order)[2] != _strength_from_games(second_order)[2]


def test_aggregate_score_elo_equivalent_is_undefined_for_extreme_or_empty_results():
    from tools.analytics.arena_tournament import _aggregate_score_elo_equivalent

    assert _aggregate_score_elo_equivalent([]) is None
    assert _aggregate_score_elo_equivalent([game("challenger", index=0)]) is None
