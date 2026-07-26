class Piece:
    def __init__(self, team, name, cost, acronym, path_type="physical"):
        self.team = team
        self.name = name
        self.cost = cost
        self.acronym = acronym
        self.path_type = path_type
        self.stun_timer = 0  # Turnos impossibilitado de agir

    def can_act(self):
        return self.stun_timer == 0

    def get_valid_moves(self, r, c, board):
        return []

    def get_valid_attacks(self, r, c, board):
        return []

    def is_enemy(self, other_piece):
        if other_piece is None:
            return False
        return self.team != other_piece.team

class Bone(Piece):
    def __init__(self, team):
        super().__init__(team, "Bone", cost=10, acronym="B", path_type="physical")

    def get_valid_moves(self, r, c, board):
        if not self.can_act(): return []
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None:
                    moves.append((nr, nc))
        return moves
        
    def get_valid_attacks(self, r, c, board):
        if not self.can_act(): return []
        attacks = []
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.is_enemy(board[nr][nc]):
                attacks.append((nr, nc))
        return attacks

class Sentry(Piece):
    def __init__(self, team):
        super().__init__(team, "Sentry", cost=50, acronym="Se", path_type="physical")

    def get_valid_moves(self, r, c, board):
        if not self.can_act(): return []
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            for step in range(1, 4):
                nr, nc = r + (dr * step), c + (dc * step)
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] is None:
                        moves.append((nr, nc))
                    else:
                        break # Bate noutra peça (físico)
        return moves

    def get_valid_attacks(self, r, c, board):
        if not self.can_act(): return []
        attacks = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            for step in range(1, 4):
                nr, nc = r + (dr * step), c + (dc * step)
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target is not None:
                        if self.is_enemy(target):
                            attacks.append((nr, nc))
                        break # A linha de visão é bloqueada após a primeira peça
        return attacks

# (Mantém o Ghoul, Obelisk e BoneLord como estavam no passo anterior, adicionando apenas o `if not self.can_act(): return []` no topo das funções de movimento/ataque se quiseres testá-los já).