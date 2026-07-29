# server/app.py
import asyncio
import websockets
import json
import sys
import os

# Garantir que o servidor consegue importar o motor do jogo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.game_state import GameState

# Variáveis globais do servidor
jogadores = {}  # Mapeia websocket -> cor ('brancas' ou 'pretas')
gs = GameState(time_limit_seconds=600)

async def enviar_estado_para_todos():
    """Converte o tabuleiro para JSON e envia para todos os jogadores ligados."""
    estado_json = json.dumps({
        "tipo": "estado_jogo",
        "dados": gs.to_dict()
    })
    
    if jogadores:
        await asyncio.wait([socket.send(estado_json) for socket in jogadores.keys()])

async def gerir_conexao(websocket):
    global gs
    
    # Atribuir cor ao novo jogador
    if len(jogadores) == 0:
        cor = 'brancas'
    elif len(jogadores) == 1:
        cor = 'pretas'
    else:
        await websocket.send(json.dumps({"tipo": "erro", "mensagem": "Sala cheia. Apenas espetador."}))
        return

    jogadores[websocket] = cor
    print(f"[+] Jogador ligado como {cor.upper()}")
    
    # Enviar cor atribuída ao cliente
    await websocket.send(json.dumps({"tipo": "setup", "cor": cor}))
    await enviar_estado_para_todos()

    try:
        async for mensagem in websocket:
            dados = json.loads(mensagem)
            
            if dados["tipo"] == "acao":
                # Validar se é o turno da pessoa certa
                turno_atual = 'brancas' if gs.white_to_move else 'pretas'
                if cor == turno_atual:
                    # Executar ação no motor centralizado
                    if dados["action_type"] == "stun":
                        gs.make_action(
                            start_pos=tuple(dados["start"]),
                            end_pos=tuple(dados["end"]),
                            action_type="stun",
                            affected_area=dados.get("area")
                        )
                    elif dados["action_type"] == "spawn":
                        gs.make_action(
                            start_pos=tuple(dados["start"]),
                            end_pos=tuple(dados["end"]),
                            action_type="spawn",
                            spawn_name=dados.get("spawn_name")
                        )
                    elif dados["action_type"] == "spell":
                        gs.make_action(
                            start_pos=tuple(dados["start"]),
                            end_pos=tuple(dados["end"]),
                            action_type="spell",
                            spell_name=dados.get("spell_name")
                        )
                    else:
                        gs.make_action(
                            start_pos=tuple(dados["start"]),
                            end_pos=tuple(dados["end"]),
                            action_type=dados["action_type"]
                        )
                    await enviar_estado_para_todos()
                else:
                    await websocket.send(json.dumps({"tipo": "erro", "mensagem": "Não é o teu turno!"}))
                    
    except websockets.exceptions.ConnectionClosed:
        print(f"[-] Jogador {cor.upper()} desconectado.")
    finally:
        del jogadores[websocket]
        # Se todos saírem, reseta o jogo
        if len(jogadores) == 0:
            print("[!] Sala vazia. A resetar tabuleiro.")
            gs = GameState(time_limit_seconds=600)

async def main():
    porto = 8765
    print(f"🚀 Servidor RedWar a iniciar na porta {porto} (Aberto à Rede!)...")
    # O "0.0.0.0" permite que o servidor aceite conexões do Router/Internet, e não apenas do próprio PC.
    async with websockets.serve(gerir_conexao, "0.0.0.0", porto):
        await asyncio.Future()  # Corre para sempre

if __name__ == "__main__":
    asyncio.run(main())