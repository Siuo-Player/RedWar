from __future__ import annotations

from pathlib import Path

from ai.bot import CppEngineBot
from tools.analytics.arena_tournament import run_headless_match
from tools.scripts.build_cpp_engine import compile_cpp_project

LITE_NODES = 100_000


def test_frozen_lite_ares_completes_representative_game(monkeypatch):
    """Exercise the frozen 100k Ares profile through the real engine/game loop."""
    monkeypatch.setenv("PYTHONHASHSEED", "0")

    engine_path = compile_cpp_project("engine")
    assert Path(engine_path).is_file()

    white = CppEngineBot(nodes=LITE_NODES, executable_path=str(engine_path))
    black = CppEngineBot(nodes=LITE_NODES, executable_path=str(engine_path))
    try:
        result = run_headless_match(
            white,
            black,
            opening_index=0,
            opening_seed=101,
        )
    finally:
        white.bridge.close()
        black.bridge.close()

    assert result["valid"] is True
    assert result["termination_reason"] == "game_over"
    assert result["winner"]
    assert result["seed"] == 101
    assert result["plies"] > 0
    assert result["actions"]
    assert result["final_rwen"]
