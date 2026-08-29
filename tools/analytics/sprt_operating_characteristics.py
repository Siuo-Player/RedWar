"""Deterministic Monte Carlo operating-characteristics diagnostics for SPRT.

This module evaluates the existing SPRT decision layer under synthetic outcomes
whose true Elo delta and draw rate are known by construction. It does not alter
SPRT boundaries or make promotion decisions.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict
from statistics import mean
from typing import Any

from tools.analytics.sprt import SPRTConfig, evaluate_sequence, win_probability


def simulate_outcomes(
    *,
    true_elo_delta: float,
    draw_rate: float,
    trials: int,
    seed: int,
    max_games: int,
) -> list[dict[str, Any]]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if max_games <= 0:
        raise ValueError("max_games must be positive")
    if not 0.0 <= draw_rate < 1.0:
        raise ValueError("draw_rate must be in [0, 1)")

    rng = random.Random(seed)
    results: list[dict[str, Any]] = []
    decisive_win_probability = win_probability(true_elo_delta)
    for _ in range(trials):
        sequence: list[str] = []
        for _ in range(max_games):
            draw = rng.random() < draw_rate
            if draw:
                sequence.append("draw")
            else:
                sequence.append("win" if rng.random() < decisive_win_probability else "loss")
        results.append(asdict(evaluate_sequence(sequence, SPRTConfig(draw_rate=draw_rate))))
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        raise ValueError("results cannot be empty")
    trials = len(results)
    accepts = sum(item["decision"] == "accept_h1" for item in results)
    rejects = sum(item["decision"] == "reject_h1" for item in results)
    continues = sum(item["decision"] == "continue" for item in results)
    games = [int(item["games"]) for item in results]
    sorted_games = sorted(games)
    p95_index = min(len(sorted_games) - 1, max(0, int(0.95 * len(sorted_games)) - 1))
    return {
        "trials": trials,
        "accept_h1_rate": accepts / trials,
        "reject_h1_rate": rejects / trials,
        "inconclusive_rate": continues / trials,
        "mean_games_to_decision": mean(games),
        "p95_games_to_decision": sorted_games[p95_index],
    }


def calibrate_operating_characteristics(
    *,
    true_elo_delta: float,
    draw_rate: float,
    trials: int = 2000,
    seed: int = 0,
    max_games: int = 2000,
) -> dict[str, Any]:
    results = simulate_outcomes(
        true_elo_delta=true_elo_delta,
        draw_rate=draw_rate,
        trials=trials,
        seed=seed,
        max_games=max_games,
    )
    return {
        "schema_version": "redwar-sprt-operating-characteristics-v1",
        "true_elo_delta": true_elo_delta,
        "draw_rate": draw_rate,
        "seed": seed,
        "max_games": max_games,
        "sprt_config": asdict(SPRTConfig(draw_rate=draw_rate)),
        "summary": summarize(results),
        "interpretation": "synthetic_operating_characteristic_only",
        "promotion_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate RedWar SPRT operating characteristics")
    parser.add_argument("--true-elo-delta", type=float, required=True)
    parser.add_argument("--draw-rate", type=float, required=True)
    parser.add_argument("--trials", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-games", type=int, default=2000)
    args = parser.parse_args()
    print(json.dumps(calibrate_operating_characteristics(**vars(args)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
