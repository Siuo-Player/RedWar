from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_NAME = "engine.exe" if os.name == "nt" else "engine"
ENGINE = ROOT / "ai" / "cpp_engine" / ENGINE_NAME

CANONICAL = (
    ".:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,W_Bone_0_N_0:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,B_Lich_0_N_0:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,B_FrostMage_0_N_0:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. B 7"
)

NON_CANONICAL = CANONICAL.replace(":.", "")


def read_canonical(rwen: str) -> tuple[str, int]:
    result = subprocess.run(
        [str(ENGINE)],
        input=f"position rwen {rwen}\nstate canonical\nquit\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    state_line = next(line for line in lines if line.startswith("info string state canonical "))
    payload = state_line.removeprefix("info string state canonical ")
    canonical, hash_text = payload.rsplit(" hash=", 1)
    return canonical, int(hash_text)


def test_native_state_readback_is_canonical_and_stable():
    assert ENGINE.exists(), f"native engine missing: {ENGINE}. Run build_cpp_engine.py."

    canonical_a, hash_a = read_canonical(CANONICAL)
    canonical_b, hash_b = read_canonical(NON_CANONICAL)

    assert canonical_a == CANONICAL
    assert canonical_b == CANONICAL
    assert hash_a == hash_b
