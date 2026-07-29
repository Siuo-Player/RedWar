# network/client.py
import asyncio
import websockets
import json
import threading

class NetworkClient:
    def __init__(self, host="localhost", port=8765):
        self.uri = f"ws://{host}:{port}"
        self.ws = None
        self.latest_state = None
        self.cor_atribuida = None
        self.ligado = False
        
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
                    print(f"\n[Erro de Rede] {dados['mensagem']}")
                    
        except Exception as e:
            print(f"[Rede] Falha na ligação ao servidor: {e}")
            self.ligado = False

    def enviar_acao(self, start, end, action_type="move", area=None, spawn_name=None):
        if not self.ligado or not self.ws:
            print("[Rede] Erro: Não estás ligado ao servidor.")
            return
            
        pacote = {
            "tipo": "acao",
            "start": start,
            "end": end,
            "action_type": action_type,
            "area": area,
            "spawn_name": spawn_name
        }
        
        # Envia a jogada de forma segura para a thread assíncrona
        asyncio.run_coroutine_threadsafe(self.ws.send(json.dumps(pacote)), self.loop)