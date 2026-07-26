# ai/opening_tester.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord

# Importar todos os perfis disponíveis
from ai.evaluator import (
    avaliador_estrategico, 
    avaliador_guloso, 
    avaliador_agressivo, 
    avaliador_defensivo
)
from ai.search import find_best_move

def carregar_abertura_basica(gs):
    # Formação Pretas
    gs.board[0][3] = BoneLord('pretas')
    gs.board[0][2] = Obelisk('pretas')
    gs.board[0][4] = Obelisk('pretas')
    gs.board[1][2] = FrostMage('pretas')
    gs.board[1][3] = Ghoul('pretas')
    gs.board[1][4] = Ghoul('pretas')
    
    # Formação Brancas
    gs.board[7][3] = BoneLord('brancas')
    gs.board[7][2] = Obelisk('brancas')
    gs.board[7][4] = Obelisk('brancas')
    gs.board[6][2] = FrostMage('brancas')
    gs.board[6][3] = Ghoul('brancas')
    gs.board[6][4] = Ghoul('brancas')

def run_ai_match(eval_brancas, nome_brancas, eval_pretas, nome_pretas):
    gs = GameState(time_limit_seconds=99999) 
    carregar_abertura_basica(gs)
    
    print(f"\n--- A iniciar Combate Simulado ---")
    print(f"Brancas: {nome_brancas} | Pretas: {nome_pretas}\n")
    
    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        depth = 2 
        
        if gs.white_to_move:
            print(f"Turno {turnos}: Brancas ({nome_brancas}) a pensar...")
            best_move = find_best_move(gs, depth, eval_brancas)
        else:
            print(f"Turno {turnos}: Pretas ({nome_pretas}) a pensar...")
            best_move = find_best_move(gs, depth, eval_pretas)
            
        if best_move:
            if best_move["type"] == "stun":
                gs.make_action(best_move["start"], best_move["end"], "stun", best_move["area"])
                print(f"-> Magia de Stun lançada em {best_move['end']}")
            else:
                gs.make_action(best_move["start"], best_move["end"], best_move["type"])
                print(f"-> {best_move['type'].capitalize()} de {best_move['start']} para {best_move['end']}")
        else:
            gs.check_game_over()
            break

    print(f"\nFim do Jogo! Vencedor: {gs.winner}")

if __name__ == "__main__":
    # Teste de Colisão de Estilos: Agressivo vs Defensivo
    run_ai_match(avaliador_agressivo, "IA Agressiva", avaliador_defensivo, "IA Defensiva")