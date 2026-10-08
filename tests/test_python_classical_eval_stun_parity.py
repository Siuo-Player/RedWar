from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_python_evaluator_matches_classical_stun_fixture():
    # Run in a clean interpreter: other UI tests intentionally inject a stub
    # into sys.modules["ai.evaluator"], which must not shadow the real Cython
    # extension in this parity test.
    script = r"""
import json
from ai.evaluator import avaliador_mestre
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

def evaluate(stunned):
    state = GameState()
    piece = criar_peca_por_nome("BoneLord", "brancas")
    if stunned:
        piece.stun_timer = 1
    state.board[7][0] = piece
    # Keep both sides alive so the Cython evaluator does not take its
    # terminal-position fast path. Bone costs 8 and has no positional bonus.
    state.board[4][4] = criar_peca_por_nome("Bone", "pretas")
    state.turns_without_capture = 0
    return avaliador_mestre(state)

print(json.dumps([evaluate(False), evaluate(True)]))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    scores = json.loads(completed.stdout.strip().splitlines()[-1])

    # Shared fixture with ai/cpp_engine/SmokeTest.cpp:
    # BoneLord: 126 unstunned / 7 stunned. The opposing Bone contributes -8.
    assert scores == [118, -1]
