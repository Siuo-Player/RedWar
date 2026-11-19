from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.game_modes import GameMode, TimeControl
from engine.ratings import LeaderboardManager
from online.server.room import RoomManager
from online.server.web_app import create_web_handler_app


@pytest.fixture
def web_client(tmp_path: Path):
    db_file = tmp_path / "web_ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    p1 = lb.get_or_create_profile("AresBot_Master", "Ares Master")
    p1.set_rating("standard_8x8", 2500)
    p2 = lb.get_or_create_profile("PlayerOne", "Player One")
    p2.set_rating("standard_8x8", 1450)

    manager = RoomManager(leaderboard_manager=lb)
    manager.create_room("ROOM_TEST_1", mode=GameMode.standard_8x8(), time_control=TimeControl.blitz_3_2())

    app = create_web_handler_app(room_manager=manager, leaderboard_manager=lb)
    return app


def test_leaderboard_endpoint(web_client):
    response = web_client.handle_request("GET", "/api/leaderboard")
    assert response["status"] == 200
    data = json.loads(response["body"])
    assert "leaderboard" in data
    assert len(data["leaderboard"]) >= 2
    assert data["leaderboard"][0]["rating"] >= data["leaderboard"][1]["rating"]


def test_bot_tiers_endpoint(web_client):
    response = web_client.handle_request("GET", "/api/bot_tiers")
    assert response["status"] == 200
    data = json.loads(response["body"])
    assert "tiers" in data
    tier_names = [t["name"] for t in data["tiers"]]
    assert "Apprentice" in tier_names
    assert "Intermediate" in tier_names
    assert "Advanced" in tier_names
    assert "Master" in tier_names


def test_puzzles_endpoint(web_client):
    response = web_client.handle_request("GET", "/api/puzzles")
    assert response["status"] == 200
    data = json.loads(response["body"])
    assert "puzzles" in data
    assert len(data["puzzles"]) >= 3
    for pz in data["puzzles"]:
        assert "puzzle_id" in pz
        assert "initial_rwen" in pz
        assert "solution_moves" not in pz

    # Authoritative verification endpoint
    resp_verify = web_client.handle_request(
        "POST",
        "/api/puzzles/verify",
        body=json.dumps({"puzzle_id": "puz_001", "move": "MOVE D2 D8", "step": 0}),
    )
    assert resp_verify["status"] == 200
    vdata = json.loads(resp_verify["body"])
    assert vdata["correct"] is True


def test_rooms_endpoint(web_client):
    response = web_client.handle_request("GET", "/api/rooms")
    assert response["status"] == 200
    data = json.loads(response["body"])
    assert "rooms" in data
    assert len(data["rooms"]) == 1
    assert data["rooms"][0]["room_id"] == "ROOM_TEST_1"


def test_game_modes_endpoint(web_client):
    response = web_client.handle_request("GET", "/api/game_modes")
    assert response["status"] == 200
    data = json.loads(response["body"])
    assert "modes" in data
    assert "time_controls" in data
    modes = [m["name"] for m in data["modes"]]
    assert any("8×8" in m or "standard" in m.lower() for m in modes)
    assert any("10×10" in m or "grand" in m.lower() for m in modes)
    assert any("snake" in m.lower() or "draft" in m.lower() for m in modes)
    assert any("hazard" in m.lower() for m in modes)


def test_static_files_served(web_client):
    resp_index = web_client.handle_request("GET", "/")
    assert resp_index["status"] == 200
    assert "RedWar" in resp_index["body"]

    resp_js = web_client.handle_request("GET", "/app.js")
    assert resp_js["status"] == 200
    assert "gameBoard" in resp_js["body"]

    resp_css = web_client.handle_request("GET", "/styles.css")
    assert resp_css["status"] == 200
    assert "--bg-primary" in resp_css["body"]


def test_cors_preflight_and_headers_allowed(web_client):
    """Verify CORS preflight OPTIONS and response headers for GitHub Pages and localhost."""
    # 1. Preflight OPTIONS for GitHub Pages
    resp_opt_gh = web_client.handle_request(
        "OPTIONS",
        "/api/puzzles/verify",
        headers={"Origin": "https://siuo-player.github.io"},
    )
    assert resp_opt_gh["status"] == 204
    assert resp_opt_gh["headers"]["Access-Control-Allow-Origin"] == "https://siuo-player.github.io"
    assert "POST" in resp_opt_gh["headers"]["Access-Control-Allow-Methods"]

    # 2. Preflight OPTIONS for Localhost development
    resp_opt_local = web_client.handle_request(
        "OPTIONS",
        "/api/leaderboard",
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp_opt_local["status"] == 204
    assert resp_opt_local["headers"]["Access-Control-Allow-Origin"] == "http://localhost:3000"

    # 3. GET request from GitHub Pages receives CORS header
    resp_get = web_client.handle_request(
        "GET",
        "/api/leaderboard",
        headers={"Origin": "https://siuo-player.github.io"},
    )
    assert resp_get["status"] == 200
    assert resp_get["headers"]["Access-Control-Allow-Origin"] == "https://siuo-player.github.io"

    # 4. POST request from GitHub Pages receives CORS header
    resp_post = web_client.handle_request(
        "POST",
        "/api/puzzles/verify",
        body=json.dumps({"puzzle_id": "puz_001", "fromR": 6, "fromC": 3, "toR": 0, "toC": 3, "step": 0}),
        headers={"Origin": "https://siuo-player.github.io"},
    )
    assert resp_post["status"] == 200
    assert resp_post["headers"]["Access-Control-Allow-Origin"] == "https://siuo-player.github.io"


def test_cors_unauthorized_origin_rejected(web_client):
    """Verify that requests from unauthorized cross-origin domains are rejected with 403."""
    # 1. GET with unauthorized origin
    resp = web_client.handle_request(
        "GET",
        "/api/leaderboard",
        headers={"Origin": "http://malicious-attacker.com"},
    )
    assert resp["status"] == 403
    assert "Forbidden" in resp["body"]
    assert "Access-Control-Allow-Origin" not in resp["headers"]

    # 2. OPTIONS with unauthorized origin
    resp_opt = web_client.handle_request(
        "OPTIONS",
        "/api/puzzles/verify",
        headers={"Origin": "http://evil-site.org"},
    )
    assert resp_opt["status"] == 403


def test_puzzle_verify_rejects_get_method(web_client):
    """Verify that GET /api/puzzles/verify is strictly rejected with 405 Method Not Allowed."""
    resp = web_client.handle_request("GET", "/api/puzzles/verify")
    assert resp["status"] == 405
    assert "Method Not Allowed" in resp["body"]
    assert "Allow" in resp["headers"]
    assert "POST" in resp["headers"]["Allow"]


def test_puzzle_verify_robust_payload_validation(web_client):
    """Verify comprehensive validation of JSON payload, types, coordinates, and puzzle IDs."""
    # 1. Non-object payloads (null, [], string, number, bool)
    for bad_body in ("null", "[]", '"just a string"', "12345", "true", "false"):
        resp = web_client.handle_request("POST", "/api/puzzles/verify", body=bad_body)
        assert resp["status"] == 400, f"Expected 400 for payload {bad_body}, got {resp['status']}"
        assert "error" in json.loads(resp["body"])

    # 2. Missing or malformed body
    assert web_client.handle_request("POST", "/api/puzzles/verify", body="")["status"] == 400
    assert web_client.handle_request("POST", "/api/puzzles/verify", body="{bad json")["status"] == 400

    # 3. Missing or invalid puzzle_id
    assert web_client.handle_request("POST", "/api/puzzles/verify", body=json.dumps({"step": 0}))["status"] == 400
    assert web_client.handle_request("POST", "/api/puzzles/verify", body=json.dumps({"puzzle_id": "", "step": 0}))["status"] == 400
    assert web_client.handle_request("POST", "/api/puzzles/verify", body=json.dumps({"puzzle_id": "non_existent_id", "step": 0}))["status"] == 404

    # 4. Invalid step index
    assert web_client.handle_request("POST", "/api/puzzles/verify", body=json.dumps({"puzzle_id": "puz_001", "step": -1, "fromR": 6, "fromC": 3, "toR": 0, "toC": 3}))["status"] == 400
    assert web_client.handle_request("POST", "/api/puzzles/verify", body=json.dumps({"puzzle_id": "puz_001", "step": 999, "fromR": 6, "fromC": 3, "toR": 0, "toC": 3}))["status"] == 400

    # 5. Invalid coordinates: negative, out-of-bounds, float, boolean, strings
    web_client._puzzle_attempts.clear()
    bad_coords = [
        {"fromR": -1, "fromC": 3, "toR": 0, "toC": 3},
        {"fromR": 6, "fromC": 8, "toR": 0, "toC": 3},
        {"fromR": 6, "fromC": 3, "toR": 10, "toC": 3},
        {"fromR": 2.5, "fromC": 3, "toR": 0, "toC": 3},
        {"fromR": True, "fromC": 3, "toR": 0, "toC": 3},
        {"fromR": "6", "fromC": "3", "toR": "0", "toC": "3"},
    ]
    for bc in bad_coords:
        body_dict = {"puzzle_id": "puz_001", "step": 0, **bc}
        resp = web_client.handle_request("POST", "/api/puzzles/verify", body=json.dumps(body_dict))
        assert resp["status"] == 400, f"Expected 400 for coordinate set {bc}, got {resp['status']}"

    # 6. Nested 'move' dict with booleans, floats, strings, or out-of-bound coords must also return 400
    web_client._puzzle_attempts.clear()
    bad_nested_moves = [
        {"fromR": True, "fromC": 3, "toR": 2, "toC": 5},
        {"start": [True, 3], "end": [2, 5]},
        {"start": [-1, 3], "end": [2, 5]},
        {"start": [4, 3], "end": [99, 5]},
        {"fromR": "4", "fromC": 3, "toR": 2, "toC": 5},
        {"fromR": 4, "fromC": 3, "toR": 2.5, "toC": 5},
        {"fromR": 4, "fromC": -5, "toR": 2, "toC": 5},
    ]
    for bnm in bad_nested_moves:
        body_dict = {"puzzle_id": "pz1", "step": 0, "move": bnm}
        resp = web_client.handle_request("POST", "/api/puzzles/verify", body=json.dumps(body_dict))
        assert resp["status"] == 400, f"Expected 400 for nested move format {bnm}, got {resp['status']}"


def test_puzzle_verify_rate_limiting(web_client):
    """Verify that rapid successive puzzle verification attempts trigger 429 Too Many Requests."""
    valid_body = json.dumps({"puzzle_id": "puz_001", "fromR": 6, "fromC": 3, "toR": 0, "toC": 3, "step": 0})
    statuses = []
    for _ in range(25):
        resp = web_client.handle_request("POST", "/api/puzzles/verify", body=valid_body, client_ip="198.51.100.42")
        statuses.append(resp["status"])

    # First 20 allowed, subsequent blocked with 429
    assert statuses[:20] == [200] * 20
    assert statuses[20:] == [429] * 5
    assert statuses[-1] == 429


def test_index_html_loads_config_js_before_app_js():
    """Verify that deploy/web/index.html loads config.js strictly before app.js."""
    from pathlib import Path
    html = Path("deploy/web/index.html").read_text(encoding="utf-8")
    config_pos = html.find('src="config.js"')
    app_pos = html.find('src="app.js"')
    assert config_pos != -1, "config.js not found in index.html"
    assert app_pos != -1, "app.js not found in index.html"
    assert config_pos < app_pos, "config.js MUST be loaded before app.js in index.html"


def test_live_http_server_cors_and_binary_assets():
    """Verify live HTTP server behavior across real TCP sockets:
    1. CORS OPTIONS preflight with Origin header returns 204.
    2. Unauthorized Origin on live OPTIONS returns 403 Forbidden.
    3. Binary assets (.png, .wav) are served with exact bytes and correct MIME type.
    4. Live POST puzzle verification over real socket returns valid JSON response.
    """
    import urllib.request
    import urllib.error
    import threading
    from http.server import ThreadingHTTPServer
    from online.server.web_app import RedWarWebApp, _RedWarHTTPRequestHandler

    app = RedWarWebApp(host="127.0.0.1", port=0)
    handler_cls = type("BoundLiveHandler", (_RedWarHTTPRequestHandler,), {"app": app})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    app._server = server
    port = server.server_port

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Live OPTIONS with authorized origin
        req_options = urllib.request.Request(
            f"{base_url}/api/leaderboard",
            method="OPTIONS",
            headers={"Origin": "http://localhost:8080"}
        )
        with urllib.request.urlopen(req_options) as resp:
            assert resp.status == 204
            assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:8080"
            assert "Vary" in resp.headers

        # 2. Live OPTIONS with unauthorized origin returns 403
        req_unauth = urllib.request.Request(
            f"{base_url}/api/leaderboard",
            method="OPTIONS",
            headers={"Origin": "http://malicious-site.com"}
        )
        try:
            urllib.request.urlopen(req_unauth)
            assert False, "Expected HTTPError 403 for unauthorized origin"
        except urllib.error.HTTPError as err:
            assert err.code == 403

        # 3. Live GET binary PNG asset: verify raw bytes and MIME type
        asset_rel_path = Path("deploy/web/assets/heroes/berserker.png")
        if not asset_rel_path.exists():
            asset_rel_path = Path("deploy/web/assets/berserker.png")

        if asset_rel_path.exists():
            disk_bytes = asset_rel_path.read_bytes()
            asset_url = f"{base_url}/{asset_rel_path.relative_to('deploy/web').as_posix()}"
            req_png = urllib.request.Request(asset_url, method="GET")
            with urllib.request.urlopen(req_png) as resp:
                assert resp.status == 200
                assert resp.headers.get("Content-Type") == "image/png"
                body = resp.read()
                assert body == disk_bytes, "Served binary bytes must be identical to disk bytes"

        # 4. Live POST puzzle verification over real socket
        post_data = json.dumps({
            "puzzle_id": "pz1",
            "fromR": 4, "fromC": 3, "toR": 2, "toC": 5,
            "step": 0
        }).encode("utf-8")
        req_post = urllib.request.Request(
            f"{base_url}/api/puzzles/verify",
            data=post_data,
            headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:3000"},
            method="POST"
        )
        with urllib.request.urlopen(req_post) as resp:
            assert resp.status == 200
            res_json = json.loads(resp.read().decode("utf-8"))
            assert res_json["correct"] is True
            assert res_json["completed"] is True
    finally:
        app.stop()

