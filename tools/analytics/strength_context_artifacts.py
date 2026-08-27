"""Attach observational Strength context diagnostics to Arena artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# This module is also invoked directly by CI as ``python tools/analytics/...py``.
# In that mode Python puts ``tools/analytics`` on sys.path rather than the
# repository root, so the top-level ``tools`` package would otherwise be
# unimportable. Add the repository root explicitly before package imports.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from tools.analytics.strength_context_effects import summarize_strength_context_effects
from tools.analytics.strength_population import StrengthPopulationContext, validate_population_context


def enrich_arena_summary(
    results_path: str | Path,
    summary_path: str | Path | None = None,
    strength_population: dict[str, Any] | StrengthPopulationContext | None = None,
    enriched_results_path: str | Path | None = None,
) -> dict[str, Any]:
    """Attach population context and observational diagnostics without rewriting raw results."""
    results = Path(results_path)
    if not results.is_file():
        raise FileNotFoundError(results)

    if isinstance(strength_population, StrengthPopulationContext):
        normalized_population = strength_population.to_dict()
    elif isinstance(strength_population, dict):
        normalized_population = validate_population_context(strength_population).to_dict()
    elif strength_population is None:
        normalized_population = None
    else:
        raise TypeError("strength_population must be a mapping or StrengthPopulationContext")

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
            record = dict(record)
            if normalized_population is not None:
                experiment = record.get("experiment")
                if not isinstance(experiment, dict):
                    raise ValueError(f"Arena record at line {line_number} is missing experiment metadata")
                experiment = dict(experiment)
                existing = experiment.get("strength_population")
                if existing is not None and existing != normalized_population:
                    raise ValueError(
                        f"Arena record at line {line_number} has conflicting strength population context"
                    )
                experiment["strength_population"] = normalized_population
                record["experiment"] = experiment
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

    if normalized_population is not None:
        existing = payload.get("strength_population")
        if existing is not None and existing != normalized_population:
            raise ValueError("Arena summary has conflicting strength population context")
        payload["strength_population"] = normalized_population

    payload["strength_context_diagnostics"] = diagnostics
    summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if normalized_population is not None:
        if enriched_results_path is None:
            enriched_results_path = results.with_name(results.stem + ".context" + results.suffix)
        enriched = Path(enriched_results_path)
        enriched.parent.mkdir(parents=True, exist_ok=True)
        with enriched.open("w", encoding="utf-8") as handle:
            for game in games:
                handle.write(json.dumps(game, ensure_ascii=False, separators=(",", ":")) + "\n")
        payload["strength_context_results"] = str(enriched)
        summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return payload


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Attach Strength context diagnostics to an Arena summary")
    parser.add_argument("results", help="Arena JSONL game records")
    parser.add_argument("--summary", help="Arena summary JSON; defaults to <results>.summary.json")
    parser.add_argument("--context-output", help="Enriched JSONL output; raw Arena JSONL remains untouched")
    parser.add_argument("--population-id")
    parser.add_argument("--selection-policy")
    parser.add_argument("--controller-population")
    parser.add_argument("--skill-context")
    args = parser.parse_args()

    context_values = (
        args.population_id,
        args.selection_policy,
        args.controller_population,
        args.skill_context,
    )
    if any(value is not None for value in context_values):
        if not all(value is not None for value in context_values):
            raise SystemExit("all Strength population context arguments are required together")
        context = StrengthPopulationContext(
            population_id=args.population_id,
            selection_policy=args.selection_policy,
            controller_population=args.controller_population,
            skill_context=args.skill_context,
        )
    else:
        context = None

    enrich_arena_summary(args.results, args.summary, context, args.context_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
