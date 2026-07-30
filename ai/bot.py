import random
from ai.search import find_best_move, get_all_moves_ordered
from engine.config import LINHAS

def coords_para_alg(r, c):
    """Converte (r, c) em Notação Algébrica"""
    return f"{chr(65 + c)}{LINHAS - r}"

def format_agnostic_string(move_dict):
    """Traduz o dicionário do motor para a String Agnóstica."""
    if not move_dict:
        return None
        
    sr, sc = move_dict["start"]
    er, ec = move_dict["end"]
    start_alg = coords_para_alg(sr, sc)
    end_alg = coords_para_alg(er, ec)
    
    m_type = move_dict["type"]
    
    if m_type == "move": return f"MOVE {start_alg} {end_alg}"
    elif m_type == "attack": return f"ATTACK {start_alg} {end_alg}"
    elif m_type == "stun": return f"STUN {start_alg} {end_alg}"
    elif m_type == "spawn": return f"SPAWN {move_dict['spawn_name']} {start_alg} {end_alg}"
    elif m_type == "spell": return f"SPELL {move_dict['spell_name']} {start_alg} {end_alg}"
        
    return None

class BotConfig:
    def __init__(self, nome, depth_limit, noise_level):
        self.nome = nome
        self.depth_limit = depth_limit
        self.noise_level = noise_level

    def play(self, gs):
        raw_move = find_best_move(gs, depth_limit=self.depth_limit, noise_level=self.noise_level)
        return format_agnostic_string(raw_move)

class BotAleatorio:
    def __init__(self):
        self.nome = "Macaco Aleatório (100 ELO)"

    def play(self, gs):
        acoes = get_all_moves_ordered(gs)
        if not acoes: return None
        return format_agnostic_string(random.choice(acoes))

def gerar_bot_por_elo(elo):
    if elo <= 100: return BotAleatorio()
    depth_limit = max(1, elo // 400)
    noise_level = max(0, (3000 - elo) / 10)
    return BotConfig(f"Motor Dinâmico (ELO {int(elo)})", depth_limit=depth_limit, noise_level=noise_level)

BOT_ALEATORIO = BotAleatorio()
BOT_INICIANTE = gerar_bot_por_elo(900)
BOT_INTERMEDIO = gerar_bot_por_elo(1500)
BOT_AVANCADO = gerar_bot_por_elo(2000)
BOT_MESTRE = gerar_bot_por_elo(2500)