# online/server/app.py
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import websockets

from engine.game_modes import GameMode, GameModeType, TimeControl, get_preset_mode
from engine.ratings import LeaderboardManager
from online.server.authority import AuthoritativeSession
from online.server.room import GameRoom, RoomManager
from online.server.security import SecurityGuard, TokenBucketRateLimiter

rate_limiter = TokenBucketRateLimiter()

manager = RoomManager(leaderboard_manager=LeaderboardManager(storage_path="data/leaderboards/ratings.json"))

# Backward-compatible global state for legacy single-game clients/tests
jogadores: dict[Any, str] = {}
prontos: set[Any] = set()
sessao: AuthoritativeSession | None = None

# Room websocket connections: room_id -> set of websockets
_room_sockets: dict[str, set[Any]] = {}
# Connection metadata: websocket -> dict(room_id, player_id, cor, is_legacy, ready)
_connections: dict[Any, dict[str, Any]] = {}


def _mensagem_estado() -> dict[str, Any]:
    if sessao is None:
        raise RuntimeError("authoritative session is not available")
    return {"tipo": "estado_jogo", "dados": sessao.state_payload()}


async def _broadcast(payload: dict[str, Any]) -> None:
    if not jogadores:
        return
    mensagem = json.dumps(payload)
    for websocket in list(jogadores):
        try:
            await websocket.send(mensagem)
        except websockets.exceptions.ConnectionClosed:
            jogadores.pop(websocket, None)
            prontos.discard(websocket)


async def _broadcast_room(room_id: str, payload: dict[str, Any]) -> None:
    sockets = _room_sockets.get(room_id, set())
    if not sockets:
        return
    mensagem = json.dumps(payload)
    for ws in list(sockets):
        try:
            await ws.send(mensagem)
        except websockets.exceptions.ConnectionClosed:
            sockets.discard(ws)
            _connections.pop(ws, None)
    if not sockets:
        _room_sockets.pop(room_id, None)


async def _enviar_erro(websocket: Any, mensagem: str) -> None:
    try:
        await websocket.send(json.dumps({"tipo": "erro", "mensagem": mensagem}))
    except websockets.exceptions.ConnectionClosed:
        pass


def _extract_client_ip(websocket: Any) -> str:
    """Extract client IP address excluding ephemeral port to enforce per-IP rate limiting."""
    addr = getattr(websocket, "remote_address", None)
    if isinstance(addr, (list, tuple)) and len(addr) >= 1:
        return str(addr[0])
    return str(addr or "127.0.0.1")


def _extract_origin(websocket: Any) -> str | None:
    """Safely extract Origin header across websockets library versions."""
    request = getattr(websocket, "request", None)
    headers = getattr(request, "headers", None) or getattr(websocket, "request_headers", None)
    if headers:
        return headers.get("Origin") or headers.get("origin")
    return None


def _get_time_control(tc_name: str | None) -> TimeControl:
    if not tc_name:
        return TimeControl.rapid_10_0()

    name = tc_name.lower()
    if "bullet" in name:
        return TimeControl.bullet_1_0()
    if "3_2" in name or "3+2" in name:
        return TimeControl.blitz_3_2()
    if "5_0" in name or "5+0" in name:
        return TimeControl.blitz_5_0()
    if "15_10" in name or "15+10" in name:
        return TimeControl.rapid_15_10()
    return TimeControl.rapid_10_0()


def _get_game_mode(mode_name: str | None) -> GameMode:
    if not mode_name:
        return GameMode.standard_8x8()
    name = mode_name.lower()
    if "snake" in name or "draft" in name:
        return get_preset_mode(GameModeType.SNAKE_DRAFT)
    if "hazard" in name:
        return get_preset_mode(GameModeType.HAZARD_ARENA)
    if "10" in name or "grand" in name:
        return GameMode.grand_10x10()
    return GameMode.standard_8x8()


async def _clock_tick_loop(room_manager: RoomManager) -> None:
    """Periodic background task advancing active room clocks and enforcing flag fall terminations."""
    last_tick = time.monotonic()
    while True:
        try:
            await asyncio.sleep(1.0)
            now = time.monotonic()
            elapsed = now - last_tick
            last_tick = now

            for room_id, room in list(room_manager.rooms.items()):
                if room.is_started and not room.is_finished:
                    winner = room.tick_clock(elapsed)
                    if winner or room.is_finished:
                        room_manager.record_match_result(room)
                        await _broadcast_room(room_id, {
                            "tipo": "estado_jogo",
                            "dados": room.session.state_payload(),
                            "room": room.state_payload(),
                        })
                        await _broadcast_room(room_id, {
                            "tipo": "game_over",
                            "reason": room.termination_reason or "flag_fall",
                            "winner": room.winner,
                            "room": room.state_payload(),
                        })
        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[Clock] Exception in background clock tick loop: {exc}")


async def gerir_conexao(websocket: Any):
    global sessao

    # 1. Validate Origin header for CSRF / cross-site WebSocket hijacking defense
    origin = _extract_origin(websocket)
    if not SecurityGuard.validate_origin(origin):
        await _enviar_erro(websocket, "origem nao autorizada")
        try:
            await websocket.close(1008, "Policy Violation: Origin not allowed")
        except Exception:
            pass
        return

    meta: dict[str, Any] = {
        "room_id": None,
        "player_id": None,
        "cor": None,
        "is_legacy": True,
        "ready": False,
    }
    _connections[websocket] = meta

    # Check if this is a legacy connection or a room-based handshake
    # For legacy clients, assign white if 0 players, black if 1 player
    if len(jogadores) == 0:
        legacy_cor = "brancas"
        sessao = AuthoritativeSession.new()
    elif len(jogadores) == 1:
        legacy_cor = "pretas"
    else:
        legacy_cor = "espetador"

    jogadores[websocket] = legacy_cor
    meta["cor"] = legacy_cor

    try:
        # Legacy greeting
        await websocket.send(json.dumps({"tipo": "setup", "cor": legacy_cor}))
        if legacy_cor == "espetador":
            await _enviar_erro(websocket, "Sala cheia. Apenas espetador.")

        client_key = _extract_client_ip(websocket)
        async for mensagem in websocket:
            if not rate_limiter.allow_request(client_key):
                await _enviar_erro(websocket, "taxa de mensagens excedida")
                continue

            valid, dados, err_code = SecurityGuard.parse_and_validate_json(mensagem)
            if not valid or dados is None:
                if err_code == "payload_too_large":
                    await _enviar_erro(websocket, "payload excede limite maximo de 64 KB")
                elif err_code == "root_not_an_object":
                    await _enviar_erro(websocket, "mensagem deve ser um objeto JSON")
                elif err_code == "missing_or_invalid_tipo":
                    await _enviar_erro(websocket, "campo 'tipo' ausente ou invalido")
                else:
                    await _enviar_erro(websocket, "mensagem JSON inválida")
                continue

            # Strict schema validation per message type
            schema_valid, schema_err = SecurityGuard.validate_message_schema(dados)
            if not schema_valid:
                await _enviar_erro(websocket, f"formato de mensagem invalido: {schema_err}")
                continue

            tipo = dados.get("tipo")

            # Room joining request
            if tipo == "join_room":
                # Atomic room transition: detach from previous room if any
                prev_room_id = meta.get("room_id")
                if prev_room_id and prev_room_id in _room_sockets:
                    _room_sockets[prev_room_id].discard(websocket)
                    if not _room_sockets[prev_room_id]:
                        _room_sockets.pop(prev_room_id, None)

                # Remove from legacy tracking
                jogadores.pop(websocket, None)
                prontos.discard(websocket)

                room_id = str(dados.get("room_id", "default_room")).strip()[:64]
                player_id = str(dados.get("player_id", f"Player_{id(websocket)}")).strip()[:64]
                role_pref = str(dados.get("role_preference", "auto")).strip()[:16]
                tc = _get_time_control(dados.get("time_control"))
                mode = _get_game_mode(dados.get("mode"))

                room = manager.get_room(room_id)
                if room is None:
                    room = manager.create_room(room_id=room_id, mode=mode, time_control=tc)

                assigned_role = room.add_player(player_id, role_pref)
                if assigned_role is None:
                    # Anti-impersonation: player_id is already registered in this room!
                    # Reject unauthenticated hijack and NEVER leak reconnect token!
                    await _enviar_erro(
                        websocket,
                        "Identificador de jogador já em jogo nesta sala. Para retomar o controlo, use 'reconnect' com o seu token secreto."
                    )
                    continue

                meta["room_id"] = room_id
                meta["player_id"] = player_id
                meta["cor"] = assigned_role
                meta["is_legacy"] = False

                if room_id not in _room_sockets:
                    _room_sockets[room_id] = set()
                _room_sockets[room_id].add(websocket)

                token = room.player_tokens.get(player_id) if assigned_role in ("brancas", "pretas") else None

                await websocket.send(json.dumps({
                    "tipo": "room_joined",
                    "room_id": room_id,
                    "cor": assigned_role,
                    "reconnect_token": token,
                    "room": room.state_payload(),
                }))
                continue

            # Player ready notification
            if tipo == "pronto":
                meta["ready"] = True
                if meta["is_legacy"]:
                    prontos.add(websocket)
                    if len(prontos) == 2 and len(jogadores) == 2:
                        await _broadcast({"tipo": "start_game"})
                        await _broadcast(_mensagem_estado())
                else:
                    room_id = meta["room_id"]
                    room = manager.get_room(room_id)
                    if room and not room.is_started:
                        # Check if white and black are ready
                        room_sockets = _room_sockets.get(room_id, set())
                        ready_players = {
                            _connections[ws]["cor"]
                            for ws in room_sockets
                            if ws in _connections and _connections[ws].get("ready")
                        }
                        if "brancas" in ready_players and "pretas" in ready_players:
                            room.start_game()
                            await _broadcast_room(room_id, {"tipo": "start_game", "room": room.state_payload()})
                            await _broadcast_room(room_id, {
                                "tipo": "estado_jogo",
                                "dados": room.session.state_payload(),
                                "room": room.state_payload(),
                            })
                continue

            # Resignation
            if tipo == "resign":
                if not meta["is_legacy"] and meta["room_id"]:
                    room = manager.get_room(meta["room_id"])
                    if room and room.is_started and not room.is_finished:
                        room.resign(meta["player_id"])
                        manager.record_match_result(room)
                        await _broadcast_room(meta["room_id"], {
                            "tipo": "game_over",
                            "reason": "resignation",
                            "room": room.state_payload(),
                        })
                continue

            # Reconnection with token
            if tipo == "reconnect":
                token = str(dados.get("token", "")).strip()
                room_id = str(dados.get("room_id", "")).strip()
                room = manager.get_room(room_id)
                if room:
                    success, role = room.reconnect_player(token)
                    if success and role:
                        # Atomic room transition: detach from previous room
                        prev_room_id = meta.get("room_id")
                        if prev_room_id and prev_room_id in _room_sockets:
                            _room_sockets[prev_room_id].discard(websocket)
                            if not _room_sockets[prev_room_id]:
                                _room_sockets.pop(prev_room_id, None)

                        recovered_id = room.white_player if role == "brancas" else room.black_player
                        meta["room_id"] = room_id
                        meta["player_id"] = recovered_id
                        meta["cor"] = role
                        meta["is_legacy"] = False
                        if room_id not in _room_sockets:
                            _room_sockets[room_id] = set()
                        _room_sockets[room_id].add(websocket)
                        new_token = room.player_tokens.get(recovered_id, token)
                        await websocket.send(json.dumps({
                            "tipo": "reconnect_success",
                            "room_id": room_id,
                            "cor": role,
                            "player_id": recovered_id,
                            "reconnect_token": new_token,
                            "room": room.state_payload(),
                            "estado_jogo": room.session.state_payload(),
                        }))
                        continue
                await _enviar_erro(websocket, "reconexao falhou: token ou sala invalida")
                continue

            # Rematch proposal
            if tipo == "rematch":
                if not meta["is_legacy"] and meta.get("room_id"):
                    room = manager.get_room(meta["room_id"])
                    if room:
                        if not room.is_finished:
                            await _enviar_erro(websocket, "desforra indisponivel durante partida ativa")
                            continue
                        success = room.propose_rematch(meta["player_id"])
                        if success:
                            await _broadcast_room(meta["room_id"], {
                                "tipo": "rematch_update",
                                "room": room.state_payload(),
                            })
                            if room.is_started and not room.is_finished:
                                await _broadcast_room(meta["room_id"], {
                                    "tipo": "start_game",
                                    "room": room.state_payload(),
                                })
                                await _broadcast_room(meta["room_id"], {
                                    "tipo": "estado_jogo",
                                    "dados": room.session.state_payload(),
                                    "room": room.state_payload(),
                                })
                continue

            # Tactical chat emote
            if tipo == "emote":
                if not meta["is_legacy"] and meta.get("room_id"):
                    room = manager.get_room(meta["room_id"])
                    if room:
                        msg = room.process_emote(meta["player_id"], str(dados.get("emote", "gg")))
                        await _broadcast_room(meta["room_id"], msg)
                continue

            # Action request
            if tipo == "acao":
                acao = {key: value for key, value in dados.items() if key != "tipo"}

                if meta["is_legacy"]:
                    if sessao is None or len(jogadores) != 2 or len(prontos) != 2:
                        await _enviar_erro(websocket, "partida não está ativa")
                        continue
                    try:
                        sessao.apply_action(meta["cor"], acao)
                    except (TypeError, ValueError) as exc:
                        await _enviar_erro(websocket, str(exc))
                        continue
                    except Exception as exc:
                        await _enviar_erro(websocket, SecurityGuard.mask_error_message(exc))
                        continue
                    await _broadcast(_mensagem_estado())
                else:
                    room_id = meta["room_id"]
                    room = manager.get_room(room_id)
                    if room is None or not room.is_started or room.is_finished:
                        await _enviar_erro(websocket, "partida não está ativa")
                        continue
                    try:
                        room.apply_action(meta["player_id"], acao)
                    except Exception as exc:
                        await _enviar_erro(websocket, SecurityGuard.mask_error_message(exc))
                        continue

                    if room.is_finished:
                        manager.record_match_result(room)

                    await _broadcast_room(room_id, {
                        "tipo": "estado_jogo",
                        "dados": room.session.state_payload(),
                        "room": room.state_payload(),
                    })
                continue

            await _enviar_erro(websocket, "tipo de mensagem desconhecido")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        _connections.pop(websocket, None)
        jogadores.pop(websocket, None)
        prontos.discard(websocket)
        room_id = meta.get("room_id")
        if room_id and room_id in _room_sockets:
            _room_sockets[room_id].discard(websocket)
            if not _room_sockets[room_id]:
                _room_sockets.pop(room_id, None)

        if not jogadores:
            prontos.clear()
            sessao = None

        rate_limiter.prune_stale_buckets(max_idle_seconds=300.0)


async def main():
    porto = 8765
    print(f"🚀 Servidor RedWar autoritativo a iniciar na porta {porto}...")
    ticker_task = asyncio.create_task(_clock_tick_loop(manager))
    try:
        async with websockets.serve(gerir_conexao, "0.0.0.0", porto):
            await asyncio.Future()
    finally:
        ticker_task.cancel()
        try:
            await ticker_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
