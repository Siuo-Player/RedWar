"""Descriptive matchup/context analysis for Strength experiments.

The module combines raw Arena A/B records from multiple experiments, preserving
matchup direction and optional context fields such as opening or population.
Experimental controls (rules version and node budget) are always part of the
context key so incompatible runs cannot be silently pooled.
It reports score distributions and detects descriptive three-way intransitive
cycles. It does not estimate causal effects, calibrated confidence intervals,
or promotion decisions.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any, Iterable, Sequence

VALID_OUTCOMES = {"challenger", "baseline", "draw"}
CONTROL_FIELDS = ("rules_version", "node_budget")


def _experiment_field(game: dict[str, Any], field: str) -> Any:
    experiment = game.get("experiment")
    if not isinstance(experiment, dict):
        raise ValueError("valid Strength game is missing experiment metadata")
    if field not in experiment:
        raise ValueError(f"experiment metadata is missing {field}")
    return experiment[field]


def _context_key(game: dict[str, Any], context_fields: Sequence[str]) -> tuple[tuple[str, Any], ...]:
    fields = tuple(dict.fromkeys((*CONTROL_FIELDS, *context_fields)))
    values: list[tuple[str, Any]] = []
    for field in fields:
        if field in game:
            value = game[field]
        else:
            value = _experiment_field(game, field)
        values.append((field, value))
    return tuple(values)


def _score(outcome: str) -> float:
    return {"challenger": 1.0, "baseline": 0.0, "draw": 0.5}[outcome]


def summarize_matchups(
    games: Iterable[dict[str, Any]],
    *,
    context_fields: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Aggregate valid games into directional matchup/context summaries."""
    grouped: dict[tuple[str, str, tuple[tuple[str, Any], ...]], list[str]] = defaultdict(list)

    for game in games:
        if not isinstance(game, dict) or game.get("valid") is not True:
            continue
        outcome = game.get("outcome")
        if outcome not in VALID_OUTCOMES:
            raise ValueError("valid Strength game has an invalid outcome")
        challenger = str(_experiment_field(game, "challenger_version"))
        baseline = str(_experiment_field(game, "baseline_version"))
        if challenger == baseline:
            raise ValueError("Strength matchup participants must be distinct")
        grouped[(challenger, baseline, _context_key(game, context_fields))].append(str(outcome))

    result: list[dict[str, Any]] = []
    for (challenger, baseline, context), outcomes in sorted(grouped.items(), key=str):
        counts = {
            "challenger": outcomes.count("challenger"),
            "baseline": outcomes.count("baseline"),
            "draw": outcomes.count("draw"),
        }
        games_count = len(outcomes)
        score_rate = sum(_score(outcome) for outcome in outcomes) / games_count
        result.append(
            {
                "challenger": challenger,
                "baseline": baseline,
                "context": {field: value for field, value in context},
                "games": games_count,
                "challenger_wins": counts["challenger"],
                "baseline_wins": counts["baseline"],
                "draws": counts["draw"],
                "challenger_score_rate": score_rate,
            }
        )
    return result


def detect_intransitive_cycles(
    matchup_summaries: Sequence[dict[str, Any]],
    *,
    min_games: int = 4,
    strict_score_rate: float = 0.5,
) -> list[dict[str, Any]]:
    """Find descriptive A>B, B>C, C>A cycles within one context."""
    if min_games < 1:
        raise ValueError("min_games must be positive")
    if not 0.5 <= strict_score_rate <= 1.0:
        raise ValueError("strict_score_rate must be between 0.5 and 1.0")

    by_context: dict[tuple[tuple[str, Any], ...], dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)
    for summary in matchup_summaries:
        if int(summary["games"]) < min_games:
            continue
        if float(summary["challenger_score_rate"]) <= strict_score_rate:
            continue
        context = tuple(sorted(dict(summary.get("context", {})).items(), key=str))
        key = (str(summary["challenger"]), str(summary["baseline"]))
        existing = by_context[context].get(key)
        if existing is None or int(summary["games"]) > int(existing["games"]):
            by_context[context][key] = summary

    cycles: list[dict[str, Any]] = []
    for context, qualifying in sorted(by_context.items(), key=str):
        players = sorted({name for edge in qualifying for name in edge})
        for a, b, c in combinations(players, 3):
            for first, second, third in ((a, b, c), (a, c, b)):
                edges = (
                    qualifying.get((first, second)),
                    qualifying.get((second, third)),
                    qualifying.get((third, first)),
                )
                if all(edges):
                    cycles.append(
                        {
                            "context": {field: value for field, value in context},
                            "players": [first, second, third],
                            "edges": [dict(edge) for edge in edges if edge is not None],
                            "interpretation": "descriptive_intransitive_cycle",
                        }
                    )
    return cycles


def analyze_matchup_context(
    games: Iterable[dict[str, Any]],
    *,
    context_fields: Sequence[str] = ("opening_index",),
    min_games: int = 4,
    strict_score_rate: float = 0.5,
) -> dict[str, Any]:
    """Return descriptive matchup/context summaries and intransitive cycles."""
    summaries = summarize_matchups(games, context_fields=context_fields)
    cycles = detect_intransitive_cycles(
        summaries,
        min_games=min_games,
        strict_score_rate=strict_score_rate,
    )
    return {
        "matchups": summaries,
        "intransitive_cycles": cycles,
        "context_fields": list(context_fields),
        "control_fields": list(CONTROL_FIELDS),
        "min_games": min_games,
        "strict_score_rate": strict_score_rate,
        "status": "descriptive_matchup_analysis_only",
    }


__all__ = [
    "analyze_matchup_context",
    "detect_intransitive_cycles",
    "summarize_matchups",
]
