"""Experimental global Arena rating calibration.

This module is deliberately separate from the promotion gate.  It fits a
finite, regularized Bradley-Terry-family model over a comparison graph with
one fixed anchor rating and reports a Laplace/Hessian uncertainty estimate.

It is calibration infrastructure only: real Arena evidence is still required
before this becomes an authoritative historical rating product.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, log10, sqrt
from typing import Sequence

LOG10 = log10(10.0)
ELO_LOGIT = LOG10 / 400.0


@dataclass(frozen=True)
class Comparison:
    winner: str
    loser: str
    games: int = 1


@dataclass(frozen=True)
class RatingEstimate:
    ratings: dict[str, float]
    standard_errors: dict[str, float]
    iterations: int
    converged: bool


def _solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    a = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("singular rating Hessian")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= scale
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if factor == 0.0:
                continue
            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]
    return [a[i][n] for i in range(n)]


def _invert(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix)
    inverse: list[list[float]] = []
    for col in range(n):
        rhs = [1.0 if row == col else 0.0 for row in range(n)]
        inverse.append(_solve_linear([row[:] for row in matrix], rhs))
    return [list(row) for row in zip(*inverse)]


def fit_global_rating(
    comparisons: Sequence[Comparison],
    *,
    anchor: str,
    prior_sigma: float = 800.0,
    max_iterations: int = 100,
    tolerance: float = 1e-7,
) -> RatingEstimate:
    """Fit a finite regularized Bradley-Terry model in Elo units.

    The anchor is fixed at 0. A zero-mean Gaussian prior with ``prior_sigma``
    supplies finite separation for extreme results such as 100-0 matchups.
    Every rated version must be connected to the anchor by observed
    comparisons; the prior is not allowed to manufacture cross-component
    strength estimates.
    """
    if not comparisons:
        raise ValueError("at least one comparison is required")
    if prior_sigma <= 0:
        raise ValueError("prior_sigma must be positive")
    versions = {anchor}
    adjacency: dict[str, set[str]] = {anchor: set()}
    for comparison in comparisons:
        if comparison.games <= 0:
            raise ValueError("comparison games must be positive")
        versions.add(comparison.winner)
        versions.add(comparison.loser)
        adjacency.setdefault(comparison.winner, set()).add(comparison.loser)
        adjacency.setdefault(comparison.loser, set()).add(comparison.winner)

    reachable = {anchor}
    frontier = [anchor]
    while frontier:
        version = frontier.pop()
        for neighbour in adjacency[version]:
            if neighbour not in reachable:
                reachable.add(neighbour)
                frontier.append(neighbour)
    if reachable != versions:
        disconnected = sorted(versions - reachable)
        raise ValueError(
            "comparison graph must be connected to anchor; "
            f"unreachable versions: {', '.join(disconnected)}"
        )

    unknown = sorted(version for version in versions if version != anchor)
    index = {version: i for i, version in enumerate(unknown)}
    ratings = [0.0 for _ in unknown]
    prior_precision = 1.0 / (prior_sigma * prior_sigma)

    def rating_of(version: str) -> float:
        return 0.0 if version == anchor else ratings[index[version]]

    converged = False
    iterations = 0
    final_hessian: list[list[float]] | None = None
    for iteration in range(1, max_iterations + 1):
        gradient = [-prior_precision * value for value in ratings]
        hessian = [[-prior_precision if row == col else 0.0 for col in range(len(unknown))] for row in range(len(unknown))]
        for comparison in comparisons:
            winner_rating = rating_of(comparison.winner)
            loser_rating = rating_of(comparison.loser)
            logit = ELO_LOGIT * (winner_rating - loser_rating)
            if logit >= 0:
                p = 1.0 / (1.0 + exp(-logit))
            else:
                z = exp(logit)
                p = z / (1.0 + z)
            residual = comparison.games * (1.0 - p)
            curvature = comparison.games * (ELO_LOGIT ** 2) * p * (1.0 - p)
            if comparison.winner != anchor:
                wi = index[comparison.winner]
                gradient[wi] += ELO_LOGIT * residual
                hessian[wi][wi] -= curvature
            if comparison.loser != anchor:
                li = index[comparison.loser]
                gradient[li] -= ELO_LOGIT * residual
                hessian[li][li] -= curvature
            if comparison.winner != anchor and comparison.loser != anchor:
                wi = index[comparison.winner]
                li = index[comparison.loser]
                hessian[wi][li] += curvature
                hessian[li][wi] += curvature
        step = _solve_linear([row[:] for row in hessian], gradient)
        next_ratings = [value - delta for value, delta in zip(ratings, step)]
        iterations = iteration
        if max(abs(a - b) for a, b in zip(next_ratings, ratings)) < tolerance:
            ratings = next_ratings
            final_hessian = hessian
            converged = True
            break
        ratings = next_ratings
        final_hessian = hessian

    assert final_hessian is not None
    precision = [[-value for value in row] for row in final_hessian]
    covariance = _invert(precision) if unknown else []
    standard_errors = {anchor: 0.0}
    for version, position in index.items():
        variance = max(covariance[position][position], 0.0)
        standard_errors[version] = sqrt(variance)

    return RatingEstimate(
        ratings={anchor: 0.0, **{version: ratings[position] for version, position in index.items()}},
        standard_errors=standard_errors,
        iterations=iterations,
        converged=converged,
    )
