# network/client.py
import asyncio
import json
import threading

import websockets


class NetworkClient:
    def __init__(self, host="localhost", port=8765):
        self.uri = f"ws://{host}:{port}"
        self.ws = None
        self.latest_state = None
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
        self.loop.run_forever()

    async def _connect(self):
        try:
            self.ws = await websockets.connect(self.uri)
            self.ligado = True
            print("[Rede] Conectado ao servidor com sucesso!")

            async for mensagem in self.ws:
                dados = json.loads(mensagem)

                if dados["tipo"] == "setup":
                    self.cor_atribuida = dados["cor"]
                    print(f"\n[Rede] És o jogador das {self.cor_atribuida.upper()}!")

                elif dados["tipo"] == "estado_jogo":
                    self.latest_state = dados["dados"]

                elif dados["tipo"] == "erro":
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

    def fechar(self):
        """Fecha a ligação sem bloquear o loop principal do cliente."""
        loop = self.loop
        websocket = self.ws
        if loop is None or not loop.is_running():
            self.ligado = False
            return

        async def _close():
            try:
                if websocket is not None:
                    await websocket.close()
            finally:
                loop.stop()

        try:
            asyncio.run_coroutine_threadsafe(_close(), loop)
        except RuntimeError:
            self.ligado = False
