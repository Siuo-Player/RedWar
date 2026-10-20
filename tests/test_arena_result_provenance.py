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



def test_experiment_summary_never_reports_promotion(monkeypatch, tmp_path):
    from tools.analytics import arena_tournament

    class FakeBot:
        def __init__(self, nodes, executable_path):
            self.executable_path = executable_path

        def __del__(self):
            pass

    call_count = {"value": 0}

    def fake_match(bot_white, bot_black, opening_index, opening_seed):
        # Challenger wins both colour-inverted games.
        winner = "Brancas" if call_count["value"] == 0 else "Pretas"
        call_count["value"] += 1
        return {
            "winner": winner,
            "seed": opening_seed,
            "opening_index": opening_index,
            "initial_rwen": "initial",
            "final_rwen": "final",
            "plies": 1,
            "actions": [],
            "action_counts": {},
            "termination_reason": "game_over",
            "valid": True,
            "failure_reason": None,
            "failure_exception_type": None,
            "failure_detail": None,
        }

    monkeypatch.setattr(arena_tournament, "CppEngineBot", FakeBot)
    monkeypatch.setattr(arena_tournament, "run_headless_match", fake_match)
    results_path = tmp_path / "experiment.jsonl"

    exit_code = arena_tournament.start_tournament(
        challenger_engine="challenger",
        baseline_engine="baseline",
        num_games=2,
        win_threshold=0,
        nodes=1,
        results_path=str(results_path),
        challenger_version="candidate",
        baseline_version="baseline",
        rules_version="rules",
        mode="experiment",
    )

    import json

    summary = json.loads(results_path.with_suffix(".jsonl.summary.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert summary["mode"] == "experiment"
    assert summary["promotion_authority"] is False
    assert summary["promotion_decision"] == "not_authorized"
    assert summary["promoted"] is False
    assert summary["wins_challenger"] == 2
