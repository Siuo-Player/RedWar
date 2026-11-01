# network/client.py
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Optional

import websockets


class NetworkClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        room_id: Optional[str] = None,
        player_id: Optional[str] = None,
        time_control: Optional[str] = None,
    ):
        self.uri = f"ws://{host}:{port}"
        self.room_id = room_id
        self.player_id = player_id or f"Player_{id(self)}"
        self.time_control = time_control
        self.ws = None
        self.latest_state = None
        self.latest_room = None
        self.latest_clock = None
        self.latest_error = None
        self.cor_atribuida = None
        self.ligado = False
        self.loop = None

        # Inicia a rede numa Thread paralela para não bloquear a interface Pygame
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()

    def _start_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        try:
            self.ws = await websockets.connect(self.uri)
            self.ligado = True
            print("[Rede] Conectado ao servidor com sucesso!")

            # Se foi especificada uma sala, envia o pedido de adesão à sala
            if self.room_id:
                join_payload = {
                    "tipo": "join_room",
                    "room_id": self.room_id,
                    "player_id": self.player_id,
                }
                if self.time_control:
                    join_payload["time_control"] = self.time_control
                await self.ws.send(json.dumps(join_payload))

            async for mensagem in self.ws:
                dados = json.loads(mensagem)
                tipo = dados.get("tipo")

                if tipo == "setup":
                    self.cor_atribuida = dados["cor"]
                    print(f"\n[Rede] És o jogador das {self.cor_atribuida.upper()}!")
                    await self.ws.send(json.dumps({"tipo": "pronto"}))

                elif tipo == "room_joined":
                    self.cor_atribuida = dados["cor"]
                    self.latest_room = dados.get("room")
                    print(f"\n[Rede] Sala '{dados.get('room_id')}' aderida como {self.cor_atribuida.upper()}!")
                    await self.ws.send(json.dumps({"tipo": "pronto"}))

                elif tipo == "start_game":
                    if "room" in dados:
                        self.latest_room = dados["room"]
                        self.latest_clock = dados["room"].get("clock")

                elif tipo == "estado_jogo":
                    self.latest_state = dados["dados"]
                    if "room" in dados:
                        self.latest_room = dados["room"]
                        self.latest_clock = dados["room"].get("clock")

                elif tipo == "game_over":
                    if "room" in dados:
                        self.latest_room = dados["room"]

                elif tipo == "erro":
                    self.latest_error = dados["mensagem"]
                    print(f"\n[Erro de Rede] {dados['mensagem']}")

        except Exception as e:
            self.latest_error = str(e)
            print(f"[Rede] Falha na ligação ao servidor: {e}")
        finally:
            self.ligado = False

    def enviar_acao(self, start, end, action_type="move", area=None, spawn_name=None):
        if not self.ligado or not self.ws or self.loop is None:
            print("[Rede] Erro: Não estás ligado ao servidor.")
            return

        pacote = {
            "tipo": "acao",
            "type": action_type,
            "start": start,
            "end": end,
            "area": area,
            "spawn_name": spawn_name,
        }

        # Envia a jogada de forma segura para a thread assíncrona
        asyncio.run_coroutine_threadsafe(
            self.ws.send(json.dumps(pacote)),
            self.loop,
        )

    def enviar_resignation(self):
        if not self.ligado or not self.ws or self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self.ws.send(json.dumps({"tipo": "resign"})),
            self.loop,
        )

    def fechar(self):
        """Fecha a ligação sem bloquear o loop principal do cliente."""
        loop = self.loop
        websocket = self.ws
        if loop is None or not loop.is_running():
            self.ligado = False
            return

        async def _close():
            if websocket is not None:
                await websocket.close()

        try:
            asyncio.run_coroutine_threadsafe(_close(), loop)
        except RuntimeError:
            self.ligado = False
