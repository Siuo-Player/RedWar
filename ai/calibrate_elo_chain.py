# ai/calibrate_elo_chain.py
import sys
import os
import math
import argparse
import concurrent.futures
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from ai.opening_tester import carregar_abertura_basica
from ai.bot import BotConfig, BotAleatorio

# ESCADA DE TEMPOS PURA (Sem Depth Limits)
B_RANDOM = BotAleatorio()
B_T1 = BotConfig("Motor (0.1s)", time_limit_seconds=0.1)
B_T2 = BotConfig("Motor (0.5s)", time_limit_seconds=0.5)
B_T3 = BotConfig("Motor (1.0s)", time_limit_seconds=1.0)
B_T4 = BotConfig("Motor (2.0s)", time_limit_seconds=2.0)
B_T5 = BotConfig("Motor (5.0s)", time_limit_seconds=5.0)

CADEIA_BOTS = [B_RANDOM, B_T1, B_T2, B_T3, B_T4, B_T5]

def jogar_uma_partida(args):
    bot_brancas, bot_pretas, seed_val = args
    
    # GARANTIA QUE CADA JOGO É ÚNICO NA THREAD
    random.seed(seed_val)
    
    gs = GameState(time_limit_seconds=99999)
    carregar_abertura_basica(gs)

    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        best_move = bot_brancas.play(gs) if gs.white_to_move else bot_pretas.play(gs)

        if best_move:
            if best_move["type"] == "stun": gs.make_action(best_move["start"], best_move["end"], "stun", best_move.get("area", []))
            elif best_move["type"] == "spawn": gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            else: gs.make_action(best_move["start"], best_move["end"], best_move["type"])
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio"
            break

    if "Brancas" in str(gs.winner): return 1.0
    elif "Pretas" in str(gs.winner): return 0.0
    else: return 0.5

def calcular_elo_cadeia(num_jogos=100):
    print(f"⚖️ A INICIAR CALIBRAÇÃO ELO DE TEMPO ({num_jogos} jogos por matchup)...\n")

    elos_calculados = {B_RANDOM.nome: 100.0}
    executor = None # Variável de controlo para a limpeza

    try:
        for i in range(len(CADEIA_BOTS) - 1):
            bot_inferior = CADEIA_BOTS[i]
            bot_superior = CADEIA_BOTS[i+1]
            elo_inferior = elos_calculados[bot_inferior.nome]

            print(f"\n⚔️ Matchup {i+1}: {bot_superior.nome} vs {bot_inferior.nome} (Base: {elo_inferior:.0f} ELO)")

            score_superior = 0.0
            tarefas = []

            for j in range(num_jogos):
                seed_val = random.randint(1, 999999) + j
                if j % 2 == 0: tarefas.append((bot_superior, bot_inferior, seed_val))
                else: tarefas.append((bot_inferior, bot_superior, seed_val))

            concluidos = 0
            trabalhadores = max(1, (os.cpu_count() or 2) - 1)
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=trabalhadores) as process_executor:
                executor = process_executor
                futuros = [executor.submit(jogar_uma_partida, t) for t in tarefas]

                for j, futuro in enumerate(concurrent.futures.as_completed(futuros)):
                    resultado = futuro.result()
                    
                    is_superior_brancas = tarefas[j][0] == bot_superior
                    if is_superior_brancas: score_superior += resultado
                    else: score_superior += (1.0 - resultado)

                    concluidos += 1
                    sys.stdout.write(f"\rProgresso: {concluidos}/{num_jogos} | Score Acumulado: {score_superior}")
                    sys.stdout.flush()

            win_rate = score_superior / num_jogos
            win_rate_segura = max(0.001, min(0.999, win_rate))

            elo_diff = -400 * math.log10((1.0 - win_rate_segura) / win_rate_segura)
            novo_elo = elo_inferior + elo_diff

            elos_calculados[bot_superior.nome] = novo_elo
            print(f"\n📊 WR do Superior: {win_rate*100:.1f}% -> Novo ELO: {novo_elo:.0f}")

        print("\n\n🏆 TABELA DE ELO ABSOLUTA FINAL 🏆")
        print("--------------------------------------------------")
        for nome, elo in elos_calculados.items():
            print(f"{nome.ljust(25)} | {elo:.0f} ELO")

    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido (Ctrl+C). A abater as simulações ativas...")
        if executor:
            executor.shutdown(wait=False, cancel_futures=True)
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jogos", type=int, default=100)
    args = parser.parse_args()
    calcular_elo_cadeia(args.jogos)