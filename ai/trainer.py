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
from ai.search import find_best_move
from ai.evaluator import avaliador_guloso
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LIMITE_TURNOS

def preencher_draft_aleatorio(gs, team, linhas_validas, orcamento):
    pontos = orcamento
    catalogo = obter_catalogo_pecas()
    pecas_usadas = []
    for r in linhas_validas:
        for c in range(8):
            validas = [p for p in catalogo if p["cost"] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = escolha["class"](team)
            pontos -= escolha["cost"]
            pecas_usadas.append(escolha["name"])
    return pecas_usadas

def simular_jogo_treino(seed):
    random.seed(seed)
    gs = GameState(time_limit_seconds=99999)
    # TUDO IGUALADO A 200 PONTOS
    pecas_pretas = preencher_draft_aleatorio(gs, 'pretas', [0, 1], ORCAMENTO_PRETAS)
    pecas_brancas = preencher_draft_aleatorio(gs, 'brancas', [6, 7], ORCAMENTO_BRANCAS)

    turnos = 0
    while not gs.game_over and turnos < LIMITE_TURNOS:
        turnos += 1
        best_move = find_best_move(gs, depth=1, evaluator_func=avaliador_guloso) 
        if best_move:
            if best_move["type"] == "stun":
                gs.make_action(best_move["start"], best_move["end"], "stun", best_move.get("area", []))
            elif best_move["type"] == "spawn":
                gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            else:
                gs.make_action(best_move["start"], best_move["end"], best_move["type"])
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio Total"
            break
            
    return {"winner": str(gs.winner), "pecas_pretas": pecas_pretas, "pecas_brancas": pecas_brancas}

def gerar_estatisticas_treino(num_jogos=200):
    print(f"🧠 A gerar estatísticas rápidas ({num_jogos} partidas) para o Auto-Balancer...")
    piece_usage, piece_wins, outcomes = Counter(), Counter(), Counter()
    draws = 0
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futuros = [executor.submit(simular_jogo_treino, i) for i in range(num_jogos)]
        for i, futuro in enumerate(concurrent.futures.as_completed(futuros)):
            res = futuro.result()
            
            for p in res["pecas_brancas"] + res["pecas_pretas"]: piece_usage[p] += 1
            outcomes[res["winner"]] += 1
            
            if "Brancas Vencem" in res["winner"]:
                for p in res["pecas_brancas"]: piece_wins[p] += 1
            elif "Pretas Vencem" in res["winner"]:
                for p in res["pecas_pretas"]: piece_wins[p] += 1
            else:
                draws += 1
                
            sys.stdout.write(f"\rProgresso: {i+1}/{num_jogos}")
            sys.stdout.flush()

    stats = {
        "total_matches": num_jogos,
        "draws": draws,
        "outcomes": dict(outcomes),
        "piece_usage": dict(piece_usage),
        "piece_wins": dict(piece_wins)
    }
    
    with open("estatisticas_treino.json", "w") as f: json.dump(stats, f, indent=4)
    print("\n✅ estatisticas_treino.json atualizado!")

if __name__ == "__main__":
    gerar_estatisticas_treino(200)