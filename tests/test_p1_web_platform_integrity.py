from __future__ import annotations

import json
from pathlib import Path
import threading
import time
import urllib.request
import urllib.error
import pytest

from engine.ratings import LeaderboardManager
from online.server.room import RoomManager
from online.server.web_app import RedWarWebApp, DEFAULT_SECURITY_HEADERS


def test_path_traversal_prevention():
    """Verify path traversal attempts return 403 Forbidden."""
    app = RedWarWebApp()

    traversal_paths = [
        "/../launcher.py",
        "/../../main.py",
        "/../../../windows/system32/cmd.exe",
        "/....//....//launcher.py",
    ]
    for p in traversal_paths:
        resp = app.handle_request("GET", p)
        assert resp["status"] in (403, 404), f"Path {p} should be rejected or not found"
        if resp["status"] == 403:
            body = json.loads(resp["body"])
            assert "Path Traversal" in body["error"]


def test_security_headers_present():
    """Verify security headers are attached to all API and static responses."""
    app = RedWarWebApp()

    # API route
    resp_api = app.handle_request("GET", "/api/bot_tiers")
    assert resp_api["status"] == 200
    for header, expected in DEFAULT_SECURITY_HEADERS.items():
        assert resp_api["headers"].get(header) == expected

    # Static route
    resp_static = app.handle_request("GET", "/")
    assert resp_static["status"] == 200
    for header, expected in DEFAULT_SECURITY_HEADERS.items():
        assert resp_static["headers"].get(header) == expected

    # 404 route
    resp_404 = app.handle_request("GET", "/non_existent_file.xyz")
    assert resp_404["status"] == 404
    for header, expected in DEFAULT_SECURITY_HEADERS.items():
        assert resp_404["headers"].get(header) == expected


def test_live_http_server_threading(tmp_path: Path):
    """Verify live HTTP server starts, serves REST API and static content, and shuts down cleanly."""
    db_file = tmp_path / "live_ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    p = lb.get_or_create_profile("AresGrandmaster", "Ares GM")
    p.set_rating("standard_8x8", 2600)

    manager = RoomManager(leaderboard_manager=lb)
    app = RedWarWebApp(
        room_manager=manager,
        leaderboard_manager=lb,
        host="127.0.0.1",
        port=0,  # OS assigned port
    )

    # Start in thread
    server_thread = threading.Thread(target=app.run, kwargs={"port": 0}, daemon=True)
    server_thread.start()

    # Wait for server to bind
    for _ in range(30):
        if app._server is not None:
            break
        time.sleep(0.05)
    assert app._server is not None
    port = app._server.server_port

    try:
        # Query /api/leaderboard
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/leaderboard") as response:
            assert response.status == 200
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert response.headers.get("X-Frame-Options") == "DENY"
            data = json.loads(response.read().decode("utf-8"))
            assert len(data["leaderboard"]) >= 1
            assert data["leaderboard"][0]["player_id"] == "AresGrandmaster"

        # Query static index.html
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as response:
            assert response.status == 200
            content = response.read().decode("utf-8")
            assert "RedWar" in content

        # Traversal check over live HTTP
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/../launcher.py")
            urllib.request.urlopen(req)
            pytest.fail("Traversal request should have failed with HTTP 403/404")
        except urllib.error.HTTPError as e:
            assert e.code in (403, 404)

    finally:
        app.stop()
        server_thread.join(timeout=2.0)


def test_deterministic_eval_history_invariant():
    """Verify deploy/web/app.js uses deterministic centipawns in addMoveToHistory (no Math.random)."""
    app_js = Path("deploy/web/app.js").read_text(encoding="utf-8")
    # Locate addMoveToHistory
    start_idx = app_js.find("function addMoveToHistory(")
    assert start_idx != -1
    end_idx = app_js.find("}", start_idx)
    func_body = app_js[start_idx:end_idx]

    assert "Math.random" not in func_body, "Math.random found in addMoveToHistory!"
    assert "computeBoardCentipawns" in func_body, "computeBoardCentipawns should calculate evalHistory"


def test_removal_of_rpg_terminology():
    """Verify RPG terminology removed from title and platform launcher."""
    html = Path("deploy/web/index.html").read_text(encoding="utf-8")
    assert "<title>RedWar — Competitive Tactical RPG" not in html
    assert "RPG" not in html.split("<title>")[1].split("</title>")[0]

    launcher_txt = Path("launcher.py").read_text(encoding="utf-8")
    assert "Tactical Grid RPG" not in launcher_txt
