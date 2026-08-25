"""Sequential Probability Ratio Test (SPRT) utilities for A/B engine tests.

This module intentionally remains independent of the Ares search and the Arena
promotion gate. It implements the statistical decision layer only.

Model:
- wins/losses follow a Bernoulli comparison implied by Elo hypotheses;
- draws use a fixed draw-rate nuisance parameter shared by H0/H1;
- therefore draws contribute evidence of neither hypothesis under this model.

This is a conservative first implementation, not a claim of full Fishtest
compatibility. In particular, production calibration of draw-rate, paired
colour/book effects, sequential dependency assumptions, and multi-test control
must be validated before using it as an automatic promotion gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log
from typing import Iterable, Literal

Outcome = Literal["win", "loss", "draw"]
Decision = Literal["accept_h1", "reject_h1", "continue"]

ELO_SCALE = 400.0


@dataclass(frozen=True)
class SPRTConfig:
    """Configuration for a two-sided sequential comparison."""

    elo0: float = 0.0
    elo1: float = 5.0
    alpha: float = 0.05
    beta: float = 0.05
    draw_rate: float = 0.0

    def __post_init__(self) -> None:
        if not all(isfinite(x) for x in (self.elo0, self.elo1, self.alpha, self.beta, self.draw_rate)):
            raise ValueError("SPRT parameters must be finite")
        if self.elo0 == self.elo1:
            raise ValueError("elo0 and elo1 must differ")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        if not 0.0 < self.beta < 1.0:
            raise ValueError("beta must be in (0, 1)")
        if not 0.0 <= self.draw_rate < 1.0:
            raise ValueError("draw_rate must be in [0, 1)")

    @property
    def lower(self) -> float:
        return log(self.beta / (1.0 - self.alpha))

    @property
    def upper(self) -> float:
        return log((1.0 - self.beta) / self.alpha)


@dataclass(frozen=True)
class SPRTResult:
    decision: Decision
    llr: float
    games: int
    wins: int
    losses: int
    draws: int
    lower_boundary: float
    upper_boundary: float


def win_probability(elo_delta: float) -> float:
    """Return the logistic win probability for an Elo delta."""

    return 1.0 / (1.0 + 10.0 ** (-elo_delta / ELO_SCALE))


def _outcome_probability(outcome: Outcome, elo_delta: float, draw_rate: float) -> float:
    decisive = 1.0 - draw_rate
    win_p = decisive * win_probability(elo_delta)
    if outcome == "win":
        return win_p
    if outcome == "loss":
        return decisive - win_p
    if outcome == "draw":
        return draw_rate
    raise ValueError(f"unknown outcome: {outcome!r}")


def log_likelihood_ratio(outcome: Outcome, config: SPRTConfig) -> float:
    """Return log P(outcome|H1) / P(outcome|H0)."""

    p1 = _outcome_probability(outcome, config.elo1, config.draw_rate)
    p0 = _outcome_probability(outcome, config.elo0, config.draw_rate)
    if p1 <= 0.0 or p0 <= 0.0:
        return 0.0 if p1 == p0 else (float("inf") if p1 > p0 else float("-inf"))
    return log(p1 / p0)


def evaluate_sequence(outcomes: Iterable[Outcome], config: SPRTConfig) -> SPRTResult:
    """Evaluate a sequence and return the first sequential decision reached."""

    llr = 0.0
    wins = losses = draws = games = 0
    decision: Decision = "continue"

    for outcome in outcomes:
        if outcome not in ("win", "loss", "draw"):
            raise ValueError(f"unknown outcome: {outcome!r}")
        games += 1
        if outcome == "win":
            wins += 1
        elif outcome == "loss":
            losses += 1
        else:
            draws += 1
        llr += log_likelihood_ratio(outcome, config)
        if llr >= config.upper:
            decision = "accept_h1"
            break
        if llr <= config.lower:
            decision = "reject_h1"
            break

    return SPRTResult(
        decision=decision,
        llr=llr,
        games=games,
        wins=wins,
        losses=losses,
        draws=draws,
        lower_boundary=config.lower,
        upper_boundary=config.upper,
    )
