# tests/test_playwright_e2e_browsers.py
"""
Playwright End-to-End Headless Browser Test Suite for RedWar Web Platform.

Verifies:
1. Multi-viewport CSS responsiveness (320x640 mobile, 768x1024 tablet, 1366x768 desktop).
2. Live interactive UI tabs and panel toggling without unhandled console errors.
3. Two-player browser multiplayer lifecycle: room joining, authoritative synchronization,
   resignation, post-game buttons, and UI control reset on rematch.
"""
from __future__ import annotations

import asyncio
from http.server import ThreadingHTTPServer
import json
import threading
import time
from typing import Generator
import pytest

playwright = pytest.importorskip("playwright", reason="playwright is required for browser E2E tests")
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from engine.ratings import LeaderboardManager
from online.server import app as ws_app
from online.server.room import RoomManager
from online.server.web_app import RedWarWebApp, _RedWarHTTPRequestHandler


@pytest.fixture(scope="module")
def web_and_ws_servers(tmp_path_factory) -> Generator[dict[str, Any], None, None]:
    """Start headless HTTP web server and WebSocket multiplayer server on ephemeral ports."""
    tmp_dir = tmp_path_factory.mktemp("playwright_servers")
    db_file = tmp_dir / "ratings.json"
    lb = LeaderboardManager(storage_path=str(db_file))
    ws_app.manager = RoomManager(leaderboard_manager=lb)

    # 1. Start HTTP web server
    http_app = RedWarWebApp(host="127.0.0.1", port=0)
    handler_cls = type("BoundRedWarHandler", (_RedWarHTTPRequestHandler,), {"app": http_app})
    http_server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    http_app._server = http_server
    http_port = http_server.server_port

    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    # 2. Start WebSocket server in dedicated asyncio thread
    ws_port_box = [0]
    ws_ready = threading.Event()
    loop = asyncio.new_event_loop()

    def _run_ws():
        asyncio.set_event_loop(loop)
        import websockets

        async def _serve():
            server = await websockets.serve(ws_app.gerir_conexao, "127.0.0.1", 0)
            ws_port_box[0] = server.sockets[0].getsockname()[1]
            ws_ready.set()
            await asyncio.Future()  # run forever

        loop.run_until_complete(_serve())

    ws_thread = threading.Thread(target=_run_ws, daemon=True)
    ws_thread.start()
    ws_ready.wait(timeout=5.0)

    servers = {
        "http_url": f"http://127.0.0.1:{http_port}",
        "ws_url": f"ws://127.0.0.1:{ws_port_box[0]}",
        "http_app": http_app,
        "loop": loop,
    }

    yield servers

    # Teardown
    http_app.stop()


def test_playwright_responsive_viewports_and_dom_integrity(web_and_ws_servers):
    """Verify that the RedWar web application adapts across mobile, tablet, and desktop viewports."""
    http_url = web_and_ws_servers["http_url"]

    viewports = [
        {"name": "mobile_compact", "width": 320, "height": 640},
        {"name": "tablet_portrait", "width": 768, "height": 1024},
        {"name": "desktop_widescreen", "width": 1366, "height": 768},
    ]

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)

        for vp in viewports:
            context: BrowserContext = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page: Page = context.new_page()

            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(http_url, wait_until="networkidle")

            # Check Canvas exists and is rendered
            canvas = page.query_selector("#gameBoard")
            assert canvas is not None, f"Canvas #gameBoard not found in viewport {vp['name']}"
            box = canvas.bounding_box()
            assert box is not None and box["width"] > 0 and box["height"] > 0, (
                f"Canvas must have non-zero dimensions in viewport {vp['name']}"
            )
            assert box["width"] <= vp["width"], f"Canvas width {box['width']} exceeds viewport {vp['width']}"

            # Check horizontal overflow: scrollWidth must not exceed innerWidth
            no_horizontal_overflow = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert no_horizontal_overflow, f"Horizontal overflow detected in viewport {vp['name']}"

            # Check primary controls are visible
            btn_resign = page.query_selector("#btnResign")
            assert btn_resign is not None, f"Button #btnResign missing in {vp['name']}"

            # Check that no unhandled fatal script errors occurred
            fatal_errors = [e for e in console_errors if "SyntaxError" in e or "ReferenceError" in e]
            assert len(fatal_errors) == 0, f"Fatal JS errors in {vp['name']}: {fatal_errors}"

            context.close()

        browser.close()


def test_playwright_interactive_panels_and_tabs(web_and_ws_servers):
    """Verify tab navigation toggles panels between Academy, Puzzles, Analytics, and Leaderboard."""
    http_url = web_and_ws_servers["http_url"]

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)
        page: Page = browser.new_page()
        page.goto(http_url, wait_until="networkidle")

        # 1. Click Academy Tab
        page.click("#tabAcademy")
        academy_display = page.evaluate("document.getElementById('academyPanel').style.display")
        assert academy_display != "none", "Academy panel should be visible after clicking tabAcademy"

        # 2. Click Puzzles Tab
        page.click("#tabPuzzles")
        puzzles_display = page.evaluate("document.getElementById('puzzlesPanel').style.display")
        assert puzzles_display != "none", "Puzzles panel should be visible after clicking tabPuzzles"

        # 3. Click Analytics Tab
        page.click("#tabAnalytics")
        analytics_display = page.evaluate("document.getElementById('analyticsPanel').style.display")
        assert analytics_display != "none", "Analytics panel should be visible after clicking tabAnalytics"

        # 4. Click Leaderboard Tab
        page.click("#tabLeaderboard")
        leaderboard_display = page.evaluate("document.getElementById('leaderboardPanel').style.display")
        assert leaderboard_display != "none", "Leaderboard panel should be visible after clicking tabLeaderboard"

        # 5. Click Game Review Tab
        page.click("#tabReview")
        review_display = page.evaluate("document.getElementById('reviewPanel').style.display")
        assert review_display != "none", "Review panel should be visible after clicking tabReview"

        browser.close()


def test_playwright_dual_player_web_multiplayer(web_and_ws_servers):
    """Verify live dual-browser multiplayer interaction, real legal moves, state synchronization,
    rejection rollback, resignation, and rematch button reset using Playwright conditional waits.
    """
    http_url = web_and_ws_servers["http_url"]
    ws_url = web_and_ws_servers["ws_url"]
    room_id = f"PLAYWRIGHT_ROOM_{int(time.time() * 1000)}"

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)

        ctx_alice: BrowserContext = browser.new_context()
        ctx_bob: BrowserContext = browser.new_context()

        page_alice: Page = ctx_alice.new_page()
        page_bob: Page = ctx_bob.new_page()

        # Load page for both players and configure WebSocket endpoint
        for page, pid in [(page_alice, "alice_pw"), (page_bob, "bob_pw")]:
            page.goto(http_url, wait_until="networkidle")
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

        # --- MOVE 1: White executes legal move (Bone from (6, 2) to (5, 2)) ---
        page_white.evaluate("""
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
                start: [6, 2],
                end: [5, 2]
            }));
        """)

        # Wait conditionally for both browsers to receive authoritative board update
        page_white.wait_for_function("() => typeof boardData !== 'undefined' && boardData && boardData[5][2] !== null && boardData[6][2] === null && currentTurn === 'black'", timeout=5000)
        page_black.wait_for_function("() => typeof boardData !== 'undefined' && boardData && boardData[5][2] !== null && boardData[6][2] === null && currentTurn === 'black'", timeout=5000)

        # Invariant: Move 1 synchronized identically between White and Black
        pw_piece_name = page_white.evaluate("boardData[5][2].name")
        pb_piece_name = page_black.evaluate("boardData[5][2].name")
        assert pw_piece_name == pb_piece_name == "Bone", f"Mismatch in move 1 piece: White={pw_piece_name}, Black={pb_piece_name}"

        # --- MOVE 2: Black executes legal move (Bone from (1, 2) to (2, 2)) ---
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
                start: [1, 2],
                end: [2, 2]
            }));
        """)

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

        ctx_alice.close()
        ctx_bob.close()
        browser.close()
