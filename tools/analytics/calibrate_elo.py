import sys
import os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.game_state import GameState
from tools.analytics.opening_tester import carregar_abertura_basica
from ai.bot import BOT_ALEATORIO, gerar_bot_por_elo

def run_fast_match(bot_brancas, bot_pretas):
    gs = GameState(time_limit_seconds=9999)
    carregar_abertura_basica(gs) 
    
    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        if gs.white_to_move: best_move = bot_brancas.play(gs)
        else: best_move = bot_pretas.play(gs)
            
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

def calibrar_motor(num_jogos=100):
    print("⚖️ A INICIAR CALIBRAÇÃO ELO MATEMÁTICA...")
    print("A testar 'Motor Base' contra a Âncora 'Bot Aleatório' (100 ELO).\n")
    
    bot_base = gerar_bot_por_elo(300) # O motor no seu estado mais fraco
    score_total_base = 0.0
    
    for i in range(num_jogos):
        # Alternar cores para não haver vantagem de primeiro turno
        if i % 2 == 0:
            score = run_fast_match(bot_base, BOT_ALEATORIO)
        else:
            # Se o bot_base joga de pretas, invertemos o score
            score = 1.0 - run_fast_match(BOT_ALEATORIO, bot_base)
            
        score_total_base += score
        sys.stdout.write(f"\rJogos completados: {i + 1}/{num_jogos} | Score da Base: {score_total_base}")
        sys.stdout.flush()

    win_rate = score_total_base / num_jogos
    print(f"\n\n📊 RESULTADOS OBTIDOS:")
    print(f"Taxa de Sucesso Real da IA Base: {win_rate * 100:.1f}%")
    
    # Prevenção de divisão por zero caso a IA perca 100% ou ganhe 100%
    win_rate = max(0.01, min(0.99, win_rate))
    
    # Cálculo inverso do ELO
    # RA = RB - 400 * log10((1 - EA) / EA)
    elo_calculado = 100 - 400 * math.log10((1.0 - win_rate) / win_rate)
    
    print(f"🧮 ELO Matemático Calculado para a IA Base: {elo_calculado:.0f} ELO")
    
    if elo_calculado < 100:
        print("❌ ALARME CRÍTICO: A tua IA está a jogar pior que movimentos aleatórios!")
    elif 250 <= elo_calculado <= 400:
        print("✅ PERFEITO! O teu 'chute' de 300 ELO bate perfeitamente com a teoria matemática.")
    else:
        print(f"⚠️ AJUSTE NECESSÁRIO: No teu ficheiro `ai/bot.py`, deves mudar a base de 300 ELO para {elo_calculado:.0f} ELO para a escala ficar cientificamente correta.")

if __name__ == "__main__":
    calibrar_motor(100)