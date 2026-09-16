import pytest

from tools.analytics.validate_arena_lifecycle_diagnostic import validate_payload


def _record(game_index, seed=101, colour="white", outcome="challenger"):
    return {
        "game_index": game_index,
        "pair_id": game_index // 2,
        "opening_index": (game_index // 2) % 16,
        "seed": seed,
        "challenger_color": colour,
        "winner_side": colour,
        "outcome": outcome,
        "valid": True,
        "termination_reason": "capture",
        "plies": 2,
    }


def _series(records):
    totals = {"challenger": 0, "baseline": 0, "invalid": 0}
    colours = {
        "white": {"challenger": 0, "baseline": 0, "invalid": 0},
        "black": {"challenger": 0, "baseline": 0, "invalid": 0},
    }
    for record in records:
        totals[record["outcome"]] += 1
        colours[record["challenger_color"]][record["outcome"]] += 1
    return {
        "games": len(records),
        "valid_games": len(records),
        "totals": totals,
        "challenger_outcomes_by_colour": colours,
        "records": records,
    }


def _payload(games=2):
    persistent = [_record(0, colour="white"), _record(1, colour="black")]
    fresh = [_record(0, colour="white"), _record(1, colour="black")]
    if games != 2:
        raise AssertionError("test fixture only defines two games")
    persistent_series = _series(persistent)
    fresh_series = _series(fresh)
    return {
        "schema_version": "redwar-arena-lifecycle-diagnostic-v1",
        "diagnostic_status": "observational_lifecycle_sensitivity_no_promotion_decision",
        "parameters": {
            "games": games,
            "opening_seeds": list(range(101, 117)),
            "pairing_policy": "adjacent_games_same_opening_with_inverted_challenger_colour",
        },
        "persistent_per_game_process": persistent_series,
        "fresh_process_per_game": fresh_series,
        "comparison": {
            "persistent_totals": persistent_series["totals"],
            "fresh_totals": fresh_series["totals"],
        },
    }


def test_validate_accepts_identical_paired_schedule():
    validate_payload(_payload())


def test_validate_rejects_schedule_mismatch_between_modes():
    payload = _payload()
    payload["fresh_process_per_game"]["records"][1]["seed"] = 102
    with pytest.raises(ValueError, match="schedule mismatch"):
        validate_payload(payload)


def test_validate_rejects_broken_colour_inversion():
    payload = _payload()
    for series_name in ("persistent_per_game_process", "fresh_process_per_game"):
        record = payload[series_name]["records"][1]
        record["challenger_color"] = "white"
        payload[series_name]["challenger_outcomes_by_colour"] = {
            "white": {"challenger": 2, "baseline": 0, "invalid": 0},
            "black": {"challenger": 0, "baseline": 0, "invalid": 0},
        }
    with pytest.raises(ValueError, match="does not invert challenger colour"):
        validate_payload(payload)


def test_validate_rejects_summary_mismatch():
    payload = _payload()
    payload["comparison"]["fresh_totals"] = {"challenger": 1, "baseline": 1, "invalid": 0}
    with pytest.raises(ValueError, match="comparison fresh_totals"):
        validate_payload(payload)
