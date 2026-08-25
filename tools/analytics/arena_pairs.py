"""Pair identities and pentanomial aggregation for Ares Arena experiments."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Literal

Outcome = Literal["challenger", "baseline", "draw"]


@dataclass(frozen=True)
class GameOutcome:
    game_index: int
    pair_id: str
    opening_index: int
    challenger_color: Literal["white", "black"]
    outcome: Outcome


PAIR_BINS = {
    ("baseline", "baseline"): "LL",
    ("baseline", "draw"): "LD_DL",
    ("draw", "baseline"): "LD_DL",
    ("draw", "draw"): "DD_WL_LW",
    ("challenger", "baseline"): "DD_WL_LW",
    ("baseline", "challenger"): "DD_WL_LW",
    ("challenger", "draw"): "WD_DW",
    ("draw", "challenger"): "WD_DW",
    ("challenger", "challenger"): "WW",
}


def make_pair_id(game_index: int) -> str:
    if game_index < 0:
        raise ValueError("game_index must be non-negative")
    return f"pair-{game_index // 2:06d}"


def aggregate_pentanomial(games: Iterable[GameOutcome]) -> Counter[str]:
    """Aggregate complete two-game pairs into the five pentanomial bins.

    Pair members are identified by ``pair_id``. Incomplete pairs are not silently
    assigned to a bin; callers can inspect ``incomplete_pairs`` separately.
    """

    grouped: dict[str, list[GameOutcome]] = defaultdict(list)
    for game in games:
        grouped[game.pair_id].append(game)

    bins: Counter[str] = Counter()
    for pair_games in grouped.values():
        if len(pair_games) != 2:
            continue
        first, second = sorted(pair_games, key=lambda item: item.game_index)
        bins[PAIR_BINS[(first.outcome, second.outcome)]] += 1
    return bins


def incomplete_pairs(games: Iterable[GameOutcome]) -> set[str]:
    grouped: dict[str, int] = defaultdict(int)
    for game in games:
        grouped[game.pair_id] += 1
    return {pair_id for pair_id, count in grouped.items() if count != 2}


def validate_pair_structure(games: Iterable[GameOutcome]) -> None:
    """Validate that each complete pair shares an opening and flips challenger colour."""

    grouped: dict[str, list[GameOutcome]] = defaultdict(list)
    for game in games:
        grouped[game.pair_id].append(game)

    for pair_id, pair_games in grouped.items():
        if len(pair_games) != 2:
            continue
        first, second = sorted(pair_games, key=lambda item: item.game_index)
        if first.opening_index != second.opening_index:
            raise ValueError(f"{pair_id}: paired games must use the same opening")
        if first.challenger_color == second.challenger_color:
            raise ValueError(f"{pair_id}: paired games must invert challenger colour")
