from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ("cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test")

EXACT_FAILING_RWEN = (
    ".:.,.:.,.:.,B_Obelisk_0_N_0:.,.:.,B_Cleric_0_N_0:.,.:.,B_BoneLord_0_N_0:."
    "/.:.,.:.,.:.,B_Ranger_0_N_0:.,.:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,B_Inquisitor_0_N_0:.,.:.,W_Obelisk_0_N_0:.,.:.,.:."
    "/.:.,.:.,.:.,B_Nightshade_0_N_0:.,W_Lich_0_N_0:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
)


def run_helper(payload: str) -> list[str]:
    assert BRIDGE.exists(), f"missing movegen helper: {BRIDGE}"
    completed = subprocess.run(
        [str(BRIDGE)],
        input=payload + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return completed.stdout.splitlines()


def test_exact_first_aa_b_failure_has_legal_cpp_moves() -> None:
    """Diagnostic-only: verify the literal Arena-failure RWEN has root actions."""
    lines = run_helper(EXACT_FAILING_RWEN)
    assert lines and lines[0].startswith("COUNT ")
    count = int(lines[0].split()[1])
    moves = set(lines[1:-1])
    assert lines[-1] == "END"
    assert count == len(moves)
    assert count > 0

    # The C++ configuration makes Lich's normal move one-step diagonal.
    expected = {"MOVE E2 D1", "MOVE E2 F1"}
    assert expected.issubset(moves), (
        f"exact Arena-failure RWEN lacks expected Lich moves: "
        f"missing={sorted(expected - moves)} count={count}"
    )
    assert "MOVE E2 E1" not in moves


def test_exact_first_aa_b_failure_search_sees_same_root() -> None:
    """Diagnostic-only: compare root generation with the synchronous search entrypoint."""
    lines = run_helper("SEARCH " + EXACT_FAILING_RWEN)
    assert lines[:1] and lines[0].startswith("ROOT_COUNT ")
    root_count = int(lines[0].split()[1])
    assert root_count > 0
    assert lines[1].startswith("SEARCH_RESULT ")
    result = lines[1].split(" ", 1)[1]
    assert result != "0000"
    assert lines[2] == "END_SEARCH"
