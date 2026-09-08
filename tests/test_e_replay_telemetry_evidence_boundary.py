from pathlib import Path


def test_replay_is_not_treated_as_arena_evidence():
    source = Path("docs/REPLAY_STORAGE.md").read_text(encoding="utf-8")
    assert "Real player games and Arena/hold-out experiments are different evidence classes." in source
    assert "must not silently become protected promotion or hold-out evidence" in source


def test_telemetry_store_is_append_only_and_sequence_checked():
    source = Path("tools/telemetry/store.py").read_text(encoding="utf-8")
    assert "Append-only local store" in source
    assert "event.sequence <= previous_sequence" in source
    assert "TelemetryCorruptionError" in source
