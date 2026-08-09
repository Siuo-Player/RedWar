import random
import json
import os
from typing import Any
from engine.config import LINHAS, COLUNAS

ZOBRIST_TABLE = {}
TEAMS = ["brancas", "pretas"]

HEROES_FILE = os.path.join(os.path.dirname(__file__), 'heroes_config.json')
try:
    with open(HEROES_FILE, 'r', encoding='utf-8') as hf:
        HERO_DEFS = json.load(hf)
        PIECES = list(HERO_DEFS.keys())
except Exception:
    PIECES = ["Bone", "Ghoul", "Obelisk", "Phantom", "Sentry", "FrostMage", "Lich", "BoneLord"]

ZOBRIST_WTM = random.getrandbits(64)

def get_piece_zobrist_key(r, c, p):
    """
    Devolve a chave Zobrist de 64 bits para esta peça nesta casa, gerando-a
    na primeira vez que esta combinação exata aparece (e reutilizando depois).
    Antes disto pré-computava-se TODAS as combinações possíveis de
    (r, c, nome, equipa, stun, lifespan, cooldown) no arranque -- cerca de
    1.5M entradas na RAM, a maioria delas nunca usada numa partida real.
    """
    lifespan = p.lifespan if getattr(p, 'lifespan', None) is not None else -1
    cd = p.spawn_cooldown if getattr(p, 'spawn_cooldown', 0) is not None else 0
    key = (r, c, p.name, p.team, p.stun_timer, lifespan, cd)
    if key not in ZOBRIST_TABLE:
        ZOBRIST_TABLE[key] = random.getrandbits(64)
    return ZOBRIST_TABLE[key]

def coords_para_notacao(r, c):
    letras = "abcdefghijklmnopqrstuvwxyz"
    return f"{letras[c]}{LINHAS-r}"

class GameState:
    __slots__ = ('board', 'tile_effects', 'white_to_move', 'game_over', 'winner',
                 'turns_without_capture', 'move_log', 'last_move',
                 'white_time', 'black_time', 'state_history', 'current_hash', '_hash_valid', 'current_score')

    # CORREÇÃO PYLANCE: Tipagem explícita para float
    def __init__(self, time_limit_seconds: float = 600.0):
        self.board: list[list[Any]] = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.tile_effects: list[list[Any]] = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.white_to_move: bool = True
        self.game_over: bool = False
        self.winner: str | None = None
        self.turns_without_capture: int = 0
        self.move_log: list = []
        self.last_move: dict | None = None
        self.white_time: float = float(time_limit_seconds)
        self.black_time: float = float(time_limit_seconds)
        self.state_history: dict = {}
        self.current_hash: int = 0
        self._hash_valid: bool = False
        self.current_score: float | int | None = None

    def compute_initial_hash(self):
        h = 0
        if self.white_to_move: h ^= ZOBRIST_WTM
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = self.board[r][c]
                if p:
                    h ^= get_piece_zobrist_key(r, c, p)
        self.current_hash = h
        self._hash_valid = True

    def _get_attack_spawn_piece(self, piece):
        if not piece:
            return None
        behavior = HERO_DEFS.get(piece.name, {}).get("behavior", {}) or {}
        for passive in behavior.get("passives", []):
            if passive.get("trigger") == "on_kill" and passive.get("effect") == "spawn_unit":
                params = passive.get("params", {})
                if params.get("spawn_location") == "target_square":
                    unit_name = params.get("unit_name")
                    if unit_name:
                        from engine.pieces import criar_peca_por_nome
                        return criar_peca_por_nome(unit_name, piece.team)
        return None

    def get_state_hash(self):
        if not self._hash_valid:
            self.compute_initial_hash()
        return self.current_hash

    def remove_piece_hash(self, r, c):
        p = self.board[r][c]
        if p:
            self.current_hash ^= get_piece_zobrist_key(r, c, p)

    def add_piece_hash(self, r, c, p):
        if p:
            self.current_hash ^= get_piece_zobrist_key(r, c, p)

    def fast_clone(self):
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
        novo_gs.current_score = None
        return novo_gs

    def execute_action(self, acao_dict):
        """DELEGAÇÃO: O GameState absorve o dicionário abstrato e resolve a física toda."""
        m_type = acao_dict.get("type", "move")
        start_pos = acao_dict["start"]
        end_pos = acao_dict["end"]
        
        area_stun = acao_dict.get("area", [])
        if m_type == "stun" and not area_stun:
            atacante = self.board[start_pos[0]][start_pos[1]]
            if atacante:
                stuns_validos = atacante.get_valid_stuns(start_pos[0], start_pos[1], self.board, self.tile_effects)
                if stuns_validos and end_pos in stuns_validos:
                    area_stun = stuns_validos[end_pos].get("aoe", [])
                    
        self.make_action(
            start_pos, end_pos, m_type, 
            affected_area=area_stun, 
            spawn_name=acao_dict.get("spawn_name"), 
            spell_name=acao_dict.get("spell_name")
        )

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
                        alvo.stun_timer = 2 
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
                for adr, adc in [(0,0), (-1,0), (1,0), (0,-1), (0,1)]:
                    fr, fc = end_row + adr, end_col + adc
                    if 0 <= fr < LINHAS and 0 <= fc < COLUNAS:
                        self.tile_effects[fr][fc] = {"type": "fire", "timer": 3, "team": piece.team}
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
            self.remove_piece_hash(end_row, end_col)
            self.remove_piece_hash(start_row, start_col)
            spawn_piece = None
            if piece:
                spawn_piece = self._get_attack_spawn_piece(piece)
            if spawn_piece:
                self.board[start_row][start_col] = piece
                self.board[end_row][end_col] = spawn_piece
                self.add_piece_hash(start_row, start_col, piece)
                self.add_piece_hash(end_row, end_col, spawn_piece)
            else:
                self.board[start_row][start_col] = None
                self.board[end_row][end_col] = piece 
                self.add_piece_hash(end_row, end_col, piece)

        ef_destino = self.tile_effects[end_row][end_col]
        peca_destino = self.board[end_row][end_col]
        if peca_destino and ef_destino and ef_destino.get("type") == "fire":
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
        if not is_simulation:
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
                if ef and ef.get("team") == equipa_atual:
                    ef["timer"] = ef.get("timer", 1) - 1
                    if ef["timer"] <= 0:
                        self.tile_effects[r][c] = None

    def gerar_notacao(self, piece, start_pos, end_pos, action_type, spawn_name=None, spell_name=None):
        if not piece: return
        sr, sc = start_pos
        er, ec = end_pos
        s_alg = coords_para_notacao(sr, sc)
        e_alg = coords_para_notacao(er, ec)
        
        num_turno = (len(self.move_log) // 2) + 1
        prefixo = f"{num_turno}. " if piece.team == 'brancas' else f"{num_turno}... "
        
        if action_type == "move": short = f"{piece.acronym} {s_alg}-{e_alg}"
        elif action_type == "attack": short = f"{piece.acronym} {s_alg}x{e_alg}"
        elif action_type == "stun": short = f"{piece.acronym} * {e_alg}"
        elif action_type == "spawn": short = f"{piece.acronym} + {spawn_name[:2] if spawn_name else ''} {e_alg}"
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
            self.winner = f"{adversario_vencedor} Vencem (Limite tático)"
            return
            
        current_hash = self.get_state_hash()
        self.state_history[current_hash] = self.state_history.get(current_hash, 0) + 1
        if self.state_history[current_hash] >= 3:
            self.game_over = True
            self.winner = f"{adversario_vencedor} Vencem (Repetição)"
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
                        if stuns and any(info and info.get("has_enemy") for info in stuns.values()): 
                            tem_jogada = True
                if tem_jogada: break
            if tem_jogada: break

        if not tem_jogada:
            self.game_over = True
            self.winner = f"{adversario_vencedor} Vencem (Oponente sem lances)"

    def to_rwen(self) -> str:
        linhas_str = []
        for r in range(LINHAS):
            casas_str = []
            for c in range(COLUNAS):
                p = self.board[r][c]
                ef = self.tile_effects[r][c]
                
                if not p: p_str = "."
                else:
                    team = "W" if p.team == 'brancas' else "B"
                    nome = p.name.replace(" ", "")
                    vida = str(p.lifespan) if hasattr(p, 'lifespan') and p.lifespan is not None else "N"
                    cd = str(p.spawn_cooldown) if hasattr(p, 'spawn_cooldown') else "0"
                    p_str = f"{team}_{nome}_{p.stun_timer}_{vida}_{cd}"
                
                if not ef: e_str = "."
                else:
                    e_team = "W" if ef.get("team") == 'brancas' else "B"
                    e_str = f"{e_team}_{ef.get('type', 'none')}_{ef.get('timer', 0)}"
                    
                casas_str.append(f"{p_str}:{e_str}")
            linhas_str.append(",".join(casas_str))
            
        return f"{'/'.join(linhas_str)} {'W' if self.white_to_move else 'B'} {self.turns_without_capture}"