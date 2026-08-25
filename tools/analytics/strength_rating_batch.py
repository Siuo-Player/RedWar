"""Order-invariant paired-game strength estimator for the Ares Arena."""
from __future__ import annotations

from dataclasses import dataclass
from math import log10, sqrt
from typing import Iterable, Literal

Outcome = Literal["win", "draw", "loss"]

@dataclass(frozen=True)
class MatchResult:
    left: str
    right: str
    outcome: Outcome

@dataclass(frozen=True)
class BatchMatchupEstimate:
    games: int
    wins: int
    draws: int
    losses: int
    score_rate: float
    elo_delta: float
    score_rate_lower_95: float
    score_rate_upper_95: float

    @property
    def elo_delta_lower_95(self) -> float:
        return score_to_elo(self.score_rate_lower_95)

    @property
    def elo_delta_upper_95(self) -> float:
        return score_to_elo(self.score_rate_upper_95)

def score_to_elo(score_rate: float) -> float:
    """Convert a score rate to an Elo-equivalent relative delta."""
    eps = 1e-9
    p = min(max(score_rate, eps), 1.0 - eps)
    return 400.0 * log10(p / (1.0 - p))

def _wilson_interval(successes: float, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    p = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (p + z * z / (2.0 * trials)) / denominator
    margin = z * sqrt((p * (1.0 - p) / trials) + (z * z / (4.0 * trials * trials))) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)

def estimate_batch(results: Iterable[MatchResult], *, left: str, right: str) -> BatchMatchupEstimate:
    """Estimate one A/B matchup from the complete sample, independent of order.

    Draws contribute half a point. This is a descriptive Elo-equivalent effect
    size; sequential promotion decisions remain the responsibility of SPRT.
    """
    wins = draws = losses = 0
    for result in results:
        if {result.left, result.right} != {left, right}:
            raise ValueError("all results must compare the requested pair")
        outcome = result.outcome if result.left == left else {"win": "loss", "loss": "win", "draw": "draw"}[result.outcome]
        if outcome == "win":
            wins += 1
        elif outcome == "draw":
            draws += 1
        else:
            losses += 1

    games = wins + draws + losses
    if games == 0:
        raise ValueError("at least one matchup result is required")

    score = wins + 0.5 * draws
    score_rate = score / games
    lower, upper = _wilson_interval(score, games)
    return BatchMatchupEstimate(
        games=games,
        wins=wins,
        draws=draws,
        losses=losses,
        score_rate=score_rate,
        elo_delta=score_to_elo(score_rate),
        score_rate_lower_95=lower,
        score_rate_upper_95=upper,
    )
