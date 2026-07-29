import random
import json
import os
from typing import Any
from engine.config import LINHAS, COLUNAS

# =====================================================================
# ZOBRIST HASHING (Pré-calculado no arranque)
# =====================================================================
ZOBRIST_TABLE = {}
TEAMS = ["brancas", "pretas"]

# Load hero names from heroes_config.json so Zobrist covers all pieces
HEROES_FILE = os.path.join(os.path.dirname(__file__), 'heroes_config.json')
try:
    with open(HEROES_FILE, 'r', encoding='utf-8') as hf:
        HERO_DEFS = json.load(hf)
        PIECES = list(HERO_DEFS.keys())
except Exception:
    PIECES = ["Bone", "Ghoul", "Obelisk", "Phantom", "Sentry", "FrostMage", "Lich", "BoneLord"]

for r in range(LINHAS):
    for c in range(COLUNAS):
        for p in PIECES:
            for t in TEAMS:
                for s in range(6):
                    ZOBRIST_TABLE[(r, c, p, t, s)] = random.getrandbits(64)
                    
ZOBRIST_WTM = random.getrandbits(64)

def coords_para_notacao(r, c):
    letras = "abcdefghijklmnopqrstuvwxyz" # Expandido para não crashar em tabuleiros gigantes
    return f"{letras[c]}{LINHAS-r}"

class GameState:
    __slots__ = ('board', 'tile_effects', 'white_to_move', 'game_over', 'winner',
                 'turns_without_capture', 'move_log', 'last_move',
                 'white_time', 'black_time', 'state_history', 'current_hash', '_hash_valid', 'current_score')

    def __init__(self, time_limit_seconds=600):
        self.board: list[list[Any]] = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.tile_effects: list[list[Any]] = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.white_to_move = True
        self.game_over = False
        self.winner: str | None = None
        self.turns_without_capture = 0
        self.move_log = []
        self.last_move = None
        self.white_time = time_limit_seconds
        self.black_time = time_limit_seconds
        self.state_history = {}
        self.current_hash = 0
        self._hash_valid = False
        self.current_score = None

    def compute_initial_hash(self):
        h = 0
        if self.white_to_move: h ^= ZOBRIST_WTM
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = self.board[r][c]
                if p: h ^= ZOBRIST_TABLE[(r, c, p.name, p.team, p.stun_timer)]
        self.current_hash = h
        self._hash_valid = True

    def get_state_hash(self):
        if not self._hash_valid:
            self.compute_initial_hash()
        return self.current_hash

    def remove_piece_hash(self, r, c):
        p = self.board[r][c]
        if p: self.current_hash ^= ZOBRIST_TABLE[(r, c, p.name, p.team, p.stun_timer)]

    def add_piece_hash(self, r, c, p):
        if p: self.current_hash ^= ZOBRIST_TABLE[(r, c, p.name, p.team, p.stun_timer)]

    def fast_clone(self):
        # Usado apenas para a UI guardar a fotografia gráfica para o histórico visual.
        # Completamente erradicado da árvore de pesquisa da IA.
        novo_gs = GameState.__new__(GameState)
        novo_gs.white_time = self.white_time
        novo_gs.black_time = self.black_time
        novo_gs.white_to_move = self.white_to_move
        novo_gs.game_over = self.game_over
        novo_gs.winner = self.winner
        novo_gs.turns_without_capture = self.turns_without_capture
        novo_gs.state_history = self.state_history.copy()
        novo_gs.last_move = self.last_move
        novo_gs.move_log = [] 
        novo_gs.current_hash = self.current_hash
        novo_gs._hash_valid = self._hash_valid
        novo_gs.board = [row[:] for row in self.board]
        novo_gs.tile_effects = [row[:] for row in self.tile_effects]
        
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = novo_gs.board[r][c]
                if p:
                    nova_peca = p.__class__(p.team)
                    nova_peca.stun_timer = p.stun_timer
                    if hasattr(p, 'spawn_cooldown'): nova_peca.spawn_cooldown = p.spawn_cooldown
                    if hasattr(p, 'lifespan'): nova_peca.lifespan = p.lifespan
                    novo_gs.board[r][c] = nova_peca
                ef = novo_gs.tile_effects[r][c]
                if ef: novo_gs.tile_effects[r][c] = ef.copy()
        # snapshots should not carry evaluator cache
        novo_gs.current_score = None
        return novo_gs

    # =====================================================================
    # MAKE / UNMAKE CORE (Alta Performance para Pesquisa da IA)
    # =====================================================================
    def make_simulation_action(self, acao):
        if not self._hash_valid: self.compute_initial_hash()
        undo = {
            "wtm": self.white_to_move,
            "twc": self.turns_without_capture,
            "go": self.game_over,
            "win": self.winner,
            "hash": self.current_hash,
            "board": [row[:] for row in self.board],
            "tiles": [[ef.copy() if ef else None for ef in row] for row in self.tile_effects],
            "history": self.state_history.copy(),
            "last_move": self.last_move,
            "pieces": []
        }
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = self.board[r][c]
                if p:
                    undo["pieces"].append((p, p.stun_timer, getattr(p, 'lifespan', None), getattr(p, 'spawn_cooldown', 0)))

        self.make_action(
            acao["start"], acao["end"], acao["type"],
            acao.get("area"), acao.get("spawn_name"), acao.get("spell_name"),
            is_simulation=True
        )
        return undo

    def unmake_simulation_action(self, undo):
        self.white_to_move = undo["wtm"]
        self.turns_without_capture = undo["twc"]
        self.game_over = undo["go"]
        self.winner = undo["win"]
        self.current_hash = undo["hash"]
        self.board = undo["board"]
        self.tile_effects = undo["tiles"]
        self.state_history = undo["history"]
        self.last_move = undo["last_move"]
        
        # Recuperamos o relógio atómico das peças alteradas no futuro simulado
        for p, stun, life, cd in undo["pieces"]:
            p.stun_timer = stun
            if life is not None: p.lifespan = life
            if cd > 0 or hasattr(p, 'spawn_cooldown'): p.spawn_cooldown = cd
        # Invalidate cached evaluator score after restoring state
        self.current_score = None

    def make_null_move(self):
        if not self._hash_valid: self.compute_initial_hash()
        undo = {
            "wtm": self.white_to_move,
            "twc": self.turns_without_capture,
            "go": self.game_over,
            "win": self.winner,
            "hash": self.current_hash,
            "board": [row[:] for row in self.board],
            "tiles": [[ef.copy() if ef else None for ef in row] for row in self.tile_effects],
            "history": self.state_history.copy(),
            "last_move": self.last_move,
            "pieces": []
        }
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = self.board[r][c]
                if p: undo["pieces"].append((p, p.stun_timer, getattr(p, 'lifespan', None), getattr(p, 'spawn_cooldown', 0)))

        self.white_to_move = not self.white_to_move
        self.current_hash ^= ZOBRIST_WTM
        self.update_timers()
        self.turns_without_capture += 1
        # Atualiza cache do avaliador após alteração de turno
        try:
            self.recompute_score()
        except Exception:
            self.current_score = None
        return undo

    def recompute_score(self):
        try:
            from ai.evaluator import avaliador_mestre
            self.current_score = avaliador_mestre(self)
        except Exception:
            self.current_score = 0

    unmake_null_move = unmake_simulation_action

    # =====================================================================
    # NÚCLEO TÁTICO
    # =====================================================================
    def make_action(self, start_pos, end_pos, action_type="move", affected_area=None, spawn_name=None, spell_name=None, is_simulation=False):
        if self.game_over: return
        if not self._hash_valid: self.compute_initial_hash()

        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        captured_something = False

        if not is_simulation:
            self.gerar_notacao(piece, start_pos, end_pos, action_type, spawn_name, spell_name)
            
        self.last_move = {"start": start_pos, "end": end_pos}

        if action_type == "stun" and affected_area and piece:
            for (ar, ac) in affected_area:
                alvo = self.board[ar][ac]
                if alvo and alvo.team != piece.team:
                    if alvo.stun_timer > 0:
                        self.remove_piece_hash(ar, ac)
                        self.board[ar][ac] = None 
                        captured_something = True
                    else:
                        self.remove_piece_hash(ar, ac)
                        alvo.stun_timer = 3 
                        self.add_piece_hash(ar, ac, alvo)
        elif action_type == "spawn" and spawn_name and piece:
            from engine.pieces import criar_peca_por_nome
            nova_peca = criar_peca_por_nome(spawn_name, piece.team)
            if nova_peca: 
                self.board[end_row][end_col] = nova_peca
                self.add_piece_hash(end_row, end_col, nova_peca)
            self.remove_piece_hash(start_row, start_col)
            piece.stun_timer = 1 
            self.add_piece_hash(start_row, start_col, piece)
            if hasattr(piece, 'spawn_cooldown'): piece.spawn_cooldown = 4 
        elif action_type == "spell" and spell_name and piece:
            if spell_name == "ignite":
                self.tile_effects[end_row][end_col] = {"type": "fire", "timer": 3, "team": piece.team}
            elif spell_name == "purify":
                alvo = self.board[end_row][end_col]
                if alvo and alvo.team == piece.team:
                    self.remove_piece_hash(end_row, end_col)
                    alvo.stun_timer = 0
                    self.add_piece_hash(end_row, end_col, alvo)
            elif spell_name == "swap":
                alvo = self.board[end_row][end_col]
                if alvo and alvo.team == piece.team and alvo is not piece:
                    self.remove_piece_hash(start_row, start_col)
                    self.remove_piece_hash(end_row, end_col)
                    self.board[start_row][start_col], self.board[end_row][end_col] = alvo, piece
                    self.add_piece_hash(start_row, start_col, self.board[start_row][start_col])
                    self.add_piece_hash(end_row, end_col, self.board[end_row][end_col])
            elif spell_name == "barricade":
                from engine.pieces import StoneWall
                barr = StoneWall(piece.team)
                self.board[end_row][end_col] = barr
                self.add_piece_hash(end_row, end_col, barr)
        elif action_type == "move":
            self.remove_piece_hash(start_row, start_col)
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
            self.add_piece_hash(end_row, end_col, piece)
        elif action_type == "attack":
            captured_something = True
            if piece.name == "BoneLord":
                from engine.pieces import Bone
                self.remove_piece_hash(start_row, start_col)
                self.remove_piece_hash(end_row, end_col)
                novo_osso = Bone(piece.team)
                self.board[end_row][end_col] = novo_osso
                self.add_piece_hash(end_row, end_col, novo_osso)
                self.add_piece_hash(start_row, start_col, piece)
            else:
                self.remove_piece_hash(start_row, start_col)
                self.remove_piece_hash(end_row, end_col)
                self.board[start_row][start_col] = None
                self.board[end_row][end_col] = piece 
                self.add_piece_hash(end_row, end_col, piece)

        ef_destino = self.tile_effects[end_row][end_col]
        peca_destino = self.board[end_row][end_col]
        if peca_destino and ef_destino and ef_destino["type"] == "fire":
            if peca_destino.stun_timer < 2:
                self.remove_piece_hash(end_row, end_col)
                peca_destino.stun_timer = 2
                self.add_piece_hash(end_row, end_col, peca_destino)

        if captured_something: self.turns_without_capture = 0
        else: self.turns_without_capture += 1

        self.white_to_move = not self.white_to_move
        self.current_hash ^= ZOBRIST_WTM
        
        self.update_timers()
        self.check_game_over()
        # Se não for simulação, atualiza cache do avaliador para refletir novo estado
        if not is_simulation:
            try:
                self.recompute_score()
            except Exception:
                self.current_score = None

    def update_timers(self):
        equipa_atual = 'brancas' if self.white_to_move else 'pretas'
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = self.board[r][c]
                if p and p.team == equipa_atual:
                    if p.stun_timer > 0: 
                        self.remove_piece_hash(r, c)
                        p.stun_timer -= 1
                        self.add_piece_hash(r, c, p)
                        
                    if hasattr(p, 'spawn_cooldown') and p.spawn_cooldown > 0: 
                        p.spawn_cooldown -= 1
                        
                    if hasattr(p, 'lifespan') and p.lifespan is not None:
                        p.lifespan -= 1
                        if p.lifespan <= 0:
                            self.remove_piece_hash(r, c)
                            self.board[r][c] = None

                ef = self.tile_effects[r][c]
                if ef and ef["team"] == equipa_atual:
                    ef["timer"] -= 1
                    if ef["timer"] <= 0:
                        self.tile_effects[r][c] = None

    def gerar_notacao(self, piece, start_pos, end_pos, action_type, spawn_name=None, spell_name=None, affected_area=None):
        sr, sc = start_pos
        er, ec = end_pos
        s_alg = coords_para_notacao(sr, sc)
        e_alg = coords_para_notacao(er, ec)
        
        num_turno = (len(self.move_log) // 2) + 1
        prefixo = f"{num_turno}. " if piece.team == 'brancas' else f"{num_turno}... "
        
        if action_type == "move": short = f"{piece.acronym} {s_alg}-{e_alg}"
        elif action_type == "attack": short = f"{piece.acronym} {s_alg}x{e_alg}"
        elif action_type == "stun": short = f"{piece.acronym} * {e_alg}"
        elif action_type == "spawn": short = f"{piece.acronym} + {spawn_name[:2]} {e_alg}"
        elif action_type == "spell" and spell_name:
            short = f"{piece.acronym} {spell_name.upper()} {e_alg}"
        else: short = "?"
            
        estado_congelado = self.fast_clone()
        
        self.move_log.append({
            "short": prefixo + short,
            "team": piece.team,
            "estado_anterior": estado_congelado,
            "acao_escolhida": {
                "start": start_pos,
                "end": end_pos,
                "type": action_type,
                "spell_name": spell_name,
                "spawn_name": spawn_name,
                "area": affected_area
            }
        })

    def check_game_over(self):
        white_alive = any(p.team == 'brancas' for row in self.board for p in row if p)
        black_alive = any(p.team == 'pretas' for row in self.board for p in row if p)
        
        if not white_alive and not black_alive: 
            self.game_over, self.winner = True, "Empate (Aniquilação Mútua)"
        elif not white_alive: 
            self.game_over, self.winner = True, "Aniquilação - Pretas Vencem"
        elif not black_alive: 
            self.game_over, self.winner = True, "Aniquilação - Brancas Vencem"
            
        if self.game_over: return

        adversario_vencedor = 'Brancas' if self.white_to_move else 'Pretas'
            
        if self.turns_without_capture >= 50: 
            self.game_over = True
            self.winner = f"{adversario_vencedor} Vencem (Oponente esgotou limite tático)"
            return
            
        current_hash = self.get_state_hash()
        self.state_history[current_hash] = self.state_history.get(current_hash, 0) + 1
        if self.state_history[current_hash] >= 3:
            self.game_over = True
            self.winner = f"{adversario_vencedor} Vencem (Oponente forçou repetição)"
            return

        tem_jogada = False
        equipa_atual = 'brancas' if self.white_to_move else 'pretas'
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = self.board[r][c]
                if p and p.team == equipa_atual and p.can_act():
                    if p.get_valid_moves(r, c, self.board, self.tile_effects) or p.get_valid_attacks(r, c, self.board, self.tile_effects) or p.get_valid_spawns(r, c, self.board, self.tile_effects):
                        tem_jogada = True
                    else:
                        stuns = p.get_valid_stuns(r, c, self.board, self.tile_effects)
                        if any(info["has_enemy"] for info in stuns.values()): tem_jogada = True
                if tem_jogada: break
            if tem_jogada: break

        if not tem_jogada:
            self.game_over = True
            self.winner = f"{adversario_vencedor} Vencem (Oponente ficou sem movimentos)"