from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts" / "lite-windows-acceptance"
LOG = ARTIFACTS / "launcher-smoke.log"
SUMMARY = ARTIFACTS / "launcher-smoke.json"

USER32 = ctypes.windll.user32
WM_CLOSE = 0x0010
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def find_window(timeout: float = 60.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found: list[int] = []

        @EnumWindowsProc
        def callback(hwnd, _):
            if not USER32.IsWindowVisible(hwnd):
                return True
            length = USER32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            USER32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value.startswith("RedWar -"):
                found.append(hwnd)
            return True

        USER32.EnumWindows(callback, 0)
        if found:
            return found[0]
        time.sleep(0.25)
    raise TimeoutError("The real RedWar launcher did not create its SDL window")


def close_window(proc: subprocess.Popen, hwnd: int) -> None:
    if USER32.IsWindow(hwnd):
        USER32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            check=False,
            capture_output=True,
            text=True,
        )
        proc.wait(timeout=10)


def _launch_once(log_path: Path) -> dict:
    with open(log_path, "wb", buffering=0) as log:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
        env["SDL_VIDEO_WINDOW_POS"] = "40,40"
        proc = subprocess.Popen(
            ["cmd.exe", "/d", "/c", str(ROOT / "run_redwar.bat")],
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        hwnd = find_window()
        title_len = USER32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(title_len + 1)
        USER32.GetWindowTextW(hwnd, buf, title_len + 1)
        title = buf.value
        time.sleep(0.5)
        close_window(proc, hwnd)
    return {"window_title": title, "launcher_returncode": proc.returncode}


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    first = _launch_once(ARTIFACTS / "launcher-smoke-first.log")
    second = _launch_once(ARTIFACTS / "launcher-smoke-second.log")

    result = {
        "status": "passed" if first["launcher_returncode"] == 0 and second["launcher_returncode"] == 0 else "failed",
        "launches": [first, second],
        "clean_relaunch": first["launcher_returncode"] == 0 and second["launcher_returncode"] == 0,
    }
    SUMMARY.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if result["status"] != "passed":
        raise SystemExit(f"Launcher smoke failed: {result}")
