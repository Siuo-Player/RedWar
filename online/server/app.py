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
    for websocket in list(jogadores):
        try:
            await websocket.send(mensagem)
        except websockets.exceptions.ConnectionClosed:
            jogadores.pop(websocket, None)
            prontos.discard(websocket)


async def _enviar_erro(websocket, mensagem: str) -> None:
    try:
        await websocket.send(json.dumps({"tipo": "erro", "mensagem": mensagem}))
    except websockets.exceptions.ConnectionClosed:
        pass


async def gerir_conexao(websocket):
    global sessao

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
        # O cliente confirma que já entrou no ciclo de receção antes de o
        # servidor enviar o primeiro estado autoritativo.
        await websocket.send(json.dumps({"tipo": "setup", "cor": cor}))

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
            if tipo == "pronto":
                prontos.add(websocket)
                if len(prontos) == 2 and len(jogadores) == 2:
                    print("[!] Dois jogadores prontos. A iniciar partida autoritativa!")
                    await _broadcast({"tipo": "start_game"})
                    await _broadcast(_mensagem_estado())
                continue

            if tipo != "acao":
                await _enviar_erro(websocket, "tipo de mensagem desconhecido")
                continue

            if sessao is None or len(jogadores) != 2 or len(prontos) != 2:
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
        jogadores.pop(websocket, None)
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
