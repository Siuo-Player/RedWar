from typing import Any

def coords_para_notacao(r, c):
    letras = "abcdefgh"
    return f"{letras[c]}{8-r}"

class GameState:
    def __init__(self, time_limit_seconds=600):
        self.board: list[list[Any]] = [[None for _ in range(8)] for _ in range(8)]
        self.tile_effects: list[list[Any]] = [[None for _ in range(8)] for _ in range(8)]
        self.white_to_move = True
        self.game_over = False
        self.winner = None
        self.turns_without_capture = 0
        self.move_log = []
        self.last_move = None
        self.white_time = time_limit_seconds
        self.black_time = time_limit_seconds
        self.state_history = {}

    def to_dict(self):
        board_dict = []
        for r in range(8):
            linha = []
            for c in range(8):
                p = self.board[r][c]
                linha.append(p.to_dict() if p else None)
            board_dict.append(linha)
            
        return {
            "white_to_move": self.white_to_move,
            "game_over": self.game_over,
            "winner": self.winner,
            "board": board_dict,
            "tile_effects": self.tile_effects
        }

    def fast_clone(self):
        novo_gs = GameState(self.white_time)
        novo_gs.white_to_move = self.white_to_move
        novo_gs.game_over = self.game_over
        novo_gs.winner = self.winner
        novo_gs.turns_without_capture = self.turns_without_capture
        novo_gs.black_time = self.black_time
        novo_gs.state_history = self.state_history.copy()
        
        for r in range(8):
            for c in range(8):
                ef = self.tile_effects[r][c]
                novo_gs.tile_effects[r][c] = ef.copy() if ef else None
                
                p = self.board[r][c]
                if p:
                    nova_peca = p.__class__(p.team)
                    nova_peca.stun_timer = p.stun_timer
                    if hasattr(p, 'spawn_cooldown'): nova_peca.spawn_cooldown = p.spawn_cooldown
                    if hasattr(p, 'lifespan'): nova_peca.lifespan = p.lifespan
                    novo_gs.board[r][c] = nova_peca
        return novo_gs

    def get_state_hash(self):
        estado = "W" if self.white_to_move else "B"
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                estado += f"{p.team[0]}{p.name[:2]}{p.stun_timer}" if p else "."
        return hash(estado)

    def update_timers(self):
        equipa_atual = 'brancas' if self.white_to_move else 'pretas'
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.team == equipa_atual:
                    if p.stun_timer > 0: p.stun_timer -= 1
                    if hasattr(p, 'spawn_cooldown') and p.spawn_cooldown > 0: p.spawn_cooldown -= 1
                    if hasattr(p, 'lifespan') and p.lifespan is not None:
                        p.lifespan -= 1
                        if p.lifespan <= 0:
                            self.board[r][c] = None

                ef = self.tile_effects[r][c]
                if ef and ef["team"] == equipa_atual:
                    ef["timer"] -= 1
                    if ef["timer"] <= 0:
                        self.tile_effects[r][c] = None

    def gerar_notacao(self, piece, start_pos, end_pos, action_type, spawn_name):
        sr, sc = start_pos
        er, ec = end_pos
        s_alg = coords_para_notacao(sr, sc)
        e_alg = coords_para_notacao(er, ec)
        
        num_turno = (len(self.move_log) // 2) + 1
        prefixo = f"{num_turno}. " if piece.team == 'brancas' else f"{num_turno}... "
        
        if action_type == "move":
            short = f"{piece.acronym} {s_alg}-{e_alg}"
            full = f"O {piece.name} moveu-se para a casa {e_alg}."
        elif action_type == "attack":
            short = f"{piece.acronym} {s_alg}x{e_alg}"
            full = f"O {piece.name} destruiu o inimigo em {e_alg}."
        elif action_type == "stun":
            short = f"{piece.acronym} * {e_alg}"
            full = f"O {piece.name} atordoou a área {e_alg}."
        elif action_type == "spawn":
            short = f"{piece.acronym} + {spawn_name[:2]} {e_alg}"
            full = f"O {piece.name} invocou um {spawn_name} em {e_alg}."
        else:
            short, full = "?", "?"
            
        self.move_log.append({"short": prefixo + short, "full": full, "team": piece.team})

    def make_action(self, start_pos, end_pos, action_type="move", affected_area=None, spawn_name=None):
        if self.game_over: return

        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        captured_something = False

        self.gerar_notacao(piece, start_pos, end_pos, action_type, spawn_name)
        self.last_move = {"start": start_pos, "end": end_pos}

        if action_type == "stun" and affected_area and piece:
            for (ar, ac) in affected_area:
                alvo = self.board[ar][ac]
                if alvo and alvo.team != piece.team:
                    if alvo.stun_timer > 0:
                        self.board[ar][ac] = None 
                        captured_something = True
                    else:
                        alvo.stun_timer = 3 

        elif action_type == "spawn" and spawn_name and piece:
            from engine.pieces import criar_peca_por_nome
            nova_peca = criar_peca_por_nome(spawn_name, piece.team)
            if nova_peca:
                self.board[end_row][end_col] = nova_peca
            piece.stun_timer = 1 
            if hasattr(piece, 'spawn_cooldown'):
                piece.spawn_cooldown = 4 

        elif action_type == "move":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
            
        elif action_type == "attack":
            captured_something = True
            if piece.name == "BoneLord":
                from engine.pieces import Bone
                self.board[end_row][end_col] = Bone(piece.team)
            else:
                self.board[start_row][start_col] = None
                self.board[end_row][end_col] = piece 

        ef_destino = self.tile_effects[end_row][end_col]
        peca_destino = self.board[end_row][end_col]
        if peca_destino and ef_destino and ef_destino["type"] == "fire":
            peca_destino.stun_timer = max(peca_destino.stun_timer, 2)

        if captured_something: self.turns_without_capture = 0
        else: self.turns_without_capture += 1

        self.white_to_move = not self.white_to_move
        self.update_timers()
        self.check_game_over()

    def check_game_over(self):
        white_alive = any(p.team == 'brancas' for row in self.board for p in row if p)
        black_alive = any(p.team == 'pretas' for row in self.board for p in row if p)
        
        if not white_alive and not black_alive:
            self.game_over, self.winner = True, "Empate por Aniquilação Mútua"
            return
        elif not white_alive:
            self.game_over, self.winner = True, "Aniquilação - Pretas Vencem"
            return
        elif not black_alive:
            self.game_over, self.winner = True, "Aniquilação - Brancas Vencem"
            return
            
        if self.turns_without_capture >= 50:
            self.game_over, self.winner = True, "Empate por Limite de Movimentos"
            return
            
        current_hash = self.get_state_hash()
        self.state_history[current_hash] = self.state_history.get(current_hash, 0) + 1
        if self.state_history[current_hash] >= 3:
            self.game_over = True
            culpado = 'Brancas' if not self.white_to_move else 'Pretas'
            vencedor = 'Pretas' if culpado == 'Brancas' else 'Brancas'
            self.winner = f"{vencedor} Vencem (Oponente forçou repetição)"
            return

        tem_jogada = False
        equipa_atual = 'brancas' if self.white_to_move else 'pretas'
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.team == equipa_atual and p.can_act():
                    if p.get_valid_moves(r, c, self.board, self.tile_effects) or p.get_valid_attacks(r, c, self.board, self.tile_effects) or p.get_valid_spawns(r, c, self.board, self.tile_effects):
                        tem_jogada = True
                    else:
                        stuns = p.get_valid_stuns(r, c, self.board, self.tile_effects)
                        if any(info["has_enemy"] for info in stuns.values()):
                            tem_jogada = True
                if tem_jogada: break
            if tem_jogada: break

        if not tem_jogada:
            self.game_over = True
            vencedor = 'Pretas' if self.white_to_move else 'Brancas'
            self.winner = f"{vencedor} Vencem (Oponente ficou sem movimentos)"