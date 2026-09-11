import json

import pytest

from tools.analytics.promotion_gate import evaluate_sequential_promotion, load_games
from tools.analytics.strength_statistics import MAX_GAMES, PROMOTION_STAGES, PairedGame, evaluate_promotion


PROVENANCE = {
    "challenger_version": "head",
    "baseline_version": "base",
    "rules_version": "rules-v1",
    "node_budget": 10_000,
    "opening_bank_version": "canonical-promotion-bank-v1",
    "opening_policy": "fresh-opening-pairs-only",
    "colour_policy": "challenger-white-then-black-per-pair",
    "termination_policy": "game_over_or_500_plies",
    "strength_decision": "external-promotion-gate",
    "wall_clock_role": "diagnostic-only",
}


def _records(pairs: int, first: str = "challenger", second: str = "baseline", *, provenance=None, pair_start: int = 0) -> list[dict]:
    experiment = dict(PROVENANCE if provenance is None else provenance)
    rows: list[dict] = []
    for local_index in range(pairs):
        pair_index = pair_start + local_index
        pair_id = f"pair-{pair_index}"
        seed = 50_000 + pair_index
        rows.extend(
            [
                {
                    "valid": True,
                    "pair_id": pair_id,
                    "pair_member": 0,
                    "seed": seed,
                    "challenger_color": "white",
                    "outcome": first,
                    "game_index": pair_index * 2,
                    "experiment": experiment,
                },
                {
                    "valid": True,
                    "pair_id": pair_id,
                    "pair_member": 1,
                    "seed": seed,
                    "challenger_color": "black",
                    "outcome": second,
                    "game_index": pair_index * 2 + 1,
                    "experiment": experiment,
                },
            ]
        )
    return rows


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_load_games_rejects_draws(tmp_path):
    path = tmp_path / "arena.jsonl"
    _write_jsonl(path, _records(1, "draw", "challenger"))
    with pytest.raises(ValueError, match="non-binary"):
        load_games([str(path)])


def test_load_games_reads_complete_binary_pairs(tmp_path):
    path = tmp_path / "arena.jsonl"
    _write_jsonl(path, _records(3))
    games = load_games([str(path)])
    assert len(games) == 6
    assert all(isinstance(game, PairedGame) for game in games)


def test_load_games_rejects_missing_provenance(tmp_path):
    path = tmp_path / "arena.jsonl"
    row = _records(1)[0]
    row.pop("experiment")
    _write_jsonl(path, [row])
    with pytest.raises(ValueError, match="missing experiment provenance"):
        load_games([str(path)])


def test_load_games_rejects_mixed_experiment_provenance(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    alternate = dict(PROVENANCE)
    alternate["node_budget"] = 20_000
    _write_jsonl(first, _records(1))
    _write_jsonl(second, _records(1, provenance=alternate, pair_start=1))
    with pytest.raises(ValueError, match="mixed experiment provenance"):
        load_games([str(first), str(second)])


def test_load_games_rejects_duplicate_game_index(tmp_path):
    path = tmp_path / "arena.jsonl"
    rows = _records(2)
    rows[2]["game_index"] = rows[0]["game_index"]
    _write_jsonl(path, rows)
    with pytest.raises(ValueError, match="duplicate game_index"):
        load_games([str(path)])


def test_load_games_rejects_invalid_pair_member_colour(tmp_path):
    path = tmp_path / "arena.jsonl"
    rows = _records(1)
    rows[1]["challenger_color"] = "white"
    _write_jsonl(path, rows)
    with pytest.raises(ValueError, match="pair_member=1"):
        load_games([str(path)])


def test_gate_constants_match_methodology():
    assert PROMOTION_STAGES == (96, 192, 320, 512)
    assert MAX_GAMES == 512


def test_gate_accepts_without_positive_margin_constant(tmp_path):
    path = tmp_path / "arena.jsonl"
    _write_jsonl(path, _records(48, "challenger", "challenger"))
    games = load_games([str(path)])
    decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=9)
    assert decision.decision == "accept"
    assert decision.lower_bound_elo is not None
    assert decision.lower_bound_elo > 0.0


def test_gate_rejects_at_max_when_pairs_are_balanced(tmp_path):
    path = tmp_path / "arena.jsonl"
    _write_jsonl(path, _records(256, "challenger", "baseline"))
    games = load_games([str(path)])
    decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=10)
    assert decision.decision == "reject"
    assert decision.games == MAX_GAMES


def test_gate_keeps_baseline_when_first_stage_is_inconclusive(tmp_path):
    path = tmp_path / "arena.jsonl"
    _write_jsonl(path, _records(48, "challenger", "baseline"))
    games = load_games([str(path)])
    decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=11)
    assert decision.decision == "continue"
    assert decision.reason.startswith("insufficient evidence")


def test_sequential_gate_stops_at_first_accept_even_if_final_snapshot_regresses(tmp_path):
    path = tmp_path / "arena.jsonl"
    rows = _records(48, "challenger", "challenger")
    rows += _records(208, "baseline", "baseline", pair_start=48)
    _write_jsonl(path, rows)
    games = load_games([str(path)])

    final_snapshot = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=12)
    sequential = evaluate_sequential_promotion(games, bootstrap_replicates=100, bootstrap_seed=12)

    assert final_snapshot.decision == "reject"
    assert sequential.decision == "accept"
    assert sequential.games == 96
    assert sequential.stage_games == 96
