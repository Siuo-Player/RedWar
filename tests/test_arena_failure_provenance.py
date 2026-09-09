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
