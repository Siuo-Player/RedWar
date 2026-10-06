from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Callable

from PIL import ImageGrab


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts" / "lite-windows-acceptance"
SCREENSHOTS = ARTIFACTS / "os-e2e-screenshots"
REPLAY_ROOT = ARTIFACTS / "os-e2e-replays"
LOG_PATH = ARTIFACTS / "os-e2e-launcher.log"
SUMMARY_PATH = ARTIFACTS / "os-e2e-summary.json"

USER32 = ctypes.windll.user32

# GitHub-hosted Windows runners can apply DPI virtualization. Make Win32
# coordinates and screenshots refer to the same physical desktop space.
try:
    USER32.SetProcessDPIAware()
except AttributeError:
    pass

SW_RESTORE = 9
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040
WM_CLOSE = 0x0010

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


EnumWindowsProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
)

USER32.IsWindow.argtypes = [wintypes.HWND]
USER32.IsWindow.restype = wintypes.BOOL
USER32.IsWindowVisible.argtypes = [wintypes.HWND]
USER32.IsWindowVisible.restype = wintypes.BOOL
USER32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
USER32.GetWindowTextLengthW.restype = ctypes.c_int
USER32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
USER32.GetWindowTextW.restype = ctypes.c_int
USER32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
USER32.GetWindowThreadProcessId.restype = wintypes.DWORD
USER32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
USER32.EnumWindows.restype = wintypes.BOOL
USER32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
USER32.GetClientRect.restype = wintypes.BOOL
USER32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(POINT)]
USER32.ClientToScreen.restype = wintypes.BOOL
USER32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
USER32.GetWindowRect.restype = wintypes.BOOL
USER32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
USER32.ShowWindow.restype = wintypes.BOOL
USER32.SetForegroundWindow.argtypes = [wintypes.HWND]
USER32.SetForegroundWindow.restype = wintypes.BOOL
USER32.BringWindowToTop.argtypes = [wintypes.HWND]
USER32.BringWindowToTop.restype = wintypes.BOOL
USER32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
USER32.SetCursorPos.restype = wintypes.BOOL
USER32.mouse_event.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_size_t,
]
USER32.mouse_event.restype = None
USER32.PostMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
USER32.PostMessageW.restype = wintypes.BOOL
USER32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
USER32.SetWindowPos.restype = wintypes.BOOL


def get_title(hwnd: int) -> str:
    length = USER32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    USER32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def find_window_for_process(pid: int, timeout: float = 90.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found: list[int] = []

        @EnumWindowsProc
        def callback(hwnd, _lparam):
            if not USER32.IsWindowVisible(hwnd):
                return True
            owner_pid = wintypes.DWORD()
            USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_pid))
            if owner_pid.value != pid:
                return True

            title = get_title(hwnd)
            if title.startswith("RedWar -"):
                found.append(hwnd)
                return False
            return True

        USER32.EnumWindows(callback, 0)
        if found:
            return found[0]
        time.sleep(0.25)

    raise TimeoutError(f"RedWar SDL window for PID {pid} did not appear")


def client_geometry(hwnd: int) -> tuple[tuple[int, int], tuple[int, int, int, int], tuple[int, int, int, int]]:
    client = RECT()
    if not USER32.GetClientRect(hwnd, ctypes.byref(client)):
        raise ctypes.WinError()

    top_left = POINT(0, 0)
    if not USER32.ClientToScreen(hwnd, ctypes.byref(top_left)):
        raise ctypes.WinError()

    width = client.right - client.left
    height = client.bottom - client.top
    client_box = (
        top_left.x,
        top_left.y,
        top_left.x + width,
        top_left.y + height,
    )

    outer = RECT()
    if not USER32.GetWindowRect(hwnd, ctypes.byref(outer)):
        raise ctypes.WinError()
    outer_box = (outer.left, outer.top, outer.right, outer.bottom)
    return (width, height), client_box, outer_box


def bring_to_front(hwnd: int) -> None:
    USER32.ShowWindow(hwnd, SW_RESTORE)
    USER32.BringWindowToTop(hwnd)
    USER32.SetForegroundWindow(hwnd)
    time.sleep(0.15)


def client_point(
    hwnd: int,
    x: float,
    y: float,
    logical_size: tuple[int, int] = (1300, 800),
) -> tuple[int, int]:
    (width, height), client_box, _ = client_geometry(hwnd)
    logical_w, logical_h = logical_size
    return (
        client_box[0] + round(x * width / logical_w),
        client_box[1] + round(y * height / logical_h),
    )


def click_client(hwnd: int, x: float, y: float) -> None:
    bring_to_front(hwnd)
    sx, sy = client_point(hwnd, x, y)
    if not USER32.SetCursorPos(sx, sy):
        raise ctypes.WinError()
    USER32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.04)
    USER32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.30)


def drag_client(hwnd: int, x1: float, y1: float, x2: float, y2: float) -> None:
    bring_to_front(hwnd)
    sx1, sy1 = client_point(hwnd, x1, y1)
    sx2, sy2 = client_point(hwnd, x2, y2)

    USER32.SetCursorPos(sx1, sy1)
    USER32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    for step in range(1, 17):
        ratio = step / 16.0
        USER32.SetCursorPos(
            round(sx1 + (sx2 - sx1) * ratio),
            round(sy1 + (sy2 - sy1) * ratio),
        )
        time.sleep(0.025)
    USER32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.30)


def screenshot(hwnd: int, name: str) -> tuple[Path, tuple[int, int]]:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    size, client_box, _ = client_geometry(hwnd)
    image = ImageGrab.grab(bbox=client_box)
    if image.width < size[0] or image.height < size[1]:
        raise AssertionError(
            f"Screenshot unexpectedly smaller than client: {image.size} < {size}"
        )

    path = SCREENSHOTS / f"{name}.png"
    image.save(path)

    rgb = image.convert("RGB")
    sampled = list(rgb.getdata())[:: max(1, len(rgb.getdata()) // 5000)]
    if len(set(sampled)) < 8:
        raise AssertionError(f"Captured UI appears blank/uniform: {name}")
    return path, image.size


def crop_sha(
    path: Path,
    logical_box: tuple[int, int, int, int],
    logical_size: tuple[int, int] = (1300, 800),
) -> str:
    with ImageGrab.open(path) if False else __import__("PIL.Image").Image.open(path) as image:
        image = image.convert("RGB")
        width, height = image.size
        x1, y1, x2, y2 = logical_box
        box = (
            round(x1 * width / logical_size[0]),
            round(y1 * height / logical_size[1]),
            round(x2 * width / logical_size[0]),
            round(y2 * height / logical_size[1]),
        )
        return hashlib.sha256(image.crop(box).tobytes()).hexdigest()


def image_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait_until(predicate: Callable[[], bool], timeout: float, description: str) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except Exception:
            pass
        time.sleep(0.20)
    raise TimeoutError(f"Timed out waiting for {description}")


def wait_for_title(hwnd: int, expected: str, timeout: float = 15.0) -> None:
    wait_until(lambda: expected in get_title(hwnd), timeout, f"title containing {expected!r}")


def menu_center(index: int, width: int, height: int) -> tuple[int, int]:
    top = max(int(height * 0.42), 155)
    return (width // 2, top + 27 + index * 68)


def mode_center(index: int, width: int, height: int) -> tuple[int, int]:
    top = max(125, int(height * 0.28))
    if index < 3:
        return (width // 2, top + 28 + index * 70)
    return (width // 2, top + 253)


def ai_type_center(index: int, width: int, height: int) -> tuple[int, int]:
    top = int(height * 0.35)
    if index < 2:
        return (width // 2, top + 40 + index * 110)
    return (width // 2, top + 275)


def draft_geometry(width: int, height: int) -> tuple[int, int, int]:
    tile = min(width // 9, max(8, (height - 200) // 8))
    return 60, 80, tile


def ranger_center(width: int, height: int) -> tuple[int, int]:
    with open(ROOT / "engine" / "heroes_config.json", encoding="utf-8") as handle:
        heroes = json.load(handle)

    catalog = [
        (name, data)
        for name, data in heroes.items()
        if bool(data.get("draftable", True))
    ]
    catalog.sort(key=lambda item: int(item[1].get("cost", 0)), reverse=True)
    index = next(i for i, (name, _) in enumerate(catalog) if name == "Ranger")

    panel_x = 60 + 8 * draft_geometry(width, height)[2] + 30
    button_w = (350 - 60) // 2
    row = index // 2
    col = index % 2
    return (
        panel_x + 20 + col * (button_w + 20) + button_w // 2,
        90 + row * 55 + 22,
    )


def board_center(width: int, height: int, row: int, col: int) -> tuple[int, int]:
    off_x, off_y, tile = draft_geometry(width, height)
    return (
        off_x + col * tile + tile // 2,
        off_y + row * tile + tile // 2,
    )


def ready_center(width: int, height: int) -> tuple[int, int]:
    _, _, tile = draft_geometry(width, height)
    panel_x = 60 + 8 * tile + 30
    return panel_x + 175, height - 65


def surrender_center(width: int, height: int) -> tuple[int, int]:
    off_x, off_y, tile = draft_geometry(width, height)
    top = min(height - 42, off_y + 8 * tile + 54)
    return off_x + 64, top + 17


def analysis_button_center(width: int, height: int, kind: str) -> tuple[int, int]:
    _, _, tile = draft_geometry(width, height)
    panel_x = 60 + 8 * tile + 30
    if kind == "prev":
        return panel_x + 60, height - 60
    if kind == "next":
        return panel_x + 150, height - 60
    return panel_x + 265, height - 60


def close_window(proc: subprocess.Popen[bytes], hwnd: int) -> None:
    if USER32.IsWindow(hwnd):
        USER32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    try:
        proc.wait(timeout=12)
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            check=False,
            capture_output=True,
            text=True,
        )
        proc.wait(timeout=12)


def launch(log_mode: str = "a") -> tuple[subprocess.Popen[bytes], int]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    REPLAY_ROOT.mkdir(parents=True, exist_ok=True)
    log_handle = open(LOG_PATH, log_mode + "b", buffering=0)

    env = os.environ.copy()
    env["SDL_VIDEO_WINDOW_POS"] = "40,40"
    env["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    env["PYTHONUTF8"] = "1"
    env.pop("SDL_VIDEODRIVER", None)
    env.pop("SDL_AUDIODRIVER", None)
    env["REDWAR_REPLAY_DIR"] = str(REPLAY_ROOT)

    proc = subprocess.Popen(
        ["cmd.exe", "/d", "/c", str(ROOT / "run_redwar.bat")],
        cwd=ROOT,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    log_handle.close()

    hwnd = find_window_for_process(proc.pid)
    bring_to_front(hwnd)
    return proc, hwnd


def ensure_window_size(hwnd: int, target_w: int, target_h: int) -> None:
    current, _, outer = client_geometry(hwnd)
    frame_w = (outer[2] - outer[0]) - current[0]
    frame_h = (outer[3] - outer[1]) - current[1]

    if not USER32.SetWindowPos(
        hwnd,
        0,
        40,
        40,
        target_w + frame_w,
        target_h + frame_h,
        SWP_NOZORDER | SWP_SHOWWINDOW,
    ):
        raise ctypes.WinError()

    wait_until(
        lambda: client_geometry(hwnd)[0] == (target_w, target_h),
        8.0,
        f"real window resize to {target_w}x{target_h}",
    )
    bring_to_front(hwnd)


def visual_terminal(path: Path) -> bool:
    # Terminal banner uses the product's success/danger colors.
    try:
        from PIL import Image
        with Image.open(path).convert("RGB") as image:
            pixels = list(image.getdata())
        sample = pixels[::4]
        near_success = sum(
            1 for p in sample
            if abs(p[0] - 100) <= 28 and abs(p[1] - 255) <= 28 and abs(p[2] - 100) <= 28
        )
        near_danger = sum(
            1 for p in sample
            if abs(p[0] - 255) <= 28 and abs(p[1] - 70) <= 28 and abs(p[2] - 70) <= 28
        )
        return near_success > 10 or near_danger > 10
    except Exception:
        return False


def read_replay_count() -> int:
    index = REPLAY_ROOT / "index.json"
    if not index.exists():
        return 0
    data = json.loads(index.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        records = data.get("records")
        if isinstance(records, list):
            return len(records)
    return 0


def run_acceptance() -> dict:
    checks: list[dict] = []
    screenshots: list[str] = []

    proc = None
    hwnd = None

    def shot(name: str) -> Path:
        path, size = screenshot(hwnd, name)
        screenshots.append(str(path.relative_to(ROOT)))
        checks.append({"evidence": path.name, "capture_size": size})
        return path

    def action(name: str) -> None:
        if checks and "name" in checks[-1]:
            checks.append({"name": name, "passed": True})
        else:
            checks.append({"name": name, "passed": True})

    try:
        proc, hwnd = launch()

        width, height = client_geometry(hwnd)[0]
        initial = shot("01-launch-menu")
        checks.append({
            "name": "real_launcher_and_sdl_window",
            "passed": width > 0 and height > 0 and "RedWar -" in get_title(hwnd),
        })

        click_client(hwnd, *menu_center(3, width, height))
        settings_before = shot("02-settings-before")

        click_client(hwnd, width // 2, int(height * 0.28) + 81)
        settings_toggle = shot("03-settings-toggle")
        toggle_changed = image_sha(settings_before) != image_sha(settings_toggle)
        if not toggle_changed:
            raise AssertionError("Real OS click on sound toggle produced no visible change")
        checks.append({
            "name": "settings_sound_toggle_via_os_input",
            "passed": True,
        })

        click_client(hwnd, width // 2 + 75, int(height * 0.28) + 209)
        settings_volume = shot("04-settings-volume")
        if image_sha(settings_toggle) == image_sha(settings_volume):
            raise AssertionError("Real OS click on volume control produced no visible change")
        checks.append({
            "name": "settings_volume_via_os_input",
            "passed": True,
        })

        click_client(hwnd, width // 2, height - 48)
        menu_after_settings = shot("05-menu-after-settings")

        click_client(hwnd, *menu_center(0, width, height))
        click_client(hwnd, *mode_center(0, width, height))
        click_client(hwnd, *ai_type_center(0, width, height))

        # 1500 -> 100 ELO by dragging the difficulty slider to its left edge.
        drag_client(hwnd, 674, 240, 450, 240)
        difficulty = shot("06-difficulty-lite")
        click_client(hwnd, width // 2, int(height * 0.55) + 30)
        wait_for_title(hwnd, "VS Ares")
        draft = shot("07-vs-ares-draft")

        ranger_x, ranger_y = ranger_center(width, height)
        click_client(hwnd, ranger_x, ranger_y)
        for index, col in enumerate(range(4), start=1):
            before = shot(f"08-vs-ares-draft-before-{index}")
            click_client(hwnd, *board_center(width, height, 6, col))
            after = shot(f"08-vs-ares-draft-after-{index}")
            if image_sha(before) == image_sha(after):
                raise AssertionError(f"Ranger placement {index} caused no visible change")

        click_client(hwnd, *ready_center(width, height))
        wait_until(lambda: "VS Ares" in get_title(hwnd), 10.0, "VS Ares battle title")
        battle = shot("09-vs-ares-battle")

        click_client(hwnd, *board_center(width, height, 6, 0))
        selected = shot("10-vs-ares-selected")

        click_client(hwnd, *board_center(width, height, 6, 1))
        invalid = shot("11-vs-ares-invalid-action")
        if image_sha(selected) == image_sha(invalid):
            raise AssertionError("Invalid occupied-square click caused no visible UI change")

        click_client(hwnd, *board_center(width, height, 6, 0))
        selected_again = shot("12-vs-ares-selected-again")
        click_client(hwnd, *board_center(width, height, 5, 0))
        moved = shot("13-vs-ares-human-move")
        if image_sha(selected_again) == image_sha(moved):
            raise AssertionError("Real OS click sequence did not move the Ranger")

        wait_for_title(hwnd, "O Teu Turno", timeout=90.0)
        ares_after_move = shot("14-vs-ares-after-real-ares")

        click_client(hwnd, *surrender_center(width, height))
        wait_until(lambda: visual_terminal(shot("15-vs-ares-terminal-probe")), 15.0, "VS Ares terminal feedback")
        terminal = SCREENSHOTS / "15-vs-ares-terminal-probe.png"
        checks.append({
            "name": "vs_ares_real_input_play_surrender_terminal",
            "passed": True,
            "terminal_screenshot": str(terminal.relative_to(ROOT)),
        })

        click_client(hwnd, *analysis_button_center(width, height, "menu"))
        time.sleep(0.5)
        replay_menu = shot("16-vs-ares-replays")
        replay_count_before = read_replay_count()
        if replay_count_before < 1:
            raise AssertionError("VS Ares surrender did not persist a replay")
        checks.append({
            "name": "vs_ares_replay_persisted",
            "passed": True,
            "replay_count": replay_count_before,
        })

        click_client(hwnd, width // 2, height - 52)
        time.sleep(0.4)

        click_client(hwnd, *menu_center(0, width, height))
        click_client(hwnd, *mode_center(1, width, height))
        hotseat_white = shot("17-hotseat-white-draft")

        click_client(hwnd, ranger_x, ranger_y)
        for index, col in enumerate(range(4), start=1):
            click_client(hwnd, *board_center(width, height, 6, col))
            shot(f"18-hotseat-white-placement-{index}")
        click_client(hwnd, *ready_center(width, height))
        shot("19-hotseat-black-draft")

        click_client(hwnd, ranger_x, ranger_y)
        for index, col in enumerate(range(4), start=1):
            click_client(hwnd, *board_center(width, height, 0, col))
            shot(f"20-hotseat-black-placement-{index}")
        click_client(hwnd, *ready_center(width, height))
        wait_until(lambda: "Turno das Brancas" in get_title(hwnd), 10.0, "hot-seat battle title")
        shot("21-hotseat-battle")

        click_client(hwnd, *board_center(width, height, 6, 0))
        click_client(hwnd, *board_center(width, height, 5, 0))
        shot("22-hotseat-white-move")
        click_client(hwnd, *board_center(width, height, 0, 0))
        click_client(hwnd, *board_center(width, height, 1, 0))
        shot("23-hotseat-black-move")

        click_client(hwnd, *surrender_center(width, height))
        wait_until(lambda: visual_terminal(shot("24-hotseat-terminal-probe")), 15.0, "hot-seat terminal feedback")
        checks.append({
            "name": "hotseat_real_input_play_surrender_terminal",
            "passed": True,
        })

        click_client(hwnd, *analysis_button_center(width, height, "menu"))
        time.sleep(0.5)

        responsive = []
        for target in ((980, 700), (1300, 800), (1600, 900), (1920, 1080)):
            ensure_window_size(hwnd, *target)
            path = shot(f"responsive-{target[0]}x{target[1]}")
            actual = client_geometry(hwnd)[0]
            if actual != target:
                raise AssertionError(
                    f"Responsive resize mismatch: actual={actual}, target={target}"
                )
            responsive.append({
                "target_client": target,
                "actual_client": actual,
                "screenshot": str(path.relative_to(ROOT)),
            })
        checks.append({
            "name": "responsive_real_window_sizes",
            "passed": True,
            "sizes": responsive,
        })

        launcher_log = LOG_PATH.read_text(encoding="utf-8", errors="replace")
        audio_backend_unavailable = "Áudio indisponível" in launcher_log
        checks.append({
            "name": "audio_backend_startup_attempt",
            "passed": True,
            "environmental_backend_unavailable": audio_backend_unavailable,
            "human_hearing_equivalent": False,
        })

        close_window(proc, hwnd)
        checks.append({
            "name": "real_window_clean_quit",
            "passed": proc.returncode == 0,
        })
        proc = None
        hwnd = None

        proc2, hwnd2 = launch()
        shot("25-relaunch-menu")
        close_window(proc2, hwnd2)
        checks.append({
            "name": "real_launcher_relaunch_and_quit",
            "passed": proc2.returncode == 0,
        })

        if not all(item.get("passed", True) for item in checks if "name" in item):
            raise AssertionError("At least one recorded acceptance check failed")

        summary = {
            "schema_version": "redwar-lite-windows-os-e2e-v1",
            "status": "passed",
            "commit": os.environ.get("GITHUB_SHA", "unknown"),
            "runner_os": os.environ.get("RUNNER_OS", "unknown"),
            "launcher": "run_redwar.bat",
            "input": "Win32 cursor positioning + mouse_event",
            "display": "real SDL windows driver",
            "audio": {
                "backend_startup_unavailable": audio_backend_unavailable,
                "human_hearing_equivalent": False,
            },
            "checks": checks,
            "screenshots": screenshots,
            "replay_count": replay_count_before,
        }
        SUMMARY_PATH.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return summary
    except Exception as exc:
        summary = {
            "schema_version": "redwar-lite-windows-os-e2e-v1",
            "status": "failed",
            "commit": os.environ.get("GITHUB_SHA", "unknown"),
            "runner_os": os.environ.get("RUNNER_OS", "unknown"),
            "screenshots": screenshots,
            "error": f"{type(exc).__name__}: {exc}",
        }
        SUMMARY_PATH.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    finally:
        if proc is not None and hwnd is not None and proc.poll() is None:
            close_window(proc, hwnd)


if __name__ == "__main__":
    run_acceptance()
