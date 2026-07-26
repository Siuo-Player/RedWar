from typing import List, Optional
from engine.pieces import Piece, Bone, Sentry

class GameState:
    def __init__(self):
        # Agora o Python sabe que a matriz aceita Peças e None
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.board[0][0] = Sentry('pretas')
        self.board[1][0] = Bone('pretas')
        self.board[7][7] = Bone('brancas')
        
        self.white_to_move = True
        self.move_log = []
        self.active_combo_piece = None
        self.game_over = False

    def make_action(self, start_pos, end_pos, action_type="move"):
        if self.game_over: return

        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        target_piece = self.board[end_row][end_col]

        # ---------------------------------------------------------
        # NOVA REGRA: Stun num alvo já com Stun = Morte!
        # ---------------------------------------------------------
        if action_type == "stun" and target_piece:
            if target_piece.stun_timer > 0:
                self.board[end_row][end_col] = None # Hit kill!
                target_piece = None # Marcado como capturado
            else:
                target_piece.stun_timer = 2 # Fica atordoado
            # Numa ação pura de atordoamento à distância, o atacante não sai do sítio.

        elif action_type == "move":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
            
        elif action_type == "attack":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece 

        self.move_log.append({
            'start': start_pos,
            'end': end_pos,
            'piece': piece,
            'captured': target_piece if action_type in ["attack", "stun"] else None,
            'type': action_type
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
        
        if brancas_vivas == 0 or pretas_vivas == 0:
            self.game_over = True