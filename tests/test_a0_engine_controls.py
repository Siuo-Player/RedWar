from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tools.analytics.opening_book import gerar_abertura

ROOT = Path(__file__).resolve().parents[1]
CPP_DIR = ROOT / "ai" / "cpp_engine"


def _build_production_engine(output: Path) -> None:
    sources = ["board.cpp", "evaluate.cpp", "main.cpp", "movegen.cpp", "search.cpp", "nnue.cpp"]
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O2",
            "-pipe",
            *sources,
            "-o",
            str(output),
        ],
        cwd=CPP_DIR,
        check=True,
    )


def _read_until_bestmove(process: subprocess.Popen[str]) -> tuple[list[str], str]:
    assert process.stdout is not None
    lines: list[str] = []
    for raw_line in process.stdout:
        line = raw_line.rstrip("\r\n")
        lines.append(line)
        if line.startswith("bestmove "):
            return lines, line.split(" ", 1)[1]
    raise AssertionError(f"engine exited without bestmove: {lines!r}")


def _send(process: subprocess.Popen[str], command: str) -> None:
    assert process.stdin is not None
    process.stdin.write(command + "\n")
    process.stdin.flush()


def _readline(process: subprocess.Popen[str]) -> str:
    assert process.stdout is not None
    line = process.stdout.readline()
    assert line, "engine exited while a protocol response was expected"
    return line.rstrip("\r\n")


def _search(process: subprocess.Popen[str], nodes: int) -> tuple[dict[str, str], str, list[str]]:
    _send(process, f"go nodes {nodes}")
    lines, bestmove = _read_until_bestmove(process)
    info = next((line for line in lines if line.startswith("info string search ")), None)
    assert info is not None, lines
    fields = dict(field.split("=", 1) for field in info[len("info string search ") :].split())
    return fields, bestmove, lines


@pytest.mark.skipif(os.name == "nt", reason="diagnostic C++ protocol harness is POSIX-only")
def test_a0_engine_controls_and_canonical_state(tmp_path: Path) -> None:
    engine = tmp_path / "engine"
    _build_production_engine(engine)

    state = gerar_abertura(201)
    canonical_rwen = state.to_rwen()

    process = subprocess.Popen(
        [str(engine)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    try:
        _send(process, "isready")
        assert _readline(process) == "readyok"

        _send(process, f"position rwen {canonical_rwen}")
        _send(process, "state canonical")
        assert _readline(process) == f"state rwen {canonical_rwen}"
        state_hash = _readline(process)
        assert state_hash.startswith("state hash ")

        _send(process, "setoption name UseTT value false")
        assert _readline(process) == "info string UseTT false"
        _send(process, "clearhash")
        assert _readline(process) == "info string clearhash ok"
        off_fields, off_move, _ = _search(process, 2000)
        assert off_fields["tt"] == "0"
        assert int(off_fields["node_limit"]) == 2000
        assert 0 < int(off_fields["nodes"]) <= 2000
        assert off_fields["node_bound_reached"] == "1"
        assert off_fields["time_abort"] == "0"
        assert off_fields["terminal_no_move"] == "0"
        assert off_move != "0000"

        _send(process, "setoption name UseTT value true")
        assert _readline(process) == "info string UseTT true"
        _send(process, "clearhash")
        assert _readline(process) == "info string clearhash ok"
        cold_fields, cold_move, _ = _search(process, 2000)
        assert cold_fields["tt"] == "1"
        assert 0 < int(cold_fields["nodes"]) <= 2000
        assert cold_fields["node_bound_reached"] == "1"
        assert cold_fields["time_abort"] == "0"
        assert cold_fields["terminal_no_move"] == "0"
        assert cold_move != "0000"

        warm_fields, warm_move, _ = _search(process, 2000)
        assert warm_fields["tt"] == "1"
        assert 0 < int(warm_fields["nodes"]) <= 2000
        assert warm_fields["node_bound_reached"] == "1"
        assert warm_fields["time_abort"] == "0"
        assert warm_fields["terminal_no_move"] == "0"
        assert warm_move != "0000"

        # Best-move identity is not asserted across TT modes because the current
        # search API does not declare an explicit tie-breaking contract.
    finally:
        if process.poll() is None:
            _send(process, "quit")
            process.wait(timeout=30)
