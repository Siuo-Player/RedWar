"""Execute one predeclared RedWar Strength calibration run.

This wrapper binds a concrete Arena execution to a validated calibration-plan run.
It does not change Arena semantics or grant promotion authority. Calibration runs
use an impossible promotion threshold and are persisted through the existing
scientific dataset builder with the declared experiment/run identifiers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analytics.strength_calibration_protocol import validate_calibration_plan

HARNESS_PATHS = (
    "tools/analytics/strength_calibration_runner.py",
    "tools/analytics/strength_calibration_protocol.py",
    "tools/analytics/arena_tournament.py",
    "tools/analytics/strength_dataset.py",
)


def load_plan(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    payload = json.loads(source.read_text(encoding="utf-8"))
    return validate_calibration_plan(payload)


def get_run(plan: dict[str, Any], run_id: str) -> dict[str, Any]:
    for run in plan["runs"]:
        if run["run_id"] == run_id:
            return dict(run)
    raise ValueError(f"unknown run_id: {run_id}")


def resolve_games(games: int) -> int:
    if not isinstance(games, int) or isinstance(games, bool) or games <= 0 or games % 2:
        raise ValueError("games must be a positive even integer")
    return games


def _git_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("unable to resolve the calibration harness Git commit")
    return completed.stdout.strip()


def _git_blob_sha(relative_path: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative_path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"unable to resolve harness blob SHA for {relative_path}")
    return completed.stdout.strip()


def _sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_run_provenance(
    output_path: str | Path,
    *,
    plan_path: str | Path,
    run: dict[str, Any],
    selection_policy: str,
    controller_population: str,
    skill_context: str,
    games: int,
    nodes: int,
    results_path: str | Path,
    summary_path: str | Path,
    dataset_path: str | Path,
) -> Path:
    results = Path(results_path)
    dataset = Path(dataset_path)
    summary = Path(summary_path)
    dataset_payload = json.loads(dataset.read_text(encoding="utf-8"))
    manifest = {
        "schema_version": "redwar-strength-run-provenance-v1",
        "experiment_id": str(run["experiment_id"]),
        "run_id": str(run["run_id"]),
        "plan": {"path": str(Path(plan_path).resolve()), "sha256": _sha256_file(plan_path)},
        "execution": {
            "harness_git_sha": _git_sha(),
            "harness_file_blobs": {path: _git_blob_sha(path) for path in HARNESS_PATHS},
            "challenger_engine_version": str(run["challenger_version"]),
            "baseline_engine_version": str(run["baseline_version"]),
            "rules_version": str(run["rules_version"]),
            "games": games,
            "node_budget": nodes,
            "opening_seeds": [int(seed) for seed in run["opening_seeds"]],
            "seed_policy": str(run["seed_policy"]),
            "seed_generation_rule": str(run["seed_generation_rule"]),
            "selection_policy": selection_policy,
            "controller_population": controller_population,
            "skill_context": skill_context,
            "promotion_authority": False,
        },
        "artifacts": {
            "raw_results": {"path": str(results.resolve()), "sha256": _sha256_file(results)},
            "arena_summary": {"path": str(summary.resolve()), "sha256": _sha256_file(summary)},
            "dataset": {
                "path": str(dataset.resolve()),
                "sha256": _sha256_file(dataset),
                "canonical_sha256": dataset_payload["manifest"].get("canonical_sha256"),
            },
        },
        "status": "execution_provenance_captured_no_promotion_decision",
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def build_arena_command(
    run: dict[str, Any],
    *,
    challenger_engine: str,
    baseline_engine: str,
    games: int,
    nodes: int,
    selection_policy: str,
    controller_population: str,
    skill_context: str,
    results_path: str,
) -> list[str]:
    challenger_version = str(run["challenger_version"])
    baseline_version = str(run["baseline_version"])
    rules_version = str(run["rules_version"])
    if run["role"] == "calibration" and challenger_version != baseline_version:
        raise ValueError("same-engine calibration runs require identical challenger/baseline revisions")
    if nodes != int(run["node_budget"]):
        raise ValueError("nodes must match the frozen calibration-plan node_budget")
    if not all(isinstance(value, str) and value.strip() for value in (selection_policy, controller_population, skill_context)):
        raise ValueError("population context fields must be non-empty strings")
    opening_seeds = [int(seed) for seed in run.get("opening_seeds", [])]
    if len(opening_seeds) != 16:
        raise ValueError("calibration runner requires exactly 16 predeclared opening seeds")
    promotion_threshold = games + 1
    seed_text = ",".join(str(seed) for seed in opening_seeds)
    return [
        sys.executable,
        str(ROOT / "tools" / "analytics" / "arena_tournament.py"),
        "--challenger-engine", challenger_engine,
        "--baseline-engine", baseline_engine,
        "--challenger-version", challenger_version,
        "--baseline-version", baseline_version,
        "--rules-version", rules_version,
        "--jogos", str(games),
        "--margem-vitorias", str(promotion_threshold),
        "--nodes", str(nodes),
        "--opening-seeds", seed_text,
        "--seed-policy", str(run["seed_policy"]),
        "--seed-generation-rule", str(run["seed_generation_rule"]),
        "--results", results_path,
    ]


def run_calibration(
    plan_path: str | Path,
    run_id: str,
    *,
    challenger_engine: str,
    baseline_engine: str,
    selection_policy: str,
    controller_population: str,
    skill_context: str,
    games: int,
    results_path: str | Path,
    dataset_path: str | Path,
) -> dict[str, Any]:
    payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    plan_audit = validate_calibration_plan(payload)
    run = get_run(payload, run_id)
    if not run.get("execution_ready", False):
        raise ValueError(f"run {run_id} is not execution-ready: {run.get('blocker', 'no blocker recorded')}")
    if run["role"] != "calibration":
        raise ValueError("this runner executes calibration runs only")

    resolved_games = resolve_games(games)
    nodes = int(run["node_budget"])
    opening_seeds = [int(seed) for seed in run.get("opening_seeds", [])]
    if len(opening_seeds) != 16:
        raise ValueError("calibration runner requires exactly 16 predeclared opening seeds")

    results = Path(results_path)
    results.parent.mkdir(parents=True, exist_ok=True)
    command = build_arena_command(
        run,
        challenger_engine=challenger_engine,
        baseline_engine=baseline_engine,
        games=resolved_games,
        nodes=nodes,
        selection_policy=selection_policy,
        controller_population=controller_population,
        skill_context=skill_context,
        results_path=str(results),
    )
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode not in (0, 1):
        raise RuntimeError(f"Arena execution failed with unexpected exit code {completed.returncode}")

    summary_path = Path(f"{results}.summary.json")
    if not summary_path.is_file():
        raise RuntimeError(f"Arena summary was not produced: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("promoted") is not False:
        raise RuntimeError("calibration run produced a promotion=true summary; evidence is rejected")

    dataset = Path(dataset_path)
    dataset.parent.mkdir(parents=True, exist_ok=True)
    dataset_command = [
        sys.executable,
        str(ROOT / "tools" / "analytics" / "strength_dataset.py"),
        "build",
        str(results),
        "--population-id", str(run["population_id"]),
        "--selection-policy", selection_policy,
        "--controller-population", controller_population,
        "--skill-context", skill_context,
        "--experiment-id", str(run["experiment_id"]),
        "--run-id", str(run["run_id"]),
        "--head-sha", str(run["challenger_version"]),
        "--output", str(dataset),
    ]
    dataset_completed = subprocess.run(dataset_command, cwd=ROOT, check=False)
    if dataset_completed.returncode != 0:
        raise RuntimeError(f"Strength dataset build failed with exit code {dataset_completed.returncode}")

    provenance_path = dataset.with_name(f"{dataset.stem}.run-provenance.json")
    _write_run_provenance(
        provenance_path,
        plan_path=plan_path,
        run=run,
        selection_policy=selection_policy,
        controller_population=controller_population,
        skill_context=skill_context,
        games=resolved_games,
        nodes=nodes,
        results_path=results,
        summary_path=summary_path,
        dataset_path=dataset,
    )

    return {
        "schema_version": "redwar-strength-calibration-runner-v2",
        "experiment_id": run["experiment_id"],
        "run_id": run["run_id"],
        "plan_status": "validated",
        "plan_runs": plan_audit["run_count"],
        "challenger_engine": str(Path(challenger_engine).resolve()),
        "baseline_engine": str(Path(baseline_engine).resolve()),
        "games": resolved_games,
        "node_budget": nodes,
        "opening_seeds": opening_seeds,
        "selection_policy": selection_policy,
        "controller_population": controller_population,
        "skill_context": skill_context,
        "promotion_authority": False,
        "arena_exit_code": completed.returncode,
        "raw_results": str(results),
        "arena_summary": str(summary_path),
        "dataset": str(dataset),
        "run_provenance": str(provenance_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute a predeclared RedWar Strength calibration run")
    parser.add_argument("plan")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--games", required=True, type=int)
    parser.add_argument("--selection-policy", required=True)
    parser.add_argument("--controller-population", required=True)
    parser.add_argument("--skill-context", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()

    result = run_calibration(
        args.plan,
        args.run_id,
        challenger_engine=args.challenger_engine,
        baseline_engine=args.baseline_engine,
        games=args.games,
        selection_policy=args.selection_policy,
        controller_population=args.controller_population,
        skill_context=args.skill_context,
        results_path=args.results,
        dataset_path=args.dataset,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
