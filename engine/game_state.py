from typing import List, Optional
from engine.pieces import Piece, Bone, Sentry, FrostMage

class GameState:
    def __init__(self):
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        
        # Peças de Teste
        self.board[0][0] = Sentry('pretas')
        self.board[1][0] = Bone('pretas')
        self.board[1][1] = Bone('pretas')
        self.board[1][2] = Bone('pretas') 
        
        self.board[7][7] = Bone('brancas')
        self.board[7][3] = FrostMage('brancas') 
        
        self.white_to_move = True
        self.move_log = []
        self.active_combo_piece = None
        
        self.game_over = False
        self.winner = None
        self.turns_without_capture = 0 # Regra dos 50 movimentos

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
                if alvo:
                    if alvo.stun_timer > 0:
                        self.board[ar][ac] = None # Hit kill!
                        captured_something = True
                    else:
                        # Timer de 3 garante que o Stun dura até ao próximo turno do atacante
                        alvo.stun_timer = 3 

        elif action_type == "move":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
            
        elif action_type == "attack":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece 
            captured_something = True

        # Gestão do limite de 50 turnos
        if captured_something:
            self.turns_without_capture = 0
        else:
            self.turns_without_capture += 1

        self.move_log.append({
            'start': start_pos,
            'end': end_pos,
            'piece': piece,
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
        # 1. Condição de Aniquilação
        brancas_vivas = sum(1 for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'brancas')
        pretas_vivas = sum(1 for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'pretas')
        
        if brancas_vivas == 0:
            self.game_over = True
            self.winner = "Pretas Vencem por Aniquilação"
        elif pretas_vivas == 0:
            self.game_over = True
            self.winner = "Brancas Vencem por Aniquilação"

        # 2. Condição de Limite de Turnos (Prevenir Jogos Infinitos para a IA)
        elif self.turns_without_capture >= 50:
            self.game_over = True
            # Calcular o valor material total para decidir desempate
            pontos_brancas = sum(self.board[r][c].cost for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'brancas')
            pontos_pretas = sum(self.board[r][c].cost for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'pretas')
            
            if pontos_brancas > pontos_pretas:
                self.winner = "Limite 50 - Brancas Vencem por Pontos"
            elif pontos_pretas > pontos_brancas:
                self.winner = "Limite 50 - Pretas Vencem por Pontos"
            else:
                self.winner = "Limite 50 - Empate Absoluto"