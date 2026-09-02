from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ("cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test")

EXACT_FAILING_RWEN = (
    ".:.,.:.,.:.,B_Obelisk_0_N_0:.,.:.,B_Cleric_0_N_0:.,.:.,B_BoneLord_0_N_0:."
    "/.:.,.:.,.:.,B_Ranger_0_N_0:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:."
    "/.:.,.:.,B_Inquisitor_0_N_0:.,.:.,W_Obelisk_0_N_0:.,.:.,.:."
    "/.:.,.:.,.:.,B_Nightshade_0_N_0:.,W_Lich_0_N_0:.,.:.,.:."
    "/.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
)


def test_exact_first_aa_b_failure_has_legal_cpp_moves() -> None:
    """Diagnostic-only: verify the literal Arena-failure RWEN has root actions."""
    assert BRIDGE.exists(), f"missing movegen helper: {BRIDGE}"
    completed = subprocess.run(
        [str(BRIDGE)],
        input=EXACT_FAILING_RWEN + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout

    lines = completed.stdout.splitlines()
    assert lines and lines[0].startswith("COUNT ")
    count = int(lines[0].split()[1])
    moves = set(lines[1:-1])
    assert lines[-1] == "END"
    assert count == len(moves)

    expected = {"MOVE E2 D1", "MOVE E2 E1", "MOVE E2 F1"}
    assert expected.issubset(moves), (
        f"exact Arena-failure RWEN has no expected Lich root moves: "
        f"missing={sorted(expected - moves)} count={count}"
    )
