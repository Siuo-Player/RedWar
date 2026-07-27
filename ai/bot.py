# ai/bot.py
import random
from ai.search import find_best_move, get_all_moves_ordered

class BotConfig:
    def __init__(self, nome, time_limit_seconds):
        self.nome = nome
        self.time_limit_seconds = time_limit_seconds

    def play(self, gs):
        # A IA usa sempre o melhor avaliador e pesquisa infinitamente até esgotar o time_limit
        return find_best_move(gs, time_limit=self.time_limit_seconds)

class BotAleatorio:
    def __init__(self):
        self.nome = "Macaco Aleatório (100 ELO)"
        self.time_limit_seconds = 0.0

    def play(self, gs):
        # CORRIGIDO: A função agora devolve apenas uma lista já avaliada
        acoes = get_all_moves_ordered(gs)
        return random.choice(acoes) if acoes else None

def gerar_bot_por_elo(elo):
    """
    Mapeamento de ELO -> Tempo. 
    Se a UI pedir 1500 ELO, vamos estimar o tempo.
    O calibrador ajustará a nossa curva de forma científica.
    """
    if elo <= 100:
        return BotAleatorio()
        
    if elo <= 300:
        tempo = 0.1
    else:
        # Equação que aumenta o tempo de pensamento à medida que o ELO cresce
        tempo = 0.1 + ((elo - 300) / 2300.0) * 4.9
        
    return BotConfig(f"Motor Dinâmico (ELO {int(elo)})", time_limit_seconds=tempo)

# Presets oficias usados na UI e nos testes
BOT_ALEATORIO = BotAleatorio()
BOT_INICIANTE = gerar_bot_por_elo(800)
BOT_INTERMEDIO = gerar_bot_por_elo(1500)
BOT_AVANCADO = gerar_bot_por_elo(2000)
BOT_MESTRE = gerar_bot_por_elo(2600)