# engine/pieces.py
import os
import json

ARQUIVO_CUSTOS = os.path.join(os.path.dirname(__file__), 'mobs_config.json')
CUSTOS_BASE = {
    "Bone": 10, "Ghoul": 30, "Obelisk": 40, "Phantom": 45, 
    "Sentry": 50, "FrostMage": 60, "Lich": 80, "BoneLord": 100
}

def carregar_custos():
    if not os.path.exists(ARQUIVO_CUSTOS):
        with open(ARQUIVO_CUSTOS, 'w', encoding='utf-8') as f:
            json.dump(CUSTOS_BASE, f, indent=4)
        return CUSTOS_BASE
    try:
        with open(ARQUIVO_CUSTOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return CUSTOS_BASE

CUSTOS_ATUAIS = carregar_custos()

class Piece:
    def __init__(self, team, name, cost, acronym, path_type="physical"):
        self.team = team
        self.name = name
        self.cost = cost
        self.acronym = acronym
        self.path_type = path_type
        self.stun_timer = 0
        self.descricao = "Unidade genérica."
        self.passiva = "Nenhuma."

    def to_dict(self) -> dict:
        return {"team": self.team, "name": self.name, "stun_timer": self.stun_timer}

    def can_act(self) -> bool:
        return self.stun_timer == 0

    def is_enemy(self, other_piece) -> bool:
        return other_piece is not None and other_piece.team != self.team

    # Type hints corrigem o erro 'Never is not iterable' no Pylance
    def get_valid_moves(self, r, c, board) -> list: return []
    def get_valid_attacks(self, r, c, board) -> list: return []
    def get_valid_stuns(self, r, c, board) -> dict: return {}
    def get_valid_spawns(self, r, c, board) -> list: return []

class Bone(Piece):
    def __init__(self, team):
        super().__init__(team, "Bone", CUSTOS_ATUAIS.get("Bone", 10), "Bo")
        self.descricao = "Infantaria básica e frágil."
        self.passiva = "Promove para BoneLord se atingir a última linha inimiga."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_attacks(self, r, c, board) -> list:
        if not self.can_act(): return []
        attacks = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
        return attacks

class Ghoul(Piece):
    def __init__(self, team):
        super().__init__(team, "Ghoul", CUSTOS_ATUAIS.get("Ghoul", 30), "Gh")
        self.descricao = "Vanguarda agressiva. Avança letalmente para a frente."
        self.passiva = "Movimenta-se apenas para a frente e diagonais frontais."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_attacks(self, r, c, board) -> list:
        if not self.can_act(): return []
        attacks = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
        return attacks

class Obelisk(Piece):
    def __init__(self, team):
        super().__init__(team, "Obelisk", CUSTOS_ATUAIS.get("Obelisk", 40), "Ob")
        self.descricao = "Estrutura pesada defensiva."
        self.passiva = "Exerce Controlo de Área. Muito lento."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None: moves.append((nr, nc))
        return moves

class Phantom(Piece):
    def __init__(self, team):
        super().__init__(team, "Phantom", CUSTOS_ATUAIS.get("Phantom", 45), "Ph", path_type="jump")
        self.descricao = "Assassino espectral. Ignora defesas."
        self.passiva = "Salta peças em formato de L (como o Cavalo no Xadrez)."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_attacks(self, r, c, board) -> list:
        if not self.can_act(): return []
        attacks = []
        for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
        return attacks

class Sentry(Piece):
    def __init__(self, team):
        super().__init__(team, "Sentry", CUSTOS_ATUAIS.get("Sentry", 50), "Se")
        self.descricao = "Atirador de longo alcance (Rook)."
        self.passiva = "Movimenta-se e ataca em linhas retas ilimitadas."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] is None: moves.append((nr, nc))
                    else: break
                else: break
        return moves
    def get_valid_attacks(self, r, c, board) -> list:
        if not self.can_act(): return []
        attacks = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] is not None:
                        if self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
                        break
                else: break
        return attacks

class FrostMage(Piece):
    def __init__(self, team):
        super().__init__(team, "FrostMage", CUSTOS_ATUAIS.get("FrostMage", 60), "FM")
        self.descricao = "Mago de controlo tático."
        self.passiva = "Não ataca fisicamente. Lança um Stun em área (AoE) num raio de 3 casas."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            for i in range(1, 3):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] is None: moves.append((nr, nc))
                    else: break
                else: break
        return moves
    def get_valid_stuns(self, r, c, board) -> dict:
        if not self.can_act(): return {}
        stuns = {}
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 3:
                    foco_r, foco_c = r + dr, c + dc
                    if 0 <= foco_r < 8 and 0 <= foco_c < 8:
                        aoe = []
                        tem_inimigo = False 
                        for adr, adc in [(0,0), (-1,0), (1,0), (0,-1), (0,1)]:
                            ar, ac = foco_r + adr, foco_c + adc
                            if 0 <= ar < 8 and 0 <= ac < 8:
                                aoe.append((ar, ac))
                                p = board[ar][ac]
                                if p and p.team != self.team: tem_inimigo = True
                        if tem_inimigo: stuns[(foco_r, foco_c)] = aoe
        return stuns

class Lich(Piece):
    def __init__(self, team):
        super().__init__(team, "Lich", CUSTOS_ATUAIS.get("Lich", 80), "Li")
        self.descricao = "Invocador Sombrio."
        self.passiva = "Pode abdicar da ação para Invocar um Ghoul nas casas vazias frontais."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_spawns(self, r, c, board) -> list:
        if not self.can_act(): return []
        spawns = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None:
                spawns.append((nr, nc, "Ghoul"))
        return spawns

class BoneLord(Piece):
    def __init__(self, team):
        super().__init__(team, "BoneLord", CUSTOS_ATUAIS.get("BoneLord", 100), "BL")
        self.descricao = "Comandante Supremo do Exército."
        self.passiva = "Invoca Bones em qualquer casa adjacente vazia."
    def get_valid_moves(self, r, c, board) -> list:
        if not self.can_act(): return []
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_attacks(self, r, c, board) -> list:
        if not self.can_act(): return []
        attacks = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
        return attacks
    def get_valid_spawns(self, r, c, board) -> list:
        if not self.can_act(): return []
        spawns = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] is None:
                    spawns.append((nr, nc, "Bone"))
        return spawns

TODAS_AS_PECAS = [Bone, Ghoul, Obelisk, Phantom, Sentry, FrostMage, Lich, BoneLord]

def obter_catalogo_pecas():
    catalogo = []
    for PecaClass in TODAS_AS_PECAS:
        inst = PecaClass('brancas')
        catalogo.append({"name": inst.name, "cost": inst.cost, "class": PecaClass, "desc": inst.descricao, "passiva": inst.passiva})
    catalogo.sort(key=lambda x: x["cost"], reverse=True)
    return catalogo

def criar_peca_por_nome(nome, team):
    cat = obter_catalogo_pecas()
    classe = next((p["class"] for p in cat if p["name"] == nome), None)
    return classe(team) if classe else None