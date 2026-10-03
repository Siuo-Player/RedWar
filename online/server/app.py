# online/server/app.py
import asyncio
import json

import websockets

from online.server.authority import AuthoritativeSession

# Mapeia websocket -> cor ('brancas' ou 'pretas')
jogadores = {}
prontos = set()
sessao = None


def _mensagem_estado() -> dict:
    if sessao is None:
        raise RuntimeError("authoritative session is not available")
    return {"tipo": "estado_jogo", "dados": sessao.state_payload()}


async def _broadcast(payload: dict) -> None:
    if not jogadores:
        return
    mensagem = json.dumps(payload)
    resultados = await asyncio.gather(
        *(ws.send(mensagem) for ws in list(jogadores)),
        return_exceptions=True,
    )
    for ws, resultado in zip(list(jogadores), resultados):
        if isinstance(resultado, websockets.exceptions.ConnectionClosed):
            jogadores.pop(ws, None)


async def _enviar_erro(websocket, mensagem: str) -> None:
    try:
        await websocket.send(json.dumps({"tipo": "erro", "mensagem": mensagem}))
    except websockets.exceptions.ConnectionClosed:
        pass


async def gerir_conexao(websocket):
    global sessao

    # 1. Atribuir cor ao novo jogador
    if len(jogadores) == 0:
        cor = "brancas"
        sessao = AuthoritativeSession.new()
    elif len(jogadores) == 1:
        cor = "pretas"
    else:
        await _enviar_erro(websocket, "Sala cheia. Apenas espetador.")
        return

    jogadores[websocket] = cor
    print(f"[+] Jogador ligado como {cor.upper()}")

    try:
        # 2. Informa o cliente da sua cor
        await websocket.send(json.dumps({"tipo": "setup", "cor": cor}))

        # 3. Se dois jogadores estiverem prontos, inicia a partida
        if len(jogadores) == 2:
            print("[!] Dois jogadores conectados. A iniciar partida autoritativa!")
            await _broadcast({"tipo": "start_game"})
            await _broadcast(_mensagem_estado())

        async for mensagem in websocket:
            try:
                dados = json.loads(mensagem)
            except (TypeError, json.JSONDecodeError):
                await _enviar_erro(websocket, "mensagem JSON inválida")
                continue

            if not isinstance(dados, dict):
                await _enviar_erro(websocket, "mensagem deve ser um objeto JSON")
                continue

            if dados.get("tipo") != "acao":
                await _enviar_erro(websocket, "tipo de mensagem desconhecido")
                continue

            if sessao is None or len(jogadores) != 2:
                await _enviar_erro(websocket, "partida não está ativa")
                continue

            acao = {key: value for key, value in dados.items() if key != "tipo"}
            try:
                sessao.apply_action(cor, acao)
            except (TypeError, ValueError) as exc:
                await _enviar_erro(websocket, str(exc))
                continue

            await _broadcast(_mensagem_estado())

    except websockets.exceptions.ConnectionClosed:
        print(f"[-] Jogador {cor.upper()} desconectado.")
    finally:
        if websocket in jogadores:
            del jogadores[websocket]
        prontos.discard(websocket)
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
