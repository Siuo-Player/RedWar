import json

import pytest

from tools.analytics.promotion_gate import load_games
from tools.analytics.strength_statistics import MAX_GAMES, PROMOTION_STAGES, PairedGame, evaluate_promotion


def _records(pairs: int, first: str = "challenger", second: str = "baseline") -> list[dict]:
    rows: list[dict] = []
    for pair_index in range(pairs):
        pair_id = f"pair-{pair_index}"
        seed = 50_000 + pair_index
        rows.extend(
            [
                {
                    "valid": True,
                    "pair_id": pair_id,
                    "seed": seed,
                    "challenger_color": "white",
                    "outcome": first,
                    "game_index": pair_index * 2,
                },
                {
                    "valid": True,
                    "pair_id": pair_id,
                    "seed": seed,
                    "challenger_color": "black",
                    "outcome": second,
                    "game_index": pair_index * 2 + 1,
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


def test_gate_constants_match_methodology():
    assert PROMOTION_STAGES == (96, 192, 320, 512)
    assert MAX_GAMES == 512


def test_gate_accepts_and_does_not_require_positive_margin_constant(tmp_path):
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
