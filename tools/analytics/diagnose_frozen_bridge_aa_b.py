from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.engine_bridge import SubprocessEngineBridge
from engine.game_state import GameState
from tools.analytics.opening_book import gerar_abertura


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--nodes", type=int, default=250000)
    args = parser.parse_args()

    engine = str(Path(args.engine).resolve())
    gs = GameState(time_limit_seconds=99999)
    gs.board = gerar_abertura(args.seed)
    gs.white_to_move = True
    rwen = gs.to_rwen()

    bridge = SubprocessEngineBridge(engine)
    responses: list[str] = []
    try:
        bridge.ensure_running()
        bridge.send_command(f"position rwen {rwen}")
        bridge.send_command(f"go nodes {args.nodes}")
        for _ in range(32):
            response = bridge.read_response()
            responses.append(response or "<none>")
            if response and response.startswith("bestmove"):
                break

        print(f"ENGINE={engine}")
        print(f"SEED={args.seed}")
        print(f"NODES={args.nodes}")
        print(f"RWEN={rwen}")
        print(f"PROJECT_ROOT={bridge.project_root}")
        print("RESPONSES:")
        for response in responses:
            print(response)
        print("STDERR_TAIL:")
        for line in bridge.stderr_tail:
            print(line)
        return 0
    finally:
        bridge.close()


if __name__ == "__main__":
    raise SystemExit(main())
