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

from PIL import Image, ImageGrab


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts" / "lite-windows-acceptance"
SCREENSHOTS = ARTIFACTS / "screenshots"
LOG_PATH = ARTIFACTS / "launcher.log"
SUMMARY_PATH = ARTIFACTS / "acceptance-summary.json"

USER32 = ctypes.windll.user32

# Keep Win32 client coordinates and ImageGrab pixels in the same physical
# coordinate space. Hosted Windows runners can otherwise apply DPI scaling.
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

USER32.IsWindowVisible.argtypes = [wintypes.HWND]
USER32.IsWindowVisible.restype = wintypes.BOOL
USER32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
USER32.GetWindowTextLengthW.restype = ctypes.c_int
USER32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
USER32.GetWindowTextW.restype = ctypes.c_int
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
USER32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
USER32.SetCursorPos.restype = wintypes.BOOL
USER32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
USER32.mouse_event.restype = None
USER32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
USER32.PostMessageW.restype = wintypes.BOOL
USER32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
USER32.SetWindowPos.restype = wintypes.BOOL


def find_window(timeout: float = 90.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        handles: list[int] = []

        @EnumWindowsProc
        def callback(hwnd, _lparam):
            if USER32.IsWindowVisible(hwnd):
                length = USER32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                USER32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if title.startswith("RedWar -"):
                    handles.append(hwnd)
            return True

        USER32.EnumWindows(callback, 0)
        if handles:
            return handles[0]
        time.sleep(0.25)
    raise RuntimeError("RedWar SDL window did not appear")


def get_title(hwnd: int) -> str:
    length = USER32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    USER32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def get_geometry(hwnd: int) -> tuple[tuple[int, int], tuple[int, int, int, int]]:
    client = RECT()
    USER32.GetClientRect(hwnd, ctypes.byref(client))
    point = POINT(0, 0)
    if not USER32.ClientToScreen(hwnd, ctypes.byref(point)):
        raise ctypes.WinError()

    outer = RECT()
    USER32.GetWindowRect(hwnd, ctypes.byref(outer))

    size = (client.right - client.left, client.bottom - client.top)
    client_box = (point.x, point.y, point.x + size[0], point.y + size[1])
    outer_box = (outer.left, outer.top, outer.right, outer.bottom)
    return size, outer_box


def bring_to_front(hwnd: int) -> None:
    USER32.ShowWindow(hwnd, SW_RESTORE)
    USER32.SetForegroundWindow(hwnd)
    time.sleep(0.15)


def client_point(hwnd: int, x: float, y: float) -> tuple[int, int]:
    (width, height), client_box = get_geometry(hwnd)
    cx = round(x * width / 1300.0)
    cy = round(y * height / 800.0)
    return client_box[0] + cx, client_box[1] + cy


def click_client(hwnd: int, x: float, y: float) -> None:
    bring_to_front(hwnd)
    sx, sy = client_point(hwnd, x, y)
    USER32.SetCursorPos(sx, sy)
    USER32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.04)
    USER32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.25)


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
    time.sleep(0.25)


def screenshot(hwnd: int, name: str) -> Path:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    client_size, outer = get_geometry(hwnd)

    image = ImageGrab.grab(window=hwnd, include_layered_windows=True, scale_down=False)
    outer_size = (outer[2] - outer[0], outer[3] - outer[1])

    if image.size == client_size:
        client_image = image
    elif image.size == outer_size:
        client = RECT()
        USER32.GetClientRect(hwnd, ctypes.byref(client))
        point = POINT(0, 0)
        if not USER32.ClientToScreen(hwnd, ctypes.byref(point)):
            raise ctypes.WinError()
        offset_x = point.x - outer[0]
        offset_y = point.y - outer[1]
        box = (
            max(0, offset_x),
            max(0, offset_y),
            max(0, offset_x) + client_size[0],
            max(0, offset_y) + client_size[1],
        )
        client_image = image.crop(box)
    else:
        raise AssertionError(
            f"Unexpected HWND screenshot size: {image.size}; "
            f"client={client_size}, outer={outer_size}"
        )

    if client_image.size != client_size:
        raise AssertionError(
            f"Client screenshot size mismatch: {client_image.size} != {client_size}"
        )

    path = SCREENSHOTS / f"{name}.png"
    client_image.save(path)
    return path


def crop_pixels(path: Path, logical_box: tuple[int, int, int, int]) -> list[tuple[int, int, int]]:
    with Image.open(path) as image:
        image = image.convert("RGB")
        width, height = image.size
        x1, y1, x2, y2 = logical_box
        box = (
            round(x1 * width / 1300.0),
            round(y1 * height / 800.0),
            round(x2 * width / 1300.0),
            round(y2 * height / 800.0),
        )
        return list(image.crop(box).getdata())


def count_near(
    path: Path,
    target: tuple[int, int, int],
    tolerance: int = 12,
    logical_box: tuple[int, int, int, int] = (0, 0, 1300, 800),
) -> int:
    pixels = crop_pixels(path, logical_box)
    return sum(
        1
        for pixel in pixels[::4]
        if all(abs(pixel[index] - target[index]) <= tolerance for index in range(3))
    )


def assert_changed(before: Path, after: Path, label: str) -> None:
    if hashlib.sha256(before.read_bytes()).digest() == hashlib.sha256(after.read_bytes()).digest():
        raise AssertionError(f"Expected visible UI change after {label}")


def wait_until(predicate: Callable[[], bool], timeout: float, description: str) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {description}")


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

    off_x, _, tile = draft_geometry(width, height)
    panel_x = off_x + 8 * tile + 30
    button_w = (350 - 60) // 2
    button_h = 45
    row = index // 2
    col = index % 2
    x = panel_x + 20 + col * (button_w + 20)
    y = 90 + row * 55
    return x + button_w // 2, y + button_h // 2


def board_center(width: int, height: int, row: int, col: int) -> tuple[int, int]:
    off_x, off_y, tile = draft_geometry(width, height)
    return off_x + col * tile + tile // 2, off_y + row * tile + tile // 2


def ready_center(width: int, height: int) -> tuple[int, int]:
    off_x, _, tile = draft_geometry(width, height)
    panel_x = off_x + 8 * tile + 30
    return panel_x + 175, height - 65


def surrender_center(width: int, height: int) -> tuple[int, int]:
    off_x, off_y, tile = draft_geometry(width, height)
    return off_x + 64, min(height - 42, off_y + 8 * tile + 54) + 17


def analysis_next_center(width: int, height: int) -> tuple[int, int]:
    _, _, tile = draft_geometry(width, height)
    return 60 + 8 * tile + 30 + 150, height - 60


def analysis_exit_center(width: int, height: int) -> tuple[int, int]:
    _, _, tile = draft_geometry(width, height)
    return 60 + 8 * tile + 30 + 265, height - 60


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


def launch() -> tuple[subprocess.Popen, int]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    log_handle = open(LOG_PATH, "ab", buffering=0)

    env = os.environ.copy()
    env["SDL_VIDEO_WINDOW_POS"] = "40,40"
    env["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    env["REDWAR_REPLAY_DIR"] = str(ARTIFACTS / "replays")

    proc = subprocess.Popen(
        ["cmd.exe", "/d", "/c", str(ROOT / "run_redwar.bat")],
        cwd=ROOT,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
    )
    hwnd = find_window()
    bring_to_front(hwnd)
    return proc, hwnd


def ensure_size(hwnd: int, target_w: int, target_h: int) -> None:
    client, outer = get_geometry(hwnd)
    frame_w = (outer[2] - outer[0]) - client[0]
    frame_h = (outer[3] - outer[1]) - client[1]
    USER32.SetWindowPos(
        hwnd,
        0,
        40,
        40,
        target_w + frame_w,
        target_h + frame_h,
        SWP_NOZORDER | SWP_SHOWWINDOW,
    )
    wait_until(
        lambda: get_geometry(hwnd)[0] == (target_w, target_h),
        5.0,
        f"window resize to {target_w}x{target_h}",
    )
    bring_to_front(hwnd)


def audio_startup_status() -> dict:
    log = LOG_PATH.read_text(encoding="utf-8", errors="replace") if LOG_PATH.exists() else ""
    unavailable = "Áudio indisponível" in log
    return {
        "backend_startup_unavailable": unavailable,
        "human_hearing_equivalent": False,
        "note": "The Windows black-box runner verifies AudioManager startup/playback execution, but cannot establish human-perceived sound quality.",
    }


def run_acceptance() -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)

    proc, hwnd = launch()
    screenshots: list[str] = []
    checks: list[dict] = []

    def shot(name: str) -> Path:
        path = screenshot(hwnd, name)
        screenshots.append(str(path.relative_to(ROOT)))
        return path

    try:
        width, height = get_geometry(hwnd)[0]
        shot("01-menu-launch")
        checks.append({"name": "real_launcher_and_window", "passed": True})

        click_client(hwnd, *menu_center(3, width, height))
        settings_before = shot("02-settings-before")
        click_client(hwnd, width // 2, int(height * 0.28) + 81)
        settings_toggle = shot("03-settings-sound-toggle")
        click_client(hwnd, width // 2 + 75, int(height * 0.28) + 209)
        settings_volume = shot("04-settings-volume-up")
        assert_changed(settings_before, settings_toggle, "sound toggle")
        assert_changed(settings_toggle, settings_volume, "volume change")
        click_client(hwnd, width // 2, height - 48)
        shot("05-menu-after-settings")
        checks.append({"name": "settings_sound_and_volume", "passed": True})

        click_client(hwnd, *menu_center(0, width, height))
        click_client(hwnd, *mode_center(0, width, height))
        click_client(hwnd, *ai_type_center(0, width, height))
        drag_client(hwnd, 674, 240, 450, 240)
        click_client(hwnd, width // 2, int(height * 0.55) + 30)
        shot("06-vs-ares-draft")

        if "VS" not in get_title(hwnd):
            raise AssertionError(f"Unexpected VS Ares title: {get_title(hwnd)}")

        click_client(hwnd, *ranger_center(width, height))
        for col in range(4):
            before_place = shot(f"07-vs-ares-draft-before-{col + 1}")
            click_client(hwnd, *board_center(width, height, 6, col))
            after_place = shot(f"07-vs-ares-draft-after-{col + 1}")
            assert_changed(before_place, after_place, f"Ranger placement {col + 1}")

        click_client(hwnd, *ready_center(width, height))
        shot("08-vs-ares-battle-start")

        click_client(hwnd, *board_center(width, height, 6, 0))
        selected = shot("09-vs-ares-piece-selected")
        if count_near(selected, (255, 255, 50), 20, (55, 525, 140, 605)) < 3:
            raise AssertionError("Piece selection border was not rendered")
        if count_near(selected, (50, 255, 50), 85, (55, 525, 140, 605)) < 10:
            raise AssertionError("Legal move highlight was not visibly rendered")

        click_client(hwnd, *board_center(width, height, 6, 1))
        invalid_action = shot("10-vs-ares-invalid-action")
        assert_changed(selected, invalid_action, "invalid occupied-square click clearing selection")

        click_client(hwnd, *board_center(width, height, 6, 0))
        before_move = shot("11-vs-ares-before-move")
        click_client(hwnd, *board_center(width, height, 5, 0))
        after_move = shot("12-vs-ares-after-human-move")
        assert_changed(before_move, after_move, "human board move")

        wait_until(lambda: "O Teu Turno" in get_title(hwnd), 90.0, "real 100k Ares move")
        shot("13-vs-ares-after-real-ares-move")

        click_client(hwnd, *surrender_center(width, height))
        time.sleep(1.0)

        terminal = None
        for step in range(6):
            click_client(hwnd, *analysis_next_center(width, height))
            time.sleep(0.25)
            candidate = shot(f"14-vs-ares-analysis-{step + 1}")
            green = count_near(candidate, (100, 255, 100), 28, (180, 220, 1120, 620))
            red = count_near(candidate, (255, 70, 70), 28, (180, 220, 1120, 620))
            if green > 10 or red > 10:
                terminal = candidate
                break
        if terminal is None:
            raise AssertionError("VS Ares terminal banner was not visually detected")
        checks.append({"name": "vs_ares_play_and_terminal", "passed": True})

        click_client(hwnd, *analysis_exit_center(width, height))
        time.sleep(0.5)
        click_client(hwnd, *menu_center(2, width, height))
        time.sleep(0.5)
        replays = shot("15-replays-after-vs-ares")
        if count_near(replays, (100, 100, 100), 18, (300, 150, 1000, 650)) < 50:
            raise AssertionError("Persisted replay entry did not render")
        checks.append({"name": "replay_entrypoint_after_completed_game", "passed": True})
        click_client(hwnd, width // 2, height - 52)
        time.sleep(0.4)

        click_client(hwnd, *menu_center(0, width, height))
        click_client(hwnd, *mode_center(1, width, height))
        click_client(hwnd, *ranger_center(width, height))
        for col in range(4):
            before_place = shot(f"16-hotseat-white-before-{col + 1}")
            click_client(hwnd, *board_center(width, height, 6, col))
            after_place = shot(f"16-hotseat-white-after-{col + 1}")
            assert_changed(before_place, after_place, f"hot-seat white Ranger placement {col + 1}")
        click_client(hwnd, *ready_center(width, height))
        shot("16-hotseat-black-draft")

        click_client(hwnd, *ranger_center(width, height))
        for col in range(4):
            before_place = shot(f"17-hotseat-black-before-{col + 1}")
            click_client(hwnd, *board_center(width, height, 0, col))
            after_place = shot(f"17-hotseat-black-after-{col + 1}")
            assert_changed(before_place, after_place, f"hot-seat black Ranger placement {col + 1}")
        click_client(hwnd, *ready_center(width, height))
        shot("17-hotseat-battle")

        click_client(hwnd, *board_center(width, height, 6, 0))
        click_client(hwnd, *board_center(width, height, 5, 0))
        click_client(hwnd, *board_center(width, height, 1, 0))
        click_client(hwnd, *board_center(width, height, 2, 0))
        shot("18-hotseat-after-two-moves")

        click_client(hwnd, *surrender_center(width, height))
        time.sleep(0.8)

        hotseat_terminal = None
        for step in range(6):
            click_client(hwnd, *analysis_next_center(width, height))
            time.sleep(0.2)
            candidate = shot(f"19-hotseat-analysis-{step + 1}")
            if count_near(candidate, (100, 255, 100), 28, (180, 220, 1120, 620)) > 10:
                hotseat_terminal = candidate
                break
        if hotseat_terminal is None:
            raise AssertionError("Hot-seat terminal banner was not visually detected")
        checks.append({"name": "hotseat_draft_moves_and_terminal", "passed": True})

        click_client(hwnd, *analysis_exit_center(width, height))
        time.sleep(0.4)

        resize_records = []
        for target in ((980, 700), (1300, 800), (1600, 900), (1920, 1080)):
            ensure_size(hwnd, *target)
            path = shot(f"20-responsive-{target[0]}x{target[1]}")
            actual = get_geometry(hwnd)[0]
            if actual != target:
                raise AssertionError(f"Resize mismatch: actual={actual}, target={target}")
            resize_records.append({
                "target": target,
                "actual_client": actual,
                "screenshot": str(path.relative_to(ROOT)),
            })
        checks.append({"name": "responsive_real_window_sizes", "passed": True, "sizes": resize_records})

        audio = audio_startup_status()
        checks.append({"name": "audio_backend_startup", "passed": not audio["backend_startup_unavailable"]})

        close_window(proc, hwnd)
        checks.append({"name": "clean_quit", "passed": proc.returncode == 0})

        proc2, hwnd2 = launch()
        try:
            shot("21-relaunch-menu")
        finally:
            close_window(proc2, hwnd2)
        checks.append({"name": "launcher_relaunch_and_quit", "passed": proc2.returncode == 0})

        failed = [item for item in checks if not item.get("passed")]
        summary = {
            "schema_version": "redwar-lite-windows-blackbox-acceptance-v1",
            "commit": os.environ.get("GITHUB_SHA", "unknown"),
            "runner_os": os.environ.get("RUNNER_OS", "unknown"),
            "checks": checks,
            "screenshots": screenshots,
            "display": {"client_size": get_geometry(hwnd)[0], "dpi_normalized": True},
        "audio": audio,
            "status": "passed" if not failed else "failed",
        }
        SUMMARY_PATH.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if failed:
            raise AssertionError(
                "Black-box acceptance failures: " + ", ".join(str(item["name"]) for item in failed)
            )
        return summary
    except Exception as exc:
        summary = {
            "schema_version": "redwar-lite-windows-blackbox-acceptance-v1",
            "commit": os.environ.get("GITHUB_SHA", "unknown"),
            "runner_os": os.environ.get("RUNNER_OS", "unknown"),
            "checks": checks,
            "screenshots": screenshots,
            "error": f"{type(exc).__name__}: {exc}",
            "status": "failed",
        }
        SUMMARY_PATH.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    finally:
        if proc.poll() is None:
            close_window(proc, hwnd)


if __name__ == "__main__":
    run_acceptance()
