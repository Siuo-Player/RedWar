"""Attach observational Strength context diagnostics to Arena artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.analytics.strength_context_effects import summarize_strength_context_effects


def enrich_arena_summary(results_path: str | Path, summary_path: str | Path | None = None) -> dict[str, Any]:
    """Add context diagnostics to an existing Arena summary JSON artifact.

    The input JSONL is treated as the source of truth for game observations. The
    operation is descriptive only and never changes promotion or rating fields.
    """
    results = Path(results_path)
    if not results.is_file():
        raise FileNotFoundError(results)

    games: list[dict[str, Any]] = []
    with results.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid Arena JSONL at line {line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Arena record at line {line_number} must be an object")
            games.append(record)

    diagnostics = summarize_strength_context_effects(games)

    if summary_path is None:
        summary_path = results.with_suffix(results.suffix + ".summary.json")
    summary = Path(summary_path)
    if not summary.is_file():
        raise FileNotFoundError(summary)

    payload = json.loads(summary.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Arena summary must be a JSON object")

    payload["strength_context_diagnostics"] = diagnostics
    summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Attach Strength context diagnostics to an Arena summary")
    parser.add_argument("results", help="Arena JSONL game records")
    parser.add_argument("--summary", help="Arena summary JSON; defaults to <results>.summary.json")
    args = parser.parse_args()
    enrich_arena_summary(args.results, args.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
