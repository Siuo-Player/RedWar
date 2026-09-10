"""Canonical validation for the pre-match draft and placement phase."""
from __future__ import annotations

from engine.config import COLUNAS, LINHAS, ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS


def draft_budget_for_team(team: str) -> int:
    """Return the configured pre-match draft budget for ``team``."""
    if team == "brancas":
        return ORCAMENTO_BRANCAS
    if team == "pretas":
        return ORCAMENTO_PRETAS
    raise ValueError(f"Invalid team: {team!r}")


def home_rows_for_team(team: str) -> range:
    """Return the two home rows reserved for pre-match placement."""
    if team == "brancas":
        return range(LINHAS - 2, LINHAS)
    if team == "pretas":
        return range(0, 2)
    raise ValueError(f"Invalid team: {team!r}")


def validate_pre_match_setup(board, team: str, *, budget: int | None = None) -> int:
    """Validate one team's pre-match draft and placement contract.

    The board may contain no more than draft-selected pieces for the requested
    team. Runtime-created units are not subject to this check unless this
    function is explicitly called as part of pre-match setup.

    Returns the total draft cost for the team when valid.
    """
    if team not in {"brancas", "pretas"}:
        raise ValueError(f"Invalid team: {team!r}")

    configured_budget = draft_budget_for_team(team)
    limit = configured_budget if budget is None else int(budget)
    if limit < 0:
        raise ValueError(f"Draft budget must be non-negative: {limit}")

    allowed_rows = home_rows_for_team(team)
    total_cost = 0

    for row in range(LINHAS):
        for col in range(COLUNAS):
            piece = board[row][col]
            if piece is None or piece.team != team:
                continue

            if row not in allowed_rows:
                raise ValueError(
                    f"Pre-match {team} piece outside home rows: {(row, col)}"
                )

            if not getattr(piece, "draftable", True):
                raise ValueError(
                    f"Non-draftable piece cannot appear in pre-match setup: {piece.name}"
                )

            total_cost += int(piece.cost)

    if total_cost > limit:
        raise ValueError(
            f"Pre-match {team} draft exceeds budget: {total_cost} > {limit}"
        )

    return total_cost


def validate_complete_pre_match_setup(board) -> dict[str, int]:
    """Validate both teams and return their draft costs."""
    return {
        "brancas": validate_pre_match_setup(board, "brancas"),
        "pretas": validate_pre_match_setup(board, "pretas"),
    }
