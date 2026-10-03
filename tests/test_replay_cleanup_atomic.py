import json

import pytest

from tools.replay import cleanup_empty_replays


def test_cleanup_rebuild_restores_exact_old_root_after_swap_failure(tmp_path, monkeypatch):
    root = tmp_path / "replays"
    archive = root / "archive"
    archive.mkdir(parents=True)

    index = {
        "schema_version": 1,
        "hot_cache": [],
        "games": {},
        "important": {},
        "next_chunk": 2,
        "open_count": 1,
    }
    index_path = root / "index.json"
    index_path.write_text(
        json.dumps(index, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    chunk_path = archive / "chunk-000001.open"
    chunk_path.write_text("legacy replay bytes\n", encoding="utf-8")

    old_index = index_path.read_bytes()
    old_chunk = chunk_path.read_bytes()

    real_rename = cleanup_empty_replays.os.rename
    calls = 0

    def fail_second_rename(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected replacement failure")
        return real_rename(source, destination)

    monkeypatch.setattr(cleanup_empty_replays.os, "rename", fail_second_rename)

    with pytest.raises(OSError, match="injected replacement failure"):
        cleanup_empty_replays._rebuild(root, [])

    assert index_path.read_bytes() == old_index
    assert chunk_path.read_bytes() == old_chunk
    assert root.exists()
    assert archive.exists()
    assert not list(tmp_path.glob("replays.backup-*"))
    assert not list(tmp_path.glob("replays.cleanup-*"))
