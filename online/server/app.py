# online/server/app.py
from __future__ import annotations

import asyncio
import json
from typing import Any

import websockets

from engine.game_modes import GameMode, TimeControl
from engine.ratings import LeaderboardManager
from online.server.authority import AuthoritativeSession
from online.server.room import GameRoom, RoomManager

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


async def _enviar_erro(websocket: Any, mensagem: str) -> None:
    try:
        await websocket.send(json.dumps({"tipo": "erro", "mensagem": mensagem}))
    except websockets.exceptions.ConnectionClosed:
        pass


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
    if "10" in mode_name or "grand" in mode_name.lower():
        return GameMode.grand_10x10()
    return GameMode.standard_8x8()


async def gerir_conexao(websocket: Any):
    global sessao

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

    meta["cor"] = legacy_cor

    # Legacy setup notification is sent on connect
    # If the client immediately sends join_room, we transition to room mode
    try:
        if legacy_cor in ("brancas", "pretas"):
            jogadores[websocket] = legacy_cor
            await websocket.send(json.dumps({"tipo": "setup", "cor": legacy_cor}))
        else:
            await _enviar_erro(websocket, "Sala cheia. Apenas espetador.")

        async for mensagem in websocket:
            try:
                dados = json.loads(mensagem)
            except (TypeError, json.JSONDecodeError):
                await _enviar_erro(websocket, "mensagem JSON inválida")
                continue

            if not isinstance(dados, dict):
                await _enviar_erro(websocket, "mensagem deve ser um objeto JSON")
                continue

            tipo = dados.get("tipo")

            # Room joining request
            if tipo == "join_room":
                # Remove from legacy tracking
                jogadores.pop(websocket, None)
                prontos.discard(websocket)

                room_id = str(dados.get("room_id", "default_room"))
                player_id = str(dados.get("player_id", f"Player_{id(websocket)}"))
                role_pref = str(dados.get("role_preference", "auto"))
                tc = _get_time_control(dados.get("time_control"))
                mode = _get_game_mode(dados.get("mode"))

                room = manager.get_room(room_id)
                if room is None:
                    room = manager.create_room(room_id=room_id, mode=mode, time_control=tc)

                assigned_role = room.add_player(player_id, role_pref)

                meta["room_id"] = room_id
                meta["player_id"] = player_id
                meta["cor"] = assigned_role
                meta["is_legacy"] = False

                if room_id not in _room_sockets:
                    _room_sockets[room_id] = set()
                _room_sockets[room_id].add(websocket)

                await websocket.send(json.dumps({
                    "tipo": "room_joined",
                    "room_id": room_id,
                    "cor": assigned_role,
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
                    await _broadcast(_mensagem_estado())
                else:
                    room_id = meta["room_id"]
                    room = manager.get_room(room_id)
                    if room is None or not room.is_started or room.is_finished:
                        await _enviar_erro(websocket, "partida não está ativa")
                        continue
                    try:
                        room.apply_action(meta["player_id"], acao)
                    except (TypeError, ValueError) as exc:
                        await _enviar_erro(websocket, str(exc))
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


async def main():
    porto = 8765
    print(f"🚀 Servidor RedWar autoritativo a iniciar na porta {porto}...")
    async with websockets.serve(gerir_conexao, "0.0.0.0", porto):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
