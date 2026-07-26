from engine.pieces import Piece

class GameState:
    def __init__(self):
        # Tabuleiro 8x8 vazio. Vamos representá-lo como uma matriz 2D.
        # Numa casa vazia teremos None, caso contrário teremos um objeto da classe Piece.
        self.board = [
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None]
        ]
        
        self.white_to_move = True  # Define de quem é o turno
        self.move_log = []         # Regista o histórico de jogadas para permitir "Undo" e para o treino da IA
        
        # Aqui ficarão os timers globais (ex: paredes de gelo no mapa)
        self.active_effects = []

    def make_move(self, start_pos, end_pos):
        """
        Executa um movimento básico. 
        start_pos e end_pos são tuplos (linha, coluna).
        """
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        
        piece_moved = self.board[start_row][start_col]
        piece_captured = self.board[end_row][end_col] # Será None se a casa estiver vazia
        
        # 1. Mover a peça (isto assume que o movimento já foi validado antes de chamar esta função)
        self.board[start_row][start_col] = None
        self.board[end_row][end_col] = piece_moved
        
        # 2. Registar a jogada (essencial para a IA desfazer jogadas na árvore de decisão)
        self.move_log.append({
            'start': start_pos,
            'end': end_pos,
            'piece_moved': piece_moved,
            'piece_captured': piece_captured
        })
        
        # 3. Trocar o turno
        self.white_to_move = not self.white_to_move
