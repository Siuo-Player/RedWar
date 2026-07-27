import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from ai.search import find_best_move
from ai.opening_tester import carregar_abertura_basica

# Para o torneio, importamos os avaliadores. 
from ai.evaluator import avaliador_estrategico as Baseline_AI
from ai.evaluator import avaliador_agressivo as Challenger_AI

def run_headless_match(eval_brancas, eval_pretas):
    """Corre um jogo sem prints para máxima velocidade."""
    gs = GameState(time_limit_seconds=99999)
    carregar_abertura_basica(gs) 
    
    turnos = 0
    while not gs.game_over and turnos < 1000:
        turnos += 1
        depth = 2 
        
        if gs.white_to_move:
            best_move = find_best_move(gs, depth, eval_brancas)
        else:
            best_move = find_best_move(gs, depth, eval_pretas)
            
        if best_move:
            if best_move["type"] == "stun":
                gs.make_action(best_move["start"], best_move["end"], "stun", best_move["area"])
            elif best_move["type"] == "spawn":
                gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            else:
                gs.make_action(best_move["start"], best_move["end"], best_move["type"])
        else:
            gs.check_game_over()
            if not gs.game_over:
                gs.game_over = True
                gs.winner = "Bloqueio"
            break

    return gs.winner

def start_tournament(num_games, win_threshold):
    print(f"⚔️ A INICIAR TORNEIO DE ARENA: {num_games} JOGOS")
    print(f"Critério de Aprovação: {win_threshold}% de Vitórias para o Challenger\n")
    
    wins_challenger = 0
    wins_baseline = 0
    draws = 0
    
    # Metade dos jogos o Challenger joga de Brancas, metade de Pretas
    for i in range(num_games):
        if i % 2 == 0:
            winner = run_headless_match(Challenger_AI, Baseline_AI)
            # A verificação 'winner and str(winner)' protege contra resultados nulos e agrada ao Pylance
            if winner and "Brancas" in str(winner): wins_challenger += 1
            elif winner and "Pretas" in str(winner): wins_baseline += 1
            else: draws += 1
        else:
            winner = run_headless_match(Baseline_AI, Challenger_AI)
            if winner and "Pretas" in str(winner): wins_challenger += 1
            elif winner and "Brancas" in str(winner): wins_baseline += 1
            else: draws += 1
            
        if (i + 1) % 10 == 0:
            sys.stdout.write(f"\rJogos completados: {i + 1}/{num_games}")
            sys.stdout.flush()

    print("\n\n📊 RESULTADOS DO TORNEIO:")
    print(f"Challenger: {wins_challenger} | Baseline: {wins_baseline} | Empates: {draws}")
    
    if num_games > 0:
        win_rate = (wins_challenger / num_games) * 100
    else:
        win_rate = 0.0
        
    print(f"Taxa de Vitória do Challenger: {win_rate:.2f}%")
    
    if win_rate >= win_threshold:
        print("✅ CHALLENGER APROVADO! O Pull Request será aceite.")
        sys.exit(0)
    else:
        print("❌ CHALLENGER REJEITADO! A IA não demonstrou melhoria significativa.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Torneio de IA")
    parser.add_argument("--jogos", type=int, default=50, help="Número de jogos a simular")
    parser.add_argument("--threshold", type=float, default=55.0, help="Win-rate necessária para aprovar")
    args = parser.parse_args()
    
    start_tournament(args.jogos, args.threshold)