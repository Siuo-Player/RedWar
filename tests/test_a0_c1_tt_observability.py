from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_movegen_bridge_test.exe" if os.name == "nt" else "cpp_movegen_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME

# Exact non-terminal fixture from the historical A/A-B failure. Its native
# root move generation is independently known to produce four legal Lich moves.
FIXTURE = (
    ".:.,.:.,.:.,B_Obelisk_0_N_0:.,.:.,B_Cleric_0_N_0:.,.:.,B_BoneLord_0_N_0:./"
    ".:.,.:.,.:.,B_Ranger_0_N_0:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,B_Inquisitor_0_N_0:.,.:.,W_Obelisk_0_N_0:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,B_Nightshade_0_N_0:.,W_Lich_0_N_0:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
)


def run_bridge(*commands: str) -> list[str]:
    result = subprocess.run(
        [str(BRIDGE)],
        input="".join(f"{command}\n" for command in commands),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return [line for line in result.stdout.splitlines() if line]


def parse_diag(line: str) -> dict[str, int | str]:
    parts = line.split()
    data: dict[str, int | str] = {"label": parts[0]}
    for token in parts[1:]:
        key, value = token.split("=", 1)
        data[key] = int(value) if key != "move" else value
    return data


def test_tt_off_has_no_tt_activity():
    assert BRIDGE.exists(), f"native helper missing: {BRIDGE}. Run build_cpp_engine.py --movegen-test."
    lines = run_bridge(f"TT_OFF {FIXTURE}")
    assert len(lines) == 1
    diag = parse_diag(lines[0])
    assert diag["label"] == "DIAG"
    assert diag["move"] != "0000"
    assert diag["tt_probes"] == 0
    assert diag["tt_hits"] == 0
    assert diag["tt_stores"] == 0


def test_tt_clear_is_empty_before_search():
    assert BRIDGE.exists()
    lines = run_bridge(f"TT_CLEARED {FIXTURE}")
    assert len(lines) == 2
    assert lines[0] == "CLEARED before_occupied=0"
    diag = parse_diag(lines[1])
    assert diag["move"] != "0000"
    assert diag["tt_probes"] > 0
    assert diag["tt_stores"] > 0


def test_tt_warmup_makes_reuse_observable():
    assert BRIDGE.exists()
    lines = run_bridge(f"TT_WARM {FIXTURE}")
    assert len(lines) == 3
    assert lines[0] == "WARMUP_CLEAR before_occupied=0"
    warmup = parse_diag(lines[1])
    warm = parse_diag(lines[2])

    assert warmup["label"] == "WARMUP"
    assert warm["label"] == "WARM"
    assert warmup["tt_stores"] > 0
    assert warm["tt_probes"] > 0
    assert warm["tt_hits"] > 0
    assert warm["move"] == warmup["move"]
