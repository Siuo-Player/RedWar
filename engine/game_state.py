import hashlib
import json
import os
from typing import Any

from engine.config import COLUNAS, LINHAS

ZOBRIST_TABLE = {}
ZOBRIST_EFFECT_TABLE = {}
TEAMS = ["brancas", "pretas"]

HEROES_FILE = os.path.join(os.path.dirname(__file__), "heroes_config.json")
try:
    with open(HEROES_FILE, "r", encoding="utf-8") as hf:
        HERO_DEFS = json.load(hf)
        PIECES = list(HERO_DEFS.keys())
except (OSError, json.JSONDecodeError) as exc:
    raise RuntimeError(f"Unable to load hero configuration: {HEROES_FILE}") from exc


def _stable_u64(kind: str, *parts) -> int:
    payload = repr((kind,) + parts).encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8, person=b"RedWarZob").digest()
    return int.from_bytes(digest, "little", signed=False)


ZOBRIST_WTM = _stable_u64("side_to_move")


def _zobrist_value(table: dict, key: tuple, kind: str) -> int:
    value = table.get(key)
    if value is None:
        value = _stable_u64(kind, *key)
        table[key] = value
    return value


def get_piece_zobrist_key(r, c, p):
    if p is None:
        return 0
    lifespan = p.lifespan if getattr(p, "lifespan", None) is not None else -1
    cooldown = p.spawn_cooldown if getattr(p, "spawn_cooldown", 0) is not None else 0
    key = (r, c, p.name, p.team, p.stun_timer, lifespan, cooldown)
    return _zobrist_value(ZOBRIST_TABLE, key, "piece")


def get_effect_zobrist_key(r, c, effect) -> int:
    if not effect:
        return 0
    key = (r, c, effect.get("team"), effect.get("type"), int(effect.get("timer", 0)))
    return _zobrist_value(ZOBRIST_EFFECT_TABLE, key, "effect")


def get_counter_zobrist_key(turns_without_capture: int) -> int:
    return _stable_u64("twc", int(turns_without_capture))


def coords_para_notacao(r, c):
    letras = "abcdefghijklmnopqrstuvwxyz"
    if not (0 <= c < len(letras)):
        raise ValueError(f"Invalid column: {c}")
    if not (0 <= r < LINHAS):
        raise ValueError(f"Invalid row: {r}")
    return f"{letras[c]}{LINHAS - r}"


class GameState:
    __slots__ = (
        "board", "tile_effects", "white_to_move", "game_over", "winner",
        "turns_without_capture", "move_log", "last_move", "white_time",
        "black_time", "state_history", "current_hash", "_hash_valid", "current_score",
    )

    def __init__(self, time_limit_seconds: float = 600.0):
        self.board: list[list[Any]] = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.tile_effects: list[list[Any]] = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
        self.white_to_move = True
        self.game_over = False
        self.winner: str | None = None
        self.turns_without_capture = 0
        self.move_log: list = []
        self.last_move: dict | None = None
        self.white_time = float(time_limit_seconds)
        self.black_time = float(time_limit_seconds)
        self.state_history: dict[int, int] = {}
        self.current_hash = 0
        self._hash_valid = False
        self.current_score: float | int | None = None

    def compute_initial_hash(self):
        h = ZOBRIST_WTM if self.white_to_move else 0
        h ^= get_counter_zobrist_key(self.turns_without_capture)
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = self.board[r][c]
                if p is not None:
                    h ^= get_piece_zobrist_key(r, c, p)
                effect = self.tile_effects[r][c]
                if effect is not None:
                    h ^= get_effect_zobrist_key(r, c, effect)
        self.current_hash = h
        self._hash_valid = True
        return h

    def _get_attack_spawn_piece(self, piece):
        if not piece:
            return None
        behavior = HERO_DEFS.get(piece.name, {}).get("behavior", {}) or {}
        for passive in behavior.get("passives", []):
            if passive.get("trigger") == "on_kill" and passive.get("effect") == "spawn_unit":
                params = passive.get("params", {})
                if params.get("spawn_location") == "target_square":
                    unit_name = params.get("unit_name")
                    if unit_name:
                        from engine.pieces import criar_peca_por_nome
                        return criar_peca_por_nome(unit_name, piece.team)
        return None

    def get_state_hash(self):
        if not self._hash_valid:
            self.compute_initial_hash()
        return self.current_hash

    def remove_piece_hash(self, r, c):
        piece = self.board[r][c]
        if piece is not None:
            self.current_hash ^= get_piece_zobrist_key(r, c, piece)

    def add_piece_hash(self, r, c, piece):
        if piece is not None:
            self.current_hash ^= get_piece_zobrist_key(r, c, piece)

    def remove_effect_hash(self, r, c):
        effect = self.tile_effects[r][c]
        if effect is not None:
            self.current_hash ^= get_effect_zobrist_key(r, c, effect)

    def add_effect_hash(self, r, c, effect):
        if effect is not None:
            self.current_hash ^= get_effect_zobrist_key(r, c, effect)

    def set_tile_effect(self, r, c, effect):
        self.remove_effect_hash(r, c)
        self.tile_effects[r][c] = effect
        self.add_effect_hash(r, c, effect)

    def fast_clone(self):
        novo_gs = GameState.__new__(GameState)
        novo_gs.white_time = self.white_time
        novo_gs.black_time = self.black_time
        novo_gs.white_to_move = self.white_to_move
        novo_gs.game_over = self.game_over
        novo_gs.winner = self.winner
        novo_gs.turns_without_capture = self.turns_without_capture
        novo_gs.state_history = self.state_history.copy()
        novo_gs.last_move = dict(self.last_move) if self.last_move is not None else None
        novo_gs.move_log = []
        novo_gs.current_hash = self.current_hash
        novo_gs._hash_valid = self._hash_valid
        novo_gs.board = [row[:] for row in self.board]
        novo_gs.tile_effects = [row[:] for row in self.tile_effects]

        for r in range(LINHAS):
            for c in range(COLUNAS):
                piece = novo_gs.board[r][c]
                if piece:
                    cloned_piece = piece.__class__(piece.team)
                    cloned_piece.stun_timer = piece.stun_timer
                    if hasattr(piece, "spawn_cooldown"):
                        cloned_piece.spawn_cooldown = piece.spawn_cooldown
                    if hasattr(piece, "lifespan"):
                        cloned_piece.lifespan = piece.lifespan
                    novo_gs.board[r][c] = cloned_piece

                effect = novo_gs.tile_effects[r][c]
                if effect:
                    novo_gs.tile_effects[r][c] = effect.copy()

        novo_gs.current_score = None
        return novo_gs

    def execute_action(self, acao_dict):
        if not isinstance(acao_dict, dict):
            raise TypeError("Action must be a dictionary")

        m_type = str(acao_dict.get("type", "move")).lower()
        start_pos = tuple(acao_dict["start"])
        end_pos = tuple(acao_dict["end"])
        if len(start_pos) != 2 or len(end_pos) != 2:
            raise ValueError("Action coordinates must contain row and column")

        area_stun = acao_dict.get("area", [])
        if m_type == "stun" and not area_stun:
            attacker = self.board[start_pos[0]][start_pos[1]]
            if attacker:
                valid_stuns = attacker.get_valid_stuns(start_pos[0], start_pos[1], self.board, self.tile_effects)
                if end_pos in valid_stuns:
                    area_stun = valid_stuns[end_pos].get("aoe", [])

        self.make_action(
            start_pos,
            end_pos,
            m_type,
            affected_area=area_stun,
            spawn_name=acao_dict.get("spawn_name"),
            spell_name=acao_dict.get("spell_name"),
        )

    def _validate_action_coordinates(self, start_pos, end_pos):
        for position in (start_pos, end_pos):
            if len(position) != 2:
                raise ValueError("Board coordinates must have two components")
            r, c = position
            if not (0 <= r < LINHAS and 0 <= c < COLUNAS):
                raise ValueError(f"Coordinate outside board: {position}")

    def make_action(
        self,
        start_pos,
        end_pos,
        action_type="move",
        affected_area=None,
        spawn_name=None,
        spell_name=None,
        is_simulation=False,
    ):
        if self.game_over:
            return
        if not self._hash_valid:
            self.compute_initial_hash()

        self._validate_action_coordinates(start_pos, end_pos)
        action_type = str(action_type).lower()
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        if piece is None:
            raise ValueError(f"No piece at source square: {start_pos}")

        captured_real_piece = False

        if not is_simulation:
            self.gerar_notacao(piece, start_pos, end_pos, action_type, spawn_name, spell_name)

        self.last_move = {"start": start_pos, "end": end_pos}

        if action_type == "stun":
            if not affected_area:
                raise ValueError("STUN action requires an affected area")
            for ar, ac in affected_area:
                if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):
                    continue
                target = self.board[ar][ac]
                if not target or target.team == piece.team:
                    continue
                if target.stun_timer > 0:
                    captured_real_piece |= target.lifespan is None
                    self.remove_piece_hash(ar, ac)
                    self.board[ar][ac] = None
                else:
                    self.remove_piece_hash(ar, ac)
                    target.stun_timer = 2
                    self.add_piece_hash(ar, ac, target)

        elif action_type == "spawn":
            if not spawn_name:
                raise ValueError("SPAWN action requires spawn_name")
            if self.board[end_row][end_col] is not None:
                raise ValueError("SPAWN target square is occupied")
            from engine.pieces import criar_peca_por_nome
            new_piece = criar_peca_por_nome(spawn_name, piece.team)
            self.board[end_row][end_col] = new_piece
            self.add_piece_hash(end_row, end_col, new_piece)
            self.remove_piece_hash(start_row, start_col)
            piece.stun_timer = 1
            piece.spawn_cooldown = 4
            self.add_piece_hash(start_row, start_col, piece)

        elif action_type == "spell" and spell_name:
            spell_name = str(spell_name).lower()
            if spell_name == "ignite":
                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    fr, fc = end_row + dr, end_col + dc
                    if not (0 <= fr < LINHAS and 0 <= fc < COLUNAS):
                        continue
                    self.set_tile_effect(fr, fc, {"type": "fire", "timer": 3, "team": piece.team})
                    target = self.board[fr][fc]
                    if target and target.stun_timer < 2:
                        self.remove_piece_hash(fr, fc)
                        target.stun_timer = 2
                        self.add_piece_hash(fr, fc, target)

            elif spell_name == "purify":
                target = self.board[end_row][end_col]
                if not target or target.team != piece.team:
                    raise ValueError("PURIFY requires an allied target")
                self.remove_piece_hash(end_row, end_col)
                target.stun_timer = 0
                self.add_piece_hash(end_row, end_col, target)

            elif spell_name == "swap":
                target = self.board[end_row][end_col]
                if not target or target.team != piece.team or target is piece:
                    raise ValueError("SWAP requires a different allied target")
                self.remove_piece_hash(start_row, start_col)
                self.remove_piece_hash(end_row, end_col)
                self.board[start_row][start_col], self.board[end_row][end_col] = target, piece
                self.add_piece_hash(start_row, start_col, self.board[start_row][start_col])
                self.add_piece_hash(end_row, end_col, self.board[end_row][end_col])

            elif spell_name == "barricade":
                if self.board[end_row][end_col] is not None:
                    raise ValueError("BARRICADE target square is occupied")
                from engine.pieces import StoneWall
                barricade = StoneWall(piece.team)
                self.board[end_row][end_col] = barricade
                self.add_piece_hash(end_row, end_col, barricade)

            elif spell_name == "jump":
                target_piece = self.board[end_row][end_col]
                if target_piece:
                    captured_real_piece |= target_piece.lifespan is None
                    self.remove_piece_hash(end_row, end_col)
                self.remove_piece_hash(start_row, start_col)
                self.board[start_row][start_col] = None
                self.board[end_row][end_col] = piece
                self.add_piece_hash(end_row, end_col, piece)
            else:
                raise ValueError(f"Unknown spell: {spell_name}")

        elif action_type == "move":
            if self.board[end_row][end_col] is not None:
                raise ValueError("MOVE target square is occupied")
            self.remove_piece_hash(start_row, start_col)
            self.board[start_row][start_col] = None
            self.board[end_row][end_col] = piece
            self.add_piece_hash(end_row, end_col, piece)

        elif action_type == "attack":
            target_piece = self.board[end_row][end_col]
            if not target_piece or target_piece.team == piece.team:
                raise ValueError("ATTACK requires an enemy target")
            captured_real_piece |= target_piece.lifespan is None

            attacker_behavior = HERO_DEFS.get(piece.name, {}).get("behavior", {}) or {}
            has_aoe = any(
                passive.get("trigger") == "on_attack" and passive.get("effect") == "aoe_damage"
                for passive in attacker_behavior.get("passives", [])
            )

            self.remove_piece_hash(end_row, end_col)
            self.remove_piece_hash(start_row, start_col)

            spawn_piece = self._get_attack_spawn_piece(piece)
            if spawn_piece:
                self.board[start_row][start_col] = piece
                self.board[end_row][end_col] = spawn_piece
                self.add_piece_hash(start_row, start_col, piece)
                self.add_piece_hash(end_row, end_col, spawn_piece)
            else:
                self.board[start_row][start_col] = None
                self.board[end_row][end_col] = piece
                self.add_piece_hash(end_row, end_col, piece)

                if has_aoe:
                    for dr, dc in [
                        (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1),
                        (1, -1), (1, 0), (1, 1),
                    ]:
                        ar, ac = end_row + dr, end_col + dc
                        if not (0 <= ar < LINHAS and 0 <= ac < COLUNAS):
                            continue
                        target = self.board[ar][ac]
                        if target and target.team != piece.team:
                            captured_real_piece |= target.lifespan is None
                            self.remove_piece_hash(ar, ac)
                            self.board[ar][ac] = None
        else:
            raise ValueError(f"Unknown action type: {action_type}")

        destination_effect = self.tile_effects[end_row][end_col]
        destination_piece = self.board[end_row][end_col]
        if (
            destination_piece
            and destination_effect
            and destination_effect.get("type") == "fire"
            and destination_piece.stun_timer < 2
            and action_type != "stun"
            and spell_name != "ignite"
        ):
            self.remove_piece_hash(end_row, end_col)
            destination_piece.stun_timer = 2
            self.add_piece_hash(end_row, end_col, destination_piece)

        old_counter = self.turns_without_capture
        self.turns_without_capture = 0 if captured_real_piece else self.turns_without_capture + 1
        self.current_hash ^= get_counter_zobrist_key(old_counter)
        self.current_hash ^= get_counter_zobrist_key(self.turns_without_capture)

        self.white_to_move = not self.white_to_move
        self.current_hash ^= ZOBRIST_WTM

        self.update_timers()
        self.check_game_over()
        if not is_simulation:
            self.current_score = None

    def update_timers(self):
        """Advance timers belonging to the side whose turn just became active."""
        active_team = "brancas" if self.white_to_move else "pretas"
        for r in range(LINHAS):
            for c in range(COLUNAS):
                piece = self.board[r][c]
                if piece and piece.team == active_team:
                    if piece.stun_timer > 0:
                        self.remove_piece_hash(r, c)
                        piece.stun_timer -= 1
                        self.add_piece_hash(r, c, piece)

                    if hasattr(piece, "spawn_cooldown") and piece.spawn_cooldown > 0:
                        self.remove_piece_hash(r, c)
                        piece.spawn_cooldown -= 1
                        self.add_piece_hash(r, c, piece)

                    if hasattr(piece, "lifespan") and piece.lifespan is not None:
                        self.remove_piece_hash(r, c)
                        piece.lifespan -= 1
                        if piece.lifespan <= 0:
                            self.board[r][c] = None
                        else:
                            self.add_piece_hash(r, c, piece)

                effect = self.tile_effects[r][c]
                if effect and effect.get("team") == active_team:
                    self.remove_effect_hash(r, c)
                    effect["timer"] = int(effect.get("timer", 1)) - 1
                    if effect["timer"] <= 0:
                        self.tile_effects[r][c] = None
                    else:
                        self.add_effect_hash(r, c, effect)

    def gerar_notacao(self, piece, start_pos, end_pos, action_type, spawn_name=None, spell_name=None):
        if not piece:
            return
        sr, sc = start_pos
        er, ec = end_pos
        s_alg = coords_para_notacao(sr, sc)
        e_alg = coords_para_notacao(er, ec)
        num_turno = (len(self.move_log) // 2) + 1
        prefixo = f"{num_turno}. " if piece.team == "brancas" else f"{num_turno}... "

        if action_type == "move": short = f"{piece.acronym} {s_alg}-{e_alg}"
        elif action_type == "attack": short = f"{piece.acronym} {s_alg}x{e_alg}"
        elif action_type == "stun": short = f"{piece.acronym} * {e_alg}"
        elif action_type == "spawn": short = f"{piece.acronym} + {spawn_name[:2] if spawn_name else ''} {e_alg}"
        elif action_type == "spell" and spell_name: short = f"{piece.acronym} {spell_name.upper()} {e_alg}"
        else: short = "?"

        estado_congelado = self.fast_clone()
        self.move_log.append({
            "short": prefixo + short,
            "team": piece.team,
            "estado_anterior": estado_congelado,
            "acao_escolhida": {
                "start": start_pos,
                "end": end_pos,
                "type": action_type,
                "spell_name": spell_name,
                "spawn_name": spawn_name,
            },
        })

    def check_game_over(self):
        white_alive = any(p and p.team == "brancas" for row in self.board for p in row)
        black_alive = any(p and p.team == "pretas" for row in self.board for p in row)

        if not white_alive and not black_alive:
            self.game_over = True
            self.winner = "Aniquilação Mútua (Pretas Vencem no Desempate)"
            return
        if not white_alive:
            self.game_over = True
            self.winner = "Aniquilação (Pretas Vencem)"
            return
        if not black_alive:
            self.game_over = True
            self.winner = "Aniquilação (Brancas Vencem)"
            return

        adversario_vencedor = "Brancas" if self.white_to_move else "Pretas"

        def resolver_por_material():
            white_mat = sum(getattr(p, "cost", 0) for row in self.board for p in row if p and p.team == "brancas")
            black_mat = sum(getattr(p, "cost", 0) for row in self.board for p in row if p and p.team == "pretas")
            if white_mat > black_mat:
                return f"Desempate por Material ({white_mat} vs {black_mat}) - Brancas Vencem"
            return f"Desempate por Material ({black_mat} vs {white_mat}) - Pretas Vencem no Desempate"

        if self.turns_without_capture >= 50:
            self.game_over = True
            self.winner = resolver_por_material()
            return

        current_hash = self.get_state_hash()
        self.state_history[current_hash] = self.state_history.get(current_hash, 0) + 1
        if self.state_history[current_hash] >= 3:
            self.game_over = True
            self.winner = resolver_por_material()
            return

        has_move = False
        active_team = "brancas" if self.white_to_move else "pretas"
        for r in range(LINHAS):
            for c in range(COLUNAS):
                piece = self.board[r][c]
                if not piece or piece.team != active_team or not piece.can_act():
                    continue
                if (
                    piece.get_valid_moves(r, c, self.board, self.tile_effects)
                    or piece.get_valid_attacks(r, c, self.board, self.tile_effects)
                    or piece.get_valid_spawns(r, c, self.board, self.tile_effects)
                ):
                    has_move = True
                    break
                stuns = piece.get_valid_stuns(r, c, self.board, self.tile_effects)
                if stuns and any(info and info.get("has_enemy") for info in stuns.values()):
                    has_move = True
                    break
                if piece.get_valid_spells(r, c, self.board, self.tile_effects):
                    has_move = True
                    break
            if has_move:
                break

        if not has_move:
            self.game_over = True
            self.winner = f"{adversario_vencedor} Vencem (Oponente Bloqueado)"

    def to_rwen(self) -> str:
        lines = []
        for r in range(LINHAS):
            cells = []
            for c in range(COLUNAS):
                piece = self.board[r][c]
                effect = self.tile_effects[r][c]

                if not piece:
                    piece_str = "."
                else:
                    team = "W" if piece.team == "brancas" else "B"
                    name = piece.name.replace(" ", "")
                    lifespan = str(piece.lifespan) if getattr(piece, "lifespan", None) is not None else "N"
                    cooldown = str(getattr(piece, "spawn_cooldown", 0))
                    piece_str = f"{team}_{name}_{piece.stun_timer}_{lifespan}_{cooldown}"

                if not effect:
                    effect_str = "."
                else:
                    effect_team = "W" if effect.get("team") == "brancas" else "B"
                    effect_str = f"{effect_team}_{effect.get('type', 'none')}_{effect.get('timer', 0)}"

                cells.append(f"{piece_str}:{effect_str}")
            lines.append(",".join(cells))

        turn = "W" if self.white_to_move else "B"
        return f"{'/'.join(lines)} {turn} {self.turns_without_capture}"
