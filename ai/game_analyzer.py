# ai/game_analyzer.py
import sys
import os
import json
import time
from collections import Counter
import random
import concurrent.futures

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.config import LIMITE_TURNOS
from ai.bot import BOT_INTERMEDIO
from ai.opening_tester import carregar_abertura_basica

def simular_um_jogo(seed):
    start_time = time.time()
    gs = GameState(time_limit_seconds=99999)
    # Usa o novo Opening Book caótico em vez do draft cego antigo
    carregar_abertura_basica(gs, seed)
    
    resultado = {
        "turnos": 0, "tempo_segundos": 0.0, "winner": None, "mortes_por_peca": Counter(), 
        "spawns_realizados": Counter(), "abates_por_peca": Counter(), "valor_destruido_por_peca": Counter(),
        "stuns_aplicados": 0, "mortes_por_stun": 0,
        "heatmap": [[0 for _ in range(8)] for _ in range(8)], "tabuleiro_encravado": None
    }
    
    turnos = 0
    while not gs.game_over and turnos < LIMITE_TURNOS:
        turnos += 1
        best_move = BOT_INTERMEDIO.play(gs)
        
        if best_move:
            start_r, start_c = best_move["start"]
            end_r, end_c = best_move["end"]
            atacante = gs.board[start_r][start_c]
            alvo = gs.board[end_r][end_c]
            
            if best_move["type"] == "attack" and alvo:
                resultado["mortes_por_peca"][alvo.name] += 1
                if atacante:
                    resultado["abates_por_peca"][atacante.name] += 1
                    resultado["valor_destruido_por_peca"][atacante.name] += alvo.cost
            
            elif best_move["type"] == "stun":
                resultado["stuns_aplicados"] += len(best_move.get("area", []))
                if alvo and alvo.stun_timer > 0:
                    resultado["mortes_por_peca"][alvo.name] += 1
                    resultado["mortes_por_stun"] += 1
                    if atacante:
                        resultado["abates_por_peca"][atacante.name] += 1
                        resultado["valor_destruido_por_peca"][atacante.name] += alvo.cost
                        
            elif best_move["type"] == "spawn":
                resultado["spawns_realizados"][best_move.get("spawn_name")] += 1

            if best_move["type"] == "stun": gs.make_action(best_move["start"], best_move["end"], "stun", best_move.get("area", []))
            elif best_move["type"] == "spawn": gs.make_action(best_move["start"], best_move["end"], "spawn", spawn_name=best_move.get("spawn_name"))
            else: gs.make_action(best_move["start"], best_move["end"], best_move["type"])
                
            resultado["heatmap"][end_r][end_c] += 1
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio Total"
            break
            
    if turnos >= LIMITE_TURNOS:
        board_str = f"--- JOGO ENCRAVADO (Seed: {seed}) ---\n"
        for r in range(8):
            for c in range(8):
                p = gs.board[r][c]
                board_str += f"{p.acronym:^3}" if p else " . "
            board_str += "\n"
        resultado["tabuleiro_encravado"] = board_str

    resultado["turnos"] = turnos
    resultado["winner"] = str(gs.winner)
    resultado["tempo_segundos"] = time.time() - start_time
    return resultado

def correr_diagnostico_profundo(num_jogos=100):
    print(f"🔬 A INICIAR TELEMETRIA PROFUNDA ({num_jogos} Partidas)...\n")
    causas_fim = Counter()
    heatmap = [[0 for _ in range(8)] for _ in range(8)]
    mortes_por_peca, spawns_realizados, abates_por_peca, valor_destruido_por_peca = Counter(), Counter(), Counter(), Counter()
    log_encravados = ""
    stuns_aplicados = mortes_por_stun = turnos_totais = jogos_concluidos = 0
    tempo_total_processamento = 0.0
    executor = None

    try:
        with concurrent.futures.ProcessPoolExecutor() as process_executor:
            executor = process_executor
            futuros = [executor.submit(simular_um_jogo, i) for i in range(num_jogos)]
            for futuro in concurrent.futures.as_completed(futuros):
                res = futuro.result()
                turnos_totais += res["turnos"]
                tempo_total_processamento += res["tempo_segundos"]
                causas_fim[res["winner"]] += 1
                mortes_por_peca.update(res["mortes_por_peca"])
                spawns_realizados.update(res["spawns_realizados"])
                abates_por_peca.update(res["abates_por_peca"])
                valor_destruido_por_peca.update(res["valor_destruido_por_peca"])
                stuns_aplicados += res["stuns_aplicados"]
                mortes_por_stun += res["mortes_por_stun"]
                if res.get("tabuleiro_encravado"): log_encravados += res["tabuleiro_encravado"]
                for r in range(8):
                    for c in range(8): heatmap[r][c] += res["heatmap"][r][c]
                jogos_concluidos += 1
                sys.stdout.write(f"\rProcessado: {jogos_concluidos}/{num_jogos}")
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido...")
        if executor: executor.shutdown(wait=False, cancel_futures=True)
        sys.exit(0)

    print("\n\n✅ Diagnóstico concluído! A exportar ficheiros...")
    if log_encravados:
        with open("jogos_encravados_log.txt", "w", encoding="utf-8") as f: f.write(log_encravados)

    tempo_medio = tempo_total_processamento / max(1, num_jogos)

    dados_exportacao = {
        "estatisticas_gerais": {
            "partidas_simuladas": num_jogos, 
            "turnos_medios": round(turnos_totais / max(1,num_jogos), 1), 
            "tempo_medio_segundos_por_jogo": round(tempo_medio, 2),
            "causas_fim": dict(causas_fim)
        },
        "metricas_combate": {
            "mortes_totais_por_peca": dict(mortes_por_peca), "abates_realizados_por_peca": dict(abates_por_peca),
            "pontos_destruidos_por_peca": dict(valor_destruido_por_peca), "stuns_aplicados": stuns_aplicados,
            "mortes_por_stun": mortes_por_stun, "taxa_letalidade_stun": round((mortes_por_stun / max(1, stuns_aplicados)) * 100, 2) if stuns_aplicados > 0 else 0
        },
        "metricas_invocacao": {"spawns_realizados": dict(spawns_realizados)}, "heatmap": heatmap
    }

    with open("telemetria_profunda.json", "w", encoding="utf-8") as f: json.dump(dados_exportacao, f, indent=4)
    with open("relatorio_telemetria.txt", "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE TELEMETRIA PROFUNDA\n=================================\n\n1. ESTATÍSTICAS GERAIS\n")
        f.write(f" - Partidas Simuladas: {num_jogos}\n")
        f.write(f" - Turnos Médios: {round(turnos_totais / max(1,num_jogos), 1)}\n")
        f.write(f" - Tempo Médio por Jogo (CPU): {round(tempo_medio, 2)} segundos\n\n")
        f.write("2. CAUSAS DE FIM DE JOGO\n")
        for causa, qtd in causas_fim.items(): f.write(f" - {causa}: {qtd} vezes ({(qtd/max(1,num_jogos))*100:.1f}%)\n")
        f.write("\n3. LETALIDADE OFENSIVA (Quem mais MATA e DESTRÓI VALOR)\nPeça            | Abates   | Valor Destruído\n---------------------------------------------\n")
        for peca in abates_por_peca: f.write(f"{peca:<15} | {abates_por_peca[peca]:<8} | {valor_destruido_por_peca[peca]} pts\n")

if __name__ == "__main__":
    correr_diagnostico_profundo(100)