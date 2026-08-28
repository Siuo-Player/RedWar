from __future__ import annotations

import json

from tools.replay.dev_ui import DevUIReplay


def test_ui_replay_deduplicates_identical_ui_states(tmp_path):
    recorder = DevUIReplay(tmp_path)

    first = recorder.log_ui(
        {
            "phase": "BATALHA",
            "selected_position": (4, 4),
            "available_actions": [
                {"type": "move", "target": (3, 4)},
                {"type": "spell", "spell_name": "nevada", "target": (4, 4)},
            ],
        }
    )
    second = recorder.log_ui(
        {
            "phase": "BATALHA",
            "selected_position": (4, 4),
            "available_actions": [
                {"type": "move", "target": (3, 4)},
                {"type": "spell", "spell_name": "nevada", "target": (4, 4)},
            ],
        }
    )

    assert first is True
    assert second is False
    assert recorder.event_count == 1


def test_click_and_ui_state_are_distinct_evidence(tmp_path):
    recorder = DevUIReplay(tmp_path)
    recorder.log_ui({"phase": "BATALHA", "selected_position": None, "available_actions": []})
    recorder.log_click(
        phase="BATALHA",
        position=(420, 315),
        button=1,
        context={"selected_position": None, "available_actions": []},
    )
    recorder.log_ui(
        {
            "phase": "BATALHA",
            "selected_position": (4, 4),
            "available_actions": [
                {"type": "move", "target": (3, 4)},
                {"type": "spell", "spell_name": "nevada", "target": (4, 4)},
            ],
        }
    )

    path = recorder.finish(result=None)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["evidence_class"] == "developer_ui_replay"
    assert [event["event"] for event in payload["events"]] == ["ui_state", "click", "ui_state"]
    assert payload["events"][2]["state"]["available_actions"]
