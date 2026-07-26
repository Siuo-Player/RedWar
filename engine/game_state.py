from typing import List, Optional
from engine.pieces import Piece

class GameState:
    def __init__(self):
        # Tabuleiro vazio (Pronto para o Draft)
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        
        self.white_to_move = True
        self.move_log = []
        self.active_combo_piece = None
        
        self.game_over = False
        self.winner = None
        self.turns_without_capture = 0

    def make_action(self, start_pos, end_pos, action_type="move", affected_area=None):
        if self.game_over: return

        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        target_piece = self.board[end_row][end_col]
        
        captured_something = False

        if action_type == "stun" and affected_area:
            for (ar, ac) in affected_area:
                alvo = self.board[ar][ac]
                # Friendly Fire Desativado: Só afeta se for inimigo
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
        brancas_vivas = sum(1 for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'brancas')
        pretas_vivas = sum(1 for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'pretas')
        
        if brancas_vivas == 0:
            self.game_over = True
            self.winner = "Pretas Vencem"
        elif pretas_vivas == 0:
            self.game_over = True
            self.winner = "Brancas Vencem"
        elif self.turns_without_capture >= 50:
            self.game_over = True
            pontos_brancas = sum(self.board[r][c].cost for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'brancas')
            pontos_pretas = sum(self.board[r][c].cost for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'pretas')
            if pontos_brancas > pontos_pretas:
                self.winner = "Limite 50 - Brancas Vencem"
            elif pontos_pretas > pontos_brancas:
                self.winner = "Limite 50 - Pretas Vencem"
            else:
                self.winner = "Empate"