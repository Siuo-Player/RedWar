# engine/game_state.py
from typing import Any

class GameState:
    def __init__(self, time_limit_seconds=600):
        # Type hint para o Pylance não chorar ao adicionarmos peças
        self.board: list[list[Any]] = [[None for _ in range(8)] for _ in range(8)]
        self.white_to_move = True
        self.game_over = False
        self.winner = None
        self.turns_without_capture = 0
        
        self.white_time = time_limit_seconds
        self.black_time = time_limit_seconds

    def to_dict(self):
        """Serializa o estado para JSON (Multiplayer/Web)"""
        board_state = []
        for r in range(8):
            row = []
            for c in range(8):
                p = self.board[r][c]
                row.append(p.to_dict() if p else None)
            board_state.append(row)
            
        return {
            "white_to_move": self.white_to_move,
            "game_over": self.game_over,
            "winner": self.winner,
            "turns_without_capture": self.turns_without_capture,
            "white_time": self.white_time,
            "black_time": self.black_time,
            "board": board_state
        }

    def make_action(self, start_pos, end_pos, action_type="move", affected_area=None, spawn_name=None):
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

        elif action_type == "spawn" and spawn_name and piece:
            from engine.pieces import obter_catalogo_pecas
            catalogo = obter_catalogo_pecas()
            classe_alvo = next((p["class"] for p in catalogo if p["name"] == spawn_name), None)
            if classe_alvo:
                self.board[end_row][end_col] = classe_alvo(piece.team)
                piece.stun_timer = 1 

        elif action_type == "move":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
            
        elif action_type == "attack":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece 
            captured_something = True

        # Promoção do Bone
        if piece and piece.name == "Bone" and action_type in ["move", "attack"]:
            ultima_linha = 0 if piece.team == 'brancas' else 7
            if end_row == ultima_linha:
                from engine.pieces import BoneLord
                self.board[end_row][end_col] = BoneLord(piece.team)

        if captured_something:
            self.turns_without_capture = 0
        else:
            self.turns_without_capture += 1

        self.white_to_move = not self.white_to_move
        self.update_stun_timers()
        self.check_game_over()

    def update_stun_timers(self):
        equipa_atual = 'brancas' if self.white_to_move else 'pretas'
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.team == equipa_atual and p.stun_timer > 0:
                    p.stun_timer -= 1

    def check_game_over(self):
        white_alive = False
        black_alive = False
        
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p:
                    if p.team == 'brancas': white_alive = True
                    else: black_alive = True

        if not white_alive and not black_alive:
            self.game_over = True
            self.winner = "Empate por Aniquilação Mútua"
        elif not white_alive:
            self.game_over = True
            self.winner = "Aniquilação - Pretas Vencem"
        elif not black_alive:
            self.game_over = True
            self.winner = "Aniquilação - Brancas Vencem"
        elif self.turns_without_capture >= 50:
            self.game_over = True
            self.winner = "Empate por Limite de Movimentos"