"""Validate shared RWEN fixtures against both the Python and C++ backends.

The Python side uses the canonical NNUE RWEN parser.  The C++ side is checked
through the engine protocol when a built engine is available.  Keeping this
check separate lets CI validate representation compatibility without coupling
pytest to a particular compiler/toolchain.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from tools.nnue.features import load_hero_ids, parse_rwen

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "cross_backend_rwen.txt"
DEFAULT_ENGINE = ROOT / "ai" / "cpp_engine" / "engine.exe"


def load_cases() -> list[tuple[int, str]]:
    cases: list[tuple[int, str]] = []
    for line_no, raw in enumerate(FIXTURE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cases.append((line_no, line))
    return cases


def validate_python(cases: list[tuple[int, str]]) -> None:
    hero_ids = load_hero_ids()
    for line_no, rwen in cases:
        parse_rwen(rwen, hero_ids)
        parts = rwen.split()
        rows = parts[0].split("/")
        assert len(rows) == 8, f"fixture line {line_no}: expected 8 rows"
        assert all(len(row.split(",")) == 8 for row in rows), (
            f"fixture line {line_no}: expected 8 cells per row"
        )


def validate_cpp(cases: list[tuple[int, str]], engine: Path) -> None:
    if not engine.exists():
        raise FileNotFoundError(f"C++ engine not found: {engine}")

    payload = "".join(f"position rwen {rwen}\neval classical\n" for _, rwen in cases)
    payload += "quit\n"
    result = subprocess.run(
        [str(engine)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, f"C++ engine exited with {result.returncode}: {result.stderr}"
    assert "info string command error:" not in result.stdout
    assert "info score classical" in result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate shared Python/C++ RWEN fixtures")
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    parser.add_argument("--require-engine", action="store_true")
    args = parser.parse_args()

    cases = load_cases()
    validate_python(cases)

    if args.engine.exists():
        validate_cpp(cases, args.engine)
        print(f"PASS Python/C++ RWEN compatibility: {len(cases)} fixtures")
    elif args.require_engine:
        raise SystemExit(f"C++ engine not found: {args.engine}")
    else:
        print(f"PASS Python RWEN validation: {len(cases)} fixtures (C++ engine not built)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
