# ai/opening_tester.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord

# Importação corrigida: Usamos os Bots e não os avaliadores crus
from ai.bot import BOT_INICIANTE, BOT_AVANCADO

def carregar_abertura_basica(gs):
    gs.board[0][3] = BoneLord('pretas')
    gs.board[0][2] = Obelisk('pretas')
    gs.board[0][4] = Obelisk('pretas')
    gs.board[1][2] = FrostMage('pretas')
    gs.board[1][3] = Ghoul('pretas')
    gs.board[1][4] = Ghoul('pretas')
    
    gs.board[7][3] = BoneLord('brancas')
    gs.board[7][2] = Obelisk('brancas')
    gs.board[7][4] = Obelisk('brancas')
    gs.board[6][2] = FrostMage('brancas')
    gs.board[6][3] = Ghoul('brancas')
    gs.board[6][4] = Ghoul('brancas')

def run_ai_match(bot_brancas, bot_pretas):
    gs = GameState(time_limit_seconds=99999) 
    carregar_abertura_basica(gs)
    
    print(f"\n--- A iniciar Combate Simulado ---")
    print(f"Brancas: {bot_brancas.nome} | Pretas: {bot_pretas.nome}\n")
    
    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        
        if gs.white_to_move:
            print(f"Turno {turnos}: Brancas ({bot_brancas.nome}) a pensar...")
            best_move = bot_brancas.play(gs)
        else:
            print(f"Turno {turnos}: Pretas ({bot_pretas.nome}) a pensar...")
            best_move = bot_pretas.play(gs)
            
        if best_move:
            if best_move["type"] == "stun":
                gs.make_action(best_move["start"], best_move["end"], "stun", best_move["area"])
                print(f"-> Magia de Stun lançada em {best_move['end']}")
            elif best_move["type"] == "spawn":
                gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
                print(f"-> Invocação em {best_move['end']}")
            else:
                gs.make_action(best_move["start"], best_move["end"], best_move["type"])
                print(f"-> {best_move['type'].capitalize()} de {best_move['start']} para {best_move['end']}")
        else:
            gs.check_game_over()
            break

    print(f"\nFim do Jogo! Vencedor: {gs.winner}")

if __name__ == "__main__":
    run_ai_match(BOT_INICIANTE, BOT_AVANCADO)