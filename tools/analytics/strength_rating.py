"""General-purpose strength estimation from paired game results.

This module is intentionally independent from Ares search/evaluation. It provides
an interpretable Elo-compatible baseline that can later be replaced/extended by a
Bradley–Terry or Bayesian estimator without changing Arena game storage.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Iterable, Literal

Outcome = Literal["win", "draw", "loss"]


@dataclass(frozen=True)
class MatchResult:
    """One paired comparison from the experiment log."""

    left: str
    right: str
    outcome: Outcome


@dataclass(frozen=True)
class Rating:
    """Rating estimate plus a conservative uncertainty proxy."""

    value: float = 1500.0
    games: int = 0
    variance: float = 350.0**2

    @property
    def uncertainty(self) -> float:
        return sqrt(max(self.variance, 0.0))


@dataclass(frozen=True)
class StrengthEstimate:
    """Relative strength estimate between two systems.

    The current estimator exposes an engineering uncertainty proxy. Its derived
    interval is not a calibrated statistical confidence interval.
    """

    left: Rating
    right: Rating

    @property
    def delta(self) -> float:
        return self.left.value - self.right.value

    @property
    def delta_uncertainty(self) -> float:
        return sqrt(self.left.variance + self.right.variance)

    @property
    def interval_type(self) -> str:
        """Stable machine-readable label for the current interval semantics."""
        return "engineering_uncertainty_proxy_v1"

    @property
    def lower_95(self) -> float:
        """Legacy-compatible lower bound of the current 95% uncertainty proxy."""
        return self.delta - 1.96 * self.delta_uncertainty

    @property
    def upper_95(self) -> float:
        """Legacy-compatible upper bound of the current 95% uncertainty proxy."""
        return self.delta + 1.96 * self.delta_uncertainty


def expected_score(left: float, right: float) -> float:
    """Expected score for left under the standard Elo logistic model."""

    return 1.0 / (1.0 + 10.0 ** ((right - left) / 400.0))


def update_pair(left: Rating, right: Rating, outcome: Outcome, k: float = 20.0) -> tuple[Rating, Rating]:
    """Apply one Elo-compatible paired result.

    The variance update is deliberately conservative: each observed game reduces
    uncertainty, but never below a small floor. This is an engineering baseline,
    not yet the final Bayesian/Bradley–Terry estimator.
    """

    if k <= 0:
        raise ValueError("k must be positive")

    score = {"win": 1.0, "draw": 0.5, "loss": 0.0}[outcome]
    expected = expected_score(left.value, right.value)
    delta = k * (score - expected)

    floor = 20.0**2
    left_games = left.games + 1
    right_games = right.games + 1
    left_variance = max(floor, left.variance * 0.995)
    right_variance = max(floor, right.variance * 0.995)

    return (
        Rating(left.value + delta, left_games, left_variance),
        Rating(right.value - delta, right_games, right_variance),
    )


def estimate(initial: dict[str, Rating], results: Iterable[MatchResult], k: float = 20.0) -> dict[str, Rating]:
    """Estimate ratings by replaying results in deterministic order."""

    ratings = dict(initial)
    for result in results:
        if result.left not in ratings or result.right not in ratings:
            raise KeyError("all match participants must have an initial rating")
        ratings[result.left], ratings[result.right] = update_pair(
            ratings[result.left], ratings[result.right], result.outcome, k=k
        )
    return ratings


def compare(left: Rating, right: Rating) -> StrengthEstimate:
    """Build a relative-strength estimate with the current uncertainty proxy."""

    return StrengthEstimate(left=left, right=right)
