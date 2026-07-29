# ai/bot.py
import random
from ai.search import find_best_move, get_all_moves_ordered

class BotConfig:
    def __init__(self, nome, depth_limit, noise_level):
        self.nome = nome
        self.depth_limit = depth_limit
        self.noise_level = noise_level

    def play(self, gs):
        return find_best_move(gs, depth_limit=self.depth_limit, noise_level=self.noise_level)

class BotAleatorio:
    def __init__(self):
        self.nome = "Macaco Aleatório (100 ELO)"

    def play(self, gs):
        acoes = get_all_moves_ordered(gs)
        return random.choice(acoes) if acoes else None

def gerar_bot_por_elo(elo):
    if elo <= 100:
        return BotAleatorio()

    depth_limit = max(1, elo // 400)
    noise_level = max(0, (3000 - elo) / 10)
    return BotConfig(f"Motor Dinâmico (ELO {int(elo)})", depth_limit=depth_limit, noise_level=noise_level)

# Presets oficiais — escala de xadrez padrão
BOT_ALEATORIO = BotAleatorio()
BOT_INICIANTE = gerar_bot_por_elo(900)
BOT_INTERMEDIO = gerar_bot_por_elo(1500)
BOT_AVANCADO = gerar_bot_por_elo(2000)
BOT_MESTRE = gerar_bot_por_elo(2500)
