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
        assert "solution_moves" in pz


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
