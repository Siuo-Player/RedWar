# online/server/app.py
import asyncio
import websockets
import json

# Mapeia websocket -> cor ('brancas' ou 'pretas')
jogadores = {}  

async def gerir_conexao(websocket):
    # 1. Atribuir cor ao novo jogador
    if len(jogadores) == 0:
        cor = 'brancas'
    elif len(jogadores) == 1:
        cor = 'pretas'
    else:
        await websocket.send(json.dumps({"tipo": "erro", "mensagem": "Sala cheia. Apenas espetador."}))
        return

    jogadores[websocket] = cor
    print(f"[+] Jogador ligado como {cor.upper()}")
    
    # 2. Informa o cliente da sua cor
    await websocket.send(json.dumps({"tipo": "setup", "cor": cor}))
    
    # 3. Se dois jogadores estiverem prontos, inicia a partida
    if len(jogadores) == 2:
        print("[!] Dois jogadores conectados. A Iniciar Partida na Rede!")
        for ws in jogadores:
            await ws.send(json.dumps({"tipo": "start_game"}))

    try:
        async for mensagem in websocket:
            dados = json.loads(mensagem)
            
            # 4. O SERVIDOR ESPELHO: Recebe a String ("MOVE A2 A4") e retransmite para todos
            if dados.get("tipo") == "acao_agnostica":
                acao_str = dados.get("acao")
                print(f"[{cor.upper()}] Disparou tática: {acao_str}")
                
                # Retransmite para TODOS os jogadores ligados para sincronizarem os tabuleiros locais
                for ws in jogadores:
                    await ws.send(json.dumps({
                        "tipo": "acao_agnostica",
                        "acao": acao_str
                    }))
                    
    except websockets.exceptions.ConnectionClosed:
        print(f"[-] Jogador {cor.upper()} desconectado.")
    finally:
        if websocket in jogadores:
            del jogadores[websocket]

async def main():
    porto = 8765
    print(f"🚀 Servidor RedWar (Relay Agnóstico) a iniciar na porta {porto}...")
    # "0.0.0.0" permite que a rede local/internet se ligue a ti
    async with websockets.serve(gerir_conexao, "0.0.0.0", porto):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())