import random
import subprocess
import os
import sys
from engine.action_parser import ActionParser
from engine.config import LINHAS

MAX_DRAFT_BUDGET = 10_000

class CppEngineBot:
    """Controlador do bot baseado no motor externo C++."""
    def __init__(self, nodes=10000, executable_path=None):
        if not isinstance(nodes, int) or isinstance(nodes, bool) or nodes <= 0:
            raise ValueError("nodes must be a positive integer")
        self.nodes = nodes
        self.nome = f"StockWar C++ (N{nodes})"
        if executable_path is not None:
            self.exe_path = os.path.abspath(executable_path)
        else:
            binary_name = "engine.exe" if sys.platform == "win32" else "engine"
            self.exe_path = os.path.join(os.path.dirname(__file__), "cpp_engine", binary_name)
        self.process = None
        self.last_position_rwen = None

    def _ensure_engine_running(self):
        if self.process is None or self.process.poll() is not None:
            if not os.path.exists(self.exe_path):
                raise FileNotFoundError(f"Executável C++ não encontrado em: {self.exe_path}. Usa o script de build primeiro!")
            project_root = os.path.dirname(os.path.dirname(__file__))
            self.process = subprocess.Popen(
                [self.exe_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, encoding='utf-8', cwd=project_root
            )
            self._send_command("isready", ensure_running=False)

    def play(self, game_state):
        return self.escolher_jogada(game_state)

    def _send_command(self, cmd: str, ensure_running=True):
        if ensure_running: self._ensure_engine_running()
        if self.process is None or self.process.poll() is not None or not self.process.stdin: return
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()

    def _read_response(self) -> str | None:
        self._ensure_engine_running()
        if self.process is None or self.process.poll() is not None or not self.process.stdout: return None
        return self.process.stdout.readline().strip()

    def start_pondering(self, game_state):
        rwen = game_state.to_rwen()
        self.last_position_rwen = rwen
        self._send_command(f"position rwen {rwen}")
        self._send_command("go infinite")

    def stop_pondering(self):
        self._send_command("stop")
        while True:
            response = self._read_response()
            if response and response.startswith("bestmove"): break

    def escolher_jogada(self, game_state):
        rwen = game_state.to_rwen()
        self.last_position_rwen = rwen
        self._send_command(f"position rwen {rwen}")
        self._send_command(f"go nodes {self.nodes}")
        while True:
            response = self._read_response()
            if not response:
                raise RuntimeError(f"C++ engine returned no response for position: {rwen}")
            if response.startswith("bestmove"):
                parts = response.split(" ", 1)
                move_text = parts[1].strip() if len(parts) > 1 else ""
                if move_text == "0000":
                    raise RuntimeError(
                        f"C++ engine returned bestmove 0000 at {rwen} (nodes={self.nodes})"
                    )
                parsed = ActionParser.parse(move_text)
                if not parsed:
                    raise RuntimeError(
                        f"C++ engine returned unparseable move {move_text!r} at {rwen} (nodes={self.nodes})"
                    )
                origin = ActionParser.alg_to_coords(parsed['origin'], LINHAS)
                source_piece = game_state.board[origin[0]][origin[1]]
                if parsed['action'].upper() == 'STUN' and source_piece is not None and source_piece.name == 'FrostMage':
                    parsed['action'] = 'SPELL'
                    parsed['spell'] = 'nevada'
                final_action = {
                    "type": parsed["action"].lower(),
                    "start": ActionParser.alg_to_coords(parsed["origin"], LINHAS),
                    "end": ActionParser.alg_to_coords(parsed["target"], LINHAS)
                }
                if "spell" in parsed: final_action["spell_name"] = parsed["spell"]
                if "hero" in parsed: final_action["spawn_name"] = parsed["hero"]
                return final_action
        return None

    def __del__(self):
        if self.process and self.process.poll() is None:
            try:
                self._send_command("quit", ensure_running=False)
                self.process.terminate()
            except Exception:
                pass

    def gerar_draft_inteligente(self, orcamento, catalogo, equipa):
        import time
        if not isinstance(orcamento, int) or isinstance(orcamento, bool) or orcamento < 0 or orcamento > MAX_DRAFT_BUDGET:
            raise ValueError(f"orcamento must be an integer between 0 and {MAX_DRAFT_BUDGET}")
        start_time = time.time()
        pecas_validas = [p for p in catalogo if p.get("cost", 9999) <= orcamento]
        dp = [(0, []) for _ in range(orcamento + 1)]
        limite_pecas = 16
        for w in range(1, orcamento + 1):
            melhor_gasto = dp[w-1][0]
            melhor_lista = dp[w-1][1]
            for p in pecas_validas:
                c = p["cost"]
                if w >= c:
                    gasto_anterior, lista_anterior = dp[w-c]
                    if len(lista_anterior) < limite_pecas:
                        novo_gasto = gasto_anterior + c
                        if novo_gasto > melhor_gasto:
                            melhor_gasto = novo_gasto
                            melhor_lista = lista_anterior + [p]
            dp[w] = (melhor_gasto, melhor_lista)
        pontos_gastos, equipa_escolhida = dp[orcamento]
        tempo_gasto = (time.time() - start_time) * 1000.0
        equipa_escolhida = sorted(equipa_escolhida, key=lambda x: x["cost"], reverse=True)
        linhas = [6, 7] if equipa == 'brancas' else [1, 0]
        posicoes = []
        idx = 0
        for r in linhas:
            for c in range(8):
                if idx < len(equipa_escolhida):
                    posicoes.append({"r": r, "c": c, "piece_class": equipa_escolhida[idx]["class"]})
                    idx += 1
        return {"pontos_gastos": pontos_gastos, "pontos_desperdicados": orcamento-pontos_gastos, "tempo_ms": tempo_gasto, "draft": posicoes}

class BotConfig:
    def __init__(self, *args, **kwargs): pass

class BotAleatorio:
    def __init__(self): self.nome = "Bot Bebado"
    def play(self, gs): return self.escolher_jogada(gs)
    def escolher_jogada(self, gs):
        acoes = []
        current_team = 'brancas' if gs.white_to_move else 'pretas'
        for r in range(8):
            for c in range(8):
                p = gs.board[r][c]
                if p and p.team == current_team and getattr(p, 'stun_timer', 0) == 0:
                    for mv in p.get_valid_moves(r,c,gs.board,gs.tile_effects): acoes.append({"type":"move","start":(r,c),"end":mv})
                    for at in p.get_valid_attacks(r,c,gs.board,gs.tile_effects): acoes.append({"type":"attack","start":(r,c),"end":at})
                    stuns = p.get_valid_stuns(r,c,gs.board,gs.tile_effects)
                    for alvo,info in stuns.items():
                        if info.get("has_enemy"): acoes.append({"type":"stun","start":(r,c),"end":alvo,"area":info.get("aoe",[])})
                    for sp in p.get_valid_spawns(r,c,gs.board,gs.tile_effects): acoes.append({"type":"spawn","start":(r,c),"end":(sp[0],sp[1]),"spawn_name":sp[2]})
                    if hasattr(p,'get_valid_spells'):
                        for spell in p.get_valid_spells(r,c,gs.board,gs.tile_effects):
                            if isinstance(spell,dict):
                                end_pos = spell.get("target", (r,c)); spell_name = spell.get("spell_type")
                                if spell_name: acoes.append({"type":"spell","start":(r,c),"end":end_pos,"spell_name":spell_name})
                            elif isinstance(spell,(tuple,list)) and len(spell) >= 3 and spell[2]:
                                acoes.append({"type":"spell","start":(r,c),"end":(spell[0],spell[1]),"spell_name":spell[2]})
        return random.choice(acoes) if acoes else None

BOT_ALEATORIO = BotAleatorio()
BOT_INICIANTE = CppEngineBot(nodes=100_000)
BOT_INTERMEDIO = CppEngineBot(nodes=500_000)
BOT_AVANCADO = CppEngineBot(nodes=1_000_000)
BOT_INICIANTE.nome = "StockWar Iniciante (N100k)"
BOT_INTERMEDIO.nome = "StockWar Intermédio (N500k)"
BOT_AVANCADO.nome = "StockWar Avançado (N1M)"
TREINO_INICIANTE = CppEngineBot(nodes=1_000)
TREINO_INTERMEDIO = CppEngineBot(nodes=5_000)
TREINO_AVANCADO = CppEngineBot(nodes=10_000)
TREINO_INICIANTE.nome = "Treino Iniciante (N1k)"
TREINO_INTERMEDIO.nome = "Treino Intermédio (N5k)"
TREINO_AVANCADO.nome = "Treino Avançado (N10k)"

def gerar_bot_por_elo(elo):
    if elo < 800: return BOT_ALEATORIO
    if elo < 1400: return BOT_INICIANTE
    if elo < 1900: return BOT_INTERMEDIO
    return BOT_AVANCADO
