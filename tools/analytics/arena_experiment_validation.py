"""Validation contract for raw Ares Arena experiment records.

The raw JSONL is the source of truth for strength analysis. This module verifies
that each game agrees with the experiment metadata, that paired games are
structurally valid, and that invalid observations cannot be mistaken for draws.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from tools.analytics.arena_pairs import GameOutcome, incomplete_pairs, validate_pair_structure


REQUIRED_GAME_FIELDS = {
    "game_index",
    "pair_id",
    "pair_member",
    "challenger_color",
    "baseline_color",
    "opening_index",
    "seed",
    "outcome",
    "valid",
    "termination_reason",
}

VALID_OUTCOMES = {"challenger", "baseline", "draw", "invalid"}
VALID_COLOURS = {"white", "black"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_experiment_records(games: Iterable[dict], metadata: dict) -> dict:
    """Validate raw Arena games against one experiment metadata contract.

    Invalid games are allowed as observations, but they remain outside strength
    inference. The function returns audit counts rather than changing the data.
    """

    records = list(games)
    _require(records, "experiment must contain at least one game record")

    expected_games = int(metadata["games"])
    _require(len(records) == expected_games, f"expected {expected_games} game records, got {len(records)}")

    required_metadata = {
        "challenger_version",
        "baseline_version",
        "rules_version",
        "node_budget",
        "games",
        "opening_count",
    }
    missing_metadata = required_metadata - metadata.keys()
    _require(not missing_metadata, f"experiment metadata missing fields: {sorted(missing_metadata)}")

    seen_indices: set[int] = set()
    outcomes: list[str] = []
    valid_records: list[dict] = []
    invalid_records: list[dict] = []
    game_outcomes: list[GameOutcome] = []

    for expected_index, game in enumerate(records):
        _require(isinstance(game, dict), f"game {expected_index}: expected object")
        missing = REQUIRED_GAME_FIELDS - game.keys()
        _require(not missing, f"game {expected_index}: missing fields {sorted(missing)}")

        index = int(game["game_index"])
        _require(index == expected_index, f"game index sequence broken: expected {expected_index}, got {index}")
        _require(index not in seen_indices, f"duplicate game_index: {index}")
        seen_indices.add(index)

        _require(game["challenger_color"] in VALID_COLOURS, f"game {index}: invalid challenger_color")
        _require(game["baseline_color"] in VALID_COLOURS, f"game {index}: invalid baseline_color")
        _require(game["baseline_color"] != game["challenger_color"], f"game {index}: both engines have the same colour")
        _require(game["outcome"] in VALID_OUTCOMES, f"game {index}: invalid outcome")
        _require(isinstance(game["valid"], bool), f"game {index}: valid must be boolean")
        _require(str(game["pair_id"]) == f"pair-{index // 2:06d}", f"game {index}: unexpected pair_id")
        _require(int(game["pair_member"]) == index % 2, f"game {index}: unexpected pair_member")
        _require(int(game["opening_index"]) < int(metadata["opening_count"]), f"game {index}: opening_index out of range")

        experiment = game.get("experiment")
        _require(isinstance(experiment, dict), f"game {index}: missing experiment metadata")
        for key in ("challenger_version", "baseline_version", "rules_version", "node_budget", "games", "opening_count"):
            _require(experiment.get(key) == metadata[key], f"game {index}: metadata mismatch for {key}")

        if game["valid"]:
            _require(game["outcome"] in {"challenger", "baseline", "draw"}, f"game {index}: valid game has invalid outcome")
            valid_records.append(game)
        else:
            _require(game["outcome"] == "invalid", f"game {index}: invalid observation must use outcome='invalid'")
            invalid_records.append(game)

        outcomes.append(str(game["outcome"]))

    validate_pair_structure([
        GameOutcome(
            game_index=int(game["game_index"]),
            pair_id=str(game["pair_id"]),
            opening_index=int(game["opening_index"]),
            challenger_color=str(game["challenger_color"]),
            outcome=str(game["outcome"]),
        )
        for game in records
        if game["valid"]
    ])

    valid_pairs = [game for game in valid_records]
    game_outcomes = [
        GameOutcome(
            game_index=int(game["game_index"]),
            pair_id=str(game["pair_id"]),
            opening_index=int(game["opening_index"]),
            challenger_color=str(game["challenger_color"]),
            outcome=str(game["outcome"]),
        )
        for game in valid_pairs
    ]

    return {
        "games": len(records),
        "valid_games": len(valid_records),
        "invalid_games": len(invalid_records),
        "outcomes": dict(Counter(outcomes)),
        "incomplete_valid_pair_ids": sorted(incomplete_pairs(game_outcomes)),
        "complete_valid_pairs": len(valid_pairs) // 2,
        "node_budget": int(metadata["node_budget"]),
        "challenger_version": str(metadata["challenger_version"]),
        "baseline_version": str(metadata["baseline_version"]),
        "rules_version": str(metadata["rules_version"]),
    }
