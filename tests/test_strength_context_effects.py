import pytest

from tools.analytics.strength_context_effects import summarize_strength_context_effects


def game(index, outcome, colour=None, opening=None, seed=None, valid=True):
    return {
        "game_index": index,
        "outcome": outcome,
        "valid": valid,
        "challenger_color": colour or ("white" if index % 2 == 0 else "black"),
        "opening_index": index // 2 if opening is None else opening,
        "seed": 17000 + index if seed is None else seed,
    }


def test_context_effects_report_balanced_colour_opening_and_unique_seed_sets():
    games = [
        game(0, "challenger", "white", opening=0, seed=101),
        game(1, "baseline", "black", opening=0, seed=211),
        game(2, "draw", "white", opening=1, seed=307),
        game(3, "challenger", "black", opening=1, seed=401),
    ]

    result = summarize_strength_context_effects(games)

    assert result["valid_games"] == 4
    assert result["colour"]["white"]["games"] == 2
    assert result["colour"]["black"]["games"] == 2
    assert result["opening"]["0"]["games"] == 2
    assert result["opening"]["1"]["games"] == 2
    assert result["seed"]["unique_seeds"] == 4
    assert result["flags"] == {
        "colour_imbalance": False,
        "opening_imbalance": False,
        "seed_reuse": False,
    }


def test_context_effects_expose_seed_reuse_without_misclassifying_it_as_a_draw():
    games = [
        game(0, "challenger", seed=101),
        game(1, "baseline", seed=101),
    ]

    result = summarize_strength_context_effects(games)

    assert result["seed"]["unique_seeds"] == 1
    assert result["seed"]["reused_seeds"] == [("101", 2)]
    assert result["flags"]["seed_reuse"] is True


def test_context_effects_ignore_invalid_games():
    games = [
        game(0, "challenger", "white"),
        game(1, "invalid", "black", valid=False),
    ]

    result = summarize_strength_context_effects(games)

    assert result["valid_games"] == 1
    assert result["colour"]["white"]["games"] == 1
    assert result["colour"]["black"]["games"] == 0


def test_context_effects_require_at_least_one_valid_game():
    with pytest.raises(ValueError, match="valid Strength game"):
        summarize_strength_context_effects([game(0, "invalid", valid=False)])


def test_context_effects_reject_invalid_colour_in_valid_game():
    bad = game(0, "challenger")
    bad["challenger_color"] = "red"
    with pytest.raises(ValueError, match="invalid challenger_color"):
        summarize_strength_context_effects([bad])
