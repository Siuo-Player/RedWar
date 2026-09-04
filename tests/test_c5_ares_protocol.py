from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

from ai.engine_bridge import BridgeLifecycle, SubprocessEngineBridge
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "tools" / "scripts" / "build_cpp_engine.py"
ENGINE_PATH = ROOT / "ai" / "cpp_engine" / ("engine.exe" if sys.platform == "win32" else "engine")


@pytest.fixture(scope="session")
def production_engine() -> Path:
    """Build the production Ares executable required by protocol conformance tests."""
    subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=ROOT,
        check=True,
    )
    assert ENGINE_PATH.is_file()
    return ENGINE_PATH


def _fixture_position() -> GameState:
    state = GameState()
    state.board[7][0] = criar_peca_por_nome("Geomancer", "brancas")
    state.board[0][7] = criar_peca_por_nome("Geomancer", "pretas")
    return state


def _read_until_bestmove(bridge: SubprocessEngineBridge) -> list[str]:
    responses: list[str] = []
    for _ in range(32):
        response = bridge.read_response(timeout=10)
        assert response is not None
        responses.append(response)
        if response.startswith("bestmove "):
            return responses
    pytest.fail("Ares did not return bestmove within the protocol response bound")


def test_production_protocol_round_trip_and_search_lifecycle(production_engine: Path):
    state = _fixture_position()
    rwen = state.to_rwen()
    expected_identity = hashlib.sha256(rwen.encode("utf-8")).hexdigest()

    bridge = SubprocessEngineBridge(str(production_engine))
    try:
        bridge.ensure_running()
        assert bridge.lifecycle is BridgeLifecycle.RUNNING
        assert bridge.read_response(timeout=10) == "readyok"

        bridge.send_command("nnue info")
        nnue_info = bridge.read_response(timeout=10)
        assert nnue_info is not None
        assert nnue_info.startswith("info string nnue available=")
        assert "version=" in nnue_info
        assert "features=" in nnue_info

        bridge.send_command(f"position rwen {rwen}")
        assert bridge.last_request is not None
        assert bridge.last_request.state_identity == expected_identity

        bridge.send_command("eval classical")
        classical_eval = bridge.read_response(timeout=10)
        assert classical_eval is not None
        assert classical_eval.startswith("info score classical ")

        bridge.send_command("setoption name UseTT value false")
        assert bridge.read_response(timeout=10) == "info string UseTT false"
        bridge.send_command("setoption name UseTT value true")
        assert bridge.read_response(timeout=10) == "info string UseTT true"

        bridge.send_command("clearhash")
        assert bridge.read_response(timeout=10) == "info string clearhash ok"

        bridge.send_command("go nodes 1")
        assert bridge.last_request is not None
        assert bridge.last_request.state_identity == expected_identity
        responses = _read_until_bestmove(bridge)

        assert responses[-1].startswith("bestmove ")
        assert responses[-1] != "bestmove "
        diagnostics = [line for line in responses if line.startswith("info string search diagnostics ")]
        assert len(diagnostics) == 1
        diagnostic = diagnostics[0]
        for field in ("nodes=", "tt_probes=", "tt_hits=", "tt_stores="):
            assert field in diagnostic

        bridge.send_command("go nodes 0")
        error = bridge.read_response(timeout=10)
        assert error == "info string command error: invalid node count: 0"
    finally:
        bridge.close()

    assert bridge.lifecycle is BridgeLifecycle.CLOSED


def test_production_protocol_reports_unknown_commands(production_engine: Path):
    bridge = SubprocessEngineBridge(str(production_engine))
    try:
        bridge.ensure_running()
        assert bridge.read_response(timeout=10) == "readyok"
        bridge.send_command("not-a-real-command")
        assert bridge.read_response(timeout=10) == "info string unknown command: not-a-real-command"
    finally:
        bridge.close()
