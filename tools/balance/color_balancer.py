# ai/color_balancer.py
import sys
import os
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from ai.bot import BOT_INICIANTE
from engine.config import LINHAS, COLUNAS

def preencher_draft_aleatorio(gs, team, linhas_validas, orcamento):
    pontos = orcamento
    catalogo = obter_catalogo_pecas()
    
    for r in linhas_validas:
        for c in range(COLUNAS):
            if gs.board[r][c] is not None: continue 
            validas = [p for p in catalogo if p["cost"] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = escolha["class"](team)
            pontos -= escolha["cost"]

def jogar_batalha_simulada(orcamento_brancas, orcamento_pretas):
    gs = GameState(time_limit_seconds=99999)
    preencher_draft_aleatorio(gs, 'pretas', [0, 1], orcamento_pretas)
    preencher_draft_aleatorio(gs, 'brancas', [LINHAS - 2, LINHAS - 1], orcamento_brancas)
    
    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        best_move = BOT_INICIANTE.play(gs)
        
        if best_move:
            if best_move["type"] == "stun":
                gs.make_action(best_move["start"], best_move["end"], "stun", affected_area=best_move.get("area", []))
            elif best_move["type"] == "spawn":
                gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            elif best_move["type"] == "spell":
                gs.make_action(best_move["start"], best_move["end"], "spell", spell_name=best_move.get("spell_name"))
            else:
                gs.make_action(best_move["start"], best_move["end"], best_move["type"])
        else:
            gs.check_game_over()
            if not gs.game_over:
                gs.game_over = True
                gs.winner = "Bloqueio"

    return gs.winner

def testar_equilibrio_de_cor(jogos_por_teste=50):
    print("--- INICIAR TESTE DE HANDICAP DINÂMICO ---")
    orcamento_pretas = 200
    testes_brancas = [200, 190, 180, 170, 160, 150]
    
    for orcamento_brancas in testes_brancas:
        vitorias_brancas = 0
        vitorias_pretas = 0
        empates = 0
        
        sys.stdout.write(f"\nA testar Brancas [{orcamento_brancas} pts] vs Pretas [{orcamento_pretas} pts]...")
        sys.stdout.flush()
        
        for _ in range(jogos_por_teste):
            resultado = jogar_batalha_simulada(orcamento_brancas, orcamento_pretas)
            if not resultado: continue
            
            if "Brancas" in str(resultado): vitorias_brancas += 1
            elif "Pretas" in str(resultado): vitorias_pretas += 1
            else: empates += 1
                
        taxa_vitoria = (vitorias_brancas / jogos_por_teste) * 100
        print(f"\nResultados: Brancas {vitorias_brancas} | Pretas {vitorias_pretas} | Empates {empates}")
        print(f"Taxa de Vitória Brancas: {taxa_vitoria:.1f}%")
        
        if taxa_vitoria < 45.0:
            print("--> CONCLUSÃO: Orçamento insuficiente. O handicap foi demasiado pesado para as Brancas.")
            break

if __name__ == "__main__":
    testar_equilibrio_de_cor(jogos_por_teste=50)