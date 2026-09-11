"""Binary paired strength estimation for RedWar Arena experiments.

RedWar Arena is a win/loss experiment: games have no draw outcome. The
primary strength model is therefore a two-system Bradley-Terry comparison.
Uncertainty is estimated by resampling complete opening/colour-inverted pairs,
not by multiplying an arbitrary variance by a game-count constant.

The sequential promotion policy evaluates only at fixed complete-pair stages
and preserves a hard maximum game budget: ACCEPT requires evidence that the
lower confidence bound for the challenger-vs-baseline strength difference is
strictly above zero; failure to reach that condition by MAX_GAMES is REJECT.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import inf, log10
import random
from typing import Iterable, Literal, Sequence

Outcome = Literal["challenger", "baseline"]
Colour = Literal["white", "black"]
Decision = Literal["accept", "continue", "reject"]

PROMOTION_STAGES = (96, 192, 320, 512)
MAX_GAMES = PROMOTION_STAGES[-1]
STAGE_ALPHA = 0.05 / len(PROMOTION_STAGES)


@dataclass(frozen=True)
class PairedGame:
    """One Arena game in a two-game colour-inverted opening pair."""

    pair_id: str
    opening_seed: int
    challenger_colour: Colour
    outcome: Outcome
    game_index: int | None = None


@dataclass(frozen=True)
class BradleyTerryEstimate:
    """Two-system binary Bradley-Terry strength estimate."""

    delta_elo: float
    challenger_win_probability: float
    challenger_wins: int
    baseline_wins: int
    games: int


@dataclass(frozen=True)
class BootstrapInterval:
    """One-sided/two-sided percentile interval from complete opening pairs."""

    lower: float
    median: float
    upper: float
    confidence: float
    replicates: int
    cluster_count: int


@dataclass(frozen=True)
class PromotionDecision:
    """Decision at one of the fixed sequential promotion stages."""

    decision: Decision
    games: int
    pairs: int
    stage_games: int | None
    delta_elo: float | None
    lower_bound_elo: float | None
    confidence: float
    reason: str


def validate_paired_games(games: Iterable[PairedGame]) -> tuple[tuple[PairedGame, PairedGame], ...]:
    """Validate complete pairs and reject opening reuse within one experiment."""
    grouped: dict[str, list[PairedGame]] = {}
    for game in games:
        if game.outcome not in {"challenger", "baseline"}:
            raise ValueError(f"unknown binary outcome: {game.outcome}")
        if game.challenger_colour not in {"white", "black"}:
            raise ValueError(f"unknown challenger colour: {game.challenger_colour}")
        grouped.setdefault(game.pair_id, []).append(game)

    pairs: list[tuple[PairedGame, PairedGame]] = []
    seed_owner: dict[int, str] = {}
    for pair_id, members in grouped.items():
        if len(members) != 2:
            raise ValueError(f"pair {pair_id!r} must contain exactly two games")
        first, second = members
        if first.opening_seed != second.opening_seed:
            raise ValueError(f"pair {pair_id!r} must reuse the same opening seed")
        if first.challenger_colour == second.challenger_colour:
            raise ValueError(f"pair {pair_id!r} must invert challenger colour")
        previous_pair = seed_owner.get(first.opening_seed)
        if previous_pair is not None and previous_pair != pair_id:
            raise ValueError(f"opening seed {first.opening_seed} reused by pairs {previous_pair!r} and {pair_id!r}")
        seed_owner[first.opening_seed] = pair_id
        pairs.append((first, second))

    return tuple(pairs)


def fit_bradley_terry(games: Sequence[PairedGame] | Sequence[Outcome]) -> BradleyTerryEstimate:
    """Fit a two-system binary Bradley-Terry model.

    With two systems this reduces to the observed win probability. The Elo
    equivalent is 400 * log10(p / (1-p)). All-win/all-loss samples therefore
    have an infinite maximum-likelihood delta, which is intentional.
    """
    outcomes: list[Outcome] = []
    for game in games:
        outcome = game.outcome if isinstance(game, PairedGame) else game
        if outcome not in {"challenger", "baseline"}:
            raise ValueError(f"unknown binary outcome: {outcome}")
        outcomes.append(outcome)

    if not outcomes:
        raise ValueError("at least one game is required")

    wins = outcomes.count("challenger")
    losses = outcomes.count("baseline")
    games_count = wins + losses
    p = wins / games_count
    if wins == 0:
        delta_elo = -inf
    elif losses == 0:
        delta_elo = inf
    else:
        delta_elo = 400.0 * log10(wins / losses)
    return BradleyTerryEstimate(delta_elo, p, wins, losses, games_count)


def paired_bootstrap_delta(
    games: Sequence[PairedGame],
    *,
    replicates: int = 2000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapInterval:
    """Bootstrap Bradley-Terry delta by resampling complete opening pairs."""
    if replicates < 2:
        raise ValueError("replicates must be at least 2")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    pairs = validate_paired_games(games)
    if not pairs:
        raise ValueError("at least one complete pair is required")

    rng = random.Random(seed)
    deltas: list[float] = []
    for _ in range(replicates):
        sampled = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
        sample_games = [game for pair in sampled for game in pair]
        deltas.append(fit_bradley_terry(sample_games).delta_elo)

    deltas.sort()
    alpha = (1.0 - confidence) / 2.0

    def percentile(p: float) -> float:
        index = (len(deltas) - 1) * p
        lower = int(index)
        upper = min(lower + 1, len(deltas) - 1)
        fraction = index - lower
        low_value = deltas[lower]
        high_value = deltas[upper]
        if low_value == high_value:
            return low_value
        if low_value == -inf or high_value == -inf:
            return -inf
        if low_value == inf or high_value == inf:
            return inf
        return low_value + (high_value - low_value) * fraction

    return BootstrapInterval(
        lower=percentile(alpha),
        median=percentile(0.5),
        upper=percentile(1.0 - alpha),
        confidence=confidence,
        replicates=replicates,
        cluster_count=len(pairs),
    )


def _stage_for_games(games: int) -> int | None:
    if games <= 0:
        raise ValueError("games must be positive")
    return games if games in PROMOTION_STAGES else None


def evaluate_promotion(
    games: Sequence[PairedGame],
    *,
    max_games: int = MAX_GAMES,
    bootstrap_replicates: int = 2000,
    bootstrap_seed: int = 0,
) -> PromotionDecision:
    """Apply the baseline-preserving staged promotion policy.

    The estimator is inspected only at 96, 192, 320 and 512 games. A
    Bonferroni-adjusted one-sided confidence level allocates the total 5% alpha
    budget across those four fixed looks. ACCEPT requires lower_bound > 0;
    otherwise the experiment continues until MAX_GAMES, where it rejects.
    """
    if max_games != MAX_GAMES:
        raise ValueError(f"max_games must remain the fixed methodological limit {MAX_GAMES}")

    pairs = validate_paired_games(games)
    complete_games = len(pairs) * 2
    if complete_games > max_games:
        raise ValueError(f"experiment exceeds MAX_GAMES={max_games}")

    stage_games = _stage_for_games(complete_games)
    confidence = 1.0 - STAGE_ALPHA
    if stage_games is None:
        if complete_games < PROMOTION_STAGES[0]:
            reason = f"collect until first sequential look at {PROMOTION_STAGES[0]} games"
        else:
            next_stage = next(stage for stage in PROMOTION_STAGES if stage > complete_games)
            reason = f"no look between fixed stages; continue to {next_stage} games"
        return PromotionDecision("continue", complete_games, len(pairs), None, None, None, confidence, reason)

    flat_games = [game for pair in pairs for game in pair]
    estimate = fit_bradley_terry(flat_games)
    # `paired_bootstrap_delta` reports a two-sided percentile interval. To obtain
    # the declared one-sided lower bound at alpha=STAGE_ALPHA, use the equivalent
    # two-sided interval whose lower-tail percentile is exactly STAGE_ALPHA.
    bootstrap_interval_confidence = 1.0 - (2.0 * STAGE_ALPHA)
    interval = paired_bootstrap_delta(
        flat_games,
        replicates=bootstrap_replicates,
        confidence=bootstrap_interval_confidence,
        seed=bootstrap_seed,
    )

    if interval.lower > 0.0:
        return PromotionDecision(
            "accept", complete_games, len(pairs), stage_games, estimate.delta_elo,
            interval.lower, confidence,
            "lower confidence bound for challenger strength is strictly above zero",
        )

    if stage_games == MAX_GAMES:
        return PromotionDecision(
            "reject", complete_games, len(pairs), stage_games, estimate.delta_elo,
            interval.lower, confidence,
            "MAX_GAMES reached without statistical proof of challenger superiority",
        )

    return PromotionDecision(
        "continue", complete_games, len(pairs), stage_games, estimate.delta_elo,
        interval.lower, confidence,
        "insufficient evidence for challenger superiority; continue with a fresh opening batch",
    )
