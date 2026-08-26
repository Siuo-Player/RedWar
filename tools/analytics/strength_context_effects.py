"""Descriptive diagnostics for Strength experiment context effects.

The analysis is intentionally observational: it reports colour/opening/seed
composition and outcome distributions without claiming causal effects or
statistical significance. Inferential models can consume these diagnostics later.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

VALID_OUTCOMES = {"challenger", "baseline", "draw"}
VALID_COLOURS = {"white", "black"}


def _score(outcome: str) -> float:
    return {"challenger": 1.0, "baseline": 0.0, "draw": 0.5}[outcome]


def summarize_strength_context_effects(games: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize observed colour, opening and seed effects from valid games."""
    records = [
        game
        for game in games
        if isinstance(game, dict)
        and game.get("valid") is True
        and game.get("outcome") in VALID_OUTCOMES
    ]
    if not records:
        raise ValueError("at least one valid Strength game is required")

    by_colour: dict[str, Counter[str]] = {
        "white": Counter(),
        "black": Counter(),
    }
    by_opening: dict[int, Counter[str]] = defaultdict(Counter)
    opening_colours: dict[int, Counter[str]] = defaultdict(Counter)
    seeds: Counter[Any] = Counter()

    for game in records:
        colour = game.get("challenger_color")
        if colour not in VALID_COLOURS:
            raise ValueError("valid Strength game has invalid challenger_color")
        outcome = str(game["outcome"])
        opening = int(game["opening_index"])
        seed = game["seed"]
        by_colour[colour][outcome] += 1
        by_opening[opening][outcome] += 1
        opening_colours[opening][colour] += 1
        seeds[seed] += 1

    def score_rate(counter: Counter[str]) -> float:
        total = sum(counter.values())
        return sum(_score(outcome) * count for outcome, count in counter.items()) / total

    colour_summary: dict[str, dict[str, Any]] = {}
    for colour in sorted(VALID_COLOURS):
        counts = by_colour[colour]
        colour_summary[colour] = {
            "games": sum(counts.values()),
            "challenger_wins": counts["challenger"],
            "baseline_wins": counts["baseline"],
            "draws": counts["draw"],
            "challenger_score_rate": score_rate(counts) if counts else 0.0,
        }

    opening_summary: dict[str, dict[str, Any]] = {}
    for opening in sorted(by_opening):
        counts = by_opening[opening]
        opening_summary[str(opening)] = {
            "games": sum(counts.values()),
            "challenger_wins": counts["challenger"],
            "baseline_wins": counts["baseline"],
            "draws": counts["draw"],
            "challenger_score_rate": score_rate(counts),
            "challenger_games_by_colour": dict(sorted(opening_colours[opening].items())),
        }

    reused_seeds = sorted((str(seed), count) for seed, count in seeds.items() if count > 1)
    colour_counts = {colour: colour_summary[colour]["games"] for colour in sorted(VALID_COLOURS)}
    opening_counts = {opening: data["games"] for opening, data in opening_summary.items()}

    return {
        "valid_games": len(records),
        "colour": colour_summary,
        "opening": opening_summary,
        "seed": {
            "games": len(records),
            "unique_seeds": len(seeds),
            "reused_seeds": reused_seeds,
            "has_seed_reuse": bool(reused_seeds),
        },
        "flags": {
            "colour_imbalance": len(set(colour_counts.values())) > 1,
            "opening_imbalance": len(set(opening_counts.values())) > 1,
            "seed_reuse": bool(reused_seeds),
        },
    }
