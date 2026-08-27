"""Deterministic opening positions for Arena regression tests."""
from __future__ import annotations
import random
from engine.config import COLUNAS, LINHAS
from engine.pieces import obter_catalogo_pecas

# Experiment-only seed set for replication run B. This branch changes this list
# deliberately; production/main keeps the canonical opening-book seeds.
OPENING_SEEDS = (10091, 10211, 10307, 10401, 10503, 10601, 10709, 10809, 10907, 11009, 11103, 11201, 11301, 11409, 11501, 11601)


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
