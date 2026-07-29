# ai/bot.py
import os
import json
import random
import bisect
from ai.search import find_best_move, get_all_moves_ordered

class BotConfig:
    def __init__(self, nome, time_limit_seconds):
        self.nome = nome
        self.time_limit_seconds = time_limit_seconds

    def play(self, gs):
        return find_best_move(gs, time_limit=self.time_limit_seconds)

class BotAleatorio:
    def __init__(self):
        self.nome = "Macaco Aleatório (100 ELO)"
        self.time_limit_seconds = 0.0

    def play(self, gs):
        acoes = get_all_moves_ordered(gs)
        return random.choice(acoes) if acoes else None

ELO_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'analytics', 'elo_config.json')

def interpolar_tempo_por_elo(elo_alvo):
    """
    Constrói a curva contínua de tempo-ELO alinhada com a escala real da tua calibração.
    Usa bissecção linear para interpolação exata sem blocos 'elif'.
    """
    # Fallback calibrado com base nos dados reais obtidos na arena
    # Curva sanitizada com base no teto tático do RedWar
    curva_empirica = [
        (100.0, 0.0),   # Macaco Aleatório
        (220.0, 0.5),   # Base Tática (O teto do 0.5s sem a inflação do Macaco)
        (250.0, 1.0),   # Intermédio (Onde o 1.0s deveria estabilizar)
        (280.0, 2.0)    # O pico atual confirmado do motor de 2.0s
    ]

    if os.path.exists(ELO_FILE):
        try:
            with open(ELO_FILE, 'r') as f:
                dados = json.load(f)
            
            pontos = []
            for nome, elo_real in dados.items():
                if "Aleatório" in nome:
                    pontos.append((elo_real, 0.0))
                elif "Motor" in nome:
                    tempo_str = nome.split('(')[1].replace('s)', '')
                    pontos.append((elo_real, float(tempo_str)))
            
            if len(pontos) > 1:
                pontos.sort(key=lambda x: x[0])
                curva_empirica = pontos
        except:
            pass
            
    elos = [p[0] for p in curva_empirica]
    tempos = [p[1] for p in curva_empirica]

    if elo_alvo <= elos[0]:
        return tempos[0]
    if elo_alvo >= elos[-1]:
        return tempos[-1]

    idx = bisect.bisect_right(elos, elo_alvo)
    elo_inf, elo_sup = elos[idx - 1], elos[idx]
    tempo_inf, tempo_sup = tempos[idx - 1], tempos[idx]
    
    fator = (elo_alvo - elo_inf) / (elo_sup - elo_inf)
    return tempo_inf + fator * (tempo_sup - tempo_inf)

def gerar_bot_por_elo(elo):
    if elo <= 100:
        return BotAleatorio()
        
    tempo_exato = interpolar_tempo_por_elo(elo)
    return BotConfig(f"Motor Dinâmico (ELO {int(elo)})", time_limit_seconds=tempo_exato)

# Presets oficiais baseados na escala real da arena
BOT_ALEATORIO = BotAleatorio()
BOT_INICIANTE = gerar_bot_por_elo(140)
BOT_INTERMEDIO = gerar_bot_por_elo(200)
BOT_AVANCADO = gerar_bot_por_elo(250)
BOT_MESTRE = gerar_bot_por_elo(300)