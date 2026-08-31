from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def fixture_rwen() -> str:
    gs = GameState()
    gs.board = [[None for _ in range(8)] for _ in range(8)]
    gs.white_to_move = True
    for row, col, name, team in (
        (0, 3, "Obelisk", "pretas"),
        (0, 5, "Cleric", "pretas"),
        (0, 7, "BoneLord", "pretas"),
        (1, 2, "Ranger", "pretas"),
        (5, 3, "Inquisitor", "pretas"),
        (5, 4, "Obelisk", "brancas"),
        (6, 3, "Nightshade", "pretas"),
        (6, 4, "Lich", "brancas"),
    ):
        gs.board[row][col] = criar_peca_por_nome(name, team)
    return gs.to_rwen()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    args = parser.parse_args()

    engine = Path(args.engine).resolve()
    if not engine.is_file():
        raise SystemExit(f"engine not found: {engine}")

    rwen = fixture_rwen()
    env = os.environ.copy()
    process = subprocess.Popen(
        [str(engine)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=engine.parent.parent.parent,
        env=env,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    process.stdin.write("isready\n")
    process.stdin.write(f"position rwen {rwen}\n")
    process.stdin.write("go nodes 250000\n")
    process.stdin.flush()

    stdout_lines: list[str] = []
    for line in process.stdout:
        line = line.rstrip("\r\n")
        stdout_lines.append(line)
        if line.startswith("bestmove "):
            break

    process.stdin.write("quit\n")
    process.stdin.flush()
    process.wait(timeout=30)
    stderr = process.stderr.read().strip()

    print(f"ENGINE={engine}")
    print(f"RWEN={rwen}")
    print("STDOUT:")
    for line in stdout_lines:
        print(line)
    print("STDERR:")
    print(stderr)

    bestmoves = [line for line in stdout_lines if line.startswith("bestmove ")]
    if not bestmoves:
        raise SystemExit("frozen engine produced no bestmove")
    if bestmoves[-1] == "bestmove 0000":
        raise SystemExit("frozen engine reproduced non-terminal bestmove 0000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
