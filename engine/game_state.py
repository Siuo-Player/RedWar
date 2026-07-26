from typing import List, Optional
from engine.pieces import Piece

class GameState:
    def __init__(self, time_limit_seconds=180):
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        
        self.white_to_move = True
        self.move_log = []
        self.active_combo_piece = None
        
        self.game_over = False
        self.winner = None
        self.turns_without_capture = 0
        
        # Relógios de Jogo (em segundos)
        self.white_time = float(time_limit_seconds)
        self.black_time = float(time_limit_seconds)

    def update_time(self, delta_time):
        """Reduz o tempo do jogador ativo. Chamado todos os frames."""
        if self.game_over: return
        
        if self.white_to_move:
            self.white_time -= delta_time
            if self.white_time <= 0:
                self.white_time = 0
                self.game_over = True
                self.winner = "Tempo Esgotado - Pretas Vencem"
        else:
            self.black_time -= delta_time
            if self.black_time <= 0:
                self.black_time = 0
                self.game_over = True
                self.winner = "Tempo Esgotado - Brancas Vencem"

    def make_action(self, start_pos, end_pos, action_type="move", affected_area=None):
        if self.game_over: return

        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        
        captured_something = False

        if action_type == "stun" and affected_area and piece:
            for (ar, ac) in affected_area:
                alvo = self.board[ar][ac]
                if alvo and alvo.team != piece.team:
                    if alvo.stun_timer > 0:
                        self.board[ar][ac] = None 
                        captured_something = True
                    else:
                        alvo.stun_timer = 3 

        elif action_type == "move":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
            
        elif action_type == "attack":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece 
            captured_something = True

        if captured_something:
            self.turns_without_capture = 0
        else:
            self.turns_without_capture += 1

        self.move_log.append({
            'start': start_pos, 'end': end_pos,
            'piece': piece, 'type': action_type
        })

        if action_type == "attack" and piece and piece.name == "Sentry":
            self.active_combo_piece = (end_row, end_col) 
        else:
            self.end_turn()

    def end_turn(self):
        self.active_combo_piece = None
        self.white_to_move = not self.white_to_move
        
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.stun_timer > 0:
                    p.stun_timer -= 1
        
        self.check_game_over()

    def check_game_over(self):
        # Correção Pylance: Extrair as peças válidas de forma segura
        pecas_brancas = [p for linha in self.board for p in linha if p is not None and p.team == 'brancas']
        pecas_pretas = [p for linha in self.board for p in linha if p is not None and p.team == 'pretas']
        
        if not pecas_brancas:
            self.game_over = True
            self.winner = "Aniquilação - Pretas Vencem"
        elif not pecas_pretas:
            self.game_over = True
            self.winner = "Aniquilação - Brancas Vencem"
        elif self.turns_without_capture >= 50:
            self.game_over = True
            pts_brancas = sum(p.cost for p in pecas_brancas)
            pts_pretas = sum(p.cost for p in pecas_pretas)
            if pts_brancas > pts_pretas:
                self.winner = "Limite 50 Mov. - Brancas Vencem"
            elif pts_pretas > pts_brancas:
                self.winner = "Limite 50 Mov. - Pretas Vencem"
            else:
                self.winner = "Empate por Limite de Movimentos"

            # 3. Condição de Bloqueio (Sem movimentos válidos)
        if not self.game_over:
            current_team = 'brancas' if self.white_to_move else 'pretas'
            tem_jogada = False
            
            for r in range(8):
                for c in range(8):
                    p = self.board[r][c]
                    if p and p.team == current_team and p.can_act():
                        if p.get_valid_moves(r, c, self.board) or p.get_valid_attacks(r, c, self.board) or p.get_valid_stuns(r, c, self.board):
                            tem_jogada = True
                            break
                if tem_jogada: break
                
            if not tem_jogada:
                self.game_over = True
                self.winner = f"Sem Movimentos - {'Pretas' if current_team == 'brancas' else 'Brancas'} Vencem"