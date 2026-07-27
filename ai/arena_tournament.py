# ai/arena_tournament.py
import sys
import os
import argparse
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from ai.opening_tester import carregar_abertura_basica
from ai.bot import BOT_INICIANTE, BOT_INTERMEDIO, BOT_AVANCADO
import argparse

def verificar_promocao(vitorias_desafiante, vitorias_atual, margem=5):
    """
    Critério: O desafiante tem de ter estritamente mais vitórias 
    e uma diferença mínima de 5 vitórias face ao atual campeão.
    """
    diferenca = vitorias_desafiante - vitorias_atual
    return diferenca >= margem

def run_headless_match(bot_brancas, bot_pretas):
    gs = GameState(time_limit_seconds=99999)
    carregar_abertura_basica(gs) 
    
    turnos = 0
    while not gs.game_over and turnos < 200:
        turnos += 1
        if gs.white_to_move: best_move = bot_brancas.play(gs)
        else: best_move = bot_pretas.play(gs)
            
        if best_move:
            if best_move["type"] == "stun": gs.make_action(best_move["start"], best_move["end"], "stun", best_move["area"])
            elif best_move["type"] == "spawn": gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            else: gs.make_action(best_move["start"], best_move["end"], best_move["type"])
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio"
            break
    return gs.winner

def start_tournament(num_games, win_threshold):
    print(f"⚔️ A INICIAR TORNEIO DE ARENA: {num_games} JOGOS")
    wins_challenger = wins_baseline = draws = 0
    
    for i in range(num_games):
        if i % 2 == 0:
            winner = run_headless_match(BOT_AVANCADO, BOT_INTERMEDIO)
            if winner and "Brancas" in str(winner): wins_challenger += 1
            elif winner and "Pretas" in str(winner): wins_baseline += 1
            else: draws += 1
        else:
            winner = run_headless_match(BOT_INTERMEDIO, BOT_AVANCADO)
            if winner and "Pretas" in str(winner): wins_challenger += 1
            elif winner and "Brancas" in str(winner): wins_baseline += 1
            else: draws += 1
            
        sys.stdout.write(f"\rJogos completados: {i + 1}/{num_games}")
        sys.stdout.flush()

    win_rate = (wins_challenger / max(1, num_games)) * 100
    print(f"\n\nTaxa de Vitória do Challenger: {win_rate:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Torneio da Arena RedWar")
    parser.add_argument("--jogos", type=int, default=10000, help="Número total de partidas")
    parser.add_argument("--margem_vitorias", type=int, default=5, help="Diferença mínima de vitórias exigida")
    args = parser.parse_args()
    start_tournament(args.jogos, args.threshold)