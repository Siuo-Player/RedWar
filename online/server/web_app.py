from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from ai.difficulty_tiers import AresBotTier
from engine.game_modes import GameMode, GameModeType, TimeControl
from engine.puzzles import PUZZLE_BANK
from engine.ratings import LeaderboardManager
from online.server.room import RoomManager


DEFAULT_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self' 'unsafe-inline' https: data:; connect-src 'self' ws: wss: http: https:;",
}


class _RedWarHTTPRequestHandler(BaseHTTPRequestHandler):
    """Threading HTTP request handler dispatching to RedWarWebApp."""

    app: RedWarWebApp

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        MAX_BODY_BYTES = 1024 * 1024  # 1 MB max request body to prevent memory exhaustion DoS
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_length = 0

        if content_length > MAX_BODY_BYTES:
            self.send_response(413)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Payload Too Large: maximum allowed body size is 1 MB"}')
            return

        body = (
            self.rfile.read(content_length).decode("utf-8", errors="replace")
            if content_length > 0
            else ""
        )
        response = self.app.handle_request(method=method, path=self.path, body=body)
        self.send_response(response["status"])
        for k, v in response.get("headers", {}).items():
            self.send_header(k, v)
        self.end_headers()
        body_bytes = response.get("body", "").encode("utf-8")
        self.wfile.write(body_bytes)

    def log_message(self, format: str, *args: Any) -> None:
        # Standardized single-line web request log
        print(f"[Web] {self.address_string()} - {format % args}")


class RedWarWebApp:
    """REST API and static file serving application for RedWar Web."""

    def __init__(
        self,
        room_manager: Optional[RoomManager] = None,
        leaderboard_manager: Optional[LeaderboardManager] = None,
        static_dir: Optional[Path] = None,
        host: str = "0.0.0.0",
        port: int = 8000,
    ):
        self.room_manager = room_manager or RoomManager()
        self.leaderboard_manager = leaderboard_manager or LeaderboardManager()
        self.static_dir = static_dir or (Path(__file__).resolve().parents[2] / "deploy" / "web")
        self.host = host
        self.port = port
        self._server: Optional[ThreadingHTTPServer] = None

    def _response(
        self,
        status: int,
        body: str,
        content_type: str = "application/json",
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Helper to construct a response with required security headers."""
        headers = dict(DEFAULT_SECURITY_HEADERS)
        headers["Content-Type"] = content_type
        if extra_headers:
            headers.update(extra_headers)
        return {
            "status": status,
            "headers": headers,
            "body": body,
        }

    def handle_request(
        self,
        method: str,
        path: str,
        query: str = "",
        body: str = "",
    ) -> dict[str, Any]:
        """Dispatch an HTTP request and return a structured response with security headers."""
        parsed_url = urlparse(path)
        route = parsed_url.path
        query_params = parse_qs(query or parsed_url.query)

        if method != "GET":
            return self._response(
                status=405,
                body=json.dumps({"error": "Method Not Allowed"}),
            )

        if route == "/api/leaderboard":
            mode = query_params.get("mode", ["standard_8x8"])[0]
            try:
                raw_limit = int(query_params.get("limit", [50])[0])
            except (ValueError, TypeError):
                raw_limit = 50
            limit = min(max(1, raw_limit), 100)
            entries = self.leaderboard_manager.get_top_players(mode, limit=limit)
            return self._response(
                status=200,
                body=json.dumps({"leaderboard": [e.to_dict() for e in entries]}),
            )

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
            return self._response(
                status=200,
                body=json.dumps({"tiers": tiers}),
            )

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
            return self._response(
                status=200,
                body=json.dumps({"puzzles": puzzles}),
            )

        if route == "/api/rooms":
            rooms = self.room_manager.list_active_rooms()
            return self._response(
                status=200,
                body=json.dumps({"rooms": rooms}),
            )

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
            return self._response(
                status=200,
                body=json.dumps({"modes": modes, "time_controls": time_controls}),
            )

        # Static file serving with strict Path Traversal prevention
        safe_root = self.static_dir.resolve()
        if route in ("/", "/index.html"):
            index_path = safe_root / "index.html"
            if index_path.is_file():
                return self._response(
                    status=200,
                    body=index_path.read_text(encoding="utf-8"),
                    content_type="text/html; charset=utf-8",
                )

        candidate_path = (self.static_dir / route.lstrip("/")).resolve()
        try:
            is_safe = candidate_path.is_relative_to(safe_root)
        except (ValueError, AttributeError):
            is_safe = str(candidate_path).startswith(str(safe_root))

        if not is_safe:
            return self._response(
                status=403,
                body=json.dumps({"error": "Forbidden: Path Traversal Detected"}),
            )

        if candidate_path.is_file():
            mime = "text/plain"
            if candidate_path.suffix == ".html":
                mime = "text/html"
            elif candidate_path.suffix == ".js":
                mime = "application/javascript"
            elif candidate_path.suffix == ".css":
                mime = "text/css"
            elif candidate_path.suffix == ".json":
                mime = "application/json"
            return self._response(
                status=200,
                body=candidate_path.read_text(encoding="utf-8"),
                content_type=f"{mime}; charset=utf-8",
            )

        return self._response(
            status=404,
            body=json.dumps({"error": "Not Found"}),
        )

    def run(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Run the HTTP web server synchronously using ThreadingHTTPServer."""
        effective_host = host or self.host
        effective_port = port or self.port
        handler_cls = type(
            "BoundRedWarHandler",
            (_RedWarHTTPRequestHandler,),
            {"app": self},
        )
        self._server = ThreadingHTTPServer((effective_host, effective_port), handler_cls)
        print(f"RedWar Web Platform active on http://{effective_host}:{effective_port}/")
        try:
            self._server.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            print("\nShutting down RedWar Web server...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Gracefully stop and close the underlying HTTP server."""
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass
            try:
                self._server.server_close()
            except Exception:
                pass
            self._server = None


def create_web_handler_app(
    room_manager: Optional[RoomManager] = None,
    leaderboard_manager: Optional[LeaderboardManager] = None,
    static_dir: Optional[Path] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> RedWarWebApp:
    """Factory creating the Web Application instance."""
    return RedWarWebApp(
        room_manager=room_manager,
        leaderboard_manager=leaderboard_manager,
        static_dir=static_dir,
        host=host,
        port=port,
    )
