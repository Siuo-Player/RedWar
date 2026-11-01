# ai/sprt.py
"""
Stockfish-inspired SPRT (Sequential Probability Ratio Test) framework for RedWar.
Implements Wald's SPRT, Log-Likelihood Ratio (LLR), Elo difference estimation,
and 95% confidence intervals for rigorous engine evaluation.
"""
from dataclasses import dataclass
from enum import Enum
import math
from typing import Tuple


class SPRTStatus(str, Enum):
    CONTINUE = "continue"
    H0_ACCEPTED = "h0_accepted"  # Candidate failed to prove improvement
    H1_ACCEPTED = "h1_accepted"  # Candidate proved statistically significant improvement


@dataclass
class SPRTConfig:
    elo0: float = 0.0    # Null hypothesis (no improvement or regression threshold)
    elo1: float = 5.0    # Alternative hypothesis (e.g. +5 Elo target)
    alpha: float = 0.05  # Type I error rate (false positive)
    beta: float = 0.05   # Type II error rate (false negative)


def elo_to_expected_score(elo_diff: float) -> float:
    """Calculate expected score for an Elo difference using the logistic formula."""
    return 1.0 / (1.0 + math.pow(10.0, -elo_diff / 400.0))


def calculate_elo_difference(score: float) -> float:
    """Calculate Elo difference from winning percentage score."""
    clamped = max(0.001, min(0.999, score))
    return -400.0 * math.log10((1.0 / clamped) - 1.0)


class SPRTTracker:
    """
    Tracks matches between engine candidate and baseline, computing LLR
    and determining whether H0 or H1 is accepted.
    """
    def __init__(self, config: SPRTConfig = SPRTConfig()):
        self.config = config
        self.wins = 0
        self.losses = 0
        self.draws = 0

        # Wald bounds
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
        Compute current Log-Likelihood Ratio using the score variance model.
        """
        n = self.total_games
        if n == 0:
            return 0.0

        s = self.score
        # Compute empirical variance
        w = self.wins / n
        l = self.losses / n
        d = self.draws / n
        var = w * math.pow(1.0 - s, 2) + l * math.pow(0.0 - s, 2) + d * math.pow(0.5 - s, 2)
        var = max(0.04, var)  # Minimum floor variance

        delta_mu = self.mu1 - self.mu0
        mid_mu = (self.mu0 + self.mu1) / 2.0
        return (s - mid_mu) * (delta_mu / var) * n

    @property
    def status(self) -> SPRTStatus:
        if self.total_games == 0:
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

    def estimate_elo(self) -> Tuple[float, float]:
        """
        Estimate Elo difference and 95% confidence interval margin.
        Returns: (elo_diff, error_margin)
        """
        if self.total_games == 0:
            return 0.0, 0.0

        s = self.score
        elo_diff = calculate_elo_difference(s)

        # 95% Confidence Interval
        n = self.total_games
        w = self.wins / n
        l = self.losses / n
        d = self.draws / n
        var = w * math.pow(1.0 - s, 2) + l * math.pow(0.0 - s, 2) + d * math.pow(0.5 - s, 2)
        std_err = math.sqrt(max(0.01, var) / n)

        # Gradient d(Elo)/d(s) = 400 / (ln(10) * s * (1 - s))
        clamped_s = max(0.01, min(0.99, s))
        gradient = 400.0 / (math.log(10.0) * clamped_s * (1.0 - clamped_s))
        margin = 1.96 * std_err * gradient

        return round(elo_diff, 1), round(margin, 1)
