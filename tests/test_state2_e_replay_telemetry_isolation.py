from pathlib import Path

from tools.replay.storage import ReplayStore
from tools.telemetry.runtime import TelemetryRecorder
from tools.telemetry.store import TelemetryStore
from tools.replay.storage import _canonical_json


def test_telemetry_failure_does_not_block_replay_storage(tmp_path: Path):
    replay_root = tmp_path / "replays"
    telemetry_path = tmp_path / "telemetry.jsonl"

    replay = ReplayStore(replay_root)
    event = {
        "schema_version": 1,
        "game_id": "game-isolated",
        "created_at": "2026-09-08T00:00:00+00:00",
        "metadata": {"mode": "test", "engine_commit": "test", "rules_hash": "r", "hero_config_hash": "h"},
        "initial": {"side_to_move": "brancas", "turns_without_capture": 0, "pieces": [], "effects": []},
        "moves": [],
        "result": {"winner": "Brancas", "termination_reason": "test", "plies": 0, "final_hash": 0},
    }
    import hashlib, json
    event["record_sha256"] = hashlib.sha256(
        json.dumps({k: v for k, v in event.items() if k != "record_sha256"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    class FailingTelemetry(TelemetryStore):
        def append(self, _event):
            raise OSError("telemetry sink unavailable")

    recorder = TelemetryRecorder(FailingTelemetry(telemetry_path), session_id="s2e")
    assert recorder.action_rejected(reason="telemetry_probe") is None

    replay.save(event)
    assert replay.load("game-isolated")["game_id"] == "game-isolated"
    assert recorder.telemetry_write_failures == 1
