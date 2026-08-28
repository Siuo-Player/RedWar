from __future__ import annotations

import json

from tools.replay.cleanup import cleanup_zero_ply_dev_replays


def test_cleanup_removes_zero_ply_line_records_and_keeps_real_games(tmp_path):
    path = tmp_path / "legacy.json"
    records = [
        {"game_id": "empty", "moves": [], "result": {"plies": 0}},
        {"game_id": "real", "moves": [["move", 0, 0, 0, 1, None, None]], "result": {"plies": 1}},
    ]
    path.write_text("\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8")

    assert cleanup_zero_ply_dev_replays(tmp_path) == 1

    remaining = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [item["game_id"] for item in remaining] == ["real"]


def test_cleanup_preserves_schema_v2_ui_sessions(tmp_path):
    path = tmp_path / "session.json"
    payload = {
        "schema_version": 2,
        "evidence_class": "developer_ui_replay",
        "event_count": 1,
        "states": [],
        "action_sets": [],
        "events": [[1, "click", "BATALHA", 1, [1, 1], 0]],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert cleanup_zero_ply_dev_replays(tmp_path) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == payload
