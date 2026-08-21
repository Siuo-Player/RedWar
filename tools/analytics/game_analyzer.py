import sys
import os
import json
import time
from collections import Counter
import random
import concurrent.futures

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.game_state import GameState
from engine.config import  LINHAS, COLUNAS
from ai.bot import BOT_INTERMEDIO
from tools.analytics.opening_tester import carregar_abertura_basica
from engine.action_parser import ActionParser

def simular_um_jogo(seed):
    start_time = time.time()
    gs = GameState(time_limit_seconds=99999)
    carregar_abertura_basica(gs, seed)
    
    resultado = {
        "turnos": 0, "tempo_segundos": 0.0, "winner": None, "mortes_por_peca": Counter(), 
        "spawns_realizados": Counter(), "abates_por_peca": Counter(), "valor_destruido_por_peca": Counter(),
        "stuns_aplicados": 0, "mortes_por_stun": 0,
        "heatmap": [[0 for _ in range(COLUNAS)] for _ in range(LINHAS)], "tabuleiro_encravado": None
    }
    
    turnos = 0
    while not gs.game_over:
        turnos += 1
        best_move_str = BOT_INTERMEDIO.play(gs)
        
        if best_move_str:
            parsed = BOT_INTERMEDIO.play(gs)
            
            # TYPE GUARD: Garante ao Pylance que parsed é 100% um dicionário a partir daqui
            if not parsed:
                gs.game_over, gs.winner = True, "Bloqueio (Formato IA Inválido)"
                break
                
            m_type = parsed["type"].lower()
            start_r, start_c = parsed["start"]
            end_r, end_c = parsed["end"]
            
            atacante = gs.board[start_r][start_c]
            alvo = gs.board[end_r][end_c]
            
            area_stun = parsed.get("area", [])
            if m_type == "stun" and not area_stun and atacante:
                stuns_validos = atacante.get_valid_stuns(start_r, start_c, gs.board, gs.tile_effects)
                if stuns_validos and (end_r, end_c) in stuns_validos:
                    area_stun = stuns_validos[(end_r, end_c)].get("aoe", [])

            if m_type == "attack" and alvo:
                resultado["mortes_por_peca"][alvo.name] += 1
                if atacante:
                    resultado["abates_por_peca"][atacante.name] += 1
                    resultado["valor_destruido_por_peca"][atacante.name] += alvo.cost
            
            elif m_type == "stun":
                resultado["stuns_aplicados"] += len(area_stun)
                if alvo and alvo.stun_timer > 0:
                    resultado["mortes_por_peca"][alvo.name] += 1
                    resultado["mortes_por_stun"] += 1
                    if atacante:
                        resultado["abates_por_peca"][atacante.name] += 1
                        resultado["valor_destruido_por_peca"][atacante.name] += alvo.cost
                        
            elif m_type == "spawn":
                hero_name = parsed.get("spawn_name", "Unknown")
                resultado["spawns_realizados"][hero_name] += 1

            if m_type == "stun": gs.make_action((start_r, start_c), (end_r, end_c), "stun", affected_area=area_stun)
            elif m_type == "spawn": gs.make_action((start_r, start_c), (end_r, end_c), "spawn", spawn_name=parsed.get("spawn_name"))
            elif m_type == "spell": gs.make_action((start_r, start_c), (end_r, end_c), "spell", spell_name=parsed.get("spell_name"))
            else: gs.make_action((start_r, start_c), (end_r, end_c), m_type)
                
            resultado["heatmap"][end_r][end_c] += 1
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio Total"
            break
            
    

    resultado["turnos"] = turnos
    resultado["winner"] = str(gs.winner)
    resultado["tempo_segundos"] = time.time() - start_time
    return resultado

def correr_diagnostico_profundo(num_jogos=100):
    print(f"🔬 A INICIAR TELEMETRIA PROFUNDA ({num_jogos} Partidas)...\n")
    causas_fim = Counter()
    heatmap = [[0 for _ in range(COLUNAS)] for _ in range(LINHAS)]
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
                for r in range(LINHAS):
                    for c in range(COLUNAS): heatmap[r][c] += res["heatmap"][r][c]
                jogos_concluidos += 1
                sys.stdout.write(f"\rProcessado: {jogos_concluidos}/{num_jogos}")
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido...")
        if executor: executor.shutdown(wait=False, cancel_futures=True)
        sys.exit(0)

    print("\n\n✅ Diagnóstico concluído! A exportar ficheiros...")
    os.makedirs("logs", exist_ok=True)
    
    if log_encravados:
        with open(os.path.join("logs", "jogos_encravados_log.txt"), "w", encoding="utf-8") as f: f.write(log_encravados)

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

    with open(os.path.join("logs", "telemetria_profunda.json"), "w", encoding="utf-8") as f: json.dump(dados_exportacao, f, indent=4)
    with open(os.path.join("logs", "relatorio_telemetria.txt"), "w", encoding="utf-8") as f:
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