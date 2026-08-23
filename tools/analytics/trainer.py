import sys
import os
import json
from collections import Counter
import random
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LINHAS, COLUNAS
from ai.bot import TREINO_INICIANTE, TREINO_INTERMEDIO, TREINO_AVANCADO, BOT_ALEATORIO

POOL_BOTS = [
    (BOT_ALEATORIO, 100),
    (TREINO_INICIANTE, 900),
    (TREINO_INTERMEDIO, 1500),
    (TREINO_AVANCADO, 2000)
]

MAX_TURNS_PER_GAME = 200


def formatar_tempo(segundos):
    segundos = max(0, int(segundos))
    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    parts = []
    if dias > 0: parts.append(f"{dias}d")
    if horas > 0: parts.append(f"{horas}h")
    if minutos > 0: parts.append(f"{minutos}m")
    parts.append(f"{segs}s")
    return " ".join(parts) if parts else "0s"


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


def executar_acao_treino(gs, parsed):
    if not isinstance(parsed, dict): raise ValueError("Bot returned a non-dict action")
    m_type = str(parsed["type"]).lower()
    start_r, start_c = parsed["start"]
    end_r, end_c = parsed["end"]
    if m_type == "stun":
        atacante = gs.board[start_r][start_c]
        area_stun = parsed.get("area", [])
        if not area_stun and atacante:
            stuns_validos = atacante.get_valid_stuns(start_r,start_c,gs.board,gs.tile_effects)
            if stuns_validos and (end_r,end_c) in stuns_validos:
                area_stun = stuns_validos[(end_r,end_c)].get("aoe",[])
        gs.make_action((start_r,start_c),(end_r,end_c),"stun",affected_area=area_stun)
    elif m_type == "spawn":
        gs.make_action((start_r,start_c),(end_r,end_c),"spawn",spawn_name=parsed.get("spawn_name"))
    elif m_type == "spell":
        gs.make_action((start_r,start_c),(end_r,end_c),"spell",spell_name=parsed.get("spell_name"))
    elif m_type in {"move","attack"}:
        gs.make_action((start_r,start_c),(end_r,end_c),m_type)
    else:
        raise ValueError(f"Unknown action type: {m_type!r}")


def simular_jogo_treino(seed, jogo_idx, total_jogos, global_stats):
    random.seed(seed)
    gs = GameState(time_limit_seconds=99999)
    bot_brancas, elo_brancas = random.choice(POOL_BOTS)
    bot_pretas, elo_pretas = random.choice(POOL_BOTS)
    comp_pretas = preencher_draft_aleatorio(gs,"pretas",[0,1],ORCAMENTO_PRETAS)
    comp_brancas = preencher_draft_aleatorio(gs,"brancas",[LINHAS-2,LINHAS-1],ORCAMENTO_BRANCAS)
    turnos=0; invalid_action=None; invalid_action_bot=None
    while not gs.game_over and turnos < MAX_TURNS_PER_GAME:
        turnos += 1; global_stats["turnos_totais"] += 1
        decorrido=time.time()-global_stats["start_time"]
        t_medio_turno=decorrido/max(1,global_stats["turnos_totais"])
        turnos_medios_por_jogo=(global_stats["turnos_totais"]/max(1,jogo_idx-1) if jogo_idx>1 else MAX_TURNS_PER_GAME)
        turnos_estimados_restantes=max(0,(total_jogos-jogo_idx+1)*turnos_medios_por_jogo-turnos)
        segundos_restantes=turnos_estimados_restantes*t_medio_turno
        nome_b=bot_brancas.nome[:10]; nome_p=bot_pretas.nome[:10]
        sys.stdout.write(f"\r[Jogo {jogo_idx}/{total_jogos}] Turno {turnos} | B:{nome_b} vs P:{nome_p} | T/Turno: {t_medio_turno:.2f}s | Falta: {formatar_tempo(segundos_restantes)}   ")
        sys.stdout.flush()
        active_bot=bot_brancas if gs.white_to_move else bot_pretas
        parsed=active_bot.escolher_jogada(gs)
        if not parsed:
            gs.check_game_over()
            if not gs.game_over: gs.game_over,gs.winner=True,"Bloqueio Total"
            break
        try:
            executar_acao_treino(gs,parsed)
        except (KeyError,IndexError,TypeError,ValueError) as exc:
            invalid_action=str(exc); invalid_action_bot=active_bot.nome; gs.game_over=True; gs.winner="Ação inválida do bot"; break
    if not gs.game_over:
        gs.game_over=True; gs.winner=f"Empate ({MAX_TURNS_PER_GAME} turnos)"
    resultado=0.5
    if invalid_action is None:
        if "Brancas" in str(gs.winner): resultado=1.0
        elif "Pretas" in str(gs.winner): resultado=0.0
    match={"white_elo":elo_brancas,"black_elo":elo_pretas,"white_draft":comp_brancas,"black_draft":comp_pretas,"result":resultado,"valid":invalid_action is None}
    if invalid_action is not None:
        match["invalid_action"]=invalid_action; match["invalid_action_bot"]=invalid_action_bot
    return match


def gerar_estatisticas_treino(num_jogos=200):
    print(f"🧠 A gerar metadados de combate ({num_jogos} partidas heterogéneas, sequencial)...")
    historico_partidas=[]
    global_stats={"start_time":time.time(),"turnos_totais":0,"invalid_matches":0}
    for i in range(num_jogos):
        resultado=simular_jogo_treino(random.randint(1,999999)+i,i+1,num_jogos,global_stats)
        if not resultado["valid"]:
            global_stats["invalid_matches"] += 1
            print(f"\n⚠️ Partida {i+1} descartada: ação inválida do bot {resultado.get('invalid_action_bot','unknown')}: {resultado.get('invalid_action','unknown')}")
        historico_partidas.append(resultado)
    stats={"total_matches":num_jogos,"valid_matches":sum(1 for match in historico_partidas if match.get("valid",True)),"invalid_matches":global_stats["invalid_matches"],"matches":historico_partidas}
    os.makedirs("data",exist_ok=True)
    caminho_stats=os.path.join("data","estatisticas_treino.json")
    with open(caminho_stats,"w",encoding="utf-8") as f: json.dump(stats,f,indent=4)
    tempo_total=time.time()-global_stats["start_time"]
    print(f"\n✅ {caminho_stats} atualizado em {tempo_total/60:.1f} minutos! ({stats['valid_matches']} válidas, {stats['invalid_matches']} descartadas)")

if __name__ == "__main__": gerar_estatisticas_treino(200)
