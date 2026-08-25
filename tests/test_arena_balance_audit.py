from tools.analytics.arena_tournament import summarize_experiment_balance


def test_balance_audit_reports_colour_and_opening_distribution():
    games = [
        {"challenger_color": "white", "outcome": "challenger", "opening_index": 0, "seed": 101},
        {"challenger_color": "black", "outcome": "baseline", "opening_index": 1, "seed": 211},
        {"challenger_color": "white", "outcome": "draw", "opening_index": 0, "seed": 307},
        {"challenger_color": "black", "outcome": "challenger", "opening_index": 1, "seed": 401},
    ]

    audit = summarize_experiment_balance(games)

    assert audit["challenger_games_by_colour"] == {"white": 2, "black": 2}
    assert audit["colour_game_count_difference"] == 0
    assert audit["colour_wins_difference"] == 0
    assert audit["opening_games"] == {"0": 2, "1": 2}
    assert audit["opening_seed_sequences"] == {
        "0": [101, 307],
        "1": [211, 401],
    }


def test_balance_audit_exposes_colour_imbalance_instead_of_hiding_it():
    audit = summarize_experiment_balance([
        {"challenger_color": "white", "outcome": "challenger", "opening_index": 0, "seed": 101},
        {"challenger_color": "white", "outcome": "challenger", "opening_index": 1, "seed": 211},
        {"challenger_color": "black", "outcome": "baseline", "opening_index": 0, "seed": 307},
    ])

    assert audit["challenger_games_by_colour"] == {"white": 2, "black": 1}
    assert audit["colour_game_count_difference"] == 1
    assert audit["colour_wins_difference"] == 2
