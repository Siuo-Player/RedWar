"""Build a canonical scientific dataset from one raw Arena JSONL experiment.

The raw Arena JSONL remains the source of truth. The derived dataset keeps one
experiment manifest, scientific per-game fields, and one independent unit per
complete colour-inverted pair. It is evidence storage, not a promotion gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.analytics.arena_experiment_validation import validate_experiment_records
from tools.analytics.arena_strength_audit import build_independent_pair_units
from tools.analytics.strength_empirical_audit import empirical_paired_uncertainty_audit
from tools.analytics.strength_population import StrengthPopulationContext, validate_population_context

DATASET_SCHEMA_VERSION = "redwar-strength-dataset-v1"
EVIDENCE_CLASS = "real_arena"
GAME_FIELDS = (
    "game_index", "pair_id", "pair_member", "challenger_color",
    "baseline_color", "opening_index", "seed", "outcome", "valid",
    "termination_reason",
)


def _load_raw(path: str | Path) -> tuple[list[dict[str, Any]], str]:
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


def _validate_dataset_games(games: list[dict[str, Any]], experiment: dict[str, Any]) -> dict[str, Any]:
    records = [dict(game, experiment=experiment) for game in games]
    return validate_experiment_records(records, experiment, require_strength_population=True)


def _canonical_digest(bundle: dict[str, Any]) -> str:
    payload = json.loads(json.dumps(bundle, ensure_ascii=False))
    payload["manifest"].pop("canonical_sha256", None)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    records, raw_sha256 = _load_raw(results_path)
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
    games = [{field: record[field] for field in GAME_FIELDS} for record in records]
    validation = _validate_dataset_games(games, experiment)
    complete_records = [dict(game, experiment=experiment) for game in games]
    units, incomplete = build_independent_pair_units(complete_records)
    if incomplete:
        raise ValueError(
            "cannot build a scientific Strength dataset with incomplete pairs: "
            + ", ".join(incomplete)
        )

    source: dict[str, Any] = {"raw_sha256": raw_sha256}
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
        "analysis_status": "raw_real_arena_data_preserved; no_promotion_decision",
    }
    bundle = {"manifest": manifest, "games": games, "independent_units": units}
    manifest["canonical_sha256"] = _canonical_digest(bundle)
    return bundle


def audit_dataset(bundle: dict[str, Any], *, bootstrap_samples: int = 2000, seed: int = 0) -> dict[str, Any]:
    """Consume stored independent units with the existing descriptive audit."""
    loaded = load_dataset_payload(bundle)
    audit = empirical_paired_uncertainty_audit(
        loaded["independent_units"], bootstrap_samples=bootstrap_samples, seed=seed
    )
    return {
        "evidence_class": EVIDENCE_CLASS,
        "dataset_schema_version": loaded["manifest"]["schema_version"],
        "units": len(loaded["independent_units"]),
        "audit": audit,
        "status": "descriptive_empirical_audit_only",
    }


def load_dataset_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("manifest"), dict):
        raise ValueError("Strength dataset must contain a manifest")
    manifest = payload["manifest"]
    required = {"schema_version", "evidence_class", "experiment", "validation", "independent_units", "game_records"}
    missing = sorted(required - manifest.keys())
    if missing:
        raise ValueError(f"Strength dataset manifest is missing required fields: {missing}")
    if manifest.get("schema_version") != DATASET_SCHEMA_VERSION:
        raise ValueError("unsupported Strength dataset schema version")
    if manifest.get("evidence_class") != EVIDENCE_CLASS:
        raise ValueError("Strength dataset evidence class must be real_arena")
    if not isinstance(manifest.get("experiment"), dict):
        raise ValueError("Strength dataset manifest experiment must be an object")
    validate_population_context(manifest["experiment"].get("strength_population"))
    stored_digest = manifest.get("canonical_sha256")
    if not isinstance(stored_digest, str) or not stored_digest:
        raise ValueError("Strength dataset manifest is missing canonical_sha256")
    if _canonical_digest(payload) != stored_digest:
        raise ValueError("Strength dataset canonical hash does not match its contents")

    games = payload.get("games")
    units = payload.get("independent_units")
    if not isinstance(games, list) or not isinstance(units, list):
        raise ValueError("Strength dataset games and independent_units must be lists")
    if manifest["game_records"] != len(games):
        raise ValueError("Strength dataset manifest game_records does not match games")
    if manifest["independent_units"] != len(units):
        raise ValueError("Strength dataset manifest independent_units does not match units")

    validation = _validate_dataset_games(games, manifest["experiment"])
    if validation != manifest["validation"]:
        raise ValueError("dataset validation summary does not match its game records")
    rebuilt, incomplete = build_independent_pair_units(
        [dict(game, experiment=manifest["experiment"]) for game in games]
    )
    if incomplete:
        raise ValueError("dataset contains incomplete independent pairs: " + ", ".join(incomplete))
    if units != rebuilt:
        raise ValueError("dataset independent units do not match its game records")
    return payload


def load_dataset(path: str | Path) -> dict[str, Any]:
    dataset = Path(path)
    if not dataset.is_file():
        raise FileNotFoundError(dataset)
    payload = json.loads(dataset.read_text(encoding="utf-8"))
    return load_dataset_payload(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or audit a RedWar Strength dataset")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("results")
    build.add_argument("--population-id", required=True)
    build.add_argument("--selection-policy", required=True)
    build.add_argument("--controller-population", required=True)
    build.add_argument("--skill-context", required=True)
    build.add_argument("--workflow-run-id", type=int)
    build.add_argument("--artifact-id", type=int)
    build.add_argument("--head-sha")
    build.add_argument("--output", required=True)

    audit = sub.add_parser("audit")
    audit.add_argument("dataset")
    audit.add_argument("--bootstrap-samples", type=int, default=2000)
    audit.add_argument("--seed", type=int, default=0)

    args = parser.parse_args()
    if args.command == "build":
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
    else:
        result = audit_dataset(load_dataset(args.dataset), bootstrap_samples=args.bootstrap_samples, seed=args.seed)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
