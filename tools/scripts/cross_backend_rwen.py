"""Validate canonical Python GameState positions against the C++ backend."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.nnue.features import load_hero_ids, parse_rwen
from tools.scripts.cross_backend_cases import build_cases

DEFAULT_ENGINE = ROOT / "ai" / "cpp_engine" / "engine.exe"


def load_cases() -> list[tuple[int, str]]:
    return list(enumerate(build_cases(), 1))


def validate_python(cases: list[tuple[int, str]]) -> None:
    hero_ids = load_hero_ids()
    for case_no, rwen in cases:
        parse_rwen(rwen, hero_ids)
        board_text = rwen.split()[0]
        rows = board_text.split("/")
        assert len(rows) == 8, f"case {case_no}: expected 8 rows"
        assert all(len(row.split(",")) == 8 for row in rows), (
            f"case {case_no}: expected 8 cells per row"
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
    assert result.stdout.count("info score classical") == len(cases)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Python GameState RWEN against the C++ engine")
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    parser.add_argument("--require-engine", action="store_true")
    args = parser.parse_args()

    cases = load_cases()
    validate_python(cases)

    if args.engine.exists():
        validate_cpp(cases, args.engine)
        print(f"PASS Python/C++ RWEN compatibility: {len(cases)} generated cases")
    elif args.require_engine:
        raise SystemExit(f"C++ engine not found: {args.engine}")
    else:
        print(f"PASS Python RWEN validation: {len(cases)} generated cases (C++ engine not built)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
