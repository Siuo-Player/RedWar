"""Controlled 1.0-Lite Balance Lab development campaign.

This runner collects development-only self-play evidence under the frozen
StockWar-Iniciante / 100,000-node Ares baseline. It deliberately reserves a
separate deterministic seed bank for future protected hold-out validation and
does not expose that hold-out set through the development command.

No balance, rules, or Ares-policy changes are performed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import CppEngineBot
from engine.game_state import GameState
from engine.setup import validate_complete_pre_match_setup
from tools.analytics.arena_tournament import ARENA_MAX_PLIES, run_headless_match
from tools.analytics.opening_book import gerar_abertura


BASELINE_POLICY = "StockWar-Iniciante"
BASELINE_NODES = 100_000
CAMPAIGN_ID = "redwar-lite-balance-development-v1"
CAMPAIGN_SPLIT = "development"
OPENING_BANK_ID = "lite-balance-development-bank-v1"
OPENING_BANK_COUNT = 96
TOTAL_GAMES = OPENING_BANK_COUNT
MAX_OPENING_RESOLUTION_ATTEMPTS = 10_000

# Requested condition identifiers are disjoint between development and future
# protected hold-out. Each requested seed is resolved to the first deterministic
# seed whose generated opening satisfies the canonical pre-match setup contract
# and has a unique initial RWEN.
_DEVELOPMENT_REQUESTED_SEEDS = tuple(10_000 + 7 * index for index in range(96))
_HOLDOUT_REQUESTED_SEEDS = tuple(20_000_000 + 7 * index for index in range(96))


@lru_cache(maxsize=1)
def development_opening_conditions() -> tuple[dict[str, Any], ...]:
    used_position_hashes: set[str] = set()
    used_resolved_seeds: set[int] = set()
    conditions: list[dict[str, Any]] = []

    for opening_index, requested_seed in enumerate(_DEVELOPMENT_REQUESTED_SEEDS):
        resolved = None
        for attempt in range(MAX_OPENING_RESOLUTION_ATTEMPTS):
            candidate_seed = requested_seed + attempt
            if candidate_seed in used_resolved_seeds:
                continue

            board = gerar_abertura(candidate_seed)
            try:
                draft_costs = validate_complete_pre_match_setup(board)
            except ValueError:
                continue

            state = GameState()
            state.board = board
            initial_rwen = state.to_rwen()
            position_sha256 = _sha256_text(initial_rwen)
            if position_sha256 in used_position_hashes:
                continue

            resolved = {
                "opening_index": opening_index,
                "requested_seed": requested_seed,
                "resolved_seed": candidate_seed,
                "resolution_attempt": attempt,
                "initial_rwen": initial_rwen,
                "position_sha256": position_sha256,
                "white_draft_cost": int(draft_costs["brancas"]),
                "black_draft_cost": int(draft_costs["pretas"]),
            }
            break

        if resolved is None:
            raise RuntimeError(
                f"Unable to resolve legal unique opening for requested seed {requested_seed} "
                f"after {MAX_OPENING_RESOLUTION_ATTEMPTS} attempts"
            )

        used_resolved_seeds.add(int(resolved["resolved_seed"]))
        used_position_hashes.add(str(resolved["position_sha256"]))
        conditions.append(resolved)

    return tuple(conditions)


def development_opening_request_seeds() -> tuple[int, ...]:
    return _DEVELOPMENT_REQUESTED_SEEDS


def development_opening_seeds() -> tuple[int, ...]:
    return tuple(int(item["resolved_seed"]) for item in development_opening_conditions())


def protected_holdout_seeds() -> tuple[int, ...]:
    return _HOLDOUT_REQUESTED_SEEDS


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _winner_side(winner: object) -> str | None:
    text = str(winner)
    if "Brancas" in text:
        return "white"
    if "Pretas" in text:
        return "black"
    return None


def build_campaign_metadata(
    *,
    source_sha: str,
    rules_version: str,
    engine_sha256: str,
    compiler_identity: str,
    hero_config_sha256: str,
) -> dict[str, Any]:
    conditions = development_opening_conditions()
    seeds = tuple(int(item["resolved_seed"]) for item in conditions)
    return {
        "campaign_id": CAMPAIGN_ID,
        "campaign_split": CAMPAIGN_SPLIT,
        "purpose": "controlled-development-balance-evidence",
        "strength_claim_allowed": False,
        "global_balance_claim_allowed": False,
        "baseline_policy": BASELINE_POLICY,
        "node_budget": BASELINE_NODES,
        "source_sha": source_sha,
        "rules_version": rules_version,
        "engine_sha256": engine_sha256,
        "compiler_identity": compiler_identity,
        "hero_config_sha256": hero_config_sha256,
        "opening_bank_id": OPENING_BANK_ID,
        "opening_bank_size": len(conditions),
        "opening_request_seeds": list(development_opening_request_seeds()),
        "opening_seeds": list(seeds),
        "opening_conditions": list(conditions),
        "holdout_request_seeds": list(protected_holdout_seeds()),
        "opening_seed_generation": "development request=10000 + 7 * index; holdout request=20000000 + 7 * index; resolved=request + attempt, first legal unique condition",
        "opening_resolution_max_attempts": MAX_OPENING_RESOLUTION_ATTEMPTS,
        "condition_independence_policy": "one unique deterministic legal opening condition per development game; no repeated pseudo-replicates",
        "pre_match_setup_policy": "canonical validate_complete_pre_match_setup with 200-point team budgets",
        "colour_policy": "record both white and black sides; first-player is fixed by the current engine contract",
        "pairing_policy": "no duplicate relabelled self-play runs",
        "initiative_policy": "white_to_move",
        "process_policy": "fresh white and black candidate processes per game",
        "termination_policy": f"game_over_or_{ARENA_MAX_PLIES}_plies",
        "validity_policy": "valid_only_when_authoritative_game_over_has_declared_winner",
        "raw_evidence_policy": "persist raw game records before derived summaries",
        "context_policy": (
            "retain initial/final RWEN, seed, opening identity, white/black winner side, "
            "terminal reason and action trace"
        ),
        "holdout_policy": "protected seed set reserved outside this runner",
    }


def opening_condition_id(index: int) -> str:
    if not 0 <= index < OPENING_BANK_COUNT:
        raise ValueError(f"opening index outside development bank: {index}")
    return f"{OPENING_BANK_ID}:{index:02d}"


def _record_game(
    *,
    opening_index: int,
    seed: int,
    game: dict[str, Any],
    elapsed_seconds: float,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "campaign_id": CAMPAIGN_ID,
        "campaign_split": CAMPAIGN_SPLIT,
        "opening_condition_id": opening_condition_id(opening_index),
        "opening_index": opening_index,
        "seed": seed,
        "baseline_policy": BASELINE_POLICY,
        "node_budget": BASELINE_NODES,
        "source_sha": metadata["source_sha"],
        "rules_version": metadata["rules_version"],
        "engine_sha256": metadata["engine_sha256"],
        "compiler_identity": metadata["compiler_identity"],
        "hero_config_sha256": metadata["hero_config_sha256"],
        "requested_seed": metadata["opening_conditions"][opening_index]["requested_seed"],
        "seed_resolution_attempt": metadata["opening_conditions"][opening_index]["resolution_attempt"],
        "initial_position_sha256": metadata["opening_conditions"][opening_index]["position_sha256"],
        "white_draft_cost": metadata["opening_conditions"][opening_index]["white_draft_cost"],
        "black_draft_cost": metadata["opening_conditions"][opening_index]["black_draft_cost"],
        "pre_match_setup_validated": True,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "winner_side": _winner_side(game.get("winner")),
        "valid": bool(game.get("valid")),
        "termination_reason": game.get("termination_reason"),
        "failure_reason": game.get("failure_reason"),
        "failure_exception_type": game.get("failure_exception_type"),
        "failure_detail": game.get("failure_detail"),
        "plies": game.get("plies"),
        "initial_rwen": game.get("initial_rwen"),
        "final_rwen": game.get("final_rwen"),
        "actions": game.get("actions", []),
        "action_counts": game.get("action_counts", {}),
    }


def _run_one_game(
    *,
    opening_index: int,
    seed: int,
    engine_path: str,
) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    white_bot = CppEngineBot(nodes=BASELINE_NODES, executable_path=engine_path)
    black_bot = CppEngineBot(nodes=BASELINE_NODES, executable_path=engine_path)
    try:
        game = run_headless_match(
            white_bot,
            black_bot,
            opening_index=opening_index,
            opening_seed=seed,
        )
    finally:
        white_bot.__del__()
        black_bot.__del__()

    return game, time.perf_counter() - started


def run_campaign(
    *,
    source_sha: str,
    rules_version: str,
    engine_sha256: str,
    compiler_identity: str,
    hero_config_sha256: str,
    engine_path: str,
) -> dict[str, Any]:
    metadata = build_campaign_metadata(
        source_sha=source_sha,
        rules_version=rules_version,
        engine_sha256=engine_sha256,
        compiler_identity=compiler_identity,
        hero_config_sha256=hero_config_sha256,
    )
    games: list[dict[str, Any]] = []
    conditions = development_opening_conditions()

    for opening_index, condition in enumerate(conditions):
        seed = int(condition["resolved_seed"])
        game, elapsed = _run_one_game(
            opening_index=opening_index,
            seed=seed,
            engine_path=engine_path,
        )
        games.append(
            _record_game(
                opening_index=opening_index,
                seed=seed,
                game=game,
                elapsed_seconds=elapsed,
                metadata=metadata,
            )
        )

    valid_games = [game for game in games if game["valid"]]
    invalid_games = [game for game in games if not game["valid"]]
    summary = {
        "games": len(games),
        "expected_games": TOTAL_GAMES,
        "valid_games": len(valid_games),
        "invalid_games": len(invalid_games),
        "termination_reasons": _count_values(games, "termination_reason"),
        "winner_sides": _count_values(valid_games, "winner_side"),
        "initiative_policy": "white_to_move",
        "opening_conditions": len({game["opening_condition_id"] for game in games}),
        "selection_or_strength_claim_allowed": False,
    }
    return {
        "metadata": metadata,
        "summary": summary,
        "games": games,
    }


def _count_values(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def write_campaign(result: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen 1.0-Lite development Balance Lab campaign."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--rules-version", required=True)
    parser.add_argument("--engine-sha256", required=True)
    parser.add_argument("--compiler-identity", required=True)
    parser.add_argument("--hero-config-sha256", required=True)
    parser.add_argument("--engine-path", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run_campaign(
        source_sha=args.source_sha,
        rules_version=args.rules_version,
        engine_sha256=args.engine_sha256,
        compiler_identity=args.compiler_identity,
        hero_config_sha256=args.hero_config_sha256,
        engine_path=args.engine_path,
    )
    write_campaign(result, args.output)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0 if result["summary"]["invalid_games"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
