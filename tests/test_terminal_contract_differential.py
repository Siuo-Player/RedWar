from __future__ import annotations

import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "cpp_terminal_contract_test"


def _run_native(states: list[GameState]) -> list[tuple[str, int, str]]:
    assert BINARY.exists(), f"native terminal contract helper missing: {BINARY}"
    payload = "".join(f"{state.to_rwen()}\n" for state in states)
    result = subprocess.run(
        [str(BINARY)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split(maxsplit=3)
        assert len(parts) == 4 and parts[0] == "CONTRACT", line
        rows.append((parts[1], int(parts[2]), parts[3]))
    return rows


def _assert_python_terminal(
    state: GameState,
    expected_game_over: bool,
    expected_winner: str | None = None,
) -> None:
    state.state_history = {}
    state.check_game_over()
    assert state.game_over is expected_game_over
    assert state.winner == expected_winner


def test_terminal_contract_matrix_matches_python_terminal_classes():
    mutual = GameState()
    _assert_python_terminal(
        mutual,
        True,
        "Aniquilação Mútua (Pretas Vencem no Desempate)",
    )

    white_only = GameState()
    white_only.board[6][0] = criar_peca_por_nome("Geomancer", "brancas")
    _assert_python_terminal(white_only, True, "Aniquilação (Brancas Vencem)")

    black_only = GameState()
    black_only.board[1][0] = criar_peca_por_nome("Cleric", "pretas")
    _assert_python_terminal(black_only, True, "Aniquilação (Pretas Vencem)")

    blocked = GameState()
    stunned = criar_peca_por_nome("StoneWall", "brancas")
    stunned.stun_timer = 1
    blocked.board[6][0] = stunned
    blocked.board[1][0] = criar_peca_por_nome("Cleric", "pretas")
    _assert_python_terminal(blocked, True, "Brancas Vencem (Oponente Bloqueado)")

    twc50 = GameState()
    twc50.board[6][0] = criar_peca_por_nome("Geomancer", "brancas")
    twc50.board[1][0] = criar_peca_por_nome("Cleric", "pretas")
    twc50.turns_without_capture = 50
    _assert_python_terminal(twc50, True)
    assert twc50.winner is not None and "Desempate por Material" in twc50.winner

    twc49 = GameState()
    twc49.board[6][0] = criar_peca_por_nome("Geomancer", "brancas")
    twc49.board[1][0] = criar_peca_por_nome("Cleric", "pretas")
    twc49.turns_without_capture = 49
    _assert_python_terminal(twc49, False)

    native = _run_native([mutual, white_only, black_only, blocked, twc50, twc49])
    kinds = [row[0] for row in native]
    assert kinds == [
        "MUTUAL_ANNIHILATION",
        "WHITE_ANNIHILATION",
        "BLACK_ANNIHILATION",
        "BLOCKED",
        "TWC_50",
        "NON_TERMINAL",
    ]

    for kind, score, bestmove in native[:5]:
        assert bestmove == "0000"
        assert abs(score) >= 9_999_899

    assert native[0][1] < 0
    assert native[1][1] > 0
    assert native[2][1] < 0
    assert native[3][1] < 0

    twc_score = native[4][1]
    assert twc_score != 0
    if "Brancas Vencem" in twc50.winner:
        assert twc_score > 0
    else:
        assert twc_score < 0

    assert native[5][1] == 0
    assert native[5][2] != "0000"
