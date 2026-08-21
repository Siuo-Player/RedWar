# ai/opening_tester.py
import sys
import os
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord, Lich, Phantom
from engine.config import LINHAS, COLUNAS
from ai.bot import BOT_INICIANTE, BOT_AVANCADO
from engine.pieces import obter_catalogo_pecas



def carregar_abertura_basica(gs, seed_val=None):
    """
    Substitui a abertura estática por um Livro de Aberturas variado e dinâmico,
    lendo SEMPRE as peças atuais definidas no JSON do motor.
    """
    if seed_val is not None:
        random.seed(seed_val)
        
    gs.board = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
    
    # 1. Obter catálogo e extrair os objetos Class diretamente
    catalogo = obter_catalogo_pecas()
    classes_disponiveis = [item["class"] for item in catalogo]
    
    for team, filas in [('pretas', [0, 1]), ('brancas', [LINHAS-2, LINHAS-1])]:
        # Para ser realista, sorteia peças e quantidade sem forçar orçamentos exatos por agora
        pecas_a_colocar = random.sample(classes_disponiveis, min(5, len(classes_disponiveis)))
        
        for PeçaClass in pecas_a_colocar:
            for _ in range(random.randint(1, 2)):
                r = random.choice(filas)
                c = random.randint(0, COLUNAS - 1)
                
                tentativas = 0
                while gs.board[r][c] is not None and tentativas < 10:
                    r = random.choice(filas)
                    c = random.randint(0, COLUNAS - 1)
                    tentativas += 1
                    
                if gs.board[r][c] is None:
                    gs.board[r][c] = PeçaClass(team)
# =======================================================================
# Atualizar a chamada no run_ai_match para suportar a nova estrutura
# =======================================================================
def run_ai_match(bot_brancas, bot_pretas, seed_val=42):
    gs = GameState(time_limit_seconds=99999) 
    carregar_abertura_basica(gs, seed_val)
    
    print(f"\n--- A iniciar Combate Simulado (Seed: {seed_val}) ---")
    print(f"Brancas: {bot_brancas.nome} | Pretas: {bot_pretas.nome}\n")
    
    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        
        if gs.white_to_move:
            best_move = bot_brancas.play(gs)
        else:
            best_move = bot_pretas.play(gs)
            
        if best_move:
            if best_move["type"] == "stun":
                gs.make_action(best_move["start"], best_move["end"], "stun", best_move["area"])
            elif best_move["type"] == "spawn":
                gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            else:
                gs.make_action(best_move["start"], best_move["end"], best_move["type"])
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio"
            break

    print(f"\nFim do Jogo! Vencedor: {gs.winner}")

if __name__ == "__main__":
    run_ai_match(BOT_INICIANTE, BOT_AVANCADO, seed_val=random.randint(1, 9999))