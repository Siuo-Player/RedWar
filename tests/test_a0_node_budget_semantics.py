from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "tools" / "scripts" / "build_cpp_engine.py"
ENGINE_PATH = ROOT / "ai" / "cpp_engine" / ("engine.exe" if sys.platform == "win32" else "engine")

DIAGNOSTICS_RE = re.compile(r"^info string search diagnostics nodes=(\d+) tt_probes=(\d+) tt_hits=(\d+) tt_stores=(\d+)$")


def _fixture_rwen() -> str:
    state = GameState()
    state.board[7][0] = criar_peca_por_nome("Geomancer", "brancas")
    state.board[0][7] = criar_peca_por_nome("Geomancer", "pretas")
    return state.to_rwen()


def _run_fixed_budget(rwen: str, budget: int) -> tuple[int, str]:
    process = subprocess.Popen(
        [str(ENGINE_PATH)],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None

        commands = (
            f"position rwen {rwen}\n"
            f"go nodes {budget}\n"
        )
        process.stdin.write(commands)
        process.stdin.flush()

        diagnostics = None
        bestmove = None
        for _ in range(64):
            line = process.stdout.readline()
            if not line:
                break
            line = line.rstrip("\r\n")
            match = DIAGNOSTICS_RE.match(line)
            if match:
                diagnostics = int(match.group(1))
            if line.startswith("bestmove "):
                bestmove = line
                break

        assert diagnostics is not None, "missing fixed-node diagnostics"
        assert bestmove is not None, "missing bestmove"
        return diagnostics, bestmove
    finally:
        process.kill()
        process.wait(timeout=5)


def test_go_nodes_is_a_fixed_node_budget_independent_of_wall_clock():
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=ROOT, check=True)
    assert ENGINE_PATH.is_file()

    rwen = _fixture_rwen()
    for budget in (1, 7, 31):
        first = _run_fixed_budget(rwen, budget)
        second = _run_fixed_budget(rwen, budget)

        nodes, bestmove = first
        assert 1 <= nodes <= budget
        assert first == second
        assert bestmove.startswith("bestmove ")
