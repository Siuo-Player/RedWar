"""Deterministic opening positions for Arena regression tests."""
from __future__ import annotations
import random
from engine.config import COLUNAS, LINHAS
from engine.pieces import obter_catalogo_pecas

OPENING_SEEDS = (101, 211, 307, 401, 503, 601, 709, 809, 907, 1009, 1103, 1201, 1301, 1409, 1501, 1601)


def gerar_abertura(seed: int) -> list[list[object | None]]:
    rng = random.Random(seed)
    catalogo = obter_catalogo_pecas()
    if len(catalogo) < 6:
        raise RuntimeError("Opening book requires at least 6 draftable heroes")
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
