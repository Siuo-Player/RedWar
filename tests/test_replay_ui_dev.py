from __future__ import annotations

import json

from tools.replay.dev_ui import DevUIReplay


def test_ui_replay_interns_identical_states_and_action_sets(tmp_path):
    recorder = DevUIReplay(tmp_path)
    state = {
        "phase": "BATALHA",
        "selected_position": [4, 4],
        "available_actions": [
            {"type": "move", "target": (3, 4)},
            {"type": "spell", "spell_name": "nevada", "target": (4, 5)},
        ],
    }

    assert recorder.log_ui(state) is True
    assert recorder.log_ui(state) is False
    assert recorder.event_count == 2
    assert recorder.state_count == 1
    assert recorder.action_set_count == 1

    path = recorder.finish(result=None)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["evidence_class"] == "developer_ui_replay"
    assert payload["state_count"] == 1
    assert payload["action_set_count"] == 1
    assert payload["events"][0][1] == "ui"
    assert payload["events"][1][1] == "ui"
    assert payload["events"][0][2] == payload["events"][1][2]


def test_click_records_visible_state_with_all_available_actions(tmp_path):
    recorder = DevUIReplay(tmp_path)
    recorder.log_click(
        phase="BATALHA",
        position=(420, 315),
        button=1,
        context={
            "phase": "BATALHA",
            "selected_position": [4, 4],
            "available_actions": [
                {"type": "move", "target": (3, 4)},
                {"type": "attack", "target": (3, 4)},
                {"type": "spell", "spell_name": "nevada", "target": (4, 5)},
            ],
        },
    )

    path = recorder.finish(result=None)
    payload = json.loads(path.read_text(encoding="utf-8"))
    click = payload["events"][0]
    assert click[1] == "click"
    state_id = click[5]
    state = next(item for item in payload["states"] if item["state_id"] == state_id)
    action_set = payload["action_sets"][state["action_set_id"]]
    assert {item[0] for item in action_set} == {"move", "attack", "spell"}


def test_replay_does_not_store_high_frequency_hover_position(tmp_path):
    recorder = DevUIReplay(tmp_path)
    path = recorder.finish(result=None)
    payload = json.loads(path.read_text(encoding="utf-8"))
    for state in payload["states"]:
        assert "hover_position" not in state
        assert "window_size" not in state
