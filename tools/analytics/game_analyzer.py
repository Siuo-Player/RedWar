"""Analyze recorded Arena games without running another game simulation.

The Arena is responsible for producing deterministic game records. This tool
only consumes those records, which keeps simulation, measurement and reporting
separate and makes diagnostics reproducible.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido em {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Registo não é um objeto em {path}:{line_number}")
            yield value


def analisar_partidas(path: Path) -> dict:
    games = 0
    invalid_records = 0
    total_plies = 0
    outcomes = Counter()
    action_counts = Counter()
    winners_by_color = Counter()
    openings = Counter()

    for game in _iter_jsonl(path):
        games += 1
        outcome = str(game.get("outcome", "unknown"))
        outcomes[outcome] += 1

        try:
            plies = int(game.get("plies", 0))
            if plies < 0:
                raise ValueError
        except (TypeError, ValueError):
            invalid_records += 1
            plies = 0
        total_plies += plies

        challenger_color = str(game.get("challenger_color", "unknown"))
        if outcome == "challenger":
            winners_by_color[challenger_color] += 1

        opening = game.get("opening_index")
        if opening is not None:
            openings[str(opening)] += 1

        actions = game.get("action_counts", {})
        if isinstance(actions, dict):
            for action, count in actions.items():
                try:
                    value = int(count)
                    if value < 0:
                        raise ValueError
                except (TypeError, ValueError):
                    invalid_records += 1
                    continue
                action_counts[str(action)] += value
        else:
            invalid_records += 1

    average_plies = total_plies / games if games else 0.0
    challenger_wins = outcomes.get("challenger", 0)
    baseline_wins = outcomes.get("baseline", 0)
    draws = outcomes.get("draw", 0)

    return {
        "games": games,
        "invalid_records": invalid_records,
        "challenger_wins": challenger_wins,
        "baseline_wins": baseline_wins,
        "draws": draws,
        "unknown_outcomes": outcomes.get("unknown", 0),
        "margin": challenger_wins - baseline_wins,
        "challenger_win_rate": challenger_wins / games if games else 0.0,
        "average_plies": average_plies,
        "action_counts": dict(action_counts),
        "challenger_wins_by_color": dict(winners_by_color),
        "openings": dict(openings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisa jogos JSONL produzidos pela Arena")
    parser.add_argument("input", type=Path, help="Ficheiro JSONL da Arena")
    parser.add_argument("--output", type=Path, help="Escreve o resumo em JSON")
    args = parser.parse_args()

    summary = analisar_partidas(args.input)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Relatório escrito em: {args.output}")

    return 0 if summary["invalid_records"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
