from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_NAME = "engine.exe" if os.name == "nt" else "engine"
ENGINE = ROOT / "ai" / "cpp_engine" / ENGINE_NAME


def _build_rows(*, with_effect_syntax: bool) -> str:
    rows = [[".:."] * 8 for _ in range(8)]
    if not with_effect_syntax:
        rows = [["."] * 8 for _ in range(8)]

    pieces = {
        (0, 0): "W_FrostMage_0_N_0",
        (0, 1): "B_Bone_0_N_0",
        (2, 3): "W_Bone_0_N_0",
        (3, 4): "B_Lich_0_N_0",
        (5, 5): "B_FrostMage_0_N_0",
    }
    for (row, col), piece in pieces.items():
        rows[row][col] = piece + ":." if with_effect_syntax else piece

    return "/".join(",".join(row) for row in rows) + " B 7"


CANONICAL = _build_rows(with_effect_syntax=True)
NON_CANONICAL = _build_rows(with_effect_syntax=False)


def read_canonical(rwen: str) -> tuple[str, int]:
    result = subprocess.run(
        [str(ENGINE)],
        input=f"position rwen {rwen}\nisready\nstate canonical\nquit\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    command_errors = [line for line in lines if line.startswith("info string command error ")]
    assert not command_errors, "native protocol rejected input: " + " | ".join(command_errors)
    state_line = next(line for line in lines if line.startswith("info string state canonical "))
    payload = state_line.removeprefix("info string state canonical ")
    canonical, hash_text = payload.rsplit(" hash=", 1)
    return canonical, int(hash_text)


def test_fixture_shape_is_eight_by_eight():
    board = CANONICAL.split(" ", 1)[0]
    rows = board.split("/")
    assert len(rows) == 8
    assert all(len(row.split(",")) == 8 for row in rows)


def test_native_state_readback_is_canonical_and_stable():
    assert ENGINE.exists(), f"native engine missing: {ENGINE}. Run build_cpp_engine.py."

    canonical_a, hash_a = read_canonical(CANONICAL)
    canonical_b, hash_b = read_canonical(NON_CANONICAL)

    assert canonical_a == CANONICAL
    assert canonical_b == CANONICAL
    assert hash_a == hash_b
