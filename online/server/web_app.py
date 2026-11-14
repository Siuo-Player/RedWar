from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import time
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from ai.difficulty_tiers import AresBotTier
from engine.game_modes import GameMode, GameModeType, TimeControl
from engine.puzzles import PUZZLE_BANK
from engine.ratings import LeaderboardManager
from online.server.room import RoomManager


ALLOWED_ORIGIN_PATTERNS = [
    re.compile(r"^https://[a-zA-Z0-9-]+\.github\.io$"),
    re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"),
    re.compile(r"^https://(localhost|127\.0\.0\.1)(:\d+)?$"),
]


def is_allowed_origin(origin: str) -> bool:
    """Validate cross-origin request against authorized whitelist."""
    if not origin or not isinstance(origin, str):
        return False
    return any(pattern.match(origin.strip()) for pattern in ALLOWED_ORIGIN_PATTERNS)


def _normalize_puzzle_move(move_val: Any) -> Optional[tuple[int, int, int, int]]:
    """Attempt to parse move representation into canonical coordinates (from_r, from_c, to_r, to_c)."""
    if isinstance(move_val, dict):
        if "fromR" in move_val and "toR" in move_val:
            try:
                return (int(move_val["fromR"]), int(move_val["fromC"]), int(move_val["toR"]), int(move_val["toC"]))
            except (ValueError, TypeError):
                return None
        if "start" in move_val and "end" in move_val:
            try:
                s, e = move_val["start"], move_val["end"]
                return (int(s[0]), int(s[1]), int(e[0]), int(e[1]))
            except (ValueError, TypeError, IndexError):
                return None
    if isinstance(move_val, str):
        # Match '4,3->2,5' or '4,3 to 2,5' or '4,3 2,5'
        m = re.search(r"(\d+)\s*,\s*(\d+)\s*(?:->|to|\s)\s*(\d+)\s*,\s*(\d+)", move_val)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
        # Match algebraic notation like 'MOVE D4 F6' or 'D4 F6' or 'D4-F6'
        m_alg = re.search(r"\b([A-Ja-j]\d+)\b[^\w]*\b([A-Ja-j]\d+)\b", move_val)
        if m_alg:
            try:
                from engine.action_parser import ActionParser
                r1, c1 = ActionParser.alg_to_coords(m_alg.group(1), total_linhas=8)
                r2, c2 = ActionParser.alg_to_coords(m_alg.group(2), total_linhas=8)
                return (r1, c1, r2, c2)
            except Exception:
                pass
    return None



DEFAULT_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss: http: https:;"
    ),
}


class _RedWarHTTPRequestHandler(BaseHTTPRequestHandler):
    """Threading HTTP request handler dispatching to RedWarWebApp."""

    app: RedWarWebApp

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_OPTIONS(self) -> None:
        self._dispatch("OPTIONS")

    def _dispatch(self, method: str) -> None:
        if method not in ("GET", "HEAD", "POST", "OPTIONS"):
            self.send_response(405)
            self.send_header("Content-Type", "application/json")
            self.send_header("Allow", "GET, HEAD, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(b'{"error": "Method Not Allowed"}\n')
            return

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
        client_ip = self.client_address[0] if hasattr(self, "client_address") and self.client_address else "127.0.0.1"
        req_headers = dict(self.headers) if hasattr(self, "headers") and self.headers else {}
        response = self.app.handle_request(
            method=method,
            path=self.path,
            body=body,
            headers=req_headers,
            client_ip=client_ip,
        )
        self.send_response(response["status"])
        for k, v in response.get("headers", {}).items():
            self.send_header(k, v)
        self.end_headers()
        raw_body = response.get("body", "")
        if isinstance(raw_body, bytes):
            body_bytes = raw_body
        elif isinstance(raw_body, str):
            body_bytes = raw_body.encode("utf-8")
        else:
            body_bytes = b""
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
        self.leaderboard_manager = leaderboard_manager or LeaderboardManager(storage_path="data/leaderboards/ratings.json")
        self.static_dir = static_dir or (Path(__file__).resolve().parents[2] / "deploy" / "web")
        self.host = host
        self.port = port
        self._server: Optional[ThreadingHTTPServer] = None
        self._puzzle_attempts: dict[str, list[float]] = {}

    def _response(
        self,
        status: int,
        body: str | bytes,
        content_type: str = "application/json",
        extra_headers: Optional[dict[str, str]] = None,
        origin: Optional[str] = None,
    ) -> dict[str, Any]:
        """Helper to construct a response with required security headers and CORS."""
        headers = dict(DEFAULT_SECURITY_HEADERS)
        headers["Content-Type"] = content_type
        if origin and is_allowed_origin(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
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
        headers: Optional[dict[str, str]] = None,
        client_ip: str = "127.0.0.1",
    ) -> dict[str, Any]:
        """Dispatch an HTTP request and return a structured response with security and CORS headers."""
        parsed_url = urlparse(path)
        route = parsed_url.path
        query_params = parse_qs(query or parsed_url.query)
        req_headers = headers or {}
        origin = req_headers.get("Origin") or req_headers.get("origin")

        # CORS Authorization check
        if origin and not is_allowed_origin(origin):
            return {
                "status": 403,
                "headers": {
                    "Content-Type": "application/json",
                    "X-Content-Type-Options": "nosniff",
                },
                "body": json.dumps({"error": "Forbidden: Origin not allowed by CORS policy"}),
            }

        # Preflight OPTIONS request handling
        if method == "OPTIONS":
            cors_headers = {
                "Allow": "GET, HEAD, POST, OPTIONS",
            }
            if origin and is_allowed_origin(origin):
                cors_headers["Access-Control-Allow-Origin"] = origin
                cors_headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                cors_headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
                cors_headers["Access-Control-Max-Age"] = "86400"
                cors_headers["Vary"] = "Origin"
            return {
                "status": 204,
                "headers": cors_headers,
                "body": "",
            }

        # Endpoint for verifying tactical puzzle candidate moves without leaking solutions
        if route == "/api/puzzles/verify":
            if method != "POST":
                return self._response(
                    status=405,
                    body=json.dumps({"error": "Method Not Allowed: use POST to verify puzzle moves"}),
                    extra_headers={"Allow": "POST, OPTIONS"},
                    origin=origin,
                )

            # Rate Limiting: max 20 attempts per 60 seconds per IP
            now = time.time()
            attempts = self._puzzle_attempts.setdefault(client_ip, [])
            self._puzzle_attempts[client_ip] = [t for t in attempts if now - t < 60.0]
            if len(self._puzzle_attempts[client_ip]) >= 20:
                return self._response(
                    status=429,
                    body=json.dumps({"error": "Too Many Requests: rate limit exceeded for puzzle verification"}),
                    extra_headers={"Retry-After": "60"},
                    origin=origin,
                )
            self._puzzle_attempts[client_ip].append(now)

            if not body or not body.strip():
                return self._response(
                    status=400,
                    body=json.dumps({"error": "Missing request body"}),
                    origin=origin,
                )

            try:
                payload = json.loads(body)
            except Exception:
                return self._response(
                    status=400,
                    body=json.dumps({"error": "Malformed JSON payload"}),
                    origin=origin,
                )

            if not isinstance(payload, dict):
                return self._response(
                    status=400,
                    body=json.dumps({"error": "Payload must be a JSON object"}),
                    origin=origin,
                )

            puzzle_id = payload.get("puzzle_id")
            if not isinstance(puzzle_id, str) or not puzzle_id.strip():
                return self._response(
                    status=400,
                    body=json.dumps({"error": "puzzle_id must be a non-empty string"}),
                    origin=origin,
                )

            puzzle = next((p for p in PUZZLE_BANK if p.puzzle_id == puzzle_id.strip()), None)
            if not puzzle:
                return self._response(
                    status=404,
                    body=json.dumps({"error": "puzzle_not_found"}),
                    origin=origin,
                )

            raw_step = payload.get("step", 0)
            if not isinstance(raw_step, int) or isinstance(raw_step, bool) or raw_step < 0 or raw_step >= len(puzzle.solution_moves):
                return self._response(
                    status=400,
                    body=json.dumps({"error": "invalid_step_index"}),
                    origin=origin,
                )
            step = raw_step

            candidate_move: Any = None
            if "fromR" in payload or "toR" in payload:
                for fld in ("fromR", "fromC", "toR", "toC"):
                    val = payload.get(fld)
                    if not isinstance(val, int) or isinstance(val, bool) or val < 0 or val >= 8:
                        return self._response(
                            status=400,
                            body=json.dumps({"error": f"Field '{fld}' must be an integer between 0 and 7"}),
                            origin=origin,
                        )
                candidate_move = payload
            elif "move" in payload:
                candidate_move = payload.get("move")
                if not isinstance(candidate_move, (str, dict)):
                    return self._response(
                        status=400,
                        body=json.dumps({"error": "Invalid move format"}),
                        origin=origin,
                    )
            else:
                return self._response(
                    status=400,
                    body=json.dumps({"error": "Missing move coordinates in payload"}),
                    origin=origin,
                )

            expected = puzzle.solution_moves[step].strip()
            cand_coords = _normalize_puzzle_move(candidate_move)
            exp_coords = _normalize_puzzle_move(expected)

            if cand_coords is not None and exp_coords is not None:
                is_correct = (cand_coords == exp_coords)
            else:
                cand_str = str(candidate_move).strip().upper()
                is_correct = (cand_str == expected.upper())

            is_completed = is_correct and (step + 1 >= len(puzzle.solution_moves))

            return self._response(
                status=200,
                body=json.dumps({
                    "puzzle_id": puzzle.puzzle_id,
                    "correct": is_correct,
                    "completed": is_completed,
                    "step": step,
                    "explanation": puzzle.description if is_completed else "",
                }),
                origin=origin,
            )

        # All remaining endpoints are read-only (GET/HEAD)
        if method != "GET":
            return self._response(
                status=405,
                body=json.dumps({"error": "Method Not Allowed"}),
                origin=origin,
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
                origin=origin,
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
                origin=origin,
            )

        if route == "/api/puzzles":
            # Security: Omit solution_moves to avoid exposing solutions to clients
            puzzles = [
                {
                    "puzzle_id": pz.puzzle_id,
                    "title": pz.title,
                    "description": pz.description,
                    "rating": pz.rating,
                    "initial_rwen": pz.initial_rwen,
                    "theme": pz.theme,
                }
                for pz in PUZZLE_BANK
            ]
            return self._response(
                status=200,
                body=json.dumps({"puzzles": puzzles}),
                origin=origin,
            )

        if route == "/api/rooms":
            rooms = self.room_manager.list_active_rooms()
            return self._response(
                status=200,
                body=json.dumps({"rooms": rooms}),
                origin=origin,
            )

        if route == "/api/game_modes":
            modes = [
                {"type": "standard_8x8", "name": "Padrão 8×8", "rows": 8, "cols": 8, "budget": 200},
                {"type": "grand_10x10", "name": "Grand RedWar 10×10 (Experimental)", "rows": 10, "cols": 10, "budget": 300},
                {"type": "snake_draft", "name": "Tournament Snake Draft", "rows": 8, "cols": 8, "budget": 200},
                {"type": "hazard_arena", "name": "Hazard Arena", "rows": 8, "cols": 8, "budget": 200},
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
                origin=origin,
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
                    origin=origin,
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
                origin=origin,
            )

        if candidate_path.is_file():
            ext = candidate_path.suffix.lower()
            binary_mimes = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".ico": "image/x-icon",
                ".webp": "image/webp",
                ".wav": "audio/wav",
                ".mp3": "audio/mpeg",
                ".ogg": "audio/ogg",
            }
            if ext in binary_mimes:
                return self._response(
                    status=200,
                    body=candidate_path.read_bytes(),
                    content_type=binary_mimes[ext],
                    origin=origin,
                )
            mime = "text/plain"
            if ext == ".html":
                mime = "text/html"
            elif ext == ".js":
                mime = "application/javascript"
            elif ext == ".css":
                mime = "text/css"
            elif ext == ".json":
                mime = "application/json"
            elif ext == ".svg":
                mime = "image/svg+xml"
            return self._response(
                status=200,
                body=candidate_path.read_text(encoding="utf-8"),
                content_type=f"{mime}; charset=utf-8",
                origin=origin,
            )

        return self._response(
            status=404,
            body=json.dumps({"error": "Not Found"}),
            origin=origin,
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
