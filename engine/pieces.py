import os
import json
import logging
from engine.config import LINHAS, COLUNAS

_logger = logging.getLogger(__name__)

# Load hero metadata (single source of truth)
ARQUIVO_HEROES = os.path.join(os.path.dirname(__file__), 'heroes_config.json')
def carregar_heroes():
    if not os.path.exists(ARQUIVO_HEROES):
        with open(ARQUIVO_HEROES, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
        return {}
    try:
        with open(ARQUIVO_HEROES, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

HERO_DEFS = carregar_heroes()

def _validate_hero_defs():
    required_keys = {'cost', 'acronym'}
    for name, data in HERO_DEFS.items():
        missing = required_keys - set(data.keys())
        if missing:
            _logger.warning("Hero definition for %s missing keys: %s", name, missing)
        beh = data.get('behavior')
        if beh and not isinstance(beh, dict):
            _logger.warning("Hero behavior for %s should be an object", name)

_validate_hero_defs()


class Piece:
    __slots__ = ('team', 'name', 'cost', 'acronym', 'stun_timer', 'lifespan',
                 'descricao', 'passiva', 'draftable', 'spawn_cooldown')

    def __init__(self, team, name, cost, acronym):
        self.team = team
        self.name = name
        self.cost = cost
        self.acronym = acronym
        self.stun_timer = 0
        self.lifespan = None
        self.spawn_cooldown = 0
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
    def get_valid_spells(self, r, c, board, tile_effects=None) -> list: return []


# -------------------- BehaviorCompiler ---------------------------------
class BehaviorCompiler:
    @staticmethod
    def _orthogonal(max_steps=1):
        return [(-1,0,max_steps),(1,0,max_steps),(0,-1,max_steps),(0,1,max_steps)]

    @staticmethod
    def _diagonal(max_steps=1):
        return [(-1,-1,max_steps),(-1,1,max_steps),(1,-1,max_steps),(1,1,max_steps)]

    @staticmethod
    def _adjacent(max_steps=1):
        return [(-1,-1,1),(-1,0,1),(-1,1,1),(0,-1,1),(0,1,1),(1,-1,1),(1,0,1),(1,1,1)]

    @staticmethod
    def _knight():
        return [(-2,-1,1),(-2,1,1),(-1,-2,1),(-1,2,1),(1,-2,1),(1,2,1),(2,-1,1),(2,1,1)]

    @staticmethod
    def _normalize(vecs, min_steps=1, ghost=False):
        # normalize to (dr, dc, max_steps, min_steps, ghost)
        out = []
        for v in vecs:
            if len(v) == 3:
                dr,dc,max_steps = v
                out.append((dr,dc,max_steps,int(min_steps),bool(ghost)))
            elif len(v) >= 4:
                # already contains extra info
                dr,dc,max_steps = v[0],v[1],v[2]
                ms = int(v[3]) if len(v) > 3 else int(min_steps)
                gh = bool(v[4]) if len(v) > 4 else bool(ghost)
                out.append((dr,dc,max_steps,ms,gh))
        return out

    @staticmethod
    def compile(name, beh: dict):
        max_range = max(LINHAS, COLUNAS)
        move_base_white = []
        move_base_black = []
        attack_base_white = []
        attack_base_black = []

        if not beh:
            return {
                'move_white': move_base_white, 'move_black': move_base_black,
                'attack_white': attack_base_white, 'attack_black': attack_base_black
            }

        mv = beh.get('movement') or beh.get('move')
        if mv:
            t = mv.get('type')
            steps = int(mv.get('max_steps', 1)) if mv.get('max_steps') is not None else 1
            ghost = bool(mv.get('ghost_move', False))
            if t == 'orthogonal':
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._orthogonal(steps), min_steps=1, ghost=ghost)
                move_base_white = move_base_black = vecs
            elif t == 'diagonal':
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._diagonal(steps), min_steps=1, ghost=ghost)
                move_base_white = move_base_black = vecs
            elif t == 'adjacent' or t == 'adj':
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._adjacent(steps), min_steps=1, ghost=ghost)
                move_base_white = move_base_black = vecs
            elif t == 'knight':
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._knight(), min_steps=1, ghost=ghost)
                move_base_white = move_base_black = vecs
            elif t == 'ray':
                dirs = mv.get('dirs') or mv.get('deltas')
                if dirs:
                    raw = [(int(dr),int(dc), int(max_range)) for dr,dc in dirs]
                    vecs = BehaviorCompiler._normalize(raw, min_steps=mv.get('min_steps',1), ghost=ghost)
                    move_base_white = move_base_black = vecs
            elif t == 'none':
                move_base_white = move_base_black = []
            elif t == 'forward_cone':
                deltas = mv.get('deltas', [])
                black_raw = [(int(dr), int(dc), int(mv.get('max_steps',1))) for dr,dc in deltas]
                white_raw = [(-int(dr), int(dc), int(mv.get('max_steps',1))) for dr,dc in deltas]
                move_base_white = BehaviorCompiler._normalize(white_raw, min_steps=1, ghost=ghost)
                move_base_black = BehaviorCompiler._normalize(black_raw, min_steps=1, ghost=ghost)
            else:
                if 'deltas' in mv:
                    raw = [(int(d[0]), int(d[1]), int(mv.get('max_steps',1))) for d in mv.get('deltas',[])]
                    vecs = BehaviorCompiler._normalize(raw, min_steps=1, ghost=ghost)
                    move_base_white = move_base_black = vecs

        atk = beh.get('attack')
        if atk:
            t = atk.get('type')
            steps = int(atk.get('max_steps', 1)) if atk.get('max_steps') is not None else 1
            min_steps = int(atk.get('min_steps', 1))
            if t == 'orthogonal':
                raw = BehaviorCompiler._orthogonal(steps)
                vecs = BehaviorCompiler._normalize(raw, min_steps=min_steps, ghost=False)
                attack_base_white = attack_base_black = vecs
            elif t == 'diagonal':
                raw = BehaviorCompiler._diagonal(steps)
                vecs = BehaviorCompiler._normalize(raw, min_steps=min_steps, ghost=False)
                attack_base_white = attack_base_black = vecs
            elif t == 'knight':
                raw = BehaviorCompiler._knight()
                vecs = BehaviorCompiler._normalize(raw, min_steps=min_steps, ghost=False)
                attack_base_white = attack_base_black = vecs
            elif t == 'ray':
                dirs = atk.get('dirs') or atk.get('deltas')
                if dirs:
                    raw = [(int(dr),int(dc), int(max_range)) for dr,dc in dirs]
                    vecs = BehaviorCompiler._normalize(raw, min_steps=min_steps, ghost=False)
                    attack_base_white = attack_base_black = vecs
            elif t == 'pattern':
                deltas = atk.get('deltas', [])
                raw = [(int(dr), int(dc), int(atk.get('max_steps',1))) for dr,dc in deltas]
                vecs = BehaviorCompiler._normalize(raw, min_steps=min_steps, ghost=False)
                attack_base_white = attack_base_black = vecs

        if not attack_base_white and move_base_white:
            attack_base_white = move_base_white
            attack_base_black = move_base_black

        return {
            'move_white': move_base_white, 'move_black': move_base_black,
            'attack_white': attack_base_white, 'attack_black': attack_base_black
        }


# -------------------- DataPiece ---------------------------------------
class DataPiece(Piece):
    __slots__ = ('_move_vectors', '_attack_vectors')
    def __init__(self, team, name):
        data = HERO_DEFS.get(name, {})
        cost = data.get('cost', 0)
        acronym = data.get('acronym', name[:2])
        super().__init__(team, name, cost, acronym)

        self.descricao = data.get('descricao', "Unidade misteriosa.")
        self.passiva = data.get('passiva', "Sem passiva.")
        
        # --- A CORREÇÃO: LER AS MECÂNICAS ESCONDIDAS NO JSON ---
        self.draftable = data.get('draftable', True)
        self.lifespan = data.get('lifespan', None)
        self.spawn_cooldown = data.get('spawn_cooldown', 0)
        # -------------------------------------------------------

        compiled = BehaviorCompiler.compile(name, data.get('behavior', {}))
        if team == 'brancas':
            self._move_vectors = compiled.get('move_white', [])
            self._attack_vectors = compiled.get('attack_white', [])
        else:
            self._move_vectors = compiled.get('move_black', [])
            self._attack_vectors = compiled.get('attack_black', [])

    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        moves = []
        for vec in self._move_vectors:
            # support legacy (dr,dc,max_steps) or normalized (dr,dc,max_steps,min_steps,ghost)
            if len(vec) == 3:
                dr,dc,max_steps = vec
                ghost = False
            else:
                dr,dc,max_steps,_,ghost = vec
            for step in range(1, max_steps + 1):
                nr = r + dr * step
                nc = c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get('type') == 'ice':
                    break
                if board[nr][nc] is None:
                    moves.append((nr, nc))
                else:
                    if ghost:
                        # can pass through, but cannot land on occupied
                        continue
                    else:
                        break
        return moves

    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        attacks = []
        for vec in self._attack_vectors:
            if len(vec) == 3:
                dr,dc,max_steps = vec
                min_steps = 1
            else:
                dr,dc,max_steps,min_steps,_ = vec
                min_steps = int(min_steps)
            for step in range(1, max_steps + 1):
                nr = r + dr * step
                nc = c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get('type') == 'ice':
                    break
                target = board[nr][nc]
                if target is None:
                    continue
                if target.team != self.team and step >= min_steps:
                    attacks.append((nr, nc))
                    break
                else:
                    break
        return attacks

    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act(): return []
        threats = []
        for vec in self._attack_vectors:
            if len(vec) == 3:
                dr,dc,max_steps = vec
                min_steps = 1
            else:
                dr,dc,max_steps,min_steps,_ = vec
                min_steps = int(min_steps)
            for step in range(1, max_steps + 1):
                nr = r + dr * step
                nc = c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get('type') == 'ice':
                    break
                if step >= min_steps:
                    threats.append((nr, nc))
                if board[nr][nc] is not None:
                    break
        return threats


# -------------------- Concrete wrappers --------------------------------
# Pure data-driven wrappers
class Bone(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Bone')

class Ghoul(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Ghoul')

class Obelisk(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Obelisk')

class BoneLord(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'BoneLord')

class Ranger(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Ranger')

class Nightshade(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Nightshade')

class Templar(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Templar')

class StoneWall(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'StoneWall')

class Inquisitor(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Inquisitor')
    
    def get_aura_positions(self, r, c, board, tile_effects=None):
        """Return list of enemy positions within the silence aura radius."""
        if not self.can_act():
            return []
        data = HERO_DEFS.get('Inquisitor', {})
        radius = int(data.get('aura_radius', 2))
        aoe = []
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < LINHAS and 0 <= nc < COLUNAS:
                    if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get('type') == 'ice':
                        continue
                    p = board[nr][nc]
                    if p and p.team != self.team:
                        aoe.append((nr, nc))
        return aoe

    def get_valid_spells(self, r, c, board, tile_effects=None):
        """Return possible silence targets (positions) for the Inquisitor aura."""
        return self.get_aura_positions(r, c, board, tile_effects)

    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        # include normal attack threat area and aura positions as soft-threats
        threats = super().get_threat_area(r, c, board, tile_effects)
        aura = self.get_aura_positions(r, c, board, tile_effects)
        for pos in aura:
            if pos not in threats:
                threats.append(pos)
        return threats

class Berserker(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Berserker')

# Hybrid wrappers (keep space for special spell/stub methods)
class Pyromancer(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Pyromancer')

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        targets = []
        max_range = 3
        for dr in range(-max_range, max_range + 1):
            for dc in range(-max_range, max_range + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    continue
                target = board[nr][nc]
                if target is None or target.team != self.team:
                    targets.append({"target": (nr, nc), "spell_type": "ignite"})
        return targets

class Dragoon(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Dragoon')
    def get_valid_spells(self, r, c, board, tile_effects=None):
        """Return possible jump/leap landing positions for the Dragoon.

        Simple rule implemented:
         - can jump over a single obstacle in any of the 8 directions and land
           two squares away if empty or occupied by an enemy.
         - additionally can leap up to `jump_max` tiles in a straight line
           (configurable in `heroes_config.json` under Dragoon.jump_max).
        """
        if not self.can_act():
            return []
        data = HERO_DEFS.get('Dragoon', {})
        max_jump = int(data.get('jump_max', 2))
        lands = []
        dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        for dr, dc in dirs:
            # jump over single obstacle to land two away
            midr, midc = r + dr, c + dc
            landr, landc = r + dr*2, c + dc*2
            if 0 <= midr < LINHAS and 0 <= midc < COLUNAS and 0 <= landr < LINHAS and 0 <= landc < COLUNAS:
                if board[midr][midc] is not None:
                    dest = board[landr][landc]
                    if dest is None or dest.team != self.team:
                        lands.append((landr, landc))
            # straight leaps up to max_jump (can pass over empty tiles)
            for step in range(2, max_jump + 1):
                nr = r + dr * step
                nc = c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get('type') == 'ice':
                    break
                dest = board[nr][nc]
                if dest is None:
                    lands.append((nr, nc))
                else:
                    if dest.team != self.team:
                        lands.append((nr, nc))
                    break
        # deduplicate
        uniq = []
        for p in lands:
            if p not in uniq:
                uniq.append(p)
        return uniq

class Cleric(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Cleric')

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        purify_targets = []
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    continue
                target = board[nr][nc]
                if target and target.team == self.team and target.stun_timer > 0:
                    purify_targets.append({"target": (nr, nc), "spell_type": "purify"})
        return purify_targets

class Trickster(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Trickster')

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        swaps = []
        max_range = 3
        for dr in range(-max_range, max_range + 1):
            for dc in range(-max_range, max_range + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    continue
                target = board[nr][nc]
                if target and target.team == self.team and target is not board[r][c]:
                    swaps.append({"target": (nr, nc), "spell_type": "swap"})
        return swaps

class Geomancer(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Geomancer')

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        walls = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < LINHAS and 0 <= nc < COLUNAS and board[nr][nc] is None:
                walls.append({"target": (nr, nc), "spell_type": "barricade"})
        return walls

# Keep FrostMage and Lich special methods
class FrostMage(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        data = HERO_DEFS.get('FrostMage', {})
        super().__init__(team, 'FrostMage')
        self.descricao = data.get('descricao', 'Mago de controlo.')

    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:
        if not self.can_act(): return {}
        stuns = {}
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 3:
                    foco_r, foco_c = r + dr, c + dc
                    if 0 <= foco_r < LINHAS and 0 <= foco_c < COLUNAS:
                        if tile_effects and tile_effects[foco_r][foco_c] and tile_effects[foco_r][foco_c].get('type') == 'ice': continue
                        aoe = []
                        tem_inimigo = False
                        for adr, adc in [(0,0), (-1,0), (1,0), (0,-1), (0,1)]:
                            ar, ac = foco_r + adr, foco_c + adc
                            if 0 <= ar < LINHAS and 0 <= ac < COLUNAS:
                                if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get('type') == 'ice': continue
                                aoe.append((ar, ac))
                                p = board[ar][ac]
                                if p and p.team != self.team: tem_inimigo = True
                        stuns[(foco_r, foco_c)] = {"aoe": aoe, "has_enemy": tem_inimigo}
        return stuns


class Lich(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        data = HERO_DEFS.get('Lich', {})
        super().__init__(team, 'Lich')
        self.descricao = data.get('descricao', 'Invocador Sombrio.')
        self.spawn_cooldown = data.get('spawn_cooldown', 0)

    def get_valid_spawns(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act() or self.spawn_cooldown > 0: return []
        spawns = []
        dir_frente = -1 if self.team == 'brancas' else 1
        for dc in [-1, 0, 1]:
            nr, nc = r + dir_frente, c + dc
            if 0 <= nr < LINHAS and 0 <= nc < COLUNAS:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get('type') == 'ice': continue
                if board[nr][nc] is None:
                    spawns.append((nr, nc, "Ghoul"))
        return spawns


class Phantom(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Phantom')

class Sentry(DataPiece):
    __slots__ = ()
    def __init__(self, team):
        super().__init__(team, 'Sentry')


TODAS_AS_PECAS = [
    Bone, Ghoul, Obelisk, BoneLord,
    Phantom, Sentry,
    FrostMage, Lich,
    Ranger, Nightshade, Templar, StoneWall, Inquisitor, Berserker,
    Pyromancer, Dragoon, Cleric, Trickster, Geomancer
]


def obter_catalogo_pecas():
    catalogo = []
    for PecaClass in TODAS_AS_PECAS:
        try:
            inst = PecaClass('brancas')
        except Exception:
            continue
        if getattr(inst, 'draftable', True):
            catalogo.append({
                "name": inst.name, "cost": inst.cost, "class": PecaClass,
                "desc": inst.descricao, "passiva": inst.passiva
            })
    catalogo.sort(key=lambda x: x["cost"], reverse=True)
    return catalogo


def criar_peca_por_nome(nome, team):
    classe = next((cls for cls in TODAS_AS_PECAS if getattr(cls, '__name__', '') == nome), None)
    return classe(team) if classe else None
