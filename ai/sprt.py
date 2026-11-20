# ai/sprt.py
"""
Stockfish-inspired SPRT (Sequential Probability Ratio Test) framework for RedWar.
Implements Wald's exact Bernoulli SPRT, Log-Likelihood Ratio (LLR), Elo difference estimation,
and multi-tiered confidence intervals (95% CI / 1.96-sigma and 99.73% CI / 3.0-sigma)
for rigorous, regression-proof engine evaluation.

Mathematical Formulation:
Under Wald's Sequential Probability Ratio Test for Bernoulli outcomes:
- H0: score = p0 = elo_to_expected_score(elo0)
- H1: score = p1 = elo_to_expected_score(elo1)
- LLR = w_eff * ln(p1 / p0) + l_eff * ln((1 - p1) / (1 - p0))
  where w_eff = wins + 0.5 * draws, and l_eff = losses + 0.5 * draws.
This exact likelihood ratio prevents asymptotic variance floor shortcuts that could
spuriously accept H1 with tiny sample sizes (e.g. 12 consecutive wins).
In addition, a minimum sample size gate (min_games) enforces empirical discipline.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, Tuple


class SPRTStatus(str, Enum):
    CONTINUE = "continue"
    H0_ACCEPTED = "h0_accepted"  # Candidate failed to prove improvement
    H1_ACCEPTED = "h1_accepted"  # Candidate proved statistically significant improvement


@dataclass
class SPRTConfig:
    elo0: float = 0.0     # Null hypothesis (no improvement or regression threshold)
    elo1: float = 5.0     # Alternative hypothesis (e.g. +5 Elo target)
    alpha: float = 0.05   # Type I error rate (false positive)
    beta: float = 0.05    # Type II error rate (false negative)
    min_games: int = 20   # Minimum games before any hypothesis termination is allowed


def elo_to_expected_score(elo_diff: float) -> float:
    """Calculate expected score for an Elo difference using the logistic formula."""
    return 1.0 / (1.0 + math.pow(10.0, -elo_diff / 400.0))


def calculate_elo_difference(score: float) -> float:
    """Calculate Elo difference from winning percentage score."""
    clamped = max(0.001, min(0.999, score))
    return -400.0 * math.log10((1.0 / clamped) - 1.0)


class SPRTTracker:
    """
    Tracks matches between engine candidate and baseline, computing exact Wald LLR
    and determining whether H0 or H1 is accepted.
    """
    def __init__(self, config: SPRTConfig = SPRTConfig()):
        self.config = config
        self.wins = 0
        self.losses = 0
        self.draws = 0

        # Wald decision bounds
        self.upper_bound = math.log((1.0 - config.beta) / config.alpha)
        self.lower_bound = math.log(config.beta / (1.0 - config.alpha))

        self.mu0 = elo_to_expected_score(config.elo0)
        self.mu1 = elo_to_expected_score(config.elo1)

    @property
    def total_games(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def score(self) -> float:
        if self.total_games == 0:
            return 0.5
        return (self.wins + 0.5 * self.draws) / self.total_games

    @property
    def llr(self) -> float:
        """
        Compute exact Wald Log-Likelihood Ratio (LLR) under Bernoulli trial outcomes.
        LLR = w_eff * ln(p1 / p0) + l_eff * ln((1 - p1) / (1 - p0))
        """
        if self.total_games == 0:
            return 0.0

        p0 = max(0.001, min(0.999, self.mu0))
        p1 = max(0.001, min(0.999, self.mu1))

        w_eff = self.wins + 0.5 * self.draws
        l_eff = self.losses + 0.5 * self.draws

        log_w = math.log(p1 / p0)
        log_l = math.log((1.0 - p1) / (1.0 - p0))

        return w_eff * log_w + l_eff * log_l

    @property
    def status(self) -> SPRTStatus:
        if self.total_games < self.config.min_games:
            return SPRTStatus.CONTINUE

        current_llr = self.llr
        if current_llr >= self.upper_bound:
            return SPRTStatus.H1_ACCEPTED
        if current_llr <= self.lower_bound:
            return SPRTStatus.H0_ACCEPTED
        return SPRTStatus.CONTINUE

    def add_result(self, win: int = 0, loss: int = 0, draw: int = 0) -> SPRTStatus:
        """Record game results and return current status."""
        self.wins += win
        self.losses += loss
        self.draws += draw
        return self.status

    def estimate_elo(self, sigma: float = 1.96) -> Tuple[float, float]:
        """
        Estimate Elo difference and confidence interval margin for the given sigma level.
        By default uses sigma=1.96 (95% CI). For a 3-sigma gate, pass sigma=3.0 (99.73% CI).
        Returns: (elo_diff, error_margin)
        """
        if self.total_games == 0:
            return 0.0, 0.0

        s = self.score
        elo_diff = calculate_elo_difference(s)

        # Confidence Interval based on standard error
        n = self.total_games
        w = self.wins / n
        l = self.losses / n
        d = self.draws / n
        var = w * math.pow(1.0 - s, 2) + l * math.pow(0.0 - s, 2) + d * math.pow(0.5 - s, 2)
        std_err = math.sqrt(max(0.01, var) / n)

        # Gradient d(Elo)/d(s) = 400 / (ln(10) * s * (1 - s))
        clamped_s = max(0.01, min(0.99, s))
        gradient = 400.0 / (math.log(10.0) * clamped_s * (1.0 - clamped_s))
        margin = sigma * std_err * gradient

        return round(elo_diff, 1), round(margin, 1)

    def estimate_elo_multitier(self) -> Dict[str, Any]:
        """
        Provide multi-tiered confidence intervals:
        - 1.96-sigma (95% CI, p < 0.05): standard experimental screening
        - 3.00-sigma (99.73% CI, p < 0.0027): Six-Sigma Champion Promotion Gate
        """
        elo_diff, margin_95 = self.estimate_elo(sigma=1.96)
        _, margin_3sigma = self.estimate_elo(sigma=3.0)
        return {
            "delta_elo": elo_diff,
            "margin_95": margin_95,
            "ci_95": (round(elo_diff - margin_95, 1), round(elo_diff + margin_95, 1)),
            "margin_3sigma": margin_3sigma,
            "ci_3sigma": (round(elo_diff - margin_3sigma, 1), round(elo_diff + margin_3sigma, 1)),
        }
