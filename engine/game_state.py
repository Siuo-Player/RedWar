from engine.pieces import Bone, Sentry # Importa as outras que usares

class GameState:
    def __init__(self):
        # Tabuleiro inicializado apenas com algumas peças para o teste base
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.board[0][0] = Sentry('pretas')
        self.board[1][0] = Bone('pretas')
        self.board[7][7] = Bone('brancas')
        
        self.white_to_move = True
        self.move_log = []
        self.active_combo_piece = None # Para gerir a passiva do Sentry
        self.game_over = False

    def make_action(self, start_pos, end_pos, action_type="move"):
        """action_type pode ser 'move' ou 'attack'"""
        if self.game_over: return

        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        target_piece = self.board[end_row][end_col]

        # Executar a ação
        if action_type == "move":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
        elif action_type == "attack":
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece # Move-se para a casa do inimigo após matar (hit-kill)

        # Registar na log (crítico para a IA depois fazer Undo)
        self.move_log.append({
            'start': start_pos,
            'end': end_pos,
            'piece': piece,
            'captured': target_piece if action_type == "attack" else None,
            'type': action_type
        })

        # Passiva do Sentry: se for um ataque, ganha +1 turno com esta peça
        if action_type == "attack" and piece.name == "Sentry":
            self.active_combo_piece = (end_row, end_col) # Bloqueia o turno para só esta peça jogar
        else:
            self.end_turn()

    def end_turn(self):
        self.active_combo_piece = None
        self.white_to_move = not self.white_to_move
        
        # Reduzir timers de atordoamento e efeitos globais
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p.stun_timer > 0:
                    p.stun_timer -= 1
        
        self.check_game_over()

    def check_game_over(self):
        # Condição de vitória provisória: não há mais peças de uma das equipas
        brancas_vivas = sum(1 for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'brancas')
        pretas_vivas = sum(1 for r in range(8) for c in range(8) if self.board[r][c] and self.board[r][c].team == 'pretas')
        
        if brancas_vivas == 0 or pretas_vivas == 0:
            self.game_over = True