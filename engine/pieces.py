import json
import logging
import os

from engine.config import LINHAS, COLUNAS

_logger = logging.getLogger(__name__)
ARQUIVO_HEROES = os.path.join(os.path.dirname(__file__), "heroes_config.json")


def carregar_heroes():
    """Carrega o catálogo de heróis e falha cedo se a configuração estiver inválida."""
    if not os.path.exists(ARQUIVO_HEROES):
        raise FileNotFoundError(f"Hero configuration not found: {ARQUIVO_HEROES}")

    try:
        with open(ARQUIVO_HEROES, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load hero configuration: {ARQUIVO_HEROES}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Hero configuration root must be a JSON object")
    return data


HERO_DEFS = carregar_heroes()


def _validate_hero_defs():
    required_keys = {"cost", "acronym"}
    for name, data in HERO_DEFS.items():
        if not isinstance(data, dict):
            raise RuntimeError(f"Hero definition for {name!r} must be an object")

        missing = required_keys - set(data)
        if missing:
            raise RuntimeError(
                f"Hero definition for {name!r} is missing required keys: {sorted(missing)}"
            )

        if not isinstance(data["cost"], int) or data["cost"] < 0:
            raise RuntimeError(f"Hero {name!r} has an invalid cost")
        if not isinstance(data["acronym"], str) or not data["acronym"]:
            raise RuntimeError(f"Hero {name!r} has an invalid acronym")

        behavior = data.get("behavior")
        if behavior is not None and not isinstance(behavior, dict):
            raise RuntimeError(f"Hero behavior for {name!r} must be an object")


_validate_hero_defs()


class Piece:
    __slots__ = (
        "team", "name", "cost", "acronym", "stun_timer", "lifespan",
        "descricao", "passiva", "draftable", "spawn_cooldown",
    )

    def __init__(self, team, name, cost, acronym):
        if team not in ("brancas", "pretas"):
            raise ValueError(f"Invalid team: {team!r}")
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
        if self.spawn_cooldown:
            d["spawn_cooldown"] = self.spawn_cooldown
        return d

    def can_act(self) -> bool:
        return self.stun_timer == 0

    def is_enemy(self, other_piece) -> bool:
        return other_piece is not None and other_piece.team != self.team

    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        return []

    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        return []

    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        return []

    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:
        return {}

    def get_valid_spawns(self, r, c, board, tile_effects=None) -> list:
        return []

    def get_valid_spells(self, r, c, board, tile_effects=None) -> list:
        return []


class BehaviorCompiler:
    @staticmethod
    def _orthogonal(max_steps=1):
        return [(-1, 0, max_steps), (1, 0, max_steps), (0, -1, max_steps), (0, 1, max_steps)]

    @staticmethod
    def _diagonal(max_steps=1):
        return [(-1, -1, max_steps), (-1, 1, max_steps), (1, -1, max_steps), (1, 1, max_steps)]

    @staticmethod
    def _adjacent(max_steps=1):
        return [
            (-1, -1, 1), (-1, 0, 1), (-1, 1, 1),
            (0, -1, 1), (0, 1, 1),
            (1, -1, 1), (1, 0, 1), (1, 1, 1),
        ]

    @staticmethod
    def _knight():
        return [
            (-2, -1, 1), (-2, 1, 1), (-1, -2, 1), (-1, 2, 1),
            (1, -2, 1), (1, 2, 1), (2, -1, 1), (2, 1, 1),
        ]

    @staticmethod
    def _normalize(vecs, min_steps=1, ghost=False):
        out = []
        for vector in vecs:
            if len(vector) < 3:
                continue
            dr, dc, max_steps = vector[:3]
            if max_steps < 1:
                continue
            current_min = int(vector[3]) if len(vector) >= 4 else int(min_steps)
            current_ghost = bool(vector[4]) if len(vector) >= 5 else bool(ghost)
            if current_min < 1 or current_min > max_steps:
                continue
            out.append((int(dr), int(dc), int(max_steps), current_min, current_ghost))
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
                "move_white": move_base_white,
                "move_black": move_base_black,
                "attack_white": attack_base_white,
                "attack_black": attack_base_black,
            }

        if not isinstance(beh, dict):
            raise RuntimeError(f"Behavior for {name!r} must be an object")

        shared_forward = bool(beh.get("forward_dir_by_team", False))

        mv = beh.get("movement") or beh.get("move")
        if mv:
            if not isinstance(mv, dict):
                raise RuntimeError(f"Movement behavior for {name!r} must be an object")
            kind = mv.get("type")
            steps = int(mv.get("max_steps", 1) or 1)
            ghost = bool(mv.get("ghost_move", False))
            forward_by_team = bool(mv.get("forward_dir_by_team", shared_forward))

            if kind == "orthogonal":
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._orthogonal(steps), 1, ghost)
                move_base_white = move_base_black = vecs
            elif kind == "diagonal":
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._diagonal(steps), 1, ghost)
                move_base_white = move_base_black = vecs
            elif kind in ("adjacent", "adj"):
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._adjacent(steps), 1, ghost)
                move_base_white = move_base_black = vecs
            elif kind == "knight":
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._knight(), 1, ghost)
                move_base_white = move_base_black = vecs
            elif kind == "ray":
                dirs = mv.get("dirs") or mv.get("deltas")
                if dirs:
                    raw = [(int(dr), int(dc), max_range) for dr, dc in dirs]
                    vecs = BehaviorCompiler._normalize(raw, int(mv.get("min_steps", 1)), ghost)
                    move_base_white = move_base_black = vecs
            elif kind == "none":
                move_base_white = move_base_black = []
            elif kind == "forward_cone":
                deltas = mv.get("deltas", [])
                black_raw = [(int(dr), int(dc), steps) for dr, dc in deltas]
                if forward_by_team:
                    white_raw = [(-int(dr), int(dc), steps) for dr, dc in deltas]
                    move_base_white = BehaviorCompiler._normalize(white_raw, 1, ghost)
                    move_base_black = BehaviorCompiler._normalize(black_raw, 1, ghost)
                else:
                    vecs = BehaviorCompiler._normalize(black_raw, 1, ghost)
                    move_base_white = move_base_black = vecs
            elif "deltas" in mv:
                raw = [(int(d[0]), int(d[1]), steps) for d in mv.get("deltas", []) if len(d) >= 2]
                vecs = BehaviorCompiler._normalize(raw, 1, ghost)
                move_base_white = move_base_black = vecs
            else:
                raise RuntimeError(f"Unknown movement type {kind!r} for hero {name!r}")

        atk = beh.get("attack")
        attack_is_none = False
        if atk:
            if not isinstance(atk, dict):
                raise RuntimeError(f"Attack behavior for {name!r} must be an object")
            kind = atk.get("type")
            steps = int(atk.get("max_steps", 1) or 1)
            min_steps = int(atk.get("min_steps", 1) or 1)
            if kind == "none":
                attack_is_none = True
            elif kind == "orthogonal":
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._orthogonal(steps), min_steps)
                attack_base_white = attack_base_black = vecs
            elif kind == "diagonal":
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._diagonal(steps), min_steps)
                attack_base_white = attack_base_black = vecs
            elif kind == "knight":
                vecs = BehaviorCompiler._normalize(BehaviorCompiler._knight(), min_steps)
                attack_base_white = attack_base_black = vecs
            elif kind == "ray":
                dirs = atk.get("dirs") or atk.get("deltas")
                if dirs:
                    raw = [(int(dr), int(dc), max_range) for dr, dc in dirs]
                    vecs = BehaviorCompiler._normalize(raw, min_steps)
                    attack_base_white = attack_base_black = vecs
            elif kind == "forward_cone":
                deltas = atk.get("deltas", [])
                black_raw = [(int(dr), int(dc), steps) for dr, dc in deltas]
                forward_by_team = bool(atk.get("forward_dir_by_team", shared_forward))
                if forward_by_team:
                    white_raw = [(-int(dr), int(dc), steps) for dr, dc in deltas]
                    attack_base_white = BehaviorCompiler._normalize(white_raw, min_steps)
                    attack_base_black = BehaviorCompiler._normalize(black_raw, min_steps)
                else:
                    vecs = BehaviorCompiler._normalize(black_raw, min_steps)
                    attack_base_white = attack_base_black = vecs
            elif kind == "pattern":
                deltas = atk.get("deltas", [])
                raw = [(int(d[0]), int(d[1]), int(atk.get("max_steps", 1) or 1)) for d in deltas if len(d) >= 2]
                vecs = BehaviorCompiler._normalize(raw, min_steps)
                attack_base_white = attack_base_black = vecs
            elif "deltas" in atk:
                raw = [(int(d[0]), int(d[1]), steps) for d in atk.get("deltas", []) if len(d) >= 2]
                vecs = BehaviorCompiler._normalize(raw, min_steps)
                attack_base_white = attack_base_black = vecs
            else:
                raise RuntimeError(f"Unknown attack type {kind!r} for hero {name!r}")

        if not attack_base_white and move_base_white and not attack_is_none:
            attack_base_white = list(move_base_white)
            attack_base_black = list(move_base_black)

        return {
            "move_white": move_base_white,
            "move_black": move_base_black,
            "attack_white": attack_base_white,
            "attack_black": attack_base_black,
        }


class DataPiece(Piece):
    __slots__ = ("_move_vectors", "_attack_vectors")

    def __init__(self, team, name):
        if name not in HERO_DEFS:
            raise KeyError(f"Unknown hero: {name}")
        data = HERO_DEFS[name]
        super().__init__(team, name, data["cost"], data["acronym"])

        self.descricao = data.get("descricao", "Unidade misteriosa.")
        self.passiva = data.get("passiva", "Sem passiva.")
        self.draftable = bool(data.get("draftable", True))
        self.lifespan = data.get("lifespan")
        self.spawn_cooldown = int(data.get("spawn_cooldown", 0) or 0)

        compiled = BehaviorCompiler.compile(name, data.get("behavior", {}))
        if team == "brancas":
            self._move_vectors = compiled["move_white"]
            self._attack_vectors = compiled["attack_white"]
        else:
            self._move_vectors = compiled["move_black"]
            self._attack_vectors = compiled["attack_black"]

    def get_valid_moves(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act():
            return []
        moves = []
        for dr, dc, max_steps, _min_steps, ghost in self._move_vectors:
            for step in range(1, max_steps + 1):
                nr = r + dr * step
                nc = c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":
                    break
                if board[nr][nc] is None:
                    moves.append((nr, nc))
                elif not ghost:
                    break
        return moves

    def get_valid_attacks(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act():
            return []
        attacks = []
        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:
            for step in range(1, max_steps + 1):
                nr = r + dr * step
                nc = c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":
                    break
                target = board[nr][nc]
                if target is None:
                    continue
                if target.team != self.team and step >= min_steps:
                    attacks.append((nr, nc))
                break
        return attacks

    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act():
            return []
        threats = []
        for dr, dc, max_steps, min_steps, _ghost in self._attack_vectors:
            for step in range(1, max_steps + 1):
                nr = r + dr * step
                nc = c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":
                    break
                if step >= min_steps:
                    threats.append((nr, nc))
                if board[nr][nc] is not None:
                    break
        return threats


class Bone(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Bone")


class Ghoul(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Ghoul")


class Obelisk(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Obelisk")


class BoneLord(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "BoneLord")


class Ranger(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Ranger")


class Nightshade(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Nightshade")


class Templar(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Templar")


class StoneWall(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "StoneWall")


class Inquisitor(DataPiece):
    __slots__ = ()

    def __init__(self, team): super().__init__(team, "Inquisitor")

    def get_aura_positions(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        radius = int(HERO_DEFS["Inquisitor"].get("aura_radius", 2))
        aoe = []
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < LINHAS and 0 <= nc < COLUNAS:
                    if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":
                        continue
                    p = board[nr][nc]
                    if p and p.team != self.team:
                        aoe.append((nr, nc))
        return aoe

    def get_valid_spells(self, r, c, board, tile_effects=None):
        return self.get_aura_positions(r, c, board, tile_effects)

    def get_threat_area(self, r, c, board, tile_effects=None) -> list:
        threats = super().get_threat_area(r, c, board, tile_effects)
        for pos in self.get_aura_positions(r, c, board, tile_effects):
            if pos not in threats:
                threats.append(pos)
        return threats


class Berserker(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Berserker")


class Pyromancer(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Pyromancer")

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        targets = []
        for dr in range(-3, 4):
            for dc in range(-3, 4):
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

    def __init__(self, team): super().__init__(team, "Dragoon")

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        max_jump = int(HERO_DEFS["Dragoon"].get("jump_max", 2))
        lands = []
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in dirs:
            midr, midc = r + dr, c + dc
            landr, landc = r + dr * 2, c + dc * 2
            if 0 <= midr < LINHAS and 0 <= midc < COLUNAS and 0 <= landr < LINHAS and 0 <= landc < COLUNAS:
                if board[midr][midc] is not None:
                    dest = board[landr][landc]
                    if dest is None or dest.team != self.team:
                        lands.append((landr, landc))
            for step in range(2, max_jump + 1):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    break
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":
                    break
                dest = board[nr][nc]
                if dest is None:
                    lands.append((nr, nc))
                else:
                    if dest.team != self.team:
                        lands.append((nr, nc))
                    break
        return list(dict.fromkeys(lands))


class Cleric(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Cleric")

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        targets = []
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    continue
                target = board[nr][nc]
                if target and target.team == self.team and target.stun_timer > 0:
                    targets.append({"target": (nr, nc), "spell_type": "purify"})
        return targets


class Trickster(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Trickster")

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        swaps = []
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not (0 <= nr < LINHAS and 0 <= nc < COLUNAS):
                    continue
                target = board[nr][nc]
                if target and target.team == self.team:
                    swaps.append({"target": (nr, nc), "spell_type": "swap"})
        return swaps


class Geomancer(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Geomancer")

    def get_valid_spells(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        walls = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < LINHAS and 0 <= nc < COLUNAS and board[nr][nc] is None:
                walls.append({"target": (nr, nc), "spell_type": "barricade"})
        return walls


class FrostMage(DataPiece):
    __slots__ = ()

    def __init__(self, team):
        super().__init__(team, "FrostMage")

    def get_valid_stuns(self, r, c, board, tile_effects=None) -> dict:
        if not self.can_act():
            return {}
        stuns = {}
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) > 3:
                    continue
                focus_r, focus_c = r + dr, c + dc
                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):
                    continue
                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":
                    continue
                aoe = []
                has_enemy = False
                for adr, adc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ar, ac = focus_r + adr, focus_c + adc
                    if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):
                        continue
                    if tile_effects and tile_effects[ar][ac] and tile_effects[ar][ac].get("type") == "ice":
                        continue
                    aoe.append((ar, ac))
                    target = board[ar][ac]
                    if target and target.team != self.team:
                        has_enemy = True
                stuns[(focus_r, focus_c)] = {"aoe": aoe, "has_enemy": has_enemy}
        return stuns


class Lich(DataPiece):
    __slots__ = ()

    def __init__(self, team):
        super().__init__(team, "Lich")

    def get_valid_spawns(self, r, c, board, tile_effects=None) -> list:
        if not self.can_act() or self.spawn_cooldown > 0:
            return []
        spawns = []
        direction = -1 if self.team == "brancas" else 1
        for dc in (-1, 0, 1):
            nr, nc = r + direction, c + dc
            if 0 <= nr < LINHAS and 0 <= nc < COLUNAS:
                if tile_effects and tile_effects[nr][nc] and tile_effects[nr][nc].get("type") == "ice":
                    continue
                if board[nr][nc] is None:
                    spawns.append((nr, nc, "Ghoul"))
        return spawns


class Phantom(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Phantom")


class Sentry(DataPiece):
    __slots__ = ()
    def __init__(self, team): super().__init__(team, "Sentry")


TODAS_AS_PECAS = [
    Bone, Ghoul, Obelisk, BoneLord,
    Phantom, Sentry,
    FrostMage, Lich,
    Ranger, Nightshade, Templar, StoneWall, Inquisitor, Berserker,
    Pyromancer, Dragoon, Cleric, Trickster, Geomancer,
]


def obter_catalogo_pecas():
    catalogo = []
    for piece_class in TODAS_AS_PECAS:
        inst = piece_class("brancas")
        if getattr(inst, "draftable", True):
            catalogo.append({
                "name": inst.name,
                "cost": inst.cost,
                "class": piece_class,
                "desc": inst.descricao,
                "passiva": inst.passiva,
            })
    catalogo.sort(key=lambda item: item["cost"], reverse=True)
    return catalogo


def criar_peca_por_nome(nome, team):
    for cls in TODAS_AS_PECAS:
        if cls.__name__ == nome:
            return cls(team)
    raise KeyError(f"Unknown piece class: {nome}")
