from __future__ import annotations

import asyncio
import json
import pytest
import websockets

from online.server import app
from online.server.room import GameRoom, RoomManager
from online.server.security import SecurityGuard


def test_identity_theft_prevention_on_join_room():
    """Verify that an attacker cannot steal another player's seat or private token via join_room."""
    async def _run():
        app.jogadores.clear()
        app.prontos.clear()
        app.sessao = None
        app._room_sockets.clear()
        app._connections.clear()
        app.manager = RoomManager()

        server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        ws_url = f"ws://127.0.0.1:{port}"

        try:
            # 1. Alice connects and joins room
            alice_ws = await websockets.connect(ws_url)
            _ = await alice_ws.recv()  # legacy setup notification

            await alice_ws.send(json.dumps({
                "tipo": "join_room",
                "room_id": "ROOM_SECURITY_1",
                "player_id": "Alice",
                "role_preference": "brancas"
            }))
            alice_resp = json.loads(await alice_ws.recv())
            assert alice_resp["tipo"] == "room_joined"
            assert alice_resp["cor"] == "brancas"
            alice_token = alice_resp["reconnect_token"]
            assert alice_token is not None
            assert alice_token.startswith("tok_")

            # 2. Attacker connects and attempts to hijack Alice's seat using join_room
            attacker_ws = await websockets.connect(ws_url)
            _ = await attacker_ws.recv()  # legacy setup notification

            await attacker_ws.send(json.dumps({
                "tipo": "join_room",
                "room_id": "ROOM_SECURITY_1",
                "player_id": "Alice",
                "role_preference": "brancas"
            }))
            attacker_resp = json.loads(await attacker_ws.recv())

            # MUST be an error, NOT room_joined, and MUST NOT leak alice_token!
            assert attacker_resp["tipo"] == "erro"
            assert "Identificador de jogador já em jogo nesta sala" in attacker_resp["mensagem"]
            assert "reconnect_token" not in attacker_resp

            # 3. Bob legitimately joins black
            bob_ws = await websockets.connect(ws_url)
            _ = await bob_ws.recv()
            await bob_ws.send(json.dumps({
                "tipo": "join_room",
                "room_id": "ROOM_SECURITY_1",
                "player_id": "Bob",
                "role_preference": "pretas"
            }))
            bob_resp = json.loads(await bob_ws.recv())
            assert bob_resp["tipo"] == "room_joined"
            assert bob_resp["cor"] == "pretas"
            assert bob_resp["reconnect_token"] != alice_token

            # 4. Attacker attempts fake reconnect without valid token
            await attacker_ws.send(json.dumps({
                "tipo": "reconnect",
                "room_id": "ROOM_SECURITY_1",
                "token": "tok_fake_token_malicious_12345678901234567890"
            }))
            fake_reconnect_resp = json.loads(await attacker_ws.recv())
            assert fake_reconnect_resp["tipo"] == "erro"
            assert "reconexao falhou" in fake_reconnect_resp["mensagem"]

            # 5. Alice closes old socket and reconnects with her valid secret token
            await alice_ws.close()
            alice_new_ws = await websockets.connect(ws_url)
            _ = await alice_new_ws.recv()

            await alice_new_ws.send(json.dumps({
                "tipo": "reconnect",
                "room_id": "ROOM_SECURITY_1",
                "token": alice_token
            }))
            reconnect_resp = json.loads(await alice_new_ws.recv())
            assert reconnect_resp["tipo"] == "reconnect_success"
            assert reconnect_resp["cor"] == "brancas"
            assert reconnect_resp["player_id"] == "Alice"
            assert reconnect_resp["reconnect_token"] != alice_token  # Rotated!

            # 6. Reusing old token is rejected
            attacker_reusing = await websockets.connect(ws_url)
            _ = await attacker_reusing.recv()
            await attacker_reusing.send(json.dumps({
                "tipo": "reconnect",
                "room_id": "ROOM_SECURITY_1",
                "token": alice_token
            }))
            stale_resp = json.loads(await attacker_reusing.recv())
            assert stale_resp["tipo"] == "erro"

            await attacker_ws.close()
            await bob_ws.close()
            await alice_new_ws.close()
            await attacker_reusing.close()
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(_run())


def test_origin_header_validation():
    """Verify WebSocket Origin validation strictly blocks unauthorized origins."""
    async def _run():
        app.jogadores.clear()
        app.prontos.clear()
        app.sessao = None

        server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        ws_url = f"ws://127.0.0.1:{port}"

        try:
            # Allowed origin
            allowed_ws = await websockets.connect(
                ws_url,
                additional_headers={"Origin": "https://siuo-player.github.io"}
            )
            setup = json.loads(await allowed_ws.recv())
            assert setup["tipo"] == "setup"
            await allowed_ws.close()

            # Disallowed origin
            evil_ws = await websockets.connect(
                ws_url,
                additional_headers={"Origin": "http://evil-attacker.com"}
            )
            msg = await evil_ws.recv()
            err = json.loads(msg)
            assert err["tipo"] == "erro"
            assert "origem nao autorizada" in err["mensagem"]

            with pytest.raises(websockets.exceptions.ConnectionClosed):
                await evil_ws.recv()
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(_run())


def test_schema_validation_rejects_malformed_packets():
    """Verify schema validator rejects unknown types and extraneous payload attributes."""
    async def _run():
        app.jogadores.clear()
        app.prontos.clear()
        app.sessao = None

        server = await websockets.serve(app.gerir_conexao, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        ws_url = f"ws://127.0.0.1:{port}"

        try:
            ws = await websockets.connect(ws_url)
            _ = await ws.recv()  # setup

            # Malformed packet: unknown type
            await ws.send(json.dumps({"tipo": "hacker_probe_command"}))
            resp1 = json.loads(await ws.recv())
            assert resp1["tipo"] == "erro"
            assert "formato de mensagem invalido" in resp1["mensagem"]

            # Malformed packet: forbidden extra keys in pronto
            await ws.send(json.dumps({"tipo": "pronto", "exploit_field": "injected"}))
            resp2 = json.loads(await ws.recv())
            assert resp2["tipo"] == "erro"
            assert "formato de mensagem invalido" in resp2["mensagem"]

            await ws.close()
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(_run())


def test_rematch_forbidden_during_active_match():
    """Verify that rematch cannot be requested while a match is ongoing."""
    room = GameRoom("R_ACTIVE", "standard_8x8", "blitz_3_2")
    room.add_player("p1", "brancas")
    room.add_player("p2", "pretas")
    room.start_game()

    assert room.is_started is True
    assert room.is_finished is False

    # Propose rematch while ongoing
    assert room.propose_rematch("p1") is False
    assert room.rematch_proposals == set()
