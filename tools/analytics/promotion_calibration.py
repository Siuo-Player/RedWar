"""Seeded calibration harness for the binary Ares promotion gate.

This module validates the decision procedure against known synthetic strengths.
It does not measure real Ares strength and must never be treated as Arena proof.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import isfinite
import random
from typing import Iterable

from tools.analytics.promotion_gate import evaluate_sequential_promotion
from tools.analytics.strength_statistics import PairedGame, PROMOTION_STAGES


@dataclass(frozen=True)
class CalibrationResult:
    """Aggregate outcome of one synthetic strength cell."""

    delta_elo: float
    experiments: int
    bootstrap_replicates: int
    accept_count: int
    reject_count: int
    continue_count: int
    accept_rate: float
    reject_rate: float
    mean_stopping_games: float
    stopping_games: tuple[tuple[int, int], ...]

    @property
    def false_accept_or_power(self) -> float:
        return self.accept_rate


def challenger_probability(delta_elo: float) -> float:
    """Convert a Bradley-Terry Elo-equivalent difference into win probability."""
    return 1.0 / (1.0 + 10.0 ** (-delta_elo / 400.0))


def simulate_paired_games(delta_elo: float, *, pairs: int = 256, seed: int = 0) -> list[PairedGame]:
    """Generate binary WIN/LOSS games with colour inversion per opening pair."""
    if pairs <= 0:
        raise ValueError("pairs must be positive")
    rng = random.Random(seed)
    probability = challenger_probability(delta_elo)
    games: list[PairedGame] = []
    for pair_index in range(pairs):
        pair_id = f"calibration-{pair_index:03d}"
        opening_seed = 1_000_000 + pair_index
        for member, colour in enumerate(("white", "black")):
            outcome = "challenger" if rng.random() < probability else "baseline"
            games.append(
                PairedGame(
                    pair_id=pair_id,
                    opening_seed=opening_seed,
                    challenger_colour=colour,
                    outcome=outcome,
                    game_index=pair_index * 2 + member,
                )
            )
    return games


def run_calibration(
    delta_elo: float,
    *,
    experiments: int = 100,
    pairs: int = 256,
    bootstrap_replicates: int = 250,
    seed: int = 0,
) -> CalibrationResult:
    """Run deterministic seeded experiments and summarize sequential decisions."""
    if experiments <= 0:
        raise ValueError("experiments must be positive")
    if pairs < PROMOTION_STAGES[-1] // 2:
        raise ValueError(f"pairs must cover MAX_GAMES={PROMOTION_STAGES[-1]}")
    if bootstrap_replicates < 20:
        raise ValueError("bootstrap_replicates must be at least 20 for calibration")

    decisions = []
    for experiment_index in range(experiments):
        games = simulate_paired_games(
            delta_elo,
            pairs=pairs,
            seed=seed + experiment_index,
        )
        decisions.append(
            evaluate_sequential_promotion(
                games,
                bootstrap_replicates=bootstrap_replicates,
                bootstrap_seed=seed + experiment_index,
            )
        )

    counts = Counter(decision.decision for decision in decisions)
    stopping_counts = Counter(
        decision.games
        for decision in decisions
        if decision.decision in {"accept", "reject"}
    )
    terminal = [
        decision.games
        for decision in decisions
        if decision.decision in {"accept", "reject"}
    ]

    return CalibrationResult(
        delta_elo=delta_elo,
        experiments=experiments,
        bootstrap_replicates=bootstrap_replicates,
        accept_count=counts["accept"],
        reject_count=counts["reject"],
        continue_count=counts["continue"],
        accept_rate=counts["accept"] / experiments,
        reject_rate=counts["reject"] / experiments,
        mean_stopping_games=sum(terminal) / len(terminal) if terminal else float("nan"),
        stopping_games=tuple(sorted(stopping_counts.items())),
    )


def run_calibration_grid(
    deltas_elo: Iterable[float] = (-200.0, -100.0, 0.0, 50.0, 100.0, 200.0),
    *,
    experiments: int = 100,
    pairs: int = 256,
    bootstrap_replicates: int = 250,
    seed: int = 0,
) -> tuple[CalibrationResult, ...]:
    """Evaluate a fixed synthetic strength grid suitable for a holdout report."""
    return tuple(
        run_calibration(
            delta,
            experiments=experiments,
            pairs=pairs,
            bootstrap_replicates=bootstrap_replicates,
            seed=seed + index * 100_000,
        )
        for index, delta in enumerate(deltas_elo)
    )


def result_to_dict(result: CalibrationResult) -> dict[str, object]:
    """Serialize a calibration result without exposing non-finite JSON numbers."""
    mean_stopping_games: float | None = result.mean_stopping_games if isfinite(result.mean_stopping_games) else None
    return {
        "delta_elo": result.delta_elo,
        "experiments": result.experiments,
        "bootstrap_replicates": result.bootstrap_replicates,
        "accept_count": result.accept_count,
        "reject_count": result.reject_count,
        "continue_count": result.continue_count,
        "accept_rate": result.accept_rate,
        "reject_rate": result.reject_rate,
        "mean_stopping_games": mean_stopping_games,
        "stopping_games": {str(stage): count for stage, count in result.stopping_games},
    }
