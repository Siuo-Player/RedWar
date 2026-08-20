import sys
import os
import json
from collections import Counter
import random
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LIMITE_TURNOS, LINHAS, COLUNAS
from ai.bot import BOT_INICIANTE, BOT_INTERMEDIO, BOT_AVANCADO, BOT_ALEATORIO
from engine.action_parser import ActionParser

# --- FASE 4: O REGRESSO DO D6 À ARENA ---
POOL_BOTS = [
    (BOT_ALEATORIO, 100),
    (BOT_INICIANTE, 900),
    (BOT_INTERMEDIO, 1500),
    (BOT_AVANCADO, 2000)
]

def preencher_draft_aleatorio(gs, team, linhas_validas, orcamento):
    pontos = orcamento
    catalogo = obter_catalogo_pecas()
    composicao = Counter()
    
    for r in linhas_validas:
        for c in range(COLUNAS):
            validas = [p for p in catalogo if p["cost"] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = escolha["class"](team)
            pontos -= escolha["cost"]
            composicao[escolha["name"]] += 1
            
    return dict(composicao)

def simular_jogo_treino(seed, jogo_idx, total_jogos, global_stats):
    random.seed(seed)
    gs = GameState(time_limit_seconds=99999)
    
    bot_brancas, elo_brancas = random.choice(POOL_BOTS)
    bot_pretas, elo_pretas = random.choice(POOL_BOTS)
    
    comp_pretas = preencher_draft_aleatorio(gs, 'pretas', [0, 1], ORCAMENTO_PRETAS)
    comp_brancas = preencher_draft_aleatorio(gs, 'brancas', [LINHAS - 2, LINHAS - 1], ORCAMENTO_BRANCAS)

    turnos = 0
    while not gs.game_over and turnos < LIMITE_TURNOS:
        turnos += 1
        global_stats["turnos_totais"] += 1
        
        decorrido = time.time() - global_stats["start_time"]
        t_medio_turno = decorrido / max(1, global_stats["turnos_totais"])
        
        turnos_restantes_max = (total_jogos * LIMITE_TURNOS) - global_stats["turnos_totais"]
        eta_max_minutos = (turnos_restantes_max * t_medio_turno) / 60.0
        
        nome_b = bot_brancas.nome[:10]
        nome_p = bot_pretas.nome[:10]
        
        sys.stdout.write(
            f"\r[Jogo {jogo_idx}/{total_jogos}] "
            f"Turno {turnos}/{LIMITE_TURNOS} | "
            f"B:{nome_b} vs P:{nome_p} | "
            f"T/Turno: {t_medio_turno:.2f}s | "
            f"Max ETA: {eta_max_minutos:.1f}m   "
        )
        sys.stdout.flush()

        parsed = bot_brancas.escolher_jogada(gs) if gs.white_to_move else bot_pretas.escolher_jogada(gs)
        
        if parsed:
            m_type = parsed["type"].lower()
            start_r, start_c = parsed["start"]
            end_r, end_c = parsed["end"]

            if m_type == "stun":
                atacante = gs.board[start_r][start_c]
                area_stun = parsed.get("area", [])
                if not area_stun and atacante:
                    stuns_validos = atacante.get_valid_stuns(start_r, start_c, gs.board, gs.tile_effects)
                    if stuns_validos and (end_r, end_c) in stuns_validos:
                        area_stun = stuns_validos[(end_r, end_c)].get("aoe", [])
                gs.make_action((start_r, start_c), (end_r, end_c), "stun", affected_area=area_stun)
            elif m_type == "spawn":
                gs.make_action((start_r, start_c), (end_r, end_c), "spawn", spawn_name=parsed.get("spawn_name"))
            elif m_type == "spell":
                gs.make_action((start_r, start_c), (end_r, end_c), "spell", spell_name=parsed.get("spell_name"))
            else:
                gs.make_action((start_r, start_c), (end_r, end_c), m_type)
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio Total"
            break
            
    resultado = 0.5
    if "Brancas" in str(gs.winner): resultado = 1.0
    elif "Pretas" in str(gs.winner): resultado = 0.0

    return {
        "white_elo": elo_brancas,
        "black_elo": elo_pretas,
        "white_draft": comp_brancas,
        "black_draft": comp_pretas,
        "result": resultado
    }

def gerar_estatisticas_treino(num_jogos=200):
    print(f"🧠 A gerar metadados de combate ({num_jogos} partidas heterogéneas, sequencial)...")
    
    historico_partidas = []
    global_stats = {
        "start_time": time.time(),
        "turnos_totais": 0
    }
    
    for i in range(num_jogos):
        resultado = simular_jogo_treino(random.randint(1, 999999) + i, i + 1, num_jogos, global_stats)
        historico_partidas.append(resultado)

    stats = {
        "total_matches": num_jogos,
        "matches": historico_partidas
    }
    
    os.makedirs("data", exist_ok=True)
    caminho_stats = os.path.join("data", "estatisticas_treino.json")
    with open(caminho_stats, "w") as f:
        json.dump(stats, f, indent=4)
        
    tempo_total = time.time() - global_stats["start_time"]
    print(f"\n✅ {caminho_stats} atualizado em {tempo_total/60:.1f} minutos!")

if __name__ == "__main__":
    # Multiplicador 10x aplicado aqui: de 20 para 200 jogos
    gerar_estatisticas_treino(200)