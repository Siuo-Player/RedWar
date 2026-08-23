from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

LINHAS = 8
COLUNAS = 8
MAX_HEROES = 64
PIECE_FEATURES = LINHAS * COLUNAS * MAX_HEROES * 2
STUN_FEATURES = LINHAS * COLUNAS * 2 * 6
LIFESPAN_FEATURES = LINHAS * COLUNAS * 2 * 6
COOLDOWN_FEATURES = LINHAS * COLUNAS * 2 * 5
SIDE_FEATURES = 2
FEATURE_COUNT = PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES + SIDE_FEATURES


@dataclass(frozen=True)
class Piece:
    team: str
    name: str
    stun: int
    lifespan: int
    cooldown: int
    hero_id: int


def load_hero_ids(path: str | Path = "engine/heroes_config.json") -> dict[str, int]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = {name: idx for idx, name in enumerate(data.keys()) if idx < MAX_HEROES}
    if not ids:
        raise ValueError(f"No heroes found in {path}")
    return ids


def _parse_team(value: str) -> str:
    if value not in {"W", "B"}:
        raise ValueError(f"Invalid team: {value!r}")
    return value


def parse_rwen(rwen: str, hero_ids: dict[str, int]) -> tuple[list[list[Piece | None]], str, int]:
    parts = rwen.strip().split()
    if len(parts) != 3:
        raise ValueError("RWEN must be '<board> <turn> <twc>'")
    board_text, turn, twc_text = parts
    turn = _parse_team(turn)
    twc = int(twc_text)
    rows = board_text.split("/")
    if len(rows) != LINHAS:
        raise ValueError(f"Expected {LINHAS} rows")

    board: list[list[Piece | None]] = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
    for r, row in enumerate(rows):
        cells = row.split(",")
        if len(cells) != COLUNAS:
            raise ValueError(f"Row {r} has {len(cells)} cells")
        for c, cell in enumerate(cells):
            parts2 = cell.split(":", 1)
            token = parts2[0]
            if token == ".":
                continue
            fields = token.split("_")
            if len(fields) != 5:
                raise ValueError(f"Invalid piece at {(r, c)}: {token}")
            team = _parse_team(fields[0])
            name = fields[1]
            if name not in hero_ids:
                raise ValueError(f"Unknown hero {name!r}")
            lifespan = 999 if fields[3] == "N" else int(fields[3])
            board[r][c] = Piece(team, name, int(fields[2]), lifespan, int(fields[4]), hero_ids[name])
    return board, turn, twc


def _relative_color(perspective: int, piece: Piece) -> int:
    own = "W" if perspective == 0 else "B"
    return 0 if piece.team == own else 1


def feature_for_piece(perspective: int, square: int, piece: Piece) -> int:
    color = _relative_color(perspective, piece)
    return (square * MAX_HEROES + piece.hero_id) * 2 + color


def feature_for_stun(perspective: int, square: int, piece: Piece) -> int:
    color = _relative_color(perspective, piece)
    bucket = max(0, min(piece.stun, 5))
    return PIECE_FEATURES + (square * 2 + color) * 6 + bucket


def feature_for_lifespan(perspective: int, square: int, piece: Piece) -> int:
    color = _relative_color(perspective, piece)
    bucket = 5 if piece.lifespan >= 999 else max(0, min(piece.lifespan, 5))
    return PIECE_FEATURES + STUN_FEATURES + (square * 2 + color) * 6 + bucket


def feature_for_cooldown(perspective: int, square: int, piece: Piece) -> int:
    color = _relative_color(perspective, piece)
    bucket = max(0, min(piece.cooldown, 4))
    return PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + (square * 2 + color) * 5 + bucket


def feature_for_side(perspective: int, side_to_move: str) -> int:
    own = "W" if perspective == 0 else "B"
    return PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES + (0 if side_to_move == own else 1)


def active_features(rwen: str, hero_ids: dict[str, int] | None = None) -> tuple[list[int], list[int]]:
    hero_ids = hero_ids or load_hero_ids()
    board, turn, _twc = parse_rwen(rwen, hero_ids)
    result: list[list[int]] = [[], []]

    for perspective in range(2):
        for r in range(LINHAS):
            for c in range(COLUNAS):
                piece = board[r][c]
                if piece is None:
                    continue
                square = r * COLUNAS + c
                result[perspective].extend(
                    (
                        feature_for_piece(perspective, square, piece),
                        feature_for_stun(perspective, square, piece),
                        feature_for_lifespan(perspective, square, piece),
                        feature_for_cooldown(perspective, square, piece),
                    )
                )
        result[perspective].append(feature_for_side(perspective, turn))

    return result[0], result[1]


def active_features_for_many(rwens: Iterable[str], hero_ids: dict[str, int] | None = None) -> list[tuple[list[int], list[int]]]:
    ids = hero_ids or load_hero_ids()
    return [active_features(rwen, ids) for rwen in rwens]
