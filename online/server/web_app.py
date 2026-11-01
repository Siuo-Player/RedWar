from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from ai.difficulty_tiers import AresBotTier
from engine.game_modes import GameMode, GameModeType, TimeControl
from engine.puzzles import PUZZLE_BANK
from engine.ratings import LeaderboardManager
from online.server.room import RoomManager


class RedWarWebApp:
    """REST API and static file serving application for RedWar Web."""

    def __init__(
        self,
        room_manager: Optional[RoomManager] = None,
        leaderboard_manager: Optional[LeaderboardManager] = None,
        static_dir: Optional[Path] = None,
    ):
        self.room_manager = room_manager or RoomManager()
        self.leaderboard_manager = leaderboard_manager or LeaderboardManager()
        self.static_dir = static_dir or (Path(__file__).resolve().parents[2] / "deploy" / "web")

    def handle_request(
        self,
        method: str,
        path: str,
        query: str = "",
        body: str = "",
    ) -> dict[str, Any]:
        """Dispatch an HTTP request and return a structured response."""
        parsed_url = urlparse(path)
        route = parsed_url.path
        query_params = parse_qs(query or parsed_url.query)

        if method != "GET":
            return {
                "status": 405,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Method Not Allowed"}),
            }

        if route == "/api/leaderboard":
            mode = query_params.get("mode", ["standard_8x8"])[0]
            limit = int(query_params.get("limit", [50])[0])
            entries = self.leaderboard_manager.get_top_players(mode, limit=limit)
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"leaderboard": [e.to_dict() for e in entries]}),
            }

        if route == "/api/bot_tiers":
            tiers = [
                {
                    "name": tier.name.capitalize(),
                    "display_name": tier.display_name,
                    "target_elo": tier.elo,
                    "search_depth": tier.max_depth,
                    "max_nodes": tier.node_limit,
                    "blunder_rate": tier.blunder_rate,
                }
                for tier in AresBotTier
            ]
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"tiers": tiers}),
            }

        if route == "/api/puzzles":
            puzzles = [
                {
                    "puzzle_id": pz.puzzle_id,
                    "title": pz.title,
                    "description": pz.description,
                    "rating": pz.rating,
                    "initial_rwen": pz.initial_rwen,
                    "solution_moves": pz.solution_moves,
                    "theme": pz.theme,
                }
                for pz in PUZZLE_BANK
            ]
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"puzzles": puzzles}),
            }

        if route == "/api/rooms":
            rooms = self.room_manager.list_active_rooms()
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"rooms": rooms}),
            }

        if route == "/api/game_modes":
            modes = [
                {"type": "standard_8x8", "name": "Padrão 8×8", "rows": 8, "cols": 8, "budget": 200},
                {"type": "grand_10x10", "name": "Grand RedWar 10×10", "rows": 10, "cols": 10, "budget": 300},
                {"type": "puzzle", "name": "Puzzles Táticos", "rows": 8, "cols": 8, "budget": 0},
            ]
            time_controls = [
                {"name": "Bullet 1+0", "initial_seconds": 60, "increment_seconds": 0, "category": "bullet"},
                {"name": "Blitz 3+2", "initial_seconds": 180, "increment_seconds": 2, "category": "blitz"},
                {"name": "Blitz 5+0", "initial_seconds": 300, "increment_seconds": 0, "category": "blitz"},
                {"name": "Rapid 10+0", "initial_seconds": 600, "increment_seconds": 0, "category": "rapid"},
                {"name": "Rapid 15+10", "initial_seconds": 900, "increment_seconds": 10, "category": "rapid"},
                {"name": "Classical 30+0", "initial_seconds": 1800, "increment_seconds": 0, "category": "classical"},
            ]
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"modes": modes, "time_controls": time_controls}),
            }

        # Static file serving
        if route in ("/", "/index.html"):
            index_path = self.static_dir / "index.html"
            if index_path.exists():
                return {
                    "status": 200,
                    "headers": {"Content-Type": "text/html; charset=utf-8"},
                    "body": index_path.read_text(encoding="utf-8"),
                }

        file_path = self.static_dir / route.lstrip("/")
        if file_path.exists() and file_path.is_file():
            mime = "text/plain"
            if file_path.suffix == ".html":
                mime = "text/html"
            elif file_path.suffix == ".js":
                mime = "application/javascript"
            elif file_path.suffix == ".css":
                mime = "text/css"
            elif file_path.suffix == ".json":
                mime = "application/json"
            return {
                "status": 200,
                "headers": {"Content-Type": f"{mime}; charset=utf-8"},
                "body": file_path.read_text(encoding="utf-8"),
            }

        return {
            "status": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not Found"}),
        }


def create_web_handler_app(
    room_manager: Optional[RoomManager] = None,
    leaderboard_manager: Optional[LeaderboardManager] = None,
    static_dir: Optional[Path] = None,
) -> RedWarWebApp:
    """Factory creating the Web Application instance."""
    return RedWarWebApp(
        room_manager=room_manager,
        leaderboard_manager=leaderboard_manager,
        static_dir=static_dir,
    )
