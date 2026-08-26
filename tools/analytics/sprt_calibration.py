"""Descriptive calibration diagnostics for the RedWar SPRT baseline.

This module estimates the empirical draw rate and decisive win rate observed in a
set of valid Strength outcomes. It does not perform a significance test, modify
SPRT boundaries, or make a promotion decision.
"""
from __future__ import annotations

from math import log
from typing import Iterable, Literal

Outcome = Literal["win", "loss", "draw"]
ELO_SCALE = 400.0


def _validate(outcomes: Iterable[Outcome]) -> list[Outcome]:
    records = list(outcomes)
    if not records:
        raise ValueError("at least one valid Strength outcome is required")
    if any(outcome not in ("win", "loss", "draw") for outcome in records):
        raise ValueError("outcomes must be win, loss or draw")
    return records


def calibrate_sprt_baseline(outcomes: Iterable[Outcome]) -> dict[str, float | int | str]:
    """Return descriptive empirical parameters for a future SPRT calibration."""
    records = _validate(outcomes)
    wins = sum(outcome == "win" for outcome in records)
    losses = sum(outcome == "loss" for outcome in records)
    draws = sum(outcome == "draw" for outcome in records)
    decisive = wins + losses
    draw_rate = draws / len(records)

    result: dict[str, float | int | str] = {
        "games": len(records),
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "draw_rate": draw_rate,
        "decisive_games": decisive,
        "calibration_status": "insufficient_decisive_games",
    }

    if decisive:
        decisive_win_rate = wins / decisive
        result["decisive_win_rate"] = decisive_win_rate
        if 0.0 < decisive_win_rate < 1.0:
            result["implied_elo_delta"] = ELO_SCALE / log(10.0) * log(
                decisive_win_rate / (1.0 - decisive_win_rate)
            )
        else:
            result["implied_elo_delta"] = float("inf") if wins else float("-inf")
        result["calibration_status"] = "descriptive_only"
    else:
        result["decisive_win_rate"] = 0.5
        result["implied_elo_delta"] = 0.0

    return result
