from __future__ import annotations

import os
from pathlib import Path

from ai.bot import CppEngineBot
from tools.analytics.arena_tournament import run_headless_match

LITE_NODES = 100_000
ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "ai" / "cpp_engine" / ("engine.exe" if os.name == "nt" else "engine")


def test_frozen_lite_ares_completes_representative_game(monkeypatch):
    """Exercise the frozen 100k Ares profile through the real engine/game loop."""
    monkeypatch.setenv("PYTHONHASHSEED", "0")

    assert ENGINE_PATH.is_file(), (
        f"Production C++ engine is missing at {ENGINE_PATH}. "
        "Build it with: python tools/scripts/build_cpp_engine.py"
    )

    white = CppEngineBot(nodes=LITE_NODES, executable_path=str(ENGINE_PATH))
    black = CppEngineBot(nodes=LITE_NODES, executable_path=str(ENGINE_PATH))
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
