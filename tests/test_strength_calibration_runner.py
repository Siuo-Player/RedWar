import json
from pathlib import Path

import pytest

from tools.analytics.strength_calibration_runner import build_arena_command, resolve_games

PLAN = Path(__file__).parents[1] / "data" / "arena" / "strength" / "plans" / "2026-08-27-replication-v3.json"


def _run_spec() -> dict:
    payload = json.loads(PLAN.read_text(encoding="utf-8"))
    return next(item for item in payload["runs"] if item["sequence"] == 0)


def test_runner_requires_positive_even_games():
    assert resolve_games(100) == 100
    with pytest.raises(ValueError):
        resolve_games(0)
    with pytest.raises(ValueError):
        resolve_games(101)


def test_control_command_binds_frozen_revision_seed_set_and_disables_promotion():
    run = _run_spec()
    command = build_arena_command(
        run,
        challenger_engine="/tmp/challenger",
        baseline_engine="/tmp/baseline",
        games=100,
        nodes=10_000,
        selection_policy="paired-fixed-openings",
        controller_population="Ares-v1-vs-baseline-v1",
        skill_context="fixed-node-budget",
        results_path="/tmp/run.jsonl",
    )

    assert "--challenger-version" in command
    assert command[command.index("--challenger-version") + 1] == run["challenger_version"]
    assert command[command.index("--baseline-version") + 1] == run["baseline_version"]
    assert run["challenger_version"] == run["baseline_version"]
    assert command[command.index("--margem-vitorias") + 1] == "101"
    assert command[command.index("--opening-seeds") + 1] == ",".join(str(seed) for seed in run["opening_seeds"])
    assert command[command.index("--seed-policy") + 1] == run["seed_policy"]
    assert command[command.index("--seed-generation-rule") + 1] == run["seed_generation_rule"]


def test_calibration_runner_rejects_non_matching_node_budget():
    run = _run_spec()
    with pytest.raises(ValueError):
        build_arena_command(
            run,
            challenger_engine="/tmp/challenger",
            baseline_engine="/tmp/baseline",
            games=100,
            nodes=9_999,
            selection_policy="paired-fixed-openings",
            controller_population="Ares-v1-vs-baseline-v1",
            skill_context="fixed-node-budget",
            results_path="/tmp/run.jsonl",
        )
