import re

from engine.config import LINHAS, COLUNAS


class ActionParser:
    """Parseia a representação textual de ações produzida pelas IAs."""

    COORD = r"([A-Z][1-9][0-9]*)"

    PATTERN_MOVE = re.compile(rf"^MOVE\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    PATTERN_ATTACK = re.compile(rf"^ATTACK\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    PATTERN_STUN = re.compile(rf"^STUN\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    PATTERN_SPAWN = re.compile(rf"^SPAWN\s+([a-zA-Z_]+)\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    PATTERN_SPELL = re.compile(rf"^SPELL\s+([a-zA-Z_]+)\s+{COORD}\s+{COORD}$", re.IGNORECASE)

    @staticmethod
    def _valid_alg(alg: str) -> bool:
        if not isinstance(alg, str) or not re.fullmatch(r"[A-Z][1-9][0-9]*", alg.upper()):
            return False
        alg = alg.upper()
        col = ord(alg[0]) - ord("A")
        try:
            row_number = int(alg[1:])
        except ValueError:
            return False
        return 0 <= col < COLUNAS and 1 <= row_number <= LINHAS

    @classmethod
    def _parse_match(cls, match, action: str, group_count: int) -> dict | None:
        if not match:
            return None
        groups = match.groups()
        coords = groups[-2:]
        if not all(cls._valid_alg(coord) for coord in coords):
            return None

        result = {
            "action": action,
            "origin": coords[0].upper(),
            "target": coords[1].upper(),
        }
        if action == "SPAWN":
            result["hero"] = groups[0]
        elif action == "SPELL":
            result["spell"] = groups[0].lower()
        return result

    @classmethod
    def parse(cls, action_str: str) -> dict | None:
        if not isinstance(action_str, str):
            return None

        action_str = action_str.strip()
        if not action_str:
            return None

        parsed = cls._parse_match(cls.PATTERN_MOVE.fullmatch(action_str), "MOVE", 2)
        if parsed:
            return parsed
        parsed = cls._parse_match(cls.PATTERN_ATTACK.fullmatch(action_str), "ATTACK", 2)
        if parsed:
            return parsed
        parsed = cls._parse_match(cls.PATTERN_STUN.fullmatch(action_str), "STUN", 2)
        if parsed:
            return parsed
        parsed = cls._parse_match(cls.PATTERN_SPAWN.fullmatch(action_str), "SPAWN", 3)
        if parsed:
            return parsed
        return cls._parse_match(cls.PATTERN_SPELL.fullmatch(action_str), "SPELL", 3)

    @staticmethod
    def alg_to_coords(alg: str, total_linhas: int) -> tuple[int, int]:
        """Converte, por exemplo, ``A8`` em ``(0, 0)``."""
        if not isinstance(alg, str):
            raise ValueError("Coordinate must be a string")

        alg = alg.strip().upper()
        if not re.fullmatch(r"[A-Z][1-9][0-9]*", alg):
            raise ValueError(f"Invalid coordinate: {alg!r}")

        if total_linhas <= 0 or total_linhas != LINHAS:
            raise ValueError(f"Unsupported board height: {total_linhas}")

        col = ord(alg[0]) - ord("A")
        row_number = int(alg[1:])
        if not (0 <= col < COLUNAS and 1 <= row_number <= total_linhas):
            raise ValueError(f"Coordinate outside board: {alg!r}")

        return total_linhas - row_number, col
