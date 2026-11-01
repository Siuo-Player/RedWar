from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai.engine_bridge import EngineBridgeProcessExit, EngineBridgeProtocolError, EngineBridgeTimeout
from tools.analytics import arena_tournament


class RaisingBot:
    def __init__(self, exc: Exception):
        self.exc = exc

    def play(self, _state):
        raise self.exc

    def __del__(self):
        pass


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (EngineBridgeTimeout("timeout"), "timeout"),
        (EngineBridgeProcessExit("process died"), "process_engine_failure"),
        (EngineBridgeProtocolError("bad response"), "malformed_result_schema"),
        (ValueError("illegal action"), "invalid_action"),
        (RuntimeError("unparseable bestmove"), "malformed_result_schema"),
        (Exception("unexpected diagnostic failure"), "diagnostic_failure"),
    ],
)
def test_run_headless_match_classifies_execution_failures(exc: Exception, expected: str) -> None:
    game = arena_tournament.run_headless_match(
        RaisingBot(exc),
        RaisingBot(Exception("unused")),
        opening_index=0,
        opening_seed=0,
    )
    assert game["valid"] is False
    assert game["failure_reason"] == expected
    assert game["failure_exception_type"] == type(exc).__name__
    assert game["failure_detail"] == str(exc)


def test_start_tournament_persists_invalid_games_and_continues(monkeypatch, tmp_path: Path) -> None:
    class AlwaysTimeoutBot(RaisingBot):
        def __init__(self, **_kwargs):
            super().__init__(EngineBridgeTimeout("synthetic timeout"))

    monkeypatch.setattr(arena_tournament, "CppEngineBot", AlwaysTimeoutBot)
    results = tmp_path / "games.jsonl"

    result = arena_tournament.start_tournament(
        challenger_engine="challenger",
        baseline_engine="baseline",
        num_games=2,
        win_threshold=1,
        nodes=10,
        results_path=str(results),
        challenger_version="synthetic-challenger",
        baseline_version="synthetic-baseline",
        rules_version="synthetic-rules",
    )

    assert result == 1
    records = [json.loads(line) for line in results.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    assert all(record["outcome"] == "invalid" for record in records)
    assert all(record["failure_reason"] == "timeout" for record in records)
    assert all(record["valid"] is False for record in records)
    summary = json.loads(results.with_suffix(results.suffix + ".summary.json").read_text(encoding="utf-8"))
    assert summary["invalid_games"] == 2
    assert summary["valid_games"] == 0
    assert summary["invalid_game_reasons"] == {"timeout": 2}


def test_experiment_only_tournament_never_emits_a_promotion_decision(monkeypatch, tmp_path: Path, capsys) -> None:
    class CompletedBot:
        def __init__(self, **_kwargs):
            pass

        def __del__(self):
            pass

    winners = iter(["Brancas", "Brancas"])

    def completed_match(_white, _black, opening_index=0, opening_seed=None):
        return {
            "winner": next(winners),
            "seed": opening_seed,
            "opening_index": opening_index,
            "initial_rwen": "initial",
            "final_rwen": "final",
            "plies": 1,
            "actions": [],
            "action_counts": {},
            "termination_reason": "game_over",
            "valid": True,
            "failure_reason": None,
            "failure_exception_type": None,
            "failure_detail": None,
        }

    monkeypatch.setattr(arena_tournament, "CppEngineBot", CompletedBot)
    monkeypatch.setattr(arena_tournament, "run_headless_match", completed_match)
    results = tmp_path / "experiment.jsonl"

    result = arena_tournament.start_tournament(
        challenger_engine="challenger",
        baseline_engine="baseline",
        num_games=2,
        win_threshold=0,
        nodes=10,
        results_path=str(results),
        challenger_version="synthetic-challenger",
        baseline_version="synthetic-baseline",
        rules_version="synthetic-rules",
        experiment_only=True,
    )

    summary = json.loads(results.with_suffix(results.suffix + ".summary.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out
    assert result == 0
    assert summary["promoted"] is None
    assert summary["promotion_decision"] == "not_evaluated"
    assert summary["promotion_authority"] is False
    assert summary["aggregate_strength"]["elo_equivalent_delta"] == pytest.approx(0.0)
    assert summary["sequential_rating_diagnostic"]["order_invariant"] is False
    assert "SUCESSO" not in output
    assert "FALHA" not in output
    assert "sem decisão de promoção" in output
