"""Compare persistent and fresh-per-game engine lifecycles.

This is a diagnostic instrument, not a strength or promotion protocol. It uses
identical opening seeds, colour assignment, node budget, and match runner logic
for both modes while changing only whether each C++ engine process is reused
between games. A difference indicates lifecycle sensitivity; it does not by
itself identify a causal mechanism.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import CppEngineBot
from engine.game_state import GameState
from tools.analytics.arena_tournament import (
    _winner_side,
    run_headless_match,
    select_opening_seed,
)
from tools.analytics.opening_book import gerar_abertura

DEFAULT_SEEDS = tuple(range(101, 117))


class _RecordingBot:
    """Diagnostic wrapper that records the exact GameState handed to the bot."""

    def __init__(self, inner: CppEngineBot, *, game_index: int, seed: int, label: str):
        self.inner = inner
        self.game_index = game_index
        self.seed = seed
        self.label = label
        self.observed_rwen: str | None = None

    @property
    def bridge(self):
        return self.inner.bridge

    def play(self, game_state):
        self.observed_rwen = game_state.to_rwen()
        expected = GameState(time_limit_seconds=99999)
        expected.board = gerar_abertura(self.seed)
        expected_rwen = expected.to_rwen()
        print(
            f"LIFECYCLE_INPUT game_index={self.game_index} seed={self.seed} "
            f"label={self.label} matches_expected={self.observed_rwen == expected_rwen}"
        )
        if self.observed_rwen != expected_rwen:
            raise RuntimeError(
                "Arena opening-state mismatch: "
                f"game_index={self.game_index} seed={self.seed} label={self.label}"
            )
        return self.inner.play(game_state)

    def close(self):
        self.inner.bridge.close()


def parse_seeds(raw: str) -> tuple[int, ...]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("opening seeds must be a non-empty comma-separated list")
    values = tuple(int(token.strip()) for token in raw.split(",") if token.strip())
    if len(values) != 16:
        raise ValueError(f"expected exactly 16 opening seeds, got {len(values)}")
    if len(set(values)) != len(values) or any(value < 0 for value in values):
        raise ValueError("opening seeds must be unique non-negative integers")
    return values


def _play_series(
    challenger_engine: str,
    baseline_engine: str,
    *,
    nodes: int,
    games: int,
    opening_seeds: tuple[int, ...],
    fresh_per_game: bool,
) -> dict[str, object]:
    persistent_challenger = None
    persistent_baseline = None
    if not fresh_per_game:
        persistent_challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
        persistent_baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)

    records: list[dict[str, object]] = []
    temporary_wrappers: list[_RecordingBot] = []
    try:
        for game_index in range(games):
            opening_index = (game_index // 2) % len(opening_seeds)
            opening_seed = select_opening_seed(game_index, opening_seeds)
            pair_id = game_index // 2

            if fresh_per_game:
                challenger_inner = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
                baseline_inner = CppEngineBot(nodes=nodes, executable_path=baseline_engine)
            else:
                challenger_inner = persistent_challenger
                baseline_inner = persistent_baseline

            challenger = _RecordingBot(
                challenger_inner,
                game_index=game_index,
                seed=opening_seed,
                label="challenger",
            )
            baseline = _RecordingBot(
                baseline_inner,
                game_index=game_index,
                seed=opening_seed,
                label="baseline",
            )
            if fresh_per_game:
                temporary_wrappers.extend((challenger, baseline))

            if game_index % 2 == 0:
                challenger_colour = "white"
                game = run_headless_match(challenger, baseline, opening_index, opening_seed)
            else:
                challenger_colour = "black"
                game = run_headless_match(baseline, challenger, opening_index, opening_seed)

            winner_side = _winner_side(game["winner"])
            if not game["valid"]:
                outcome = "invalid"
            elif winner_side == challenger_colour:
                outcome = "challenger"
            else:
                outcome = "baseline"

            records.append(
                {
                    "game_index": game_index,
                    "pair_id": pair_id,
                    "opening_index": opening_index,
                    "seed": opening_seed,
                    "challenger_color": challenger_colour,
                    "winner_side": winner_side,
                    "outcome": outcome,
                    "valid": bool(game["valid"]),
                    "termination_reason": game["termination_reason"],
                    "plies": game["plies"],
                }
            )

            if fresh_per_game:
                challenger.close()
                baseline.close()
    finally:
        if persistent_challenger is not None:
            persistent_challenger.bridge.close()
        if persistent_baseline is not None:
            persistent_baseline.bridge.close()
        for wrapper in temporary_wrappers:
            wrapper.inner.bridge.close()

    return summarize(records)


def summarize(records: Iterable[dict[str, object]]) -> dict[str, object]:
    records = list(records)
    colour = {"white": {"challenger": 0, "baseline": 0, "invalid": 0}, "black": {"challenger": 0, "baseline": 0, "invalid": 0}}
    totals = {"challenger": 0, "baseline": 0, "invalid": 0}
    for record in records:
        outcome = str(record["outcome"])
        totals[outcome] += 1
        colour[str(record["challenger_color"])][outcome] += 1
    return {
        "games": len(records),
        "valid_games": len(records) - totals["invalid"],
        "totals": totals,
        "challenger_outcomes_by_colour": colour,
        "records": records,
    }


def compare_modes(
    persistent: dict[str, object],
    fresh: dict[str, object],
) -> dict[str, object]:
    p_totals = persistent["totals"]
    f_totals = fresh["totals"]
    return {
        "persistent_totals": p_totals,
        "fresh_totals": f_totals,
        "outcome_delta": {
            key: int(p_totals[key]) - int(f_totals[key])
            for key in ("challenger", "baseline", "invalid")
        },
        "persistent_colour_wins_difference": abs(
            int(persistent["challenger_outcomes_by_colour"]["white"]["challenger"])
            - int(persistent["challenger_outcomes_by_colour"]["black"]["challenger"])
        ),
        "fresh_colour_wins_difference": abs(
            int(fresh["challenger_outcomes_by_colour"]["white"]["challenger"])
            - int(fresh["challenger_outcomes_by_colour"]["black"]["challenger"])
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Arena sensitivity to engine process lifecycle")
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--nodes", type=int, required=True)
    parser.add_argument("--games", type=int, default=32)
    parser.add_argument("--opening-seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.nodes <= 0:
        raise SystemExit("nodes must be positive")
    if args.games <= 0 or args.games % 2:
        raise SystemExit("games must be a positive even integer")

    seeds = parse_seeds(args.opening_seeds)
    persistent = _play_series(
        args.challenger_engine,
        args.baseline_engine,
        nodes=args.nodes,
        games=args.games,
        opening_seeds=seeds,
        fresh_per_game=False,
    )
    fresh = _play_series(
        args.challenger_engine,
        args.baseline_engine,
        nodes=args.nodes,
        games=args.games,
        opening_seeds=seeds,
        fresh_per_game=True,
    )

    payload = {
        "schema_version": "redwar-arena-lifecycle-diagnostic-v1",
        "diagnostic_status": "observational_lifecycle_sensitivity_no_promotion_decision",
        "parameters": {
            "challenger_engine": str(Path(args.challenger_engine).resolve()),
            "baseline_engine": str(Path(args.baseline_engine).resolve()),
            "nodes": args.nodes,
            "games": args.games,
            "opening_seeds": list(seeds),
            "pairing_policy": "adjacent_games_same_opening_with_inverted_challenger_colour",
        },
        "persistent_per_game_process": persistent,
        "fresh_process_per_game": fresh,
        "comparison": compare_modes(persistent, fresh),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["comparison"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
