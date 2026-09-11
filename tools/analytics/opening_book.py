"""Deterministic opening positions for Arena regression and strength tests.

The historical opening book remains available unchanged.  Promotion experiments
use a separate 256-condition deterministic bank so the first 96-game batch is
48 genuinely new opening conditions and later stages add fresh conditions.
Coverage stratification is audited separately from seed generation.
"""
from __future__ import annotations

import random

from engine.config import COLUNAS, LINHAS
from engine.pieces import obter_catalogo_pecas

LEGACY_OPENING_SEEDS = (101, 211, 307, 401, 503, 601, 709, 809, 907, 1009, 1103, 1201, 1301, 1409, 1501, 1601)
PROMOTION_OPENING_SEEDS = tuple(1703 + 1009 * index for index in range(256))
OPENING_SEEDS = LEGACY_OPENING_SEEDS

if len(PROMOTION_OPENING_SEEDS) != 256 or len(set(PROMOTION_OPENING_SEEDS)) != 256:
    raise RuntimeError("Promotion opening bank must contain 256 unique seeds")


def gerar_abertura(seed: int) -> list[list[object | None]]:
    rng = random.Random(seed)
    catalogo = obter_catalogo_pecas()
    if len(catalogo) < 6:
        raise RuntimeError("Opening bank requires at least 6 draftable heroes")
    board = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
    for team, rows in (("pretas", (0, 1)), ("brancas", (LINHAS - 2, LINHAS - 1))):
        picks = rng.sample(catalogo, 6)
        positions = [(rows[0], 1), (rows[0], 3), (rows[0], 5), (rows[1], 2), (rows[1], 4), (rows[1], 6)]
        for item, (row, col) in zip(picks, positions):
            board[row][col] = item["class"](team)
    return board


def carregar_abertura_do_book(gs, index: int = 0) -> int:
    seed = OPENING_SEEDS[index % len(OPENING_SEEDS)]
    gs.board = gerar_abertura(seed)
    return seed
