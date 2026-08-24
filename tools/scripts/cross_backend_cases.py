"""Canonical cross-backend positions generated from GameState."""
from __future__ import annotations

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _case() -> GameState:
    return GameState()


def _put(gs: GameState, row: int, col: int, name: str, team: str, *, stun: int = 0, lifespan: int | None = None, cooldown: int = 0) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    piece.lifespan = lifespan
    piece.spawn_cooldown = cooldown
    gs.board[row][col] = piece


def build_cases() -> list[str]:
    cases: list[GameState] = []

    empty = _case()
    cases.append(empty)

    material = _case()
    _put(material, 0, 0, "FrostMage", "brancas")
    _put(material, 1, 1, "Templar", "pretas", stun=2, lifespan=4, cooldown=2)
    _put(material, 2, 2, "Lich", "pretas", lifespan=3)
    _put(material, 3, 3, "BoneLord", "brancas")
    _put(material, 4, 4, "FrostMage", "pretas")
    _put(material, 5, 1, "Berserker", "pretas")
    _put(material, 5, 2, "Ranger", "brancas")
    material.turns_without_capture = 17
    cases.append(material)

    mixed = _case()
    _put(mixed, 0, 0, "Cleric", "brancas", stun=0, lifespan=5, cooldown=1)
    _put(mixed, 0, 1, "Phantom", "pretas")
    _put(mixed, 1, 1, "FrostMage", "pretas", stun=2)
    _put(mixed, 1, 4, "Templar", "brancas")
    _put(mixed, 2, 2, "Lich", "brancas")
    _put(mixed, 2, 5, "Ranger", "pretas")
    _put(mixed, 3, 3, "BoneLord", "pretas")
    _put(mixed, 4, 0, "Obelisk", "brancas")
    _put(mixed, 5, 1, "Berserker", "brancas")
    mixed.white_to_move = False
    mixed.turns_without_capture = 31
    cases.append(mixed)

    return [gs.to_rwen() for gs in cases]
