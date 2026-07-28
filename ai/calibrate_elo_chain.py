# ai/calibrate_elo_chain.py
import sys
import os
import argparse
import concurrent.futures
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from ai.opening_tester import carregar_abertura_basica
from ai.bot import BotConfig, BotAleatorio

ELO_FILE = os.path.join(os.path.dirname(__file__), 'elo_config.json')

B_RANDOM = BotAleatorio()
B_T1 = BotConfig("Motor (0.1s)", time_limit_seconds=0.1)
B_T2 = BotConfig("Motor (0.5s)", time_limit_seconds=0.5)
B_T3 = BotConfig("Motor (1.0s)", time_limit_seconds=1.0)
B_T4 = BotConfig("Motor (2.0s)", time_limit_seconds=2.0)
B_T5 = BotConfig("Motor (5.0s)", time_limit_seconds=5.0)

CADEIA_BOTS = [B_RANDOM, B_T1, B_T2, B_T3, B_T4, B_T5]

def carregar_elos():
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, 'r') as f:
            return json.load(f)
    return {bot.nome: 100.0 for bot in CADEIA_BOTS}

def gravar_elos(elos):
    with open(ELO_FILE, 'w') as f:
        json.dump(elos, f, indent=4)

def jogar_uma_partida(args):
    bot_brancas, bot_pretas, seed_val = args
    random.seed(seed_val)
    
    gs = GameState(time_limit_seconds=99999)
    carregar_abertura_basica(gs, seed_val)

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

def calcular_elo_iterativo(minutos_limite, jogos_por_ronda):
    print(f"⚖️ A INICIAR CALIBRAÇÃO ELO ITERATIVA (Limite: {minutos_limite} min) ⚖️\n")
    elos = carregar_elos()
    
    # Garante que o Aleatório é a nossa âncora constante
    elos[B_RANDOM.nome] = 100.0
    
    start_time = time.time()
    segundos_limite = minutos_limite * 60
    ronda = 1
    executor = None

    # Fator de Volatilidade: Quanto maior, mais o ELO salta. 16 é padrão para estabilização suave.
    K_FACTOR = 16.0 

    try:
        while time.time() - start_time < segundos_limite:
            print(f"\n=================== RONDA {ronda} ===================")
            
            for i in range(len(CADEIA_BOTS) - 1):
                bot_inferior = CADEIA_BOTS[i]
                bot_superior = CADEIA_BOTS[i+1]
                
                elo_inf = elos.get(bot_inferior.nome, 100.0)
                elo_sup = elos.get(bot_superior.nome, 100.0)

                print(f"\n⚔️ {bot_superior.nome} [{elo_sup:.0f}] vs {bot_inferior.nome} [{elo_inf:.0f}]")

                score_superior = 0.0
                tarefas = []

                for j in range(jogos_por_ronda):
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
                        sys.stdout.write(f"\rProgresso: {concluidos}/{jogos_por_ronda} | Score Sup: {score_superior}")
                        sys.stdout.flush()

                # ---- MATEMÁTICA ELO ITERATIVA ----
                # 1. Calcular a expectativa de vitória do superior (0.0 a 1.0)
                expectativa_sup = 1.0 / (1.0 + 10.0 ** ((elo_inf - elo_sup) / 400.0))
                
                # 2. Taxa de vitória real
                win_rate_real = score_superior / jogos_por_ronda
                
                # 3. Ajuste (K_FACTOR * Jogos * (Real - Esperado))
                ajuste = K_FACTOR * jogos_por_ronda * (win_rate_real - expectativa_sup)
                
                novo_elo_sup = elo_sup + ajuste
                novo_elo_inf = elo_inf - ajuste
                
                elos[bot_superior.nome] = novo_elo_sup
                
                # O macaco aleatório nunca perde ELO, é o zero absoluto da escala
                if bot_inferior.nome != B_RANDOM.nome:
                    elos[bot_inferior.nome] = novo_elo_inf

                print(f"\n📊 Expectativa: {expectativa_sup*100:.1f}% | Real: {win_rate_real*100:.1f}%")
                print(f"📈 Ajuste: {'+' if ajuste > 0 else ''}{ajuste:.1f} ELO")

            # Gravar no disco após cada ronda completa
            elos[B_RANDOM.nome] = 100.0
            gravar_elos(elos)
            
            print("\n💾 Progresso guardado no elo_config.json!")
            print("--------------------------------------------------")
            for nome, elo in elos.items():
                print(f"{nome.ljust(25)} | {elo:.0f} ELO")
            
            ronda += 1
            tempo_decorrido = time.time() - start_time
            print(f"⏱️ Tempo restante: {int((segundos_limite - tempo_decorrido) // 60)} minutos")

        print("\n✅ TEMPO LIMITE ATINGIDO. Calibração concluída por hoje.")

    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido manualmente (Ctrl+C). A abater as simulações ativas...")
        if executor:
            executor.shutdown(wait=False, cancel_futures=True)
        gravar_elos(elos)
        print("💾 O progresso feito até ao momento foi gravado em segurança.")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jogos", type=int, default=20, help="Jogos por matchup em cada ronda")
    parser.add_argument("--minutos", type=int, default=30, help="Tempo máximo que o script fica a correr")
    args = parser.parse_args()
    calcular_elo_iterativo(args.minutos, args.jogos)