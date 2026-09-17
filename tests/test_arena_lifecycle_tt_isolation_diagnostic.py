from __future__ import annotations

import pytest

from tools.analytics.arena_lifecycle_tt_isolation_diagnostic import _clear_transposition_table


class _FakeBridge:
    def __init__(self, response: str):
        self.response = response
        self.commands: list[str] = []

    def send_command(self, command: str) -> None:
        self.commands.append(command)

    def read_response(self):
        return self.response


class _FakeBot:
    def __init__(self, response: str):
        self.bridge = _FakeBridge(response)


def test_clear_transposition_table_requires_protocol_ack():
    bot = _FakeBot("info string clearhash ok")

    _clear_transposition_table(bot)

    assert bot.bridge.commands == ["clearhash"]


def test_clear_transposition_table_fails_closed_on_unexpected_ack():
    bot = _FakeBot("info string something-else")

    with pytest.raises(RuntimeError, match="clearhash failed"):
        _clear_transposition_table(bot)

    assert bot.bridge.commands == ["clearhash"]
