"""Build a canonical scientific dataset from one raw Arena JSONL experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.analytics.arena_experiment_validation import validate_experiment_records
from tools.analytics.arena_strength_audit import build_independent_pair_units
from tools.analytics.strength_population import StrengthPopulationContext

DATASET_SCHEMA_VERSION = "redwar-strength-dataset-v1"
EVIDENCE_CLASS = "real_arena"
GAME_FIELDS = (
    "game_index", "pair_id", "pair_member", "challenger_color",
    "baseline_color", "opening_index", "seed", "outcome", "valid",
    "termination_reason",
)


def _load(path: str | Path) -> tuple[list[dict[str, Any]], str]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    raw = source.read_bytes()
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid Arena JSONL at line {line_number}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"Arena record at line {line_number} must be an object")
        records.append(record)
    if not records:
        raise ValueError("Arena JSONL must contain at least one game record")
    return records, hashlib.sha256(raw).hexdigest()


def build_dataset(
    results_path: str | Path,
    *,
    population_id: str,
    selection_policy: str,
    controller_population: str,
    skill_context: str,
    workflow_run_id: int | None = None,
    artifact_id: int | None = None,
    head_sha: str | None = None,
) -> dict[str, Any]:
    records, raw_sha256 = _load(results_path)
    context = StrengthPopulationContext(
        population_id=population_id,
        selection_policy=selection_policy,
        controller_population=controller_population,
        skill_context=skill_context,
    )
    first = records[0].get("experiment")
    if not isinstance(first, dict):
        raise ValueError("first Arena record is missing experiment metadata")
    experiment = dict(first)
    experiment["strength_population"] = context.to_dict()

    games = []
    for record in records:
        games.append({field: record[field] for field in GAME_FIELDS} | {"experiment": experiment})

    validation = validate_experiment_records(
        games, experiment, require_strength_population=True
    )
    units, incomplete = build_independent_pair_units(games)
    if incomplete:
        raise ValueError(
            "cannot build a scientific Strength dataset with incomplete pairs: "
            + ", ".join(incomplete)
        )

    source: dict[str, Any] = {"raw_sha256": raw_sha256, "raw_path": str(results_path)}
    if workflow_run_id is not None:
        source["workflow_run_id"] = int(workflow_run_id)
    if artifact_id is not None:
        source["artifact_id"] = int(artifact_id)
    if head_sha is not None:
        source["head_sha"] = head_sha

    manifest = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "source_artifact": source,
        "experiment": experiment,
        "validation": validation,
        "independent_unit_policy": "one complete colour-inverted A/B pair is one independent resampling unit",
        "independent_units": len(units),
        "game_records": len(games),
        "scientific_game_fields": list(GAME_FIELDS),
    }
    bundle = {"manifest": manifest, "games": games, "independent_units": units}
    canonical = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["canonical_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a reproducible RedWar Strength dataset")
    parser.add_argument("results")
    parser.add_argument("--population-id", required=True)
    parser.add_argument("--selection-policy", required=True)
    parser.add_argument("--controller-population", required=True)
    parser.add_argument("--skill-context", required=True)
    parser.add_argument("--workflow-run-id", type=int)
    parser.add_argument("--artifact-id", type=int)
    parser.add_argument("--head-sha")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = build_dataset(
        args.results,
        population_id=args.population_id,
        selection_policy=args.selection_policy,
        controller_population=args.controller_population,
        skill_context=args.skill_context,
        workflow_run_id=args.workflow_run_id,
        artifact_id=args.artifact_id,
        head_sha=args.head_sha,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(bundle["manifest"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
