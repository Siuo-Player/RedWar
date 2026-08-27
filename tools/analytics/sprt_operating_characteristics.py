"""Synthetic operating-characteristic diagnostics for the isolated RedWar SPRT.

This module is deliberately diagnostic-only. It estimates empirical decision
rates under controlled synthetic Bernoulli/Elo data; it does not change SPRT
logic and cannot authorize engine promotion.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from math import isfinite
from typing import Any

from tools.analytics.sprt import SPRTConfig, evaluate_sequence, win_probability


@dataclass(frozen=True)
class OperatingCharacteristics:
    """Monte Carlo summary for one assumed true generating process."""

    true_elo_delta: float
    true_draw_rate: float
    trials: int
    max_games: int
    seed: int
    accept_h1: int
    reject_h1: int
    continue_at_max_games: int
    false_positive_rate: float | None
    false_negative_rate: float | None
    stopping_rate: float
    mean_games_to_decision: float | None
    mean_draws: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "true_elo_delta": self.true_elo_delta,
            "true_draw_rate": self.true_draw_rate,
            "trials": self.trials,
            "max_games": self.max_games,
            "seed": self.seed,
            "decisions": {
                "accept_h1": self.accept_h1,
                "reject_h1": self.reject_h1,
                "continue_at_max_games": self.continue_at_max_games,
            },
            "rates": {
                "false_positive_rate": self.false_positive_rate,
                "false_negative_rate": self.false_negative_rate,
                "stopping_rate": self.stopping_rate,
            },
            "mean_games_to_decision": self.mean_games_to_decision,
            "mean_draws_per_trial": self.mean_draws,
        }


def _validate_inputs(trials: int, max_games: int, seed: int) -> None:
    if not isinstance(trials, int) or isinstance(trials, bool) or trials <= 0:
        raise ValueError("trials must be a positive integer")
    if not isinstance(max_games, int) or isinstance(max_games, bool) or max_games <= 0:
        raise ValueError("max_games must be a positive integer")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")


def _sample_outcome(rng: random.Random, true_elo_delta: float, draw_rate: float) -> str:
    if rng.random() < draw_rate:
        return "draw"
    return "win" if rng.random() < win_probability(true_elo_delta) else "loss"


def simulate_operating_characteristics(
    config: SPRTConfig,
    *,
    true_elo_delta: float,
    trials: int = 2000,
    max_games: int = 1000,
    seed: int = 0,
    true_draw_rate: float | None = None,
) -> OperatingCharacteristics:
    """Estimate SPRT operating characteristics under a controlled generator.

    The null/alternative error-rate interpretation is only meaningful when
    ``true_elo_delta`` is the corresponding configured hypothesis. The
    simulation nevertheless records raw decision counts for any supplied truth.
    """
    if not isfinite(true_elo_delta):
        raise ValueError("true_elo_delta must be finite")
    _validate_inputs(trials, max_games, seed)
    if true_draw_rate is None:
        true_draw_rate = config.draw_rate
    if not 0.0 <= true_draw_rate < 1.0 or not isfinite(true_draw_rate):
        raise ValueError("true_draw_rate must be finite and in [0, 1)")

    rng = random.Random(seed)
    accept_h1 = reject_h1 = continue_at_max_games = 0
    decided_games: list[int] = []
    total_draws = 0

    for _ in range(trials):
        outcomes: list[str] = []
        draws = 0
        for _game in range(max_games):
            outcome = _sample_outcome(rng, true_elo_delta, true_draw_rate)
            outcomes.append(outcome)
            if outcome == "draw":
                draws += 1
            result = evaluate_sequence(outcomes, config)
            if result.decision != "continue":
                if result.decision == "accept_h1":
                    accept_h1 += 1
                else:
                    reject_h1 += 1
                decided_games.append(result.games)
                break
        else:
            continue_at_max_games += 1
        total_draws += draws

    stopping_rate = (accept_h1 + reject_h1) / trials
    mean_games = (sum(decided_games) / len(decided_games)) if decided_games else None
    false_positive_rate = accept_h1 / trials if true_elo_delta == config.elo0 else None
    false_negative_rate = reject_h1 / trials if true_elo_delta == config.elo1 else None

    return OperatingCharacteristics(
        true_elo_delta=true_elo_delta,
        true_draw_rate=true_draw_rate,
        trials=trials,
        max_games=max_games,
        seed=seed,
        accept_h1=accept_h1,
        reject_h1=reject_h1,
        continue_at_max_games=continue_at_max_games,
        false_positive_rate=false_positive_rate,
        false_negative_rate=false_negative_rate,
        stopping_rate=stopping_rate,
        mean_games_to_decision=mean_games,
        mean_draws=total_draws / trials,
    )


def run_standard_suite(
    config: SPRTConfig,
    *,
    trials: int = 2000,
    max_games: int = 1000,
    seed: int = 0,
    true_draw_rate: float | None = None,
) -> dict[str, Any]:
    """Run known-null and known-positive synthetic diagnostics."""
    draw_rate = config.draw_rate if true_draw_rate is None else true_draw_rate
    null = simulate_operating_characteristics(
        config,
        true_elo_delta=config.elo0,
        trials=trials,
        max_games=max_games,
        seed=seed,
        true_draw_rate=draw_rate,
    )
    positive = simulate_operating_characteristics(
        config,
        true_elo_delta=config.elo1,
        trials=trials,
        max_games=max_games,
        seed=seed + 1,
        true_draw_rate=draw_rate,
    )
    return {
        "schema_version": "redwar-sprt-operating-characteristics-v1",
        "config": {
            "elo0": config.elo0,
            "elo1": config.elo1,
            "alpha": config.alpha,
            "beta": config.beta,
            "draw_rate": config.draw_rate,
        },
        "null": null.to_dict(),
        "known_positive": positive.to_dict(),
        "interpretation": "synthetic_diagnostic_only; no_promotion_authority; repeated_condition_dependence_not_validated",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run synthetic RedWar SPRT operating-characteristic diagnostics")
    parser.add_argument("--elo0", type=float, default=0.0)
    parser.add_argument("--elo1", type=float, default=5.0)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--beta", type=float, default=0.05)
    parser.add_argument("--draw-rate", type=float, default=0.0)
    parser.add_argument("--trials", type=int, default=2000)
    parser.add_argument("--max-games", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    config = SPRTConfig(
        elo0=args.elo0,
        elo1=args.elo1,
        alpha=args.alpha,
        beta=args.beta,
        draw_rate=args.draw_rate,
    )
    result = run_standard_suite(
        config,
        trials=args.trials,
        max_games=args.max_games,
        seed=args.seed,
        true_draw_rate=args.draw_rate,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
