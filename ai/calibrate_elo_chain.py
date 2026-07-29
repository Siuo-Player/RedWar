# ai/calibrate_elo_chain.py
import sys
import os
import argparse
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from ai.opening_tester import carregar_abertura_basica
from ai.bot import BotConfig, BotAleatorio

ELO_FILE = os.path.join(os.path.dirname(__file__), 'elo_config.json')

B_RANDOM = BotAleatorio()
B_T1 = BotConfig("Motor (0.5s)", time_limit_seconds=0.5)
B_T2 = BotConfig("Motor (1.0s)", time_limit_seconds=1.0)
B_T3 = BotConfig("Motor (2.0s)", time_limit_seconds=2.0)

CADEIA_BOTS = [B_RANDOM, B_T1, B_T2, B_T3]

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
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio"
            break

    if "Brancas" in str(gs.winner): return 1.0
    elif "Pretas" in str(gs.winner): return 0.0
    else: return 0.5

def calcular_elo_iterativo(minutos_limite, jogos_por_ronda):
    print(f"⚖️ A INICIAR CALIBRAÇÃO ELO SEQUENCIAL PURA (Limite: {minutos_limite} min) ⚖️\n")
    elos = carregar_elos()
    elos[B_RANDOM.nome] = 100.0
    
    start_time = time.time()
    segundos_limite = minutos_limite * 60
    ronda = 1
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
                concluidos = 0
                start_time_duel = time.time()

                for j in range(jogos_por_ronda):
                    seed_val = random.randint(1, 999999) + j
                    
                    if j % 2 == 0: 
                        tarefa = (bot_superior, bot_inferior, seed_val)
                        is_superior_brancas = True
                    else: 
                        tarefa = (bot_inferior, bot_superior, seed_val)
                        is_superior_brancas = False
                        
                    resultado = jogar_uma_partida(tarefa)
                    
                    if is_superior_brancas: score_superior += resultado
                    else: score_superior += (1.0 - resultado)

                    concluidos += 1
                    
                    # CÁLCULOS DE TELEMETRIA
                    tempo_decorrido = time.time() - start_time
                    tempo_duelo = time.time() - start_time_duel
                    tempo_por_jogo = tempo_duelo / concluidos
                    
                    # INDICADORES VISUAIS ATUALIZADOS
                    sys.stdout.write(f"\rProgresso: {concluidos}/{jogos_por_ronda} | Score: {score_superior} | T/Jogo: {tempo_por_jogo:.1f}s | Relógio: {tempo_decorrido/60:.1f}m/{minutos_limite}m  ")
                    sys.stdout.flush()

                expectativa_sup = 1.0 / (1.0 + 10.0 ** ((elo_inf - elo_sup) / 400.0))
                win_rate_real = score_superior / max(1, jogos_por_ronda)
                ajuste = K_FACTOR * jogos_por_ronda * (win_rate_real - expectativa_sup)
                
                elos[bot_superior.nome] = elo_sup + ajuste
                if bot_inferior.nome != B_RANDOM.nome:
                    elos[bot_inferior.nome] = elo_inf - ajuste

                print(f"\n📊 Expectativa: {expectativa_sup*100:.1f}% | Real: {win_rate_real*100:.1f}%")
                print(f"📈 Ajuste: {'+' if ajuste > 0 else ''}{ajuste:.1f} ELO")

                # Trava de Segurança: Se esgotar o tempo a meio da ronda, não lança o próximo duelo
                if time.time() - start_time >= segundos_limite:
                    print("\n⏳ Tempo global esgotado a meio da ronda. A abortar simulações pendentes...")
                    break

            elos[B_RANDOM.nome] = 100.0
            gravar_elos(elos)
            
            print("\n💾 Progresso guardado no elo_config.json!")
            for nome, elo in elos.items(): print(f"{nome.ljust(25)} | {elo:.0f} ELO")
            
            ronda += 1
            tempo_decorrido = time.time() - start_time
            if tempo_decorrido < segundos_limite:
                print(f"⏱️ Tempo restante: {int((segundos_limite - tempo_decorrido) // 60)} minutos")

        print("\n✅ TEMPO LIMITE ATINGIDO.")

    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido manualmente (Ctrl+C).")
        gravar_elos(elos)
        print("💾 Progresso guardado com sucesso.")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jogos", type=int, default=10, help="Jogos por matchup em cada ronda")
    parser.add_argument("--minutos", type=int, default=30, help="Tempo máximo que o script fica a correr")
    args = parser.parse_args()
    calcular_elo_iterativo(args.minutos, args.jogos)