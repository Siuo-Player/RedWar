class Piece:
    def __init__(self, team, name, cost, acronym, path_type="physical"):
        self.team = team
        self.name = name
        self.cost = cost
        self.acronym = acronym
        self.path_type = path_type
        self.stun_timer = 0

    def can_act(self):
        return self.stun_timer == 0

    def get_valid_moves(self, r, c, board):
        return []

    def get_valid_attacks(self, r, c, board):
        return []

    def get_valid_stuns(self, r, c, board):
        """Retorna um dicionário: {(foco_r, foco_c): [(afetado_r, afetado_c), ...]}"""
        return {}

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
                        break
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
                        break
        return attacks

class FrostMage(Piece):
    """Mago de Gelo: Não ataca fisicamente, mas lança Stun em Área (Cruz)."""
    def __init__(self, team):
        super().__init__(team, "FrostMage", cost=60, acronym="FM", path_type="jump")

    def get_valid_moves(self, r, c, board):
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None:
                moves.append((nr, nc))
        return moves

    def get_valid_stuns(self, r, c, board):
        if not self.can_act(): return {}
        stuns = {}
        # O Mago pode mirar (focar) em qualquer casa num raio de 3
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 3:
                    foco_r, foco_c = r + dr, c + dc
                    if 0 <= foco_r < 8 and 0 <= foco_c < 8:
                        # A área afetada é o foco + as 4 casas adjacentes
                        aoe = []
                        for adr, adc in [(0,0), (-1,0), (1,0), (0,-1), (0,1)]:
                            ar, ac = foco_r + adr, foco_c + adc
                            if 0 <= ar < 8 and 0 <= ac < 8:
                                aoe.append((ar, ac))
                        stuns[(foco_r, foco_c)] = aoe
        return stuns