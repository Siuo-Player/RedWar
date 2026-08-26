import pytest

from tools.analytics.arena_experiment_validation import validate_experiment_records


METADATA = {
    "challenger_version": "c1",
    "baseline_version": "b1",
    "rules_version": "r1",
    "node_budget": 10_000,
    "games": 4,
    "opening_count": 2,
}


def game(index, outcome, valid=True, opening=None):
    opening = index // 2 if opening is None else opening
    return {
        "game_index": index,
        "pair_id": f"pair-{index // 2:06d}",
        "pair_member": index % 2,
        "challenger_color": "white" if index % 2 == 0 else "black",
        "baseline_color": "black" if index % 2 == 0 else "white",
        "opening_index": opening,
        "seed": 17_000 + index,
        "outcome": outcome,
        "valid": valid,
        "termination_reason": "game_over" if valid else "max_plies",
        "experiment": dict(METADATA),
    }


def test_valid_experiment_records_are_accepted():
    records = [
        game(0, "challenger"),
        game(1, "baseline"),
        game(2, "draw"),
        game(3, "challenger"),
    ]

    audit = validate_experiment_records(records, METADATA)

    assert audit["games"] == 4
    assert audit["valid_games"] == 4
    assert audit["invalid_games"] == 0
    assert audit["complete_valid_pairs"] == 2
    assert audit["incomplete_valid_pair_ids"] == []


def test_invalid_observation_is_explicit_and_excluded_from_pairs():
    records = [
        game(0, "challenger"),
        game(1, "invalid", valid=False),
        game(2, "draw"),
        game(3, "challenger"),
    ]

    audit = validate_experiment_records(records, METADATA)

    assert audit["valid_games"] == 3
    assert audit["invalid_games"] == 1
    assert audit["outcomes"]["invalid"] == 1
    assert audit["incomplete_valid_pair_ids"] == ["pair-000000"]
    assert audit["complete_valid_pairs"] == 1


def test_invalid_game_cannot_be_encoded_as_draw():
    records = [game(0, "draw", valid=False), game(1, "baseline"), game(2, "draw"), game(3, "challenger")]
    with pytest.raises(ValueError, match="outcome='invalid'"):
        validate_experiment_records(records, METADATA)


def test_metadata_mismatch_is_rejected():
    records = [game(i, "draw") for i in range(4)]
    records[2]["experiment"]["rules_version"] = "other"
    with pytest.raises(ValueError, match="metadata mismatch"):
        validate_experiment_records(records, METADATA)
