"""Audit derived manual telemetry against canonical replay evidence.

The audit is deliberately read-only and makes missingness explicit. It never
interprets a missing telemetry event as player rejection, and it never replaces
canonical replay semantics with telemetry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def _canonical_player_actions(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract the human player's actions from the canonical replay.

    Local replay metadata currently declares the human side. Actions alternate
    by ply, so the player's plies are every other action beginning at ply zero
    when the player starts. The function refuses to guess for unsupported replay
    metadata rather than silently manufacturing observations.
    """
    metadata = record.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("replay metadata is required")
    player_side = metadata.get("player_side")
    if player_side not in {"brancas", "pretas"}:
        raise ValueError("unsupported or missing replay player_side")

    moves = record.get("moves", [])
    if not isinstance(moves, list):
        raise ValueError("replay moves must be a list")
    start_index = 0 if player_side == "brancas" else 1
    actions: list[dict[str, Any]] = []
    for compact in moves[start_index::2]:
        if not isinstance(compact, list) or len(compact) != 7:
            raise ValueError("malformed compact replay action")
        action: dict[str, Any] = {
            "type": str(compact[0]),
            "start": [int(compact[1]), int(compact[2])],
            "end": [int(compact[3]), int(compact[4])],
        }
        if compact[5] is not None:
            action["spell_name"] = compact[5]
        if compact[6] is not None:
            action["spawn_name"] = compact[6]
        actions.append(action)
    return actions


def _normalize_action(action: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "type": str(action.get("type", "")).lower(),
        "start": list(action.get("start", [])),
        "end": list(action.get("end", [])),
    }
    if action.get("spell_name") is not None:
        normalized["spell_name"] = action["spell_name"]
    if action.get("spawn_name") is not None:
        normalized["spawn_name"] = action["spawn_name"]
    return normalized


def _load_telemetry(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    records: list[dict[str, Any]] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError("telemetry JSONL record must be an object")
        records.append(payload)
    return records


def audit_replay_telemetry(
    replay_records: Iterable[Mapping[str, Any]],
    telemetry_records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare canonical player actions with observed accepted telemetry.

    Matching is per game and in sequence order. Telemetry for a game that does
    not exist in the replay corpus is reported as extra/unattributed evidence.
    Missing telemetry is observable missingness only; it is not assigned a
    player-intent interpretation.
    """
    replay_by_game: dict[str, Mapping[str, Any]] = {}
    for record in replay_records:
        game_id = record.get("game_id")
        if not game_id:
            raise ValueError("replay record game_id is required")
        if game_id in replay_by_game:
            raise ValueError(f"duplicate replay game_id: {game_id}")
        replay_by_game[str(game_id)] = record

    selected_by_game: dict[str, list[Mapping[str, Any]]] = {}
    telemetry_game_ids: set[str] = set()
    malformed_without_game_id = 0
    for event in telemetry_records:
        event_type = event.get("event_type")
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue
        game_id = payload.get("game_id")
        if game_id is not None:
            telemetry_game_ids.add(str(game_id))
        if event_type == "action_selected":
            if game_id is None:
                malformed_without_game_id += 1
                continue
            action = payload.get("action")
            if not isinstance(action, Mapping):
                malformed_without_game_id += 1
                continue
            selected_by_game.setdefault(str(game_id), []).append(action)

    per_game: dict[str, dict[str, Any]] = {}
    total_expected = 0
    total_observed = 0
    total_matched = 0
    for game_id, replay in replay_by_game.items():
        expected = _canonical_player_actions(replay)
        observed = selected_by_game.get(game_id, [])
        total_expected += len(expected)
        total_observed += len(observed)

        matched = 0
        mismatched = 0
        for expected_action, observed_action in zip(expected, observed):
            if _normalize_action(expected_action) == _normalize_action(observed_action):
                matched += 1
            else:
                mismatched += 1
        missing = max(0, len(expected) - len(observed))
        extra = max(0, len(observed) - len(expected))
        total_matched += matched
        per_game[game_id] = {
            "expected_player_actions": len(expected),
            "observed_action_selected": len(observed),
            "matched": matched,
            "action_mismatch": mismatched,
            "missing_telemetry": missing,
            "extra_telemetry": extra,
            "telemetry_present": game_id in telemetry_game_ids,
            "missingness_interpretation": "observability_gap_not_player_intent",
        }

    extra_games = sorted(telemetry_game_ids.difference(replay_by_game))
    games_without_telemetry = sorted(
        game_id for game_id in replay_by_game if game_id not in telemetry_game_ids
    )
    coverage = (total_matched / total_expected) if total_expected else None
    return {
        "schema_version": "redwar-replay-telemetry-completeness-v1",
        "replay_games": len(replay_by_game),
        "telemetry_games": len(telemetry_game_ids),
        "games_without_telemetry": games_without_telemetry,
        "extra_unattributed_telemetry_games": extra_games,
        "malformed_action_selected_without_game_id": malformed_without_game_id,
        "expected_player_actions": total_expected,
        "observed_action_selected": total_observed,
        "matched_player_actions": total_matched,
        "missing_telemetry_actions": max(0, total_expected - total_observed),
        "action_mismatches": sum(item["action_mismatch"] for item in per_game.values()),
        "telemetry_coverage": coverage,
        "per_game": per_game,
        "status": "audit_only_no_intent_inference",
    }


def audit_files(replay_path: str | Path, telemetry_path: str | Path) -> dict[str, Any]:
    replay_payload = json.loads(Path(replay_path).read_text(encoding="utf-8"))
    if isinstance(replay_payload, dict) and "games" in replay_payload:
        replay_records = replay_payload["games"]
    else:
        replay_records = [replay_payload]
    if not isinstance(replay_records, list):
        raise ValueError("replay input must contain a game object or a games list")
    return audit_replay_telemetry(replay_records, _load_telemetry(telemetry_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit canonical replay against derived manual telemetry")
    parser.add_argument("replay")
    parser.add_argument("telemetry")
    args = parser.parse_args()
    print(json.dumps(audit_files(args.replay, args.telemetry), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
