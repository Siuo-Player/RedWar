# ai/opening_tester.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord
from ai.evaluator import avaliador_estrategico, avaliador_guloso
from ai.search import find_best_move

def carregar_abertura_basica(gs):
    # Formação Pretas (Vai usar a IA Gulosa)
    gs.board[0][3] = BoneLord('pretas')
    gs.board[0][2] = Obelisk('pretas')
    gs.board[0][4] = Obelisk('pretas')
    gs.board[1][2] = FrostMage('pretas')
    gs.board[1][3] = Ghoul('pretas')
    gs.board[1][4] = Ghoul('pretas')
    
    # Formação Brancas (Vai usar a IA Estratégica)
    gs.board[7][3] = BoneLord('brancas')
    gs.board[7][2] = Obelisk('brancas')
    gs.board[7][4] = Obelisk('brancas')
    gs.board[6][2] = FrostMage('brancas')
    gs.board[6][3] = Ghoul('brancas')
    gs.board[6][4] = Ghoul('brancas')

def run_ai_match():
    # Tempo limite ignorado nas simulações de IA pura
    gs = GameState(time_limit_seconds=99999) 
    carregar_abertura_basica(gs)
    
    print("A iniciar Batalha de IAs (Abertura Básica)...")
    print("Brancas: IA Estratégica (Avalia Mobilidade) | Pretas: IA Gulosa (Avalia Material)\n")
    
    turnos = 0
    # Limite de 150 turnos para evitar loops eternos de evasão
    while not gs.game_over and turnos < 150:
        turnos += 1
        depth = 2 # Profundidade de previsão
        
        if gs.white_to_move:
            print(f"Turno {turnos}: IA Branca a pensar...")
            best_move = find_best_move(gs, depth, avaliador_estrategico)
        else:
            print(f"Turno {turnos}: IA Preta a pensar...")
            best_move = find_best_move(gs, depth, avaliador_guloso)
            
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
    run_ai_match()