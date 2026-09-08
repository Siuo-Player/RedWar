import pytest
from pathlib import Path


def test_online_server_has_not_become_authoritative_yet():
    source = Path("online/server/app.py").read_text(encoding="utf-8")
    if "GameState" not in source or "execute_action" not in source:
        pytest.fail(
            "G blocker: online/server/app.py is still relay-only; "
            "server-side GameState/execute_action authority is not implemented"
        )
