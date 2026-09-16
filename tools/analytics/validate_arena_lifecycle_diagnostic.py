"""Validate lifecycle-diagnostic evidence structure without judging strength.

The validator is deliberately fail-closed: it checks that the persistent and
fresh-process series contain the same paired experimental schedule and that the
reported summaries are consistent with their raw records. It does not infer
lifecycle sensitivity or make any promotion decision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "redwar-arena-lifecycle-diagnostic-v1"
REQUIRED_OUTCOMES = {"challenger", "baseline", "invalid"}
REQUIRED_COLOURS = {"white", "black"}


def _fail(message: str) -> None:
    raise ValueError(message)


def _validate_series(name: str, series: dict[str, Any], expected_games: int) -> None:
    records = series.get("records")
    if not isinstance(records, list):
        _fail(f"{name}: records must be a list")
    if len(records) != expected_games:
        _fail(f"{name}: expected {expected_games} records, got {len(records)}")

    totals = series.get("totals")
    if not isinstance(totals, dict) or set(totals) != REQUIRED_OUTCOMES:
        _fail(f"{name}: totals keys are invalid")
    if sum(int(totals[key]) for key in REQUIRED_OUTCOMES) != expected_games:
        _fail(f"{name}: totals do not sum to games")

    colours = series.get("challenger_outcomes_by_colour")
    if not isinstance(colours, dict) or set(colours) != REQUIRED_COLOURS:
        _fail(f"{name}: colour summary keys are invalid")

    seen_indices: set[int] = set()
    computed_totals = {key: 0 for key in REQUIRED_OUTCOMES}
    computed_colours = {
        colour: {key: 0 for key in REQUIRED_OUTCOMES}
        for colour in REQUIRED_COLOURS
    }

    for record in records:
        if not isinstance(record, dict):
            _fail(f"{name}: record is not an object")
        game_index = record.get("game_index")
        pair_id = record.get("pair_id")
        colour = record.get("challenger_color")
        outcome = record.get("outcome")
        opening_index = record.get("opening_index")
        seed = record.get("seed")

        if not isinstance(game_index, int) or game_index < 0 or game_index >= expected_games:
            _fail(f"{name}: invalid game_index {game_index!r}")
        if game_index in seen_indices:
            _fail(f"{name}: duplicate game_index {game_index}")
        seen_indices.add(game_index)
        if pair_id != game_index // 2:
            _fail(f"{name}: game {game_index} has incorrect pair_id {pair_id!r}")
        if colour not in REQUIRED_COLOURS:
            _fail(f"{name}: game {game_index} has invalid challenger_color {colour!r}")
        if outcome not in REQUIRED_OUTCOMES:
            _fail(f"{name}: game {game_index} has invalid outcome {outcome!r}")
        if not isinstance(opening_index, int) or opening_index < 0:
            _fail(f"{name}: game {game_index} has invalid opening_index")
        if not isinstance(seed, int) or seed < 0:
            _fail(f"{name}: game {game_index} has invalid seed")

        computed_totals[outcome] += 1
        computed_colours[colour][outcome] += 1

    if seen_indices != set(range(expected_games)):
        _fail(f"{name}: game indices are not the complete 0..{expected_games - 1} range")
    if computed_totals != {key: int(totals[key]) for key in REQUIRED_OUTCOMES}:
        _fail(f"{name}: totals disagree with records")
    if computed_colours != {
        colour: {key: int(colours[colour][key]) for key in REQUIRED_OUTCOMES}
        for colour in REQUIRED_COLOURS
    }:
        _fail(f"{name}: colour summary disagrees with records")


def validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != EXPECTED_SCHEMA:
        _fail("unexpected lifecycle diagnostic schema_version")
    if payload.get("diagnostic_status") != "observational_lifecycle_sensitivity_no_promotion_decision":
        _fail("unexpected diagnostic_status")

    parameters = payload.get("parameters")
    if not isinstance(parameters, dict):
        _fail("parameters must be an object")
    games = parameters.get("games")
    if not isinstance(games, int) or games <= 0 or games % 2:
        _fail("parameters.games must be a positive even integer")
    seeds = parameters.get("opening_seeds")
    if not isinstance(seeds, list) or len(seeds) != 16 or len(set(seeds)) != 16:
        _fail("parameters.opening_seeds must contain 16 unique values")
    if any(not isinstance(seed, int) or seed < 0 for seed in seeds):
        _fail("parameters.opening_seeds must contain non-negative integers")
    if parameters.get("pairing_policy") != "adjacent_games_same_opening_with_inverted_challenger_colour":
        _fail("unexpected pairing_policy")

    persistent = payload.get("persistent_per_game_process")
    fresh = payload.get("fresh_process_per_game")
    if not isinstance(persistent, dict) or not isinstance(fresh, dict):
        _fail("both lifecycle series are required")

    _validate_series("persistent", persistent, games)
    _validate_series("fresh", fresh, games)

    for index in range(games):
        p = persistent["records"][index]
        f = fresh["records"][index]
        for key in ("game_index", "pair_id", "opening_index", "seed", "challenger_color"):
            if p[key] != f[key]:
                _fail(f"schedule mismatch at game {index}: field {key}")

    for start in range(0, games, 2):
        first = persistent["records"][start]
        second = persistent["records"][start + 1]
        if first["seed"] != second["seed"]:
            _fail(f"persistent pair {start // 2} does not reuse the same seed")
        if {first["challenger_color"], second["challenger_color"]} != {"white", "black"}:
            _fail(f"persistent pair {start // 2} does not invert challenger colour")

        first = fresh["records"][start]
        second = fresh["records"][start + 1]
        if first["seed"] != second["seed"]:
            _fail(f"fresh pair {start // 2} does not reuse the same seed")
        if {first["challenger_color"], second["challenger_color"]} != {"white", "black"}:
            _fail(f"fresh pair {start // 2} does not invert challenger colour")

    comparison = payload.get("comparison")
    if not isinstance(comparison, dict):
        _fail("comparison must be an object")
    if comparison.get("persistent_totals") != persistent["totals"]:
        _fail("comparison persistent_totals disagrees with persistent series")
    if comparison.get("fresh_totals") != fresh["totals"]:
        _fail("comparison fresh_totals disagrees with fresh series")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Arena lifecycle diagnostic evidence")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    validate_payload(payload)
    print("ARENA LIFECYCLE EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
