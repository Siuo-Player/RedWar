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
    Implementa Lazy-Loading e Auto-Healing para não criar processos zombie.
    """
    def __init__(self, depth=4):
        self.depth = depth
        self.nome = f"StockWar C++ (D{depth})"
        self.exe_path = os.path.join(os.path.dirname(__file__), "cpp_engine", "engine.exe")
        self.process = None

    def _ensure_engine_running(self):
        # Lazy load: Se o processo não existe ou já crashou/fechou, arranca um novo
        if self.process is None or self.process.poll() is not None:
            if not os.path.exists(self.exe_path):
                raise FileNotFoundError(f"Executável C++ não encontrado em: {self.exe_path}. Usa o script de build primeiro!")

            project_root = os.path.dirname(os.path.dirname(__file__))
            self.process = subprocess.Popen(
                [self.exe_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                cwd=project_root
            )
            self._send_command("isready", ensure_running=False)

    def play(self, game_state):
        # Alias para suportar scripts antigos de analytics
        return self.escolher_jogada(game_state)
        
    def _send_command(self, cmd: str, ensure_running=True):
        if ensure_running:
            self._ensure_engine_running()
            
        # Type Guard explícito para o Pylance: se for None, aborta antes de chamar .poll()
        if self.process is None or self.process.poll() is not None or not self.process.stdin:
            return
            
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
        
    def _read_response(self) -> str | None:
        self._ensure_engine_running()
        
        # Type Guard explícito para o Pylance
        if self.process is None or self.process.poll() is not None or not self.process.stdout:
            return None
            
        return self.process.stdout.readline().strip()

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
                            # Correção: Ler o tuplo por índices (0: linha, 1: coluna, 2: nome)
                            acoes.append({"type": "spell", "start": (r, c), "end": (spell[0], spell[1]), "spell_name": spell[2]})
        if acoes:
            return random.choice(acoes)
        return None

    def __del__(self):
        if self.process and self.process.poll() is None:
            try:
                self._send_command("quit", ensure_running=False)
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

# As instâncias já não abrem N processos em simultâneo graças ao Lazy Load
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