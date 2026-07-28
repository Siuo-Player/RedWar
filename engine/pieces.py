import os
import json

ARQUIVO_CUSTOS = os.path.join(os.path.dirname(__file__), 'mobs_config.json')
CUSTOS_BASE = {
    "Bone": 10, "Ghoul": 30, "Obelisk": 40, "Phantom": 45, 
    "Sentry": 90, "FrostMage": 60, "Lich": 80, "BoneLord": 100
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
    def __init__(self, team, name, cost, acronym):
        self.team = team
        self.name = name
        self.cost = cost
        self.acronym = acronym
        self.stun_timer = 0
        self.lifespan = None
        self.descricao = "Unidade genérica."
        self.passiva = "Nenhuma."
        self.draftable = True

    def to_dict(self) -> dict:
        d = {"team": self.team, "name": self.name, "stun_timer": self.stun_timer}
        if self.lifespan is not None:
            d["lifespan"] = self.lifespan
        return d

    def can_act(self) -> bool:
        return self.stun_timer == 0

    def is_enemy(self, other_piece) -> bool:
        return other_piece is not None and other_piece.team != self.team

    def get_valid_moves(self, r, c, board, tile_effects=None) -> list: return []
    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list: return []
    def get_threat_area(self, r, c, board, tile_effects=None) -> list: return []
    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict: return {}
    def get_valid_spawns(self, r, c, board, tile_effects=None) -> list: return []

class Bone(Piece):
    def __init__(self, team):
        super().__init__(team, "Bone", CUSTOS_ATUAIS.get("Bone", 10), "Bo")
        self.descricao = "Infantaria invocada."
        self.passiva = "Desintegra-se após 5 turnos."
        self.draftable = False
        self.lifespan = 5 

    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if board[nr][nc] is None: moves.append((nr, nc))
        return moves

    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        attacks = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
        return attacks

    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        threats = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                threats.append((nr, nc))
        return threats

class Ghoul(Piece):
    def __init__(self, team):
        super().__init__(team, "Ghoul", CUSTOS_ATUAIS.get("Ghoul", 30), "Gh")
        self.descricao = "Vanguarda agressiva invocada."
        self.passiva = "Avança letalmente. Desintegra-se após 5 turnos."
        self.draftable = False
        self.lifespan = 5 
    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        attacks = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
        return attacks
    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        threats = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                threats.append((nr, nc))
        return threats

class Obelisk(Piece):
    def __init__(self, team):
        super().__init__(team, "Obelisk", CUSTOS_ATUAIS.get("Obelisk", 40), "Ob")
        self.descricao = "Estrutura pesada."
    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if board[nr][nc] is None: moves.append((nr, nc))
        return moves

class Phantom(Piece):
    def __init__(self, team):
        super().__init__(team, "Phantom", CUSTOS_ATUAIS.get("Phantom", 45), "Ph")
        self.descricao = "Assassino espectral."
        self.passiva = "Salta em L."
    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        attacks = []
        for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
        return attacks
    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        threats = []
        for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                threats.append((nr, nc))
        return threats

class Sentry(Piece):
    def __init__(self, team):
        super().__init__(team, "Sentry", CUSTOS_ATUAIS.get("Sentry", 50), "Se")
        self.descricao = "Atirador."
        self.passiva = "Ataque em linha reta."
    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": break
                    if board[nr][nc] is None: moves.append((nr, nc))
                    else: break
                else: break
        return moves
    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        attacks = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": break
                    if board[nr][nc] is not None:
                        if self.is_enemy(board[nr][nc]): attacks.append((nr, nc))
                        break
                else: break
        return attacks
    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        threats = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": break
                    threats.append((nr, nc))
                    if board[nr][nc] is not None: break 
                else: break
        return threats

class FrostMage(Piece):
    def __init__(self, team):
        super().__init__(team, "FrostMage", CUSTOS_ATUAIS.get("FrostMage", 60), "FM")
        self.descricao = "Mago de controlo."
    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            for i in range(1, 3):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": break
                    if board[nr][nc] is None: moves.append((nr, nc))
                    else: break
                else: break
        return moves
    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:
        if not self.can_act(): return {}
        stuns = {}
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 3:
                    foco_r, foco_c = r + dr, c + dc
                    if 0 <= foco_r < 8 and 0 <= foco_c < 8:
                        if tile_effects and tile_effects[foco_r][foco_c] and tile_effects[foco_r][foco_c]["type"] == "ice": continue
                        aoe = []
                        tem_inimigo = False 
                        for adr, adc in [(0,0), (-1,0), (1,0), (0,-1), (0,1)]:
                            ar, ac = foco_r + adr, foco_c + adc
                            if 0 <= ar < 8 and 0 <= ac < 8:
                                if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac]["type"] == "ice": continue
                                aoe.append((ar, ac))
                                p = board[ar][ac]
                                if p and p.team != self.team: tem_inimigo = True
                        
                        stuns[(foco_r, foco_c)] = {"aoe": aoe, "has_enemy": tem_inimigo}
        return stuns

class Lich(Piece):
    def __init__(self, team):
        super().__init__(team, "Lich", CUSTOS_ATUAIS.get("Lich", 80), "Li")
        self.descricao = "Invocador Sombrio."
        self.spawn_cooldown = 0
    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_spawns(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act() or self.spawn_cooldown > 0: return []
        spawns = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if board[nr][nc] is None:
                    spawns.append((nr, nc, "Ghoul"))
        return spawns

class BoneLord(Piece):
    def __init__(self, team):
        super().__init__(team, "BoneLord", CUSTOS_ATUAIS.get("BoneLord", 100), "BL")
        self.descricao = "Comandante Necromante."
    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                    if board[nr][nc] is None: moves.append((nr, nc))
        return moves
    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        attacks = []
        padroes_ataque = [
            (-3, -1), (-3, 1), (3, -1), (3, 1),  
            (-1, -3), (1, -3), (-1, 3), (1, 3),  
            (-2, -2), (-2, 2), (2, -2), (2, 2)   
        ]
        for dr, dc in padroes_ataque:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                if self.is_enemy(board[nr][nc]): 
                    attacks.append((nr, nc))
        return attacks
    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        threats = []
        padroes_ataque = [
            (-3, -1), (-3, 1), (3, -1), (3, 1),  
            (-1, -3), (1, -3), (-1, 3), (1, 3),  
            (-2, -2), (-2, 2), (2, -2), (2, 2)   
        ]
        for dr, dc in padroes_ataque:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc]["type"] == "ice": continue
                threats.append((nr, nc))
        return threats

TODAS_AS_PECAS = [Bone, Ghoul, Obelisk, Phantom, Sentry, FrostMage, Lich, BoneLord]

def obter_catalogo_pecas():
    catalogo = []
    for PecaClass in TODAS_AS_PECAS:
        inst = PecaClass('brancas')
        if getattr(inst, 'draftable', True):
            catalogo.append({
                "name": inst.name, "cost": inst.cost, "class": PecaClass, 
                "desc": inst.descricao, "passiva": inst.passiva
            })
    catalogo.sort(key=lambda x: x["cost"], reverse=True)
    return catalogo

def criar_peca_por_nome(nome, team):
    classe = next((cls for cls in TODAS_AS_PECAS if cls.__name__ == nome), None)
    return classe(team) if classe else None