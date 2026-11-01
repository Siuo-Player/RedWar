"""RedWar — Unified Platform Launcher.

Supports launching:
- Desktop Pygame Client (`launcher.py desktop` or `launcher.py`)
- Web Platform REST API & HTTP Server (`launcher.py web --port 8000`)
- Online Multiplayer Pygame Client (`launcher.py multiplayer --server ws://localhost:8765`)
- Ares AI Arena Benchmark (`launcher.py arena --nodes 100 --games 4`)
"""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

VERSION = "1.0.0"


def run_desktop() -> None:
    """Launch the Pygame desktop application."""
    from main import JogoController
    from tools.replay.hover_visuals import install_hover_visuals
    from tools.replay.interaction import install_intent_interaction

    app = JogoController()
    install_hover_visuals(app)
    install_intent_interaction(app)
    app.run()


def run_web(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Launch the Web Platform HTTP & REST API server."""
    from online.server.web_app import RedWarWebApp

    app = RedWarWebApp(host=host, port=port)
    print(f"RedWar Web Platform running at http://{host}:{port}/")
    app.run()


def run_multiplayer(server: str = "ws://localhost:8765") -> None:
    """Launch the multiplayer desktop client."""
    from online.client.multiplayer_main import main as mp_main

    mp_main()


def run_arena(nodes: int = 100, games: int = 4) -> None:
    """Run an Ares Arena diagnostic match session."""
    from tools.analytics.benchmark_engine import main as benchmark_main

    print(f"Running Ares engine benchmark with {games} matches, {nodes} node budget...")
    benchmark_main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RedWar: Tactical Grid RPG & Stockfish-style AI Platform",
        prog="launcher.py",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"RedWar {VERSION}"
    )

    subparsers = parser.add_subparsers(dest="mode", help="Execution mode")
    parser.set_defaults(mode="desktop")

    # desktop mode
    p_desktop = subparsers.add_parser("desktop", help="Launch the Desktop Pygame client")

    # web mode
    p_web = subparsers.add_parser("web", help="Launch the Web platform HTTP & REST API server")
    p_web.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    p_web.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")

    # multiplayer mode
    p_mp = subparsers.add_parser("multiplayer", help="Launch the Pygame online multiplayer client")
    p_mp.add_argument("--server", default="ws://localhost:8765", help="WebSocket server URI")

    # arena mode
    p_arena = subparsers.add_parser("arena", help="Run Ares AI diagnostic arena tournament")
    p_arena.add_argument("--nodes", type=int, default=100, help="Node search budget")
    p_arena.add_argument("--games", type=int, default=4, help="Number of games to run")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    mode = args.mode or "desktop"

    if mode == "desktop":
        run_desktop()
    elif mode == "web":
        run_web(host=getattr(args, "host", "0.0.0.0"), port=getattr(args, "port", 8000))
    elif mode == "multiplayer":
        run_multiplayer(server=getattr(args, "server", "ws://localhost:8765"))
    elif mode == "arena":
        run_arena(nodes=getattr(args, "nodes", 100), games=getattr(args, "games", 4))
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
