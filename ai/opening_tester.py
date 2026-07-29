# ai/opening_tester.py
import sys
import os
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord, Lich, Phantom
from engine.config import LINHAS, COLUNAS
from ai.bot import BOT_INICIANTE, BOT_AVANCADO

# Catálogo disponível para o Opening Book
CATALOGO = [Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord, Lich, Phantom]

def carregar_abertura_basica(gs, seed_val=None):
    """
    Substitui a abertura estática por um Livro de Aberturas (Opening Book) variado.
    Garante que os motores não jogam a mesma partida determinística repetidamente.
    """
    if seed_val is not None:
        random.seed(seed_val)
        
    # Limpar o tabuleiro primeiro
    gs.board = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
    
    # Orçamento para a abertura (ex: 300 pontos de peças aleatórias mas espelhadas em custo/poder)
    # Para ser justo, geramos uma composição simétrica em termos de massa tática, 
    # mas distribuída de forma assimétrica nas posições iniciais.
    
    for team, filas in [('pretas', [0, 1]), ('brancas', [LINHAS-2, LINHAS-1])]:
        pecas_a_colocar = random.sample(CATALOGO, 5) # Escolhe 5 classes diferentes
        
        for PeçaClass in pecas_a_colocar:
            # Tentar colocar até 2 instâncias de cada peça escolhida
            for _ in range(random.randint(1, 2)):
                r = random.choice(filas)
                c = random.randint(0, COLUNAS - 1)
                
                # Evitar sobreposição
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