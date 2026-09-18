"""Controlled selection experiment for the 1.0-Lite Ares Balance Baseline.

This experiment measures execution reliability and reproducibility only.  It
must not be interpreted as a strength comparison or as balance evidence.
Each candidate plays against itself from the same deterministic opening
conditions, with colours inverted between paired games.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ai.bot import CppEngineBot
from tools.analytics.arena_tournament import run_headless_match
from tools.analytics.opening_book import OPENING_SEEDS

CANDIDATE_PROFILES: dict[str, int] = {
    "StockWar-Iniciante": 100_000,
    "StockWar-Intermedio": 500_000,
    "StockWar-Avancado": 1_000_000,
}

DEFAULT_PAIRS = 8
DEFAULT_REPLAY_CHECKS = 1
DEFAULT_OPENING_COUNT = 16


def candidate_profiles() -> dict[str, int]:
    return dict(CANDIDATE_PROFILES)


def fixed_opening_seeds(count: int = DEFAULT_OPENING_COUNT) -> tuple[int, ...]:
    if count <= 0:
        raise ValueError("opening count must be positive")
    if count > len(OPENING_SEEDS):
        raise ValueError(f"opening count cannot exceed {len(OPENING_SEEDS)}")
    seeds = tuple(int(seed) for seed in OPENING_SEEDS[:count])
    if len(set(seeds)) != len(seeds):
        raise RuntimeError("canonical opening seeds must be unique")
    return seeds


def action_digest(game: dict[str, Any]) -> str:
    payload = {
        "seed": game.get("seed"),
        "initial_rwen": game.get("initial_rwen"),
        "final_rwen": game.get("final_rwen"),
        "plies": game.get("plies"),
        "actions": game.get("actions", []),
        "winner": game.get("winner"),
        "termination_reason": game.get("termination_reason"),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_candidate_game(candidate: str, nodes: int, seed: int, opening_index: int, candidate_color: str) -> dict[str, Any]:
    start = time.perf_counter()
    candidate_white = CppEngineBot(nodes=nodes)
    candidate_black = CppEngineBot(nodes=nodes)
    try:
        if candidate_color == "white":
            game = run_headless_match(candidate_white, candidate_black, opening_index, seed)
        elif candidate_color == "black":
            game = run_headless_match(candidate_black, candidate_white, opening_index, seed)
        else:
            raise ValueError("candidate_color must be white or black")
    finally:
        candidate_white.__del__()
        candidate_black.__del__()

    elapsed = time.perf_counter() - start
    return {
        "candidate": candidate,
        "nodes": nodes,
        "seed": seed,
        "opening_index": opening_index,
        "candidate_color": candidate_color,
        "elapsed_seconds": round(elapsed, 6),
        "valid": bool(game.get("valid")),
        "winner": game.get("winner"),
        "plies": game.get("plies"),
        "termination_reason": game.get("termination_reason"),
        "failure_reason": game.get("failure_reason"),
        "failure_exception_type": game.get("failure_exception_type"),
        "failure_detail": game.get("failure_detail"),
        "action_digest": action_digest(game),
        "initial_rwen": game.get("initial_rwen"),
        "final_rwen": game.get("final_rwen"),
    }


def build_metadata(source_sha: str, rules_version: str, pairs: int, seeds: tuple[int, ...]) -> dict[str, Any]:
    return {
        "experiment_id": "redwar-lite-ares-baseline-selection-v1",
        "purpose": "instrument-reliability-and-reproducibility-only",
        "decision_role": "select-one-reproducible-lite-balance-agent",
        "strength_claim_allowed": False,
        "balance_claim_allowed": False,
        "source_sha": source_sha,
        "rules_version": rules_version,
        "candidate_profiles": CANDIDATE_PROFILES,
        "pair_count_per_candidate": pairs,
        "opening_count": len(seeds),
        "opening_seeds": list(seeds),
        "opening_policy": "canonical-opening-book-v1",
        "colour_policy": "candidate-white-then-black-per-pair",
        "pairing_policy": "same-candidate-self-play-with-colour-inversion",
        "process_policy": "fresh-candidate-processes-per-game",
        "termination_policy": "game_over_or_arena_max_plies",
        "invalid_policy": "record-invalid-and-do-not-convert-to-draw",
        "hero_population_policy": "canonical-opening-book-6-random-sampled-catalogue-heroes-per-side",
        "intervention_policy": "no-hero-or-economy-changes",
    }


def run_experiment(
    *,
    source_sha: str,
    rules_version: str,
    pairs: int = DEFAULT_PAIRS,
    opening_count: int = DEFAULT_OPENING_COUNT,
    replay_checks: int = DEFAULT_REPLAY_CHECKS,
) -> dict[str, Any]:
    if pairs <= 0:
        raise ValueError("pairs must be positive")
    if replay_checks < 0:
        raise ValueError("replay_checks must be non-negative")

    seeds = fixed_opening_seeds(opening_count)
    metadata = build_metadata(source_sha, rules_version, pairs, seeds)
    games: list[dict[str, Any]] = []

    for candidate, nodes in CANDIDATE_PROFILES.items():
        for pair_index in range(pairs):
            seed = seeds[pair_index % len(seeds)]
            opening_index = pair_index % len(seeds)
            for member, colour in enumerate(("white", "black")):
                record = run_candidate_game(candidate, nodes, seed, opening_index, colour)
                record.update(
                    {
                        "game_index": len(games),
                        "pair_id": f"{candidate}-pair-{pair_index:04d}",
                        "pair_member": member,
                    }
                )
                games.append(record)

        for check_index in range(replay_checks):
            seed = seeds[check_index % len(seeds)]
            opening_index = check_index % len(seeds)
            first = run_candidate_game(candidate, nodes, seed, opening_index, "white")
            second = run_candidate_game(candidate, nodes, seed, opening_index, "white")
            games.append(
                {
                    "game_index": len(games),
                    "pair_id": f"{candidate}-replay-check-{check_index:04d}",
                    "pair_member": 0,
                    "candidate": candidate,
                    "nodes": nodes,
                    "seed": seed,
                    "opening_index": opening_index,
                    "candidate_color": "white",
                    "replay_check": True,
                    "first_digest": first["action_digest"],
                    "second_digest": second["action_digest"],
                    "deterministic_match": first["action_digest"] == second["action_digest"],
                    "first": first,
                    "second": second,
                }
            )

    return {"metadata": metadata, "games": games}


def summarize(result: dict[str, Any]) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for candidate in CANDIDATE_PROFILES:
        candidate_games = [
            game for game in result["games"]
            if game.get("candidate") == candidate and not game.get("replay_check")
        ]
        termination: dict[str, int] = {}
        for game in candidate_games:
            reason = str(game.get("termination_reason"))
            termination[reason] = termination.get(reason, 0) + 1
        replay_checks = [
            game for game in result["games"]
            if game.get("candidate") == candidate and game.get("replay_check")
        ]
        summaries[candidate] = {
            "nodes": CANDIDATE_PROFILES[candidate],
            "games": len(candidate_games),
            "valid_games": sum(bool(game.get("valid")) for game in candidate_games),
            "invalid_games": sum(not bool(game.get("valid")) for game in candidate_games),
            "termination_reasons": termination,
            "replay_checks": len(replay_checks),
            "replay_checks_deterministic": all(bool(game.get("deterministic_match")) for game in replay_checks),
            "total_elapsed_seconds": round(sum(float(game.get("elapsed_seconds", 0.0)) for game in candidate_games), 6),
            "max_game_elapsed_seconds": round(max((float(game.get("elapsed_seconds", 0.0)) for game in candidate_games), default=0.0), 6),
        }
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled 1.0-Lite Ares baseline selection experiment")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--rules-version", required=True)
    parser.add_argument("--pairs", type=int, default=DEFAULT_PAIRS)
    parser.add_argument("--opening-count", type=int, default=DEFAULT_OPENING_COUNT)
    parser.add_argument("--replay-checks", type=int, default=DEFAULT_REPLAY_CHECKS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run_experiment(
        source_sha=args.source_sha,
        rules_version=args.rules_version,
        pairs=args.pairs,
        opening_count=args.opening_count,
        replay_checks=args.replay_checks,
    )
    result["summary"] = summarize(result)
    result["decision_policy"] = {
        "select_on": ["no_unresolved_invalid_or_hang_conditions", "reproducible_action_traces", "complete_provenance"],
        "do_not_select_on": ["hero_win_rate", "aggregate_strength", "auto_pricer", "competitive_arena_rating"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
