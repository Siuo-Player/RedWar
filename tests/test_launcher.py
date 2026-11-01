from __future__ import annotations

import pytest
import sys
from unittest.mock import patch, MagicMock

import launcher


def test_launcher_parser_defaults():
    parser = launcher.build_parser()
    args = parser.parse_args([])
    assert args.mode == "desktop"


def test_launcher_parser_web_mode():
    parser = launcher.build_parser()
    args = parser.parse_args(["web", "--port", "8080", "--host", "127.0.0.1"])
    assert args.mode == "web"
    assert args.port == 8080
    assert args.host == "127.0.0.1"


def test_launcher_parser_multiplayer_mode():
    parser = launcher.build_parser()
    args = parser.parse_args(["multiplayer", "--server", "ws://127.0.0.1:8765"])
    assert args.mode == "multiplayer"
    assert args.server == "ws://127.0.0.1:8765"


def test_launcher_parser_arena_mode():
    parser = launcher.build_parser()
    args = parser.parse_args(["arena", "--nodes", "100", "--games", "4"])
    assert args.mode == "arena"
    assert args.nodes == 100
    assert args.games == 4


def test_launcher_version():
    with pytest.raises(SystemExit) as exc:
        launcher.main(["--version"])
    assert exc.value.code == 0


@patch("launcher.run_desktop")
def test_launcher_dispatch_desktop(mock_desktop):
    launcher.main(["desktop"])
    mock_desktop.assert_called_once()


@patch("launcher.run_web")
def test_launcher_dispatch_web(mock_web):
    launcher.main(["web", "--port", "9090"])
    mock_web.assert_called_once_with(host="0.0.0.0", port=9090)


@patch("launcher.run_multiplayer")
def test_launcher_dispatch_multiplayer(mock_mp):
    launcher.main(["multiplayer", "--server", "ws://localhost:8765"])
    mock_mp.assert_called_once_with(server="ws://localhost:8765")


@patch("launcher.run_arena")
def test_launcher_dispatch_arena(mock_arena):
    launcher.main(["arena", "--nodes", "200", "--games", "8"])
    mock_arena.assert_called_once_with(nodes=200, games=8)

