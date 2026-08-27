"""Execute one predeclared RedWar Strength calibration run.

This wrapper binds a concrete Arena execution to a validated calibration-plan run.
It does not change Arena semantics or grant promotion authority. Calibration runs
use an impossible promotion threshold and are persisted through the existing
scientific dataset builder with the declared experiment/run identifiers.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analytics.strength_calibration_protocol import validate_calibration_plan


DEFAULT_GAMES = 100


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


def _resolve_games(run: dict[str, Any], games: int | None) -> int:
    resolved = games if games is not None else run.get("games", DEFAULT_GAMES)
    if not isinstance(resolved, int) or isinstance(resolved, bool) or resolved <= 0 or resolved % 2:
        raise ValueError("games must be a positive even integer")
    return resolved


def build_arena_command(
    run: dict[str, Any],
    *,
    challenger_engine: str,
    baseline_engine: str,
    games: int,
    nodes: int,
    opening_seeds: list[int],
    results_path: str,
) -> list[str]:
    challenger_version = str(run["challenger_version"])
    baseline_version = str(run["baseline_version"])
    rules_version = str(run["rules_version"])
    if run["role"] == "calibration" and challenger_version != baseline_version:
        raise ValueError("same-engine calibration runs require identical challenger/baseline revisions")
    if nodes != int(run["node_budget"]):
        raise ValueError("nodes must match the frozen calibration-plan node_budget")
    if not opening_seeds:
        raise ValueError("opening_seeds must not be empty")

    # games + 1 is strictly above the maximum possible win-margin for this run.
    # This keeps the Arena's legacy promotion calculation from ever evaluating
    # true while retaining its existing game/result semantics.
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
    results_path: str | Path,
    dataset_path: str | Path,
    games: int | None = None,
) -> dict[str, Any]:
    payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    validate_calibration_plan(payload)
    run = get_run(payload, run_id)
    if not run.get("execution_ready", False):
        raise ValueError(f"run {run_id} is not execution-ready: {run.get('blocker', 'no blocker recorded')}")
    if run["role"] != "calibration":
        raise ValueError("this runner executes calibration runs only")

    resolved_games = _resolve_games(run, games)
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
        opening_seeds=opening_seeds,
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
        "--selection-policy", str(run["opening_policy"]),
        "--controller-population", "Ares-v1-vs-baseline-v1",
        "--skill-context", "fixed-node-budget",
        "--experiment-id", str(run["experiment_id"]),
        "--run-id", str(run["run_id"]),
        "--head-sha", str(run["challenger_version"]),
        "--output", str(dataset),
    ]
    dataset_completed = subprocess.run(dataset_command, cwd=ROOT, check=False)
    if dataset_completed.returncode != 0:
        raise RuntimeError(f"Strength dataset build failed with exit code {dataset_completed.returncode}")

    manifest = {
        "schema_version": "redwar-strength-calibration-runner-v1",
        "experiment_id": run["experiment_id"],
        "run_id": run["run_id"],
        "plan_path": str(Path(plan_path)),
        "challenger_engine": str(Path(challenger_engine).resolve()),
        "baseline_engine": str(Path(baseline_engine).resolve()),
        "games": resolved_games,
        "node_budget": nodes,
        "opening_seeds": opening_seeds,
        "promotion_authority": False,
        "arena_exit_code": completed.returncode,
        "raw_results": str(results),
        "arena_summary": str(summary_path),
        "dataset": str(dataset),
    }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute a predeclared RedWar Strength calibration run")
    parser.add_argument("plan")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--games", type=int)
    args = parser.parse_args()

    result = run_calibration(
        args.plan,
        args.run_id,
        challenger_engine=args.challenger_engine,
        baseline_engine=args.baseline_engine,
        results_path=args.results,
        dataset_path=args.dataset,
        games=args.games,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
