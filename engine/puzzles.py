from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.config import COLUNAS, LINHAS
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def load_rwen_into_game_state(rwen: str, state: GameState) -> None:
    """Populate an authoritative GameState from a canonical RWEN string."""
    parts = rwen.strip().split()
    if len(parts) != 3:
        raise ValueError("RWEN must be '<board> <turn> <twc>'")
    board_text, turn, twc_text = parts
    rows = board_text.split("/")

    state.white_to_move = (turn.upper() == "W")
    state.turns_without_capture = int(twc_text)
    state.board = [[None for _ in range(len(rows[0].split(",")))] for _ in range(len(rows))]
    state.tile_effects = [[None for _ in range(len(rows[0].split(",")))] for _ in range(len(rows))]

    for r, row in enumerate(rows):
        cells = row.split(",")
        for c, cell in enumerate(cells):
            parts2 = cell.split(":", 1)
            token = parts2[0]
            if token != ".":
                fields = token.split("_")
                if len(fields) >= 5:
                    team_str = "brancas" if fields[0] == "W" else "pretas"
                    hero_name = fields[1]
                    piece = criar_peca_por_nome(hero_name, team_str)
                    piece.stun_timer = int(fields[2])
                    piece.lifespan = None if fields[3] == "N" else int(fields[3])
                    piece.spawn_cooldown = int(fields[4])
                    state.board[r][c] = piece

            if len(parts2) == 2 and parts2[1] != ".":
                eff_fields = parts2[1].split("_")
                if len(eff_fields) >= 3:
                    eff_team = "brancas" if eff_fields[0] == "W" else "pretas"
                    state.tile_effects[r][c] = {
                        "team": eff_team,
                        "type": eff_fields[1],
                        "timer": int(eff_fields[2]),
                    }

    state.compute_initial_hash()


@dataclass(frozen=True)
class TacticalPuzzle:
    puzzle_id: str
    title: str
    description: str
    rating: int
    initial_rwen: str
    solution_moves: list[str]
    theme: str = "tactics"


class PuzzleRunner:
    """Manages the state and verification of a tactical puzzle."""

    def __init__(self, puzzle: TacticalPuzzle):
        self.puzzle = puzzle
        self.current_step = 0
        self._state = GameState()
        load_rwen_into_game_state(puzzle.initial_rwen, self._state)

    def get_state(self) -> GameState:
        return self._state

    def is_solved(self) -> bool:
        return self.current_step >= len(self.puzzle.solution_moves)

    def submit_move(self, move_uci: str) -> tuple[bool, bool]:
        """Submit a candidate move in UCI format.

        Returns (is_correct, is_puzzle_completed).
        """
        if self.is_solved():
            return False, True

        expected = self.puzzle.solution_moves[self.current_step].strip().upper()
        attempted = move_uci.strip().upper()

        if attempted == expected:
            self.current_step += 1
            completed = self.is_solved()
            return True, completed
        return False, False


PUZZLE_BANK: list[TacticalPuzzle] = [
    TacticalPuzzle(
        puzzle_id="puz_001",
        title="Lethal Second Stun Execution",
        description="Exploit the stunned enemy Ranger to execute a permanent kill.",
        rating=950,
        initial_rwen=".:.,.:.,.:.,B_Ranger_0_N_1:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,W_Dragoon_0_N_0:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0",
        solution_moves=["MOVE D2 D8", "ATTACK D8 D8"],
        theme="lethal_second_stun",
    ),
    TacticalPuzzle(
        puzzle_id="puz_002",
        title="Nevada Frost Freeze",
        description="Cast Nevada to freeze the advancing enemy vanguard.",
        rating=1250,
        initial_rwen=".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,B_Inquisitor_0_N_0:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,W_FrostMage_0_N_0:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0",
        solution_moves=["SPELL D2 D7 nevada"],
        theme="area_freeze",
    ),
    TacticalPuzzle(
        puzzle_id="puz_003",
        title="Dragoon Leap Fork",
        description="Leap across obstacles to threaten multiple high-value targets.",
        rating=1550,
        initial_rwen=".:.,.:.,B_Cleric_0_N_0:.,.:.,B_BoneLord_0_N_0:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,W_Dragoon_0_N_0:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0",
        solution_moves=["SPELL D2 D7 jump"],
        theme="dragoon_jump_fork",
    ),
]
