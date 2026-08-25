import pytest

from tools.analytics.arena_pairs import GameOutcome, aggregate_pentanomial, incomplete_pairs, make_pair_id, validate_pair_structure


def game(index, outcome, color, opening=0, pair=None):
    return GameOutcome(
        game_index=index,
        pair_id=pair or make_pair_id(index),
        opening_index=opening,
        challenger_color=color,
        outcome=outcome,
    )


def test_pair_id_is_stable_for_adjacent_games():
    assert make_pair_id(0) == make_pair_id(1)
    assert make_pair_id(1) != make_pair_id(2)


def test_all_pentanomial_bins():
    outcomes = [
        ("baseline", "baseline", "LL"),
        ("baseline", "draw", "LD_DL"),
        ("draw", "baseline", "LD_DL"),
        ("draw", "draw", "DD_WL_LW"),
        ("challenger", "baseline", "DD_WL_LW"),
        ("baseline", "challenger", "DD_WL_LW"),
        ("challenger", "draw", "WD_DW"),
        ("draw", "challenger", "WD_DW"),
        ("challenger", "challenger", "WW"),
    ]
    for offset, (first, second, expected) in enumerate(outcomes):
        pair = f"pair-{offset}"
        games = [
            game(offset * 2, first, "white", pair=pair),
            game(offset * 2 + 1, second, "black", pair=pair),
        ]
        assert aggregate_pentanomial(games) == {expected: 1}


def test_incomplete_pairs_are_reported_not_binned():
    games = [game(0, "challenger", "white"), game(2, "baseline", "white")]
    assert incomplete_pairs(games) == {"pair-000000", "pair-000001"}
    assert aggregate_pentanomial(games) == {}


def test_pair_structure_requires_same_opening_and_colour_flip():
    validate_pair_structure([
        game(0, "challenger", "white", opening=3),
        game(1, "baseline", "black", opening=3),
    ])

    with pytest.raises(ValueError, match="same opening"):
        validate_pair_structure([
            game(0, "challenger", "white", opening=3),
            game(1, "baseline", "black", opening=4),
        ])

    with pytest.raises(ValueError, match="invert challenger colour"):
        validate_pair_structure([
            game(0, "challenger", "white", opening=3),
            game(1, "baseline", "white", opening=3),
        ])
