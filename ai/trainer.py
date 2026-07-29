# ai/trainer.py
import sys
import os
import json
from collections import Counter
import random
import concurrent.futures

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LIMITE_TURNOS, LINHAS, COLUNAS
from ai.bot import BOT_INICIANTE, BOT_INTERMEDIO, BOT_AVANCADO, BOT_ALEATORIO

# Vamos usar um pool de bots com ELOs conhecidos para gerar dados ricos
POOL_BOTS = [
    (BOT_ALEATORIO, 100),
    (BOT_INICIANTE, 900),
    (BOT_INTERMEDIO, 1500),
    (BOT_AVANCADO, 2000)
]

def preencher_draft_aleatorio(gs, team, linhas_validas, orcamento):
    pontos = orcamento
    catalogo = obter_catalogo_pecas()
    composicao = Counter()
    
    for r in linhas_validas:
        for c in range(COLUNAS):
            validas = [p for p in catalogo if p["cost"] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = escolha["class"](team)
            pontos -= escolha["cost"]
            composicao[escolha["name"]] += 1
            
    return dict(composicao)

def simular_jogo_treino(seed):
    random.seed(seed)
    gs = GameState(time_limit_seconds=99999)
    
    # Sorteia dois bots diferentes ou iguais para a partida
    bot_brancas, elo_brancas = random.choice(POOL_BOTS)
    bot_pretas, elo_pretas = random.choice(POOL_BOTS)
    
    comp_pretas = preencher_draft_aleatorio(gs, 'pretas', [0, 1], ORCAMENTO_PRETAS)
    comp_brancas = preencher_draft_aleatorio(gs, 'brancas', [6, 7], ORCAMENTO_BRANCAS)

    turnos = 0
    while not gs.game_over and turnos < LIMITE_TURNOS:
        turnos += 1
        best_move = bot_brancas.play(gs) if gs.white_to_move else bot_pretas.play(gs)
        
        if best_move:
            if best_move["type"] == "stun": gs.make_action(best_move["start"], best_move["end"], "stun", best_move.get("area", []))
            elif best_move["type"] == "spawn": gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            else: gs.make_action(best_move["start"], best_move["end"], best_move["type"])
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio Total"
            break
            
    resultado = 0.5
    if "Brancas" in str(gs.winner): resultado = 1.0
    elif "Pretas" in str(gs.winner): resultado = 0.0

    return {
        "white_elo": elo_brancas,
        "black_elo": elo_pretas,
        "white_draft": comp_brancas,
        "black_draft": comp_pretas,
        "result": resultado # 1.0 (Brancas), 0.0 (Pretas), 0.5 (Empate)
    }

def gerar_estatisticas_treino(num_jogos=200):
    print(f"🧠 A gerar metadados de combate ({num_jogos} partidas heterogéneas)...")
    
    historico_partidas = []
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futuros = [executor.submit(simular_jogo_treino, random.randint(1, 999999) + i) for i in range(num_jogos)]
        for i, futuro in enumerate(concurrent.futures.as_completed(futuros)):
            historico_partidas.append(futuro.result())
            sys.stdout.write(f"\rProgresso: {i+1}/{num_jogos}")
            sys.stdout.flush()

    stats = {
        "total_matches": num_jogos,
        "matches": historico_partidas
    }
    
    with open("estatisticas_treino.json", "w") as f:
        json.dump(stats, f, indent=4)
    print("\n✅ estatisticas_treino.json atualizado com metadados ELO!")

if __name__ == "__main__":
    gerar_estatisticas_treino(200)