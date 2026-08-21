# ai/bot.py
import random
import subprocess
import os
import sys
from engine.action_parser import ActionParser
from engine.config import LINHAS

class CppEngineBot:
    """
    Controlador do Bot baseado no motor externo C++ (Arquitetura UCI).
    Comunica via Standard I/O ignorando o GIL do Python para máxima performance.
    Implementa Lazy-Loading e Auto-Healing para não criar processos zombie.
    """
    def __init__(self, nodes=10000):
        self.nodes = nodes
        self.nome = f"StockWar C++ (N{nodes})"
        
        # --- VERIFICAÇÃO CROSS-PLATFORM ---
        if sys.platform == "win32":
            binary_name = "engine.exe" # No teu PC
        else:
            binary_name = "engine"     # No GitHub (Linux)
            
        self.exe_path = os.path.join(os.path.dirname(__file__), "cpp_engine", binary_name)
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
                stderr=subprocess.DEVNULL,
                text=True,
                encoding='utf-8',
                cwd=project_root
            )
            self._send_command("isready", ensure_running=False)

    def play(self, game_state):
        return self.escolher_jogada(game_state)
        
    def _send_command(self, cmd: str, ensure_running=True):
        if ensure_running:
            self._ensure_engine_running()
            
        if self.process is None or self.process.poll() is not None or not self.process.stdin:
            return
            
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
        
    def _read_response(self) -> str | None:
        self._ensure_engine_running()
        
        if self.process is None or self.process.poll() is not None or not self.process.stdout:
            return None
            
        return self.process.stdout.readline().strip()

    def start_pondering(self, game_state):
        """
        MODO PREDADOR: Põe a IA a calcular os infinitos futuros possíveis
        enquanto o jogador humano está a pensar no seu turno.
        """
        rwen_str = game_state.to_rwen()
        self._send_command(f"position rwen {rwen_str}")
        self._send_command("go infinite")

    def stop_pondering(self):
        """
        O jogador humano moveu a peça. Manda parar a especulação, 
        absorve o lixo gerado no Standard Output e prepara o cérebro.
        """
        self._send_command("stop")
        
        # O C++ vai cuspir um "bestmove" que ele achava que o humano devia fazer.
        # Nós consumimos e ignoramos essa linha para limpar o canal de comunicação.
        while True:
            response = self._read_response()
            if response and response.startswith("bestmove"):
                break

    def escolher_jogada(self, game_state):
        rwen_str = game_state.to_rwen()
        self._send_command(f"position rwen {rwen_str}")
        self._send_command(f"go nodes {self.nodes}")
        
        while True:
            response = self._read_response()
            if not response:
                break
            
            if response.startswith("bestmove"):
                parts = response.split(" ", 1)
                if len(parts) > 1:
                    raw_action = parts[1].strip()
                    
                    parsed = ActionParser.parse(raw_action)
                    if not parsed:
                        return None
                        
                    final_action = {
                        "type": parsed["action"].lower(),
                        "start": ActionParser.alg_to_coords(parsed["origin"], LINHAS),
                        "end": ActionParser.alg_to_coords(parsed["target"], LINHAS)
                    }
                    
                    if "spell" in parsed:
                        final_action["spell_name"] = parsed["spell"]
                    if "hero" in parsed:
                        final_action["spawn_name"] = parsed["hero"]
                        
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
        """
        Resolve o Problema da Mochila (Unbounded Knapsack DP) para encontrar
        a equipa perfeita que gasta o máximo de pontos possíveis, limitando a 16 peças.
        """
        import time
        start_time = time.time()
        
        pecas_validas = [p for p in catalogo if p.get("cost", 9999) <= orcamento]
        
        # dp[w] = (max_pontos_gastos, lista_de_pecas)
        dp = [(0, []) for _ in range(orcamento + 1)]
        limite_pecas = 16 # O limite físico da zona de draft (2 linhas x 8 colunas)
        
        for w in range(1, orcamento + 1):
            melhor_gasto = dp[w-1][0]
            melhor_lista = dp[w-1][1]
            
            for p in pecas_validas:
                c = p["cost"]
                if w >= c:
                    gasto_anterior, lista_anterior = dp[w - c]
                    # Garante que não compra mais peças do que o espaço no tabuleiro
                    if len(lista_anterior) < limite_pecas:
                        novo_gasto = gasto_anterior + c
                        if novo_gasto > melhor_gasto:
                            melhor_gasto = novo_gasto
                            melhor_lista = lista_anterior + [p]
            
            dp[w] = (melhor_gasto, melhor_lista)
            
        pontos_gastos, equipa_escolhida = dp[orcamento]
        tempo_gasto = (time.time() - start_time) * 1000.0 # em milissegundos
        
        # --- POSICIONAMENTO TÁTICO ---
        # Ordenamos a equipa: Peças mais caras/Tanques primeiro (vão para a linha da frente)
        equipa_escolhida = sorted(equipa_escolhida, key=lambda x: x["cost"], reverse=True)
        
        # Determinar as linhas de draft consoante a fação
        if equipa == 'brancas':
            linhas = [6, 7] # Linha 6 é a Frente, 7 é a Retaguarda
        else:
            linhas = [1, 0] # Linha 1 é a Frente, 0 é a Retaguarda
            
        posicoes = []
        idx = 0
        for r in linhas:
            for c in range(8):
                if idx < len(equipa_escolhida):
                    posicoes.append({
                        "r": r, "c": c,
                        "piece_class": equipa_escolhida[idx]["class"]
                    })
                    idx += 1
                    
        return {
            "pontos_gastos": pontos_gastos,
            "pontos_desperdicados": orcamento - pontos_gastos,
            "tempo_ms": tempo_gasto,
            "draft": posicoes
        }

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
                            acoes.append({"type": "stun", "start": (r, c), "end": alvo, "area": info.get("aoe", [])})
                    for sp in p.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                        acoes.append({"type": "spawn", "start": (r, c), "end": (sp[0], sp[1]), "spawn_name": sp[2]})
                    if hasattr(p, 'get_valid_spells'):
                        for spell in p.get_valid_spells(r, c, gs.board, gs.tile_effects):
                            # TYPE GUARD ROBUSTO
                            if isinstance(spell, dict):
                                end_pos = spell.get("target", (r, c))
                                spell_name = spell.get("spell_type", "Unknown")
                            else:
                                end_pos = (spell[0], spell[1]) if len(spell) >= 2 else (r, c)
                                spell_name = spell[2] if len(spell) >= 3 else "Unknown"
                            
                            acoes.append({"type": "spell", "start": (r, c), "end": end_pos, "spell_name": spell_name})
        if acoes:
            return random.choice(acoes)
        return None
        
BOT_ALEATORIO = BotAleatorio()

BOT_INICIANTE = CppEngineBot(nodes=5000)
BOT_INTERMEDIO = CppEngineBot(nodes=50000) 
BOT_AVANCADO = CppEngineBot(nodes=250000)
BOT_INICIANTE.nome = "StockWar Iniciante (D2)"
BOT_INTERMEDIO.nome = "StockWar Intermédio (D4)"
BOT_AVANCADO.nome = "StockWar Avançado (D6)"

def gerar_bot_por_elo(elo):
    if elo < 800: return BOT_ALEATORIO
    if elo < 1400: return BOT_INICIANTE
    if elo < 1900: return BOT_INTERMEDIO
    return BOT_AVANCADO