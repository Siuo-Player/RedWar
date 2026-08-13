# ai/bot.py
import random
import subprocess
import os
from engine.action_parser import ActionParser
from engine.config import LINHAS

class CppEngineBot:
    """
    Controlador do Bot baseado no motor externo C++ (Arquitetura UCI).
    Comunica via Standard I/O ignorando o GIL do Python para máxima performance.
    """
    def __init__(self, depth=4):
        self.depth = depth
        self.nome = "StockWar C++" # <--- O Pylance agora já reconhece o nome!
        
        # Aponta para o Cérebro nativo e correto
        exe_path = os.path.join(os.path.dirname(__file__), "cpp_engine", "engine.exe")
        
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"Executável C++ não encontrado em: {exe_path}. Usa o script de build primeiro!")

        project_root = os.path.dirname(os.path.dirname(__file__))
        self.process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            cwd=project_root
        )
        
        self._send_command("isready")

    def play(self, game_state):
        # Alias para suportar scripts antigos de analytics
        return self.escolher_jogada(game_state)
        
    def _send_command(self, cmd: str):
        if self.process.poll() is not None or not self.process.stdin:
            return
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
        
    def _read_response(self) -> str | None:
        if self.process.poll() is not None or not self.process.stdout:
            return None
        return self.process.stdout.readline().strip()

    def escolher_jogada(self, game_state):
        rwen_str = game_state.to_rwen()
        
        self._send_command(f"position rwen {rwen_str}")
        self._send_command(f"go depth {self.depth}")
        
        while True:
            response = self._read_response()
            if not response:
                break
            
            if response.startswith("bestmove"):
                parts = response.split(" ", 1)
                if len(parts) > 1:
                    raw_action = parts[1].strip()
                    
                    # 1. ActionParser extrai o dicionário bruto Agnóstico (ex: {"action": "MOVE", "origin": "A2", "target": "A3"})
                    parsed = ActionParser.parse(raw_action)
                    if not parsed:
                        return None
                        
                    # 2. Converter coordenadas Algébricas (A2) para índices de matriz (R, C) para o GameState consumir
                    final_action = {
                        "type": parsed["action"].lower(),
                        "start": ActionParser.alg_to_coords(parsed["origin"], LINHAS),
                        "end": ActionParser.alg_to_coords(parsed["target"], LINHAS)
                    }
                    
                    # Se transportar nomes de spells/spawns, mantemos no dicionário
                    if "spell" in parsed:
                        final_action["spell_name"] = parsed["spell"]
                    if "hero" in parsed:
                        final_action["spawn_name"] = parsed["hero"]
                        
                    # (Nota: As ações de 'stun' baseadas em área (affected_area) são calculadas em C++ puro.
                    #  O Python apenas precisa de saber o ponto de focagem "end", e a validação do board resolve a área).
                    return final_action
                        
        return None

    def __del__(self):
        try:
            self._send_command("quit")
            self.process.terminate()
        except Exception:
            pass




# --- BLOCO DE RETROCOMPATIBILIDADE PARA FERRAMENTAS DE ANALYTICS ---
class BotConfig:
    def __init__(self, *args, **kwargs):
        pass

class BotAleatorio:
    def __init__(self):
        self.nome = "Bot Bebado"
        
    def play(self, gs):
        return self.escolher_jogada(gs)
        
    def escolher_jogada(self, gs):
        acoes = []
        current_team = 'brancas' if gs.white_to_move else 'pretas'
        for r in range(8):
            for c in range(8):
                p = gs.board[r][c]
                if p and p.team == current_team and getattr(p, 'stun_timer', 0) == 0:
                    for mv in p.get_valid_moves(r, c, gs.board, gs.tile_effects):
                        acoes.append({"type": "move", "start": (r, c), "end": mv})
                    for at in p.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                        acoes.append({"type": "attack", "start": (r, c), "end": at})
                    stuns = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)
                    for alvo, info in stuns.items():
                        if info.get("has_enemy"):
                            acoes.append({"type": "stun", "start": (r, c), "end": alvo, "area": info["aoe"]})
                    for sp in p.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                        acoes.append({"type": "spawn", "start": (r, c), "end": (sp[0], sp[1]), "spawn_name": sp[2]})
                    if hasattr(p, 'get_valid_spells'):
                        for spell in p.get_valid_spells(r, c, gs.board, gs.tile_effects):
                            acoes.append({"type": "spell", "start": (r, c), "end": spell["target"], "spell_name": spell["spell_type"]})
        if acoes:
            return random.choice(acoes)
        return None
        
BOT_ALEATORIO = BotAleatorio()
BOT_INICIANTE = CppEngineBot(depth=2)
BOT_INICIANTE.nome = "StockWar Iniciante (D2)"

BOT_INTERMEDIO = CppEngineBot(depth=4)
BOT_INTERMEDIO.nome = "StockWar Intermédio (D4)"

BOT_AVANCADO = CppEngineBot(depth=6)
BOT_AVANCADO.nome = "StockWar Avançado (D6)"

def gerar_bot_por_elo(elo):
    if elo < 800: return BOT_ALEATORIO
    if elo < 1400: return BOT_INICIANTE
    if elo < 1900: return BOT_INTERMEDIO
    return BOT_AVANCADO