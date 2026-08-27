"""Reproducible descriptive report for raw Arena Strength datasets.

Strict mode uses the current Arena/Strength validation contract. Legacy mode is
explicitly opt-in and only supports historical artifacts whose schema predates
per-game validity/termination provenance. Legacy output is never presented as
current validated Strength evidence.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

from tools.analytics.arena_experiment_validation import REQUIRED_GAME_FIELDS, validate_experiment_records
from tools.analytics.arena_strength_audit import audit_arena_results, build_independent_pair_units, load_arena_records
from tools.analytics.sprt_calibration import calibrate_sprt_baseline
from tools.analytics.sprt import SPRTConfig, evaluate_sequence
from tools.analytics.strength_empirical_audit import empirical_paired_uncertainty_audit

OUTCOME_MAP = {"challenger": "win", "baseline": "loss", "draw": "draw"}


def _load_raw(path: str | Path) -> list[dict[str, Any]]:
    raw = Path(path)
    if not raw.is_file():
        raise FileNotFoundError(raw)
    records: list[dict[str, Any]] = []
    with raw.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
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
    return records


def _legacy_missing_fields(records: Sequence[dict[str, Any]]) -> list[str]:
    missing: set[str] = set()
    for record in records:
        missing.update(REQUIRED_GAME_FIELDS - record.keys())
    return sorted(missing)


def _legacy_structural_audit(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Validate the subset of the current contract that legacy artifacts expose."""
    first = records[0]
    experiment = first.get("experiment")
    if not isinstance(experiment, dict):
        raise ValueError("legacy Arena artifact is missing experiment metadata")

    expected_games = experiment.get("games")
    if not isinstance(expected_games, int) or isinstance(expected_games, bool):
        raise ValueError("legacy Arena metadata.games must be an integer")
    if len(records) != expected_games:
        raise ValueError(f"expected {expected_games} games, got {len(records)}")

    required_metadata = ("challenger_version", "baseline_version", "rules_version", "node_budget", "opening_count")
    for field in required_metadata:
        if field not in experiment:
            raise ValueError(f"legacy Arena experiment missing {field}")

    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    outcomes: list[str] = []
    for expected_index, record in enumerate(records):
        if record.get("game_index") != expected_index:
            raise ValueError(f"game index sequence broken at {expected_index}")
        if record.get("outcome") not in OUTCOME_MAP:
            raise ValueError(f"legacy game {expected_index} has invalid outcome")

        game_experiment = record.get("experiment")
        if game_experiment != experiment:
            raise ValueError(f"legacy game {expected_index}: experiment metadata mismatch")

        pair_id = record.get("pair_id")
        if not isinstance(pair_id, str):
            raise ValueError(f"legacy game {expected_index}: missing pair_id")
        by_pair[pair_id].append(record)
        outcomes.append(OUTCOME_MAP[str(record["outcome"])])

    malformed_pairs: list[str] = []
    inverted_color_pairs = 0
    same_seed_pairs = 0
    for pair_id, games in sorted(by_pair.items()):
        if len(games) != 2:
            malformed_pairs.append(pair_id)
            continue
        first_game, second_game = sorted(games, key=lambda item: int(item.get("pair_member", -1)))
        if {first_game.get("challenger_color"), second_game.get("challenger_color")} == {"white", "black"}:
            inverted_color_pairs += 1
        if first_game.get("seed") == second_game.get("seed") and first_game.get("opening_index") == second_game.get("opening_index"):
            same_seed_pairs += 1

    return {
        "games": len(records),
        "pairs": len(by_pair),
        "malformed_pair_ids": malformed_pairs,
        "colour_inverted_pairs": inverted_color_pairs,
        "same_seed_and_opening_pairs": same_seed_pairs,
        "outcomes": {name: outcomes.count(name) for name in ("win", "loss", "draw")},
        "missing_current_game_fields": _legacy_missing_fields(records),
        "validation_status": "legacy_structural_audit_only",
    }


def _run_sprt(outcomes: Sequence[str], elo1_values: Sequence[float], alpha: float, beta: float, draw_rate: float) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for elo1 in elo1_values:
        config = SPRTConfig(elo0=0.0, elo1=elo1, alpha=alpha, beta=beta, draw_rate=draw_rate)
        result = evaluate_sequence(outcomes, config)
        reports.append(
            {
                "elo0": config.elo0,
                "elo1": config.elo1,
                "alpha": config.alpha,
                "beta": config.beta,
                "draw_rate": config.draw_rate,
                "decision": result.decision,
                "llr": result.llr,
                "games_used": result.games,
                "wins": result.wins,
                "losses": result.losses,
                "draws": result.draws,
                "lower_boundary": result.lower_boundary,
                "upper_boundary": result.upper_boundary,
            }
        )
    return reports


def analyze_real_arena(
    results_path: str | Path,
    *,
    allow_legacy: bool = False,
    bootstrap_samples: int = 20_000,
    seed: int = 0,
    sprt_elo1: Sequence[float] = (5.0, 100.0, 150.0),
    alpha: float = 0.05,
    beta: float = 0.05,
    draw_rate: float = 0.0,
) -> dict[str, Any]:
    """Return a strict or explicitly legacy descriptive Arena Strength report."""
    records = _load_raw(results_path)
    missing = _legacy_missing_fields(records)

    if not missing:
        strict_result = audit_arena_results(
            results_path,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        )
        outcomes = []
        for record in records:
            if record.get("valid") is True:
                outcomes.append(OUTCOME_MAP[str(record["outcome"])])
        status = "current_schema_descriptive_audit"
        validation = {"validation_status": "current_schema_validated"}
        paired = strict_result["audit"]
        experiment = strict_result["experiment"]
    else:
        if not allow_legacy:
            raise ValueError(
                "Arena artifact uses a legacy per-game schema; rerun with --allow-legacy "
                "for a descriptive historical audit"
            )
        validation = _legacy_structural_audit(records)
        outcomes = [OUTCOME_MAP[str(record["outcome"])] for record in records]
        units, incomplete = build_independent_pair_units(
            [
                {**record, "valid": True}
                for record in records
            ]
        )
        if incomplete:
            raise ValueError("legacy artifact contains malformed complete pairs: " + ", ".join(incomplete))
        paired = empirical_paired_uncertainty_audit(
            units,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        )
        experiment = dict(records[0]["experiment"])
        status = "legacy_real_arena_descriptive_calibration"

    calibration = calibrate_sprt_baseline(outcomes)
    sprt = _run_sprt(outcomes, sprt_elo1, alpha, beta, draw_rate)
    return {
        "status": status,
        "experiment": experiment,
        "validation": validation,
        "calibration": calibration,
        "paired_bootstrap": paired,
        "sprt": sprt,
        "promotion_decision": "not_evaluated",
        "raw_source": str(results_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Descriptive Strength report from raw Arena JSONL")
    parser.add_argument("results", help="Raw Arena JSONL file")
    parser.add_argument("--allow-legacy", action="store_true", help="Allow explicit descriptive analysis of pre-validity Arena artifacts")
    parser.add_argument("--bootstrap-samples", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sprt-elo1", type=float, nargs="+", default=[5.0, 100.0, 150.0])
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--beta", type=float, default=0.05)
    parser.add_argument("--draw-rate", type=float, default=0.0)
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = analyze_real_arena(
        args.results,
        allow_legacy=args.allow_legacy,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
        sprt_elo1=args.sprt_elo1,
        alpha=args.alpha,
        beta=args.beta,
        draw_rate=args.draw_rate,
    )
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
