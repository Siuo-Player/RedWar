"""Ares 2.0 AI Engine Search Enhancements for RedWar.

Implements Stockfish-inspired search heuristics:
- Transposition Table with Zobrist hashing & replacement strategies
- MVV-LVA (Most Valuable Victim - Least Valuable Attacker) move ordering
  with dedicated 2-hit stun lethal kill prioritization
- 2-Slot Killer Move Ordering per ply
- History Heuristic table for quiet move ordering
- Dynamic Clock Allocation (Time Management)
- Quiescence Search on tactical captures and stun attacks
- Full Iterative Deepening Negamax Search Engine with Alpha-Beta Pruning
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from engine.legal_actions import legal_actions, to_legacy_dicts
from ai.domain_eval import RedWarDomainEvaluator
from ai.opening_book import get_opening_move


class TTFlag(IntEnum):
    EXACT = 0
    LOWERBOUND = 1
    UPPERBOUND = 2


@dataclass
class TTEntry:
    hash_key: int
    depth: int
    score: float
    flag: TTFlag
    best_move: Optional[dict[str, Any]] = None


class TranspositionTable:
    """Fixed-capacity hash table indexed by Zobrist hash with depth-preferred replacement."""

    def __init__(self, size_power_of_two: int = 16):
        self.capacity = 1 << size_power_of_two
        self.mask = self.capacity - 1
        self._table: list[Optional[TTEntry]] = [None] * self.capacity
        self.hits = 0
        self.stores = 0

    def store(self, hash_key: int, depth: int, score: float, flag: TTFlag, best_move: Optional[dict[str, Any]] = None) -> None:
        idx = hash_key & self.mask
        existing = self._table[idx]
        if existing is None or depth >= existing.depth or existing.hash_key != hash_key:
            self._table[idx] = TTEntry(hash_key=hash_key, depth=depth, score=score, flag=flag, best_move=best_move)
            self.stores += 1

    def probe(self, hash_key: int) -> Optional[TTEntry]:
        idx = hash_key & self.mask
        entry = self._table[idx]
        if entry is not None and entry.hash_key == hash_key:
            self.hits += 1
            return entry
        return None

    def clear(self) -> None:
        self._table = [None] * self.capacity
        self.hits = 0
        self.stores = 0


@dataclass
class KillerMoveTable:
    max_depth: int = 32
    slots: list[list[Optional[str]]] = field(default_factory=list)

    def __post_init__(self):
        if not self.slots:
            self.slots = [[None, None] for _ in range(self.max_depth)]

    def record_killer(self, ply: int, move_repr: str) -> None:
        if 0 <= ply < self.max_depth:
            slot0, _ = self.slots[ply]
            if slot0 != move_repr:
                self.slots[ply][1] = slot0
                self.slots[ply][0] = move_repr

    def get_killers(self, ply: int) -> tuple[Optional[str], Optional[str]]:
        if 0 <= ply < self.max_depth:
            return self.slots[ply][0], self.slots[ply][1]
        return None, None

    def clear(self) -> None:
        for ply in range(self.max_depth):
            self.slots[ply][0] = None
            self.slots[ply][1] = None


class HistoryTable:
    """Tracks quiet moves that generated beta cutoffs across previous searches."""

    def __init__(self):
        self._history: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}

    def record_cutoff(self, from_sq: tuple[int, int], to_sq: tuple[int, int], depth: int) -> None:
        key = (from_sq, to_sq)
        bonus = depth * depth
        self._history[key] = min(8_000, self._history.get(key, 0) + bonus)

    def get_score(self, from_sq: tuple[int, int], to_sq: tuple[int, int]) -> int:
        return self._history.get((from_sq, to_sq), 0)

    def clear(self) -> None:
        self._history.clear()


class DynamicTimeManager:
    """Stockfish-style dynamic time allocation based on remaining clock and game phase."""

    @staticmethod
    def allocate_time_budget(
        remaining_seconds: float,
        increment_seconds: float = 0.0,
        moves_to_go: int = 30,
        tactical_alert: bool = False,
    ) -> float:
        if remaining_seconds <= 0.0:
            return 0.05

        effective_moves = max(10, min(50, moves_to_go))
        base_budget = (remaining_seconds / effective_moves) + (0.75 * increment_seconds)

        multiplier = 1.8 if tactical_alert else 1.0
        allocated = base_budget * multiplier

        max_allowed = max(0.05, remaining_seconds * 0.35)
        return max(0.05, min(allocated, max_allowed))

    @staticmethod
    def allocate_nodes(
        base_nodes: int,
        time_ratio: float = 1.0,
        tactical_alert: bool = False,
    ) -> int:
        factor = 1.5 if tactical_alert else 1.0
        scaled = int(base_nodes * factor * max(0.2, min(2.0, time_ratio)))
        return max(500, min(scaled, 1_000_000))


def move_to_string_key(move: dict[str, Any]) -> str:
    """Produce a deterministic compact string key for move comparison."""
    m_type = move.get("type", "")
    start = move.get("start", ())
    end = move.get("end", ())
    spell = move.get("spell_name") or ""
    return f"{m_type}:{start}->{end}:{spell}"


def mvv_lva_score(state: Any, move: dict[str, Any]) -> int:
    """Calculate Most Valuable Victim - Least Valuable Attacker priority for RedWar."""
    m_type = str(move.get("type", "")).lower()
    end = move.get("end")
    start = move.get("start")
    if not end or len(end) != 2:
        return 0

    tr, tc = end
    target = state.board[tr][tc] if 0 <= tr < len(state.board) and 0 <= tc < len(state.board[0]) else None
    if not target:
        return 0

    attacker = state.board[start[0]][start[1]] if start and len(start) == 2 else None
    attacker_cost = int(getattr(attacker, "cost", 15))
    victim_cost = int(getattr(target, "cost", 15))

    target_stun = getattr(target, "stun_timer", 0)
    # 2-hit stun lethality: if target is already stunned, an attack or lethal spell KILLS IT!
    if target_stun > 0:
        return 300_000 + (victim_cost * 100) - attacker_cost
    else:
        # Applying first stun to target
        return 120_000 + (victim_cost * 20) - attacker_cost


def sort_moves_ares2(
    moves: list[dict[str, Any]],
    ply: int,
    killer_table: KillerMoveTable,
    history_table: HistoryTable,
    tt_best_move: Optional[str] = None,
    state: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Order candidate legal moves using TT, MVV-LVA, Killers, History, and Tacticals."""
    killer1, killer2 = killer_table.get_killers(ply)

    def score_move(m: dict[str, Any]) -> int:
        key = move_to_string_key(m)
        if tt_best_move and key == tt_best_move:
            return 1_000_000

        m_type = str(m.get("type", "")).lower()

        # Tactical captures and attacks prioritized via MVV-LVA
        if state is not None and (m_type == "attack" or (m_type == "spell" and m.get("spell_name"))):
            score = mvv_lva_score(state, m)
            if score > 0:
                return score

        if m_type == "attack":
            return 100_000
        if m_type == "stun":
            return 50_000
        if m_type == "spell":
            return 40_000

        # Quiet moves
        if key == killer1:
            return 20_000
        if key == killer2:
            return 18_000

        start = m.get("start")
        end = m.get("end")
        if start and end and len(start) == 2 and len(end) == 2:
            hist = history_table.get_score(tuple(start), tuple(end))
            if hist > 0:
                return 1_000 + hist

        # Center proximity tie-break for quiet moves
        if end and len(end) == 2:
            center_r, center_c = 3.5, 3.5
            dist = abs(end[0] - center_r) + abs(end[1] - center_c)
            return int(max(0, 100 - dist * 10))

        return 0

    return sorted(moves, key=score_move, reverse=True)


def quiescence_search(
    state: Any,
    alpha: float,
    beta: float,
    team: str,
    q_depth: int = 0,
    max_qdepth: int = 3,
    evaluator: Optional[RedWarDomainEvaluator] = None,
) -> float:
    """Quiescence search resolving tactical exchanges (captures and stun strikes) at leaf nodes."""
    if evaluator is None:
        evaluator = RedWarDomainEvaluator()

    stand_pat = evaluator.evaluate(state, team)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    if q_depth >= max_qdepth:
        return alpha

    # Generate only tactical moves (attacks, lethal spells)
    all_actions = to_legacy_dicts(legal_actions(state))
    tactical_moves = [
        m for m in all_actions
        if str(m.get("type", "")).lower() in ("attack", "stun") or
        (str(m.get("type", "")).lower() == "spell" and m.get("spell_name") in (
            "chain_lightning", "arcane_blast", "aimed_shot", "sentinel_shot", "spectral_strike", "bone_v"
        ))
    ]

    if not tactical_moves:
        return alpha

    # Order tactical moves by MVV-LVA
    tactical_moves.sort(key=lambda m: mvv_lva_score(state, m), reverse=True)

    enemy_team = "pretas" if team == "brancas" else "brancas"
    for move in tactical_moves:
        clone = state.fast_clone()
        clone.execute_action(move)
        score = -quiescence_search(clone, -beta, -alpha, enemy_team, q_depth + 1, max_qdepth, evaluator)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


class AresEngine:
    """State-of-the-art Ares AI Search Engine for RedWar."""

    def __init__(self, tt_size_power: int = 16):
        self.tt = TranspositionTable(size_power_of_two=tt_size_power)
        self.killer_table = KillerMoveTable()
        self.history_table = HistoryTable()
        self.evaluator = RedWarDomainEvaluator()
        self.nodes_visited = 0
        self.cutoffs = 0

    def reset(self) -> None:
        self.tt.clear()
        self.killer_table.clear()
        self.history_table.clear()
        self.nodes_visited = 0
        self.cutoffs = 0

    def choose_best_move(
        self,
        state: Any,
        max_depth: int = 3,
        time_limit: float = 1.0,
        skill_level: int = 3,
        use_opening_book: bool = True,
    ) -> Optional[dict[str, Any]]:
        if skill_level == 1:
            max_depth = 1
            time_limit = min(0.3, time_limit)
            use_opening_book = False
        elif skill_level == 2:
            max_depth = 2
            time_limit = min(0.6, time_limit)
        result = self.search(state, max_depth=max_depth, time_limit=time_limit, use_opening_book=use_opening_book)
        return result.get("best_move")

    def search(
        self,
        state: Any,
        max_depth: int = 3,
        time_limit: float = 1.0,
        max_nodes: int = 100_000,
        use_opening_book: bool = True,
    ) -> dict[str, Any]:
        """Perform iterative deepening negamax search with alpha-beta pruning."""
        start_time = time.time()
        self.nodes_visited = 0
        self.cutoffs = 0
        best_overall_move: Optional[dict[str, Any]] = None
        best_overall_score = -float("inf")
        team = "brancas" if getattr(state, "white_to_move", True) else "pretas"
        completed_depth = 0

        # Opening book probe (active in multi-piece opening formations)
        total_pieces = sum(1 for row in getattr(state, "board", []) for p in row if p is not None)
        if total_pieces >= 6 and len(getattr(state, "move_log", [])) <= 8:
            book_action = get_opening_move(state, team)
            if book_action is not None:
                return {
                    "best_move": book_action,
                    "score": 0.0,
                    "depth_reached": 1,
                    "nodes_visited": 1,
                    "cutoffs": 0,
                    "tt_hits": 0,
                    "elapsed_seconds": 0.001,
                    "is_book": True,
                }

        # Iterative Deepening
        for depth in range(1, max_depth + 1):
            if time.time() - start_time >= time_limit:
                break

            score, move = self._negamax(
                state=state,
                depth=depth,
                ply=0,
                alpha=-float("inf"),
                beta=float("inf"),
                team=team,
                start_time=start_time,
                time_limit=time_limit,
                max_nodes=max_nodes,
            )

            if move is not None:
                best_overall_move = move
                best_overall_score = score
                completed_depth = depth

            if self.nodes_visited >= max_nodes:
                break

        elapsed = time.time() - start_time
        return {
            "best_move": best_overall_move,
            "score": best_overall_score,
            "depth_reached": completed_depth,
            "nodes_visited": self.nodes_visited,
            "cutoffs": self.cutoffs,
            "tt_hits": self.tt.hits,
            "elapsed_seconds": elapsed,
        }

    def _negamax(
        self,
        state: Any,
        depth: int,
        ply: int,
        alpha: float,
        beta: float,
        team: str,
        start_time: float,
        time_limit: float,
        max_nodes: int,
    ) -> tuple[float, Optional[dict[str, Any]]]:
        self.nodes_visited += 1

        if self.nodes_visited % 512 == 0 and (time.time() - start_time >= time_limit or self.nodes_visited >= max_nodes):
            return self.evaluator.evaluate(state, team), None

        # Transposition table probe
        z_hash = getattr(state, "current_hash", 0)
        tt_best_move_str: Optional[str] = None
        tt_entry = self.tt.probe(z_hash) if z_hash else None
        if tt_entry is not None and tt_entry.depth >= depth:
            if tt_entry.best_move:
                tt_best_move_str = move_to_string_key(tt_entry.best_move)
            if tt_entry.flag == TTFlag.EXACT:
                return tt_entry.score, tt_entry.best_move
            elif tt_entry.flag == TTFlag.LOWERBOUND:
                alpha = max(alpha, tt_entry.score)
            elif tt_entry.flag == TTFlag.UPPERBOUND:
                beta = min(beta, tt_entry.score)
            if alpha >= beta:
                self.cutoffs += 1
                return tt_entry.score, tt_entry.best_move

        # Base case: run Quiescence Search on tactical leaf nodes
        if depth <= 0:
            q_score = quiescence_search(state, alpha, beta, team, evaluator=self.evaluator)
            return q_score, None

        raw_actions = to_legacy_dicts(legal_actions(state))
        if not raw_actions:
            state.check_game_over()
            if getattr(state, "game_over", False):
                return -50_000.0, None  # Loss
            return 0.0, None  # Stalemate / draw

        # Move ordering
        ordered_actions = sort_moves_ares2(
            moves=raw_actions,
            ply=ply,
            killer_table=self.killer_table,
            history_table=self.history_table,
            tt_best_move=tt_best_move_str,
            state=state,
        )

        best_move = None
        best_score = -float("inf")
        initial_alpha = alpha
        enemy_team = "pretas" if team == "brancas" else "brancas"

        moves_searched = 0
        for move in ordered_actions:
            if time.time() - start_time >= time_limit or self.nodes_visited >= max_nodes:
                break

            clone = state.fast_clone()
            clone.execute_action(move)
            m_type = str(move.get("type", "")).lower()
            is_tactical = (
                m_type in ("attack", "stun")
                or str(move.get("spell_name", "")).lower() in (
                    "bone_v", "spectral_strike", "aimed_shot", "sentinel_shot",
                    "chain_lightning", "arcane_blast", "sniper_shot"
                )
            )

            # Late Move Reductions (LMR)
            do_lmr = (depth >= 3 and moves_searched >= 3 and not is_tactical)
            reduction = 1 if do_lmr else 0

            score, _ = self._negamax(
                state=clone,
                depth=depth - 1 - reduction,
                ply=ply + 1,
                alpha=-beta,
                beta=-alpha,
                team=enemy_team,
                start_time=start_time,
                time_limit=time_limit,
                max_nodes=max_nodes,
            )
            score = -score

            # Re-search at full depth if reduced search exceeded alpha
            if do_lmr and score > alpha:
                score, _ = self._negamax(
                    state=clone,
                    depth=depth - 1,
                    ply=ply + 1,
                    alpha=-beta,
                    beta=-alpha,
                    team=enemy_team,
                    start_time=start_time,
                    time_limit=time_limit,
                    max_nodes=max_nodes,
                )
                score = -score

            moves_searched += 1

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                self.cutoffs += 1
                # Record killer and history for quiet cutoffs
                m_type = str(move.get("type", "")).lower()
                if m_type not in ("attack", "stun"):
                    key = move_to_string_key(move)
                    self.killer_table.record_killer(ply, key)
                    start = move.get("start")
                    end = move.get("end")
                    if start and end and len(start) == 2 and len(end) == 2:
                        self.history_table.record_cutoff(tuple(start), tuple(end), depth)
                break

        # Store in TT
        if z_hash:
            if best_score <= initial_alpha:
                flag = TTFlag.UPPERBOUND
            elif best_score >= beta:
                flag = TTFlag.LOWERBOUND
            else:
                flag = TTFlag.EXACT
            self.tt.store(z_hash, depth, best_score, flag, best_move)

        return best_score, best_move


def ares_search_position(state: Any, max_depth: int = 3, time_budget: float = 1.0) -> dict[str, Any]:
    """Top-level convenience function for searching a position with AresEngine."""
    engine = AresEngine()
    return engine.search(state, max_depth=max_depth, time_limit=time_budget)
