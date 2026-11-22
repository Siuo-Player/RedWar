# tests/test_playwright_e2e_browsers.py
"""
Playwright End-to-End Headless Browser Test Suite for RedWar Web Platform.

Verifies:
1. Multi-viewport CSS responsiveness (320x640 mobile, 768x1024 tablet, 1366x768 desktop)
   with zero horizontal overflow and strict error tracking (pageerror and console error).
2. Live interactive UI tabs and panel toggling with real visibility assertions (is_visible)
   and mutual exclusivity verification across Academy, Puzzles, Analytics, Leaderboard, and Review.
3. Two-player browser multiplayer lifecycle: room joining, authoritative synchronization,
   resignation, post-game buttons, and UI control reset on rematch with clean WS server teardown.
"""
from __future__ import annotations

import asyncio
from http.server import ThreadingHTTPServer
import json
import threading
import time
from typing import Any, Generator
import pytest

playwright = pytest.importorskip("playwright", reason="playwright is required for browser E2E tests")
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from engine.ratings import LeaderboardManager
from online.server import app as ws_app
from online.server.room import RoomManager
from online.server.web_app import RedWarWebApp, _RedWarHTTPRequestHandler


@pytest.fixture(scope="module")
def web_and_ws_servers(tmp_path_factory) -> Generator[dict[str, Any], None, None]:
    """Start HTTP and WebSocket servers and always stop their threads and event loop."""
    tmp_dir = tmp_path_factory.mktemp("playwright_servers")
    db_file = tmp_dir / "ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    ws_app.manager = RoomManager(leaderboard_manager=lb)

    http_app = RedWarWebApp(host="127.0.0.1", port=0)
    handler_cls = type("BoundRedWarHandler", (_RedWarHTTPRequestHandler,), {"app": http_app})
    http_server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    http_app._server = http_server
    http_port = http_server.server_port
    http_thread = threading.Thread(target=http_server.serve_forever, name="redwar-playwright-http", daemon=True)
    http_thread.start()

    loop = asyncio.new_event_loop()
    loop_started = threading.Event()

    def _run_ws_loop() -> None:
        asyncio.set_event_loop(loop)
        loop_started.set()
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    ws_thread = threading.Thread(target=_run_ws_loop, name="redwar-playwright-ws", daemon=True)
    ws_thread.start()

    ws_server = None
    try:
        assert loop_started.wait(timeout=5.0), "WebSocket event loop failed to start within 5.0 seconds"

        async def _start_ws_server():
            import websockets

            return await websockets.serve(ws_app.gerir_conexao, "127.0.0.1", 0)

        start_future = asyncio.run_coroutine_threadsafe(_start_ws_server(), loop)
        ws_server = start_future.result(timeout=5.0)
        ws_port = ws_server.sockets[0].getsockname()[1]

        yield {
            "http_url": f"http://127.0.0.1:{http_port}",
            "ws_url": f"ws://127.0.0.1:{ws_port}",
            "http_app": http_app,
        }
    finally:
        cleanup_errors: list[Exception] = []
        try:
            http_app.stop()
        except Exception as exc:
            cleanup_errors.append(exc)
        finally:
            http_thread.join(timeout=3.0)
        if http_thread.is_alive():
            cleanup_errors.append(RuntimeError("HTTP server thread did not stop cleanly"))

        try:
            if ws_server is not None and not loop.is_closed():
                async def _stop_ws_server() -> None:
                    ws_server.close()
                    await ws_server.wait_closed()

                stop_future = asyncio.run_coroutine_threadsafe(_stop_ws_server(), loop)
                stop_future.result(timeout=5.0)
        except Exception as exc:
            cleanup_errors.append(exc)
        finally:
            if not loop.is_closed():
                loop.call_soon_threadsafe(loop.stop)
            ws_thread.join(timeout=3.0)
            if ws_thread.is_alive():
                cleanup_errors.append(RuntimeError("WebSocket event-loop thread did not stop cleanly"))

        if cleanup_errors:
            details = "; ".join(str(error) for error in cleanup_errors)
            raise RuntimeError(f"Playwright server teardown failed: {details}") from cleanup_errors[0]


@pytest.fixture(scope="module")
def chromium_browser() -> Generator[Browser, None, None]:
    """Reuse one Chromium process while keeping each test in its own BrowserContext."""
    with sync_playwright() as playwright_instance:
        browser = playwright_instance.chromium.launch(headless=True)
        yield browser
        browser.close()


def _is_ignorable_favicon(url_or_message: str) -> bool:
    return "favicon.ico" in url_or_message.lower()


def attach_browser_error_capture(page: Page) -> list[str]:
    """Collect uncaught JS errors, console errors, failed requests, and HTTP error responses."""
    errors: list[str] = []

    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    page.on(
        "console",
        lambda message: errors.append(f"console: {message.text}")
        if message.type == "error" and not _is_ignorable_favicon(message.text)
        else None,
    )
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"request failed: {request.method} {request.url} ({request.failure})"
        )
        if not _is_ignorable_favicon(request.url)
        else None,
    )
    page.on(
        "response",
        lambda response: errors.append(f"HTTP {response.status}: {response.url}")
        if response.status >= 400 and not _is_ignorable_favicon(response.url)
        else None,
    )
    return errors


def assert_browser_has_no_errors(errors: list[str], label: str) -> None:
    assert not errors, f"{label} reported browser/runtime/network errors:\n" + "\n".join(errors)


def click_canvas_square(page: Page, r: int, c: int, grid_size: int = 8) -> None:
    """Simulate a real mouse click on the given board coordinates on the canvas."""
    canvas = page.query_selector("#gameBoard")
    assert canvas is not None, "Canvas #gameBoard not found"
    box = canvas.bounding_box()
    assert box is not None, "Canvas bounding box is None"
    cell_w = box["width"] / grid_size
    cell_h = box["height"] / grid_size
    x = box["x"] + c * cell_w + cell_w / 2
    y = box["y"] + r * cell_h + cell_h / 2
    page.mouse.click(x, y)


def test_playwright_responsive_viewports_and_dom_integrity(web_and_ws_servers, chromium_browser):
    """Verify that the RedWar web application adapts across mobile, tablet, and desktop viewports,
    and maintains zero horizontal overflow across all major interactive tabs with strict JS error capturing.
    """
    http_url = web_and_ws_servers["http_url"]

    viewports = [
        {"name": "mobile_compact", "width": 320, "height": 640},
        {"name": "tablet_portrait", "width": 768, "height": 1024},
        {"name": "desktop_widescreen", "width": 1366, "height": 768},
    ]

    for vp in viewports:
        context: BrowserContext = chromium_browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
        page: Page = context.new_page()

        browser_errors = attach_browser_error_capture(page)

        page.goto(http_url, wait_until="domcontentloaded")
        page.evaluate("""async () => {
            await document.fonts.ready;
            await Promise.all(
                Array.from(document.images, image => image.decode().catch(() => undefined))
            );
            await new Promise(resolve =>
                requestAnimationFrame(() => requestAnimationFrame(resolve))
            );
        }""")

        # Check Canvas exists and is rendered
        canvas = page.query_selector("#gameBoard")
        assert canvas is not None, f"Canvas #gameBoard not found in viewport {vp['name']}"
        box = canvas.bounding_box()
        assert box is not None and box["width"] > 0 and box["height"] > 0, (
            f"Canvas must have non-zero dimensions in viewport {vp['name']}"
        )
        assert box["width"] <= vp["width"], f"Canvas width {box['width']} exceeds viewport {vp['width']}"

        # Check horizontal overflow across all tabs: scrollWidth must not exceed innerWidth
        tab_selectors = ["#tabAcademy", "#tabPuzzles", "#tabAnalytics", "#tabLeaderboard", "#tabReview"]
        for tab_sel in tab_selectors:
            el = page.query_selector(tab_sel)
            if el:
                page.click(tab_sel)
                overflow = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth")
                assert overflow, f"Horizontal overflow detected in {vp['name']} on tab {tab_sel}"

        # Check primary controls are visible
        btn_resign = page.query_selector("#btnResign")
        assert btn_resign is not None, f"Button #btnResign missing in {vp['name']}"

        assert_browser_has_no_errors(browser_errors, f"Responsive viewport {vp['name']}")

        context.close()


def test_playwright_interactive_panels_and_tabs(web_and_ws_servers, chromium_browser):
    """Verify tab navigation toggles panels between Academy, Puzzles, Analytics, Leaderboard, and Review
    using real visibility checks (is_visible) and verifying mutual exclusivity (inactive panels are hidden).
    """
    http_url = web_and_ws_servers["http_url"]

    context: BrowserContext = chromium_browser.new_context()
    page: Page = context.new_page()

    browser_errors = attach_browser_error_capture(page)

    page.goto(http_url, wait_until="domcontentloaded")
    page.evaluate("""async () => {
        await document.fonts.ready;
        await Promise.all(
            Array.from(document.images, image => image.decode().catch(() => undefined))
        );
        await new Promise(resolve =>
            requestAnimationFrame(() => requestAnimationFrame(resolve))
        );
    }""")

    # 1. Click Academy Tab -> academyPanel visible, others hidden
    page.click("#tabAcademy")
    assert page.is_visible("#academyPanel"), "Academy panel should be visible after clicking tabAcademy"
    assert not page.is_visible("#puzzlesPanel"), "Puzzles panel should be hidden"
    assert not page.is_visible("#analyticsPanel"), "Analytics panel should be hidden"
    assert not page.is_visible("#leaderboardPanel"), "Leaderboard panel should be hidden"
    assert not page.is_visible("#reviewPanel"), "Review panel should be hidden"
    assert not page.is_visible("#playPanel"), "Play panel should be hidden"

    # 2. Click Puzzles Tab -> puzzlesPanel visible, others hidden
    page.click("#tabPuzzles")
    assert page.is_visible("#puzzlesPanel"), "Puzzles panel should be visible after clicking tabPuzzles"
    assert not page.is_visible("#academyPanel"), "Academy panel should be hidden"
    assert not page.is_visible("#analyticsPanel"), "Analytics panel should be hidden"
    assert not page.is_visible("#leaderboardPanel"), "Leaderboard panel should be hidden"
    assert not page.is_visible("#reviewPanel"), "Review panel should be hidden"
    assert not page.is_visible("#playPanel"), "Play panel should be hidden"

    # 3. Click Analytics Tab -> analyticsPanel visible, others hidden
    page.click("#tabAnalytics")
    assert page.is_visible("#analyticsPanel"), "Analytics panel should be visible after clicking tabAnalytics"
    assert not page.is_visible("#academyPanel"), "Academy panel should be hidden"
    assert not page.is_visible("#puzzlesPanel"), "Puzzles panel should be hidden"
    assert not page.is_visible("#leaderboardPanel"), "Leaderboard panel should be hidden"
    assert not page.is_visible("#reviewPanel"), "Review panel should be hidden"
    assert not page.is_visible("#playPanel"), "Play panel should be hidden"

    # 4. Click Leaderboard Tab -> leaderboardPanel visible, others hidden
    page.click("#tabLeaderboard")
    assert page.is_visible("#leaderboardPanel"), "Leaderboard panel should be visible after clicking tabLeaderboard"
    assert not page.is_visible("#academyPanel"), "Academy panel should be hidden"
    assert not page.is_visible("#puzzlesPanel"), "Puzzles panel should be hidden"
    assert not page.is_visible("#analyticsPanel"), "Analytics panel should be hidden"
    assert not page.is_visible("#reviewPanel"), "Review panel should be hidden"
    assert not page.is_visible("#playPanel"), "Play panel should be hidden"

    # 5. Click Game Review Tab -> reviewPanel visible, others hidden
    page.click("#tabReview")
    assert page.is_visible("#reviewPanel"), "Review panel should be visible after clicking tabReview"
    assert not page.is_visible("#academyPanel"), "Academy panel should be hidden"
    assert not page.is_visible("#puzzlesPanel"), "Puzzles panel should be hidden"
    assert not page.is_visible("#analyticsPanel"), "Analytics panel should be hidden"
    assert not page.is_visible("#leaderboardPanel"), "Leaderboard panel should be hidden"
    assert not page.is_visible("#playPanel"), "Play panel should be hidden"

    # 6. Click Play Tab -> playPanel visible, others hidden
    page.click("#tabPlay")
    assert page.is_visible("#playPanel"), "Play panel should be visible after clicking tabPlay"
    assert not page.is_visible("#academyPanel"), "Academy panel should be hidden"
    assert not page.is_visible("#puzzlesPanel"), "Puzzles panel should be hidden"
    assert not page.is_visible("#analyticsPanel"), "Analytics panel should be hidden"
    assert not page.is_visible("#leaderboardPanel"), "Leaderboard panel should be hidden"
    assert not page.is_visible("#reviewPanel"), "Review panel should be hidden"

    assert_browser_has_no_errors(browser_errors, "Interactive tab switching")
    context.close()


def test_playwright_dual_player_web_multiplayer(web_and_ws_servers, chromium_browser):
    """Verify live dual-browser multiplayer interaction, real legal moves, state synchronization,
    rejection rollback, resignation, and rematch button reset using Playwright conditional waits.
    """
    http_url = web_and_ws_servers["http_url"]
    ws_url = web_and_ws_servers["ws_url"]
    room_id = f"PLAYWRIGHT_ROOM_{int(time.time() * 1000)}"

    ctx_alice: BrowserContext = chromium_browser.new_context()
    ctx_bob: BrowserContext = chromium_browser.new_context()

    page_alice: Page = ctx_alice.new_page()
    page_bob: Page = ctx_bob.new_page()

    alice_errors = attach_browser_error_capture(page_alice)
    bob_errors = attach_browser_error_capture(page_bob)

    # Load page for both players and configure WebSocket endpoint
    for page, pid in [(page_alice, "alice_pw"), (page_bob, "bob_pw")]:
        page.goto(http_url, wait_until="domcontentloaded")
        page.evaluate(f"""
            localStorage.setItem('redwar_ws_url', '{ws_url}');
            localStorage.setItem('redwar_online_player_id', '{pid}');
        """)

    # Connect Alice to room
    page_alice.evaluate(f"""
        document.getElementById('opponentSelect').value = 'online_room';
        connectOnlineWebSocket('{room_id}');
    """)
    page_alice.wait_for_function("() => typeof socket !== 'undefined' && socket && socket.readyState === 1", timeout=5000)

    # Connect Bob to room
    page_bob.evaluate(f"""
        document.getElementById('opponentSelect').value = 'online_room';
        connectOnlineWebSocket('{room_id}');
    """)
    page_bob.wait_for_function("() => typeof socket !== 'undefined' && socket && socket.readyState === 1", timeout=5000)

    # Both players send ready handshake
    page_alice.evaluate("if (typeof socket !== 'undefined' && socket && socket.readyState === 1) socket.send(JSON.stringify({ tipo: 'pronto' }));")
    page_bob.evaluate("if (typeof socket !== 'undefined' && socket && socket.readyState === 1) socket.send(JSON.stringify({ tipo: 'pronto' }));")

    # Wait conditionally for match start on both browsers
    page_alice.wait_for_function("() => typeof myOnlineColor !== 'undefined' && (myOnlineColor === 'brancas' || myOnlineColor === 'pretas')", timeout=5000)
    page_bob.wait_for_function("() => typeof myOnlineColor !== 'undefined' && (myOnlineColor === 'brancas' || myOnlineColor === 'pretas')", timeout=5000)
    page_alice.wait_for_function("() => typeof isGameOver !== 'undefined' && !isGameOver && typeof currentTurn !== 'undefined' && currentTurn === 'white'", timeout=5000)
    page_bob.wait_for_function("() => typeof isGameOver !== 'undefined' && !isGameOver && typeof currentTurn !== 'undefined' && currentTurn === 'white'", timeout=5000)

    alice_color = page_alice.evaluate("myOnlineColor")
    bob_color = page_bob.evaluate("myOnlineColor")
    assert {alice_color, bob_color} == {"brancas", "pretas"}, f"Colors assigned: Alice={alice_color}, Bob={bob_color}"

    page_white = page_alice if alice_color == "brancas" else page_bob
    page_black = page_bob if alice_color == "brancas" else page_alice

    # --- MOVE 1: White executes legal move via REAL CANVAS CLICKS (Bone from (6, 2) to (5, 2)) ---
    click_canvas_square(page_white, 6, 2)
    click_canvas_square(page_white, 5, 2)

    # Wait conditionally for both browsers to receive authoritative board update
    page_white.wait_for_function("() => typeof boardData !== 'undefined' && boardData && boardData[5][2] !== null && boardData[6][2] === null && currentTurn === 'black'", timeout=5000)
    page_black.wait_for_function("() => typeof boardData !== 'undefined' && boardData && boardData[5][2] !== null && boardData[6][2] === null && currentTurn === 'black'", timeout=5000)

    # Invariant: Move 1 synchronized identically between White and Black
    pw_piece_name = page_white.evaluate("boardData[5][2].name")
    pb_piece_name = page_black.evaluate("boardData[5][2].name")
    assert pw_piece_name == pb_piece_name == "Bone", f"Mismatch in move 1 piece: White={pw_piece_name}, Black={pb_piece_name}"

    # --- MOVE 2: Black executes legal move via REAL CANVAS CLICKS (Bone from (1, 2) to (2, 2)) ---
    click_canvas_square(page_black, 1, 2)
    click_canvas_square(page_black, 2, 2)

    # Wait conditionally for both browsers to receive authoritative board update
    page_white.wait_for_function("() => typeof boardData !== 'undefined' && boardData && boardData[2][2] !== null && boardData[1][2] === null && currentTurn === 'white'", timeout=5000)
    page_black.wait_for_function("() => typeof boardData !== 'undefined' && boardData && boardData[2][2] !== null && boardData[1][2] === null && currentTurn === 'white'", timeout=5000)

    pw_b22 = page_white.evaluate("boardData[2][2].name")
    pb_b22 = page_black.evaluate("boardData[2][2].name")
    assert pw_b22 == pb_b22 == "Bone", f"Mismatch in move 2 piece: White={pw_b22}, Black={pb_b22}"

    # --- MOVE REJECTION & ROLLBACK: Black attempts illegal out-of-turn move ---
    page_black.evaluate("""
        isOnlineMovePending = true;
        prePendingMoveSnapshot = {
            boardData: JSON.parse(JSON.stringify(boardData)),
            currentTurn: currentTurn,
            moveHistory: [...moveHistory],
            evalHistory: [...evalHistory],
            classifiedMoves: JSON.parse(JSON.stringify(classifiedMoves))
        };
        socket.send(JSON.stringify({
            tipo: 'acao',
            type: 'move',
            start: [2, 2],
            end: [3, 2]
        }));
    """)
    page_black.wait_for_function("() => typeof isOnlineMovePending !== 'undefined' && !isOnlineMovePending", timeout=5000)
    black_turn_after_reject = page_black.evaluate("currentTurn")
    assert black_turn_after_reject == "white", "Turn must roll back to white after illegal out-of-turn move"

    # --- RESIGNATION ---
    alice_resign_disp = page_alice.evaluate("document.getElementById('btnResign').style.display")
    assert alice_resign_disp != "none", "btnResign must be visible during active match"

    page_white.click("#btnResign")
    page_white.wait_for_function("() => typeof isGameOver !== 'undefined' && isGameOver", timeout=5000)
    page_black.wait_for_function("() => typeof isGameOver !== 'undefined' && isGameOver", timeout=5000)

    # Invariant: Post-game UI shows rematch and hides resign
    page_white.wait_for_function("() => document.getElementById('btnRematch').style.display !== 'none'", timeout=5000)
    page_white.wait_for_function("() => document.getElementById('btnResign').style.display === 'none'", timeout=5000)

    # --- REMATCH ---
    page_white.click("#btnRematch")
    page_black.click("#btnRematch")

    # Wait for color swap
    page_alice.wait_for_function(f"() => typeof myOnlineColor !== 'undefined' && myOnlineColor !== '{alice_color}'", timeout=5000)
    alice_new_color = page_alice.evaluate("myOnlineColor")
    assert alice_new_color != alice_color, f"Colors must be swapped on rematch (was {alice_color}, now {alice_new_color})"

    page_alice.wait_for_function("() => document.getElementById('btnResign').style.display !== 'none'", timeout=5000)
    page_alice.wait_for_function("() => document.getElementById('btnRematch').style.display === 'none'", timeout=5000)

    assert_browser_has_no_errors(alice_errors, "Alice browser")
    assert_browser_has_no_errors(bob_errors, "Bob browser")

    ctx_alice.close()
    ctx_bob.close()



def test_playwright_hero_academy_catalogue_and_support_spells(web_and_ws_servers, chromium_browser):
    """Load all 30 lessons in Chromium and solve legal ally/overlapping-destination spells."""
    page = chromium_browser.new_page()
    browser_errors = attach_browser_error_capture(page)

    page.goto(web_and_ws_servers["http_url"], wait_until="domcontentloaded")
    page.wait_for_function(
        "() => document.querySelectorAll('#heroSelect option').length === 30",
        timeout=10000,
    )

    # Loading the catalogue must not silently switch a normal match into Academy mode.
    assert page.evaluate("isAcademyMode") is False
    options = page.locator("#heroSelect option")
    labels = [option.text_content() for option in options.all()]
    assert any("Bone" in label and "não draftável" in label for label in labels)
    assert any("Ghoul" in label and "não draftável" in label for label in labels)
    assert any("StoneWall" in label and "não draftável" in label for label in labels)

    page.click("#tabAcademy")
    assert page.evaluate("isAcademyMode") is True

    # Purify targets an allied unit. The click handler must not mistake it for a selection change.
    page.select_option("#heroSelect", "cleric")
    click_canvas_square(page, 5, 3)
    click_canvas_square(page, 4, 3)
    page.wait_for_function(
        "() => document.getElementById('academyFeedback').textContent.includes('Sucesso!')",
        timeout=3000,
    )

    # Pyromancer's Ignite shares its destination with a possible movement candidate.
    # The Academy must select the required spell action rather than the movement.
    page.select_option("#heroSelect", "pyromancer")
    click_canvas_square(page, 5, 3)
    click_canvas_square(page, 4, 4)
    page.wait_for_function(
        "() => document.getElementById('academyFeedback').textContent.includes('Sucesso!')",
        timeout=3000,
    )

    assert_browser_has_no_errors(browser_errors, "Hero Academy browser")
    page.context.close()



def test_playwright_board_drag_matches_click_move(web_and_ws_servers, chromium_browser):
    """Dragging a friendly piece to a legal empty square must execute the same move as click-to-move."""
    page = chromium_browser.new_page()
    errors = attach_browser_error_capture(page)
    page.goto(web_and_ws_servers["http_url"], wait_until="domcontentloaded")
    page.wait_for_function(
        "() => typeof boardData !== 'undefined' && boardData && boardData[6] && boardData[6][2] !== null",
        timeout=5000,
    )

    canvas = page.locator("#gameBoard")
    box = canvas.bounding_box()
    assert box is not None
    cell_w, cell_h = box["width"] / 8, box["height"] / 8
    start = (box["x"] + 2.5 * cell_w, box["y"] + 6.5 * cell_h)
    end = (box["x"] + 2.5 * cell_w, box["y"] + 5.5 * cell_h)

    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(*end, steps=5)
    page.mouse.up()

    page.wait_for_function(
        "() => boardData[5][2] !== null && boardData[6][2] === null",
        timeout=1500,
    )
    assert page.evaluate("boardData[5][2].name") == "Bone"
    assert_browser_has_no_errors(errors, "Board drag interaction")
    page.context.close()


def test_playwright_reduced_motion_disables_board_related_transitions(web_and_ws_servers, chromium_browser):
    """The UI must honor prefers-reduced-motion without changing game state or functionality."""
    context = chromium_browser.new_context(reduced_motion="reduce")
    page = context.new_page()
    errors = attach_browser_error_capture(page)
    page.goto(web_and_ws_servers["http_url"], wait_until="domcontentloaded")

    transition_duration = page.locator(".eval-bar-fill").evaluate(
        "(element) => getComputedStyle(element).transitionDuration"
    )
    durations = [float(value.strip().removesuffix("s")) for value in transition_duration.split(",")]
    assert all(duration <= 0.01 for duration in durations), (
        f"Reduced-motion preference must disable non-essential transitions; got {transition_duration}"
    )
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
    assert_browser_has_no_errors(errors, "Reduced motion")
    context.close()
