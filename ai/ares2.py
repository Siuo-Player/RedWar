"""Ares 2.0 AI Engine Search Enhancements for RedWar.

Implements Stockfish-inspired search heuristics:
- Transposition Table with Zobrist hashing & generational replacement strategies
- MVV-LVA (Most Valuable Victim - Least Valuable Attacker) move ordering
  with dedicated 2-hit stun lethal kill prioritization
- Tactical Check-Response Move Ordering: neutralizing executioners and blocking sniper rays
- Capture History Table (Capthist) as fine-grained tactical tie-breaker
- 2-Slot Killer Move Ordering per ply
- Countermove Heuristic for quiet refutations
- History Heuristic table with Stockfish gravity aging formula
- Dynamic Clock Allocation (Time Management)
- Quiescence Search on tactical captures and stun attacks with Delta Pruning
- Dynamic Widening Aspiration Windows
- Tactical Threat Detection & Singular/Threat Extension (+1 ply when stunned ally under fire)
- Reverse Futility Pruning (Static Null-Move Pruning)
- Adaptive Null-Move Pruning with RedWar stun-safety guards
- Late Move Reductions (LMR) with killer, countermove & threat protection
- Full Iterative Deepening Negamax Search Engine with Alpha-Beta Pruning
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import math
import time
from typing import Any, Dict, List, Optional, Tuple, Set

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
    generation: int = 0
    best_move: Optional[dict[str, Any]] = None


class TranspositionTable:
    """Fixed-capacity hash table indexed by Zobrist hash with generational replacement."""

    def __init__(self, size_power_of_two: int = 16):
        self.capacity = 1 << size_power_of_two
        self.mask = self.capacity - 1
        self._table: list[Optional[TTEntry]] = [None] * self.capacity
        self.hits = 0
        self.stores = 0
        self.generation = 0

    def new_search(self) -> None:
        """Advance generation counter so fresh search results take precedence over stale plies."""
        self.generation = (self.generation + 1) & 0xFF

    def store(
        self,
        hash_key: int,
        depth: int,
        score: float,
        flag: TTFlag,
        best_move: Optional[dict[str, Any]] = None,
    ) -> None:
        idx = hash_key & self.mask
        existing = self._table[idx]
        replace = False

        if existing is None:
            replace = True
        elif existing.generation != self.generation:
            # Stale generation entry: always replace with current search data
            replace = True
        elif depth >= existing.depth:
            # Same generation: depth-preferred replacement
            replace = True
        elif existing.hash_key != hash_key and depth >= existing.depth - 1:
            # Collision from another position: replace within tolerance
            replace = True

        if replace:
            self._table[idx] = TTEntry(
                hash_key=hash_key,
                depth=depth,
                score=score,
                flag=flag,
                generation=self.generation,
                best_move=best_move,
            )
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
        self.generation = 0


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


@dataclass
class CounterMoveTable:
    """Records quiet refutation countermoves indexed by the opponent's previous move key."""
    table: dict[str, str] = field(default_factory=dict)

    def record_countermove(self, prev_move_key: str, refutation_key: str) -> None:
        if prev_move_key and refutation_key:
            self.table[prev_move_key] = refutation_key

    def get_countermove(self, prev_move_key: Optional[str]) -> Optional[str]:
        if not prev_move_key:
            return None
        return self.table.get(prev_move_key)

    def clear(self) -> None:
        self.table.clear()


class CaptureHistoryTable:
    """Tracks tactical captures and attacks that generated beta cutoffs (Stockfish Capthist)."""

    def __init__(self):
        self._table: dict[tuple[str, str, tuple[int, int]], int] = {}

    def record_cutoff(self, attacker: str, target: str, to_sq: tuple[int, int], depth: int) -> None:
        key = (attacker, target, to_sq)
        bonus = depth * depth
        curr = self._table.get(key, 0)
        delta = bonus - (curr * abs(bonus) // 16384)
        self._table[key] = max(-8_000, min(8_000, curr + delta))

    def get_score(self, attacker: str, target: str, to_sq: tuple[int, int]) -> int:
        return self._table.get((attacker, target, to_sq), 0)

    def decay(self, factor: float = 0.90) -> None:
        for k in list(self._table.keys()):
            val = int(self._table[k] * factor)
            if val == 0:
                del self._table[k]
            else:
                self._table[k] = val

    def clear(self) -> None:
        self._table.clear()


class HistoryTable:
    """Tracks quiet moves that generated beta cutoffs with Stockfish gravity aging."""

    def __init__(self):
        self._history: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}

    def record_cutoff(self, from_sq: tuple[int, int], to_sq: tuple[int, int], depth: int) -> None:
        key = (from_sq, to_sq)
        bonus = depth * depth
        curr = self._history.get(key, 0)
        # Stockfish gravity formula: avoids saturation ceiling
        delta = bonus - (curr * abs(bonus) // 16384)
        self._history[key] = max(-8_000, min(8_000, curr + delta))

    def get_score(self, from_sq: tuple[int, int], to_sq: tuple[int, int]) -> int:
        return self._history.get((from_sq, to_sq), 0)

    def decay(self, factor: float = 0.90) -> None:
        """Decay historical scores between moves to adapt to positional shifts."""
        for k in list(self._history.keys()):
            val = int(self._history[k] * factor)
            if val == 0:
                del self._history[k]
            else:
                self._history[k] = val

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
        return 350_000 + (victim_cost * 100) - attacker_cost
    else:
        # Applying first stun to target
        return 130_000 + (victim_cost * 25) - attacker_cost


def is_under_imminent_threat(state: Any, team: str) -> bool:
    """Check if any allied piece with stun_timer > 0 is exposed to immediate enemy execution."""
    board = getattr(state, "board", [])
    if not board:
        return False

    stunned_allies = []
    enemy_strikers = []
    for r in range(len(board)):
        for c in range(len(board[0])):
            p = board[r][c]
            if p:
                if p.team == team and getattr(p, "stun_timer", 0) > 0:
                    stunned_allies.append((r, c, p))
                elif p.team != team:
                    enemy_strikers.append((r, c, p))

    if not stunned_allies or not enemy_strikers:
        return False

    for ar, ac, _ in stunned_allies:
        for er, ec, enemy in enemy_strikers:
            # Adjacent melee strike (Chebyshev distance <= 1)
            if max(abs(ar - er), abs(ac - ec)) <= 1:
                return True
            # Sniper in direct orthogonal line-of-fire within 3 squares
            enemy_name = getattr(enemy, "name", "")
            if enemy_name in ("Marksman", "Ranger", "Sentinel") and (ar == er or ac == ec) and 1 <= max(abs(ar - er), abs(ac - ec)) <= 3:
                return True

    return False


def get_imminent_threat_targets_and_blocks(state: Any, team: str) -> tuple[Set[tuple[int, int]], Set[tuple[int, int]]]:
    """Find enemy executioners threatening stunned allies, and block squares along sniper lines."""
    board = getattr(state, "board", [])
    if not board:
        return set(), set()

    stunned_allies = []
    enemy_strikers = []
    for r in range(len(board)):
        for c in range(len(board[0])):
            p = board[r][c]
            if p:
                if p.team == team and getattr(p, "stun_timer", 0) > 0:
                    stunned_allies.append((r, c, p))
                elif p.team != team:
                    enemy_strikers.append((r, c, p))

    threat_targets: Set[tuple[int, int]] = set()
    block_squares: Set[tuple[int, int]] = set()

    for ar, ac, _ in stunned_allies:
        for er, ec, enemy in enemy_strikers:
            dist = max(abs(ar - er), abs(ac - ec))
            if dist <= 1:
                threat_targets.add((er, ec))
            enemy_name = getattr(enemy, "name", "")
            if enemy_name in ("Marksman", "Ranger", "Sentinel") and (ar == er or ac == ec) and 1 <= dist <= 3:
                threat_targets.add((er, ec))
                step_r = 0 if ar == er else (1 if er > ar else -1)
                step_c = 0 if ac == ec else (1 if ec > ac else -1)
                curr_r, curr_c = ar + step_r, ac + step_c
                while (curr_r, curr_c) != (er, ec):
                    block_squares.add((curr_r, curr_c))
                    curr_r += step_r
                    curr_c += step_c

    return threat_targets, block_squares


def sort_moves_ares2(
    moves: list[dict[str, Any]],
    ply: int,
    killer_table: KillerMoveTable,
    history_table: HistoryTable,
    counter_table: Optional[CounterMoveTable] = None,
    capture_history: Optional[CaptureHistoryTable] = None,
    prev_move_key: Optional[str] = None,
    tt_best_move: Optional[str] = None,
    pv_best_move: Optional[str] = None,
    state: Optional[Any] = None,
    enable_threat_ordering: bool = True,
) -> list[dict[str, Any]]:
    """Order candidate legal moves using PV, TT, MVV-LVA + Capthist, Threat Responses, Killers, Countermove, History."""
    killer1, killer2 = killer_table.get_killers(ply)
    counter_move = counter_table.get_countermove(prev_move_key) if counter_table and prev_move_key else None

    team = "brancas" if getattr(state, "white_to_move", True) else "pretas"
    threat_targets, block_squares = (
        get_imminent_threat_targets_and_blocks(state, team)
        if (state is not None and enable_threat_ordering) else (set(), set())
    )

    def score_move(m: dict[str, Any]) -> int:
        key = move_to_string_key(m)
        if pv_best_move and key == pv_best_move:
            return 2_000_000
        if tt_best_move and key == tt_best_move:
            return 1_000_000

        m_type = str(m.get("type", "")).lower()
        end = m.get("end")
        end_sq = tuple(end) if (end and len(end) == 2) else None

        # Tactical captures and attacks prioritized via MVV-LVA + bounded Capture History
        if state is not None and (m_type == "attack" or (m_type == "spell" and m.get("spell_name"))):
            score = mvv_lva_score(state, m)
            if score > 0:
                if capture_history is not None:
                    start = m.get("start")
                    if start and end and len(start) == 2 and len(end) == 2:
                        attacker_p = state.board[start[0]][start[1]]
                        target_p = state.board[end[0]][end[1]]
                        if attacker_p and target_p:
                            raw_capthist = capture_history.get_score(
                                getattr(attacker_p, "name", ""),
                                getattr(target_p, "name", ""),
                                tuple(end),
                            )
                            capthist_bonus = max(-500, min(500, raw_capthist))
                            score += capthist_bonus
                return score

        # Check-response ordering: neutralizing executioner or blocking sniper line
        if enable_threat_ordering:
            if end_sq and end_sq in threat_targets:
                return 280_000
            if end_sq and end_sq in block_squares:
                return 80_000

        if m_type == "attack":
            return 100_000
        if m_type == "stun":
            return 50_000
        if m_type == "spell":
            return 45_000

        # Quiet moves: Killer 1 > Countermove > Killer 2
        if key == killer1:
            return 20_000
        if counter_move and key == counter_move:
            return 19_000
        if key == killer2:
            return 18_000

        start = m.get("start")
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
    capture_history: Optional[CaptureHistoryTable] = None,
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

    # Delta Pruning: if even capturing the highest-cost piece cannot raise alpha, prune
    BIG_DELTA = 65.0
    if stand_pat + BIG_DELTA < alpha:
        return alpha

    # Generate only tactical moves (attacks, lethal spells)
    all_actions = to_legacy_dicts(legal_actions(state))
    tactical_moves = [
        m for m in all_actions
        if str(m.get("type", "")).lower() in ("attack", "stun") or
        (str(m.get("type", "")).lower() == "spell" and m.get("spell_name") in (
            "chain_lightning", "arcane_blast", "aimed_shot", "sentinel_shot",
            "spectral_strike", "bone_v", "sniper_shot"
        ))
    ]

    if not tactical_moves:
        return alpha

    # Order tactical moves by MVV-LVA + bounded Capture History
    def score_tactical(m: dict[str, Any]) -> int:
        score = mvv_lva_score(state, m)
        if capture_history is not None:
            start = m.get("start")
            end = m.get("end")
            if start and end and len(start) == 2 and len(end) == 2:
                attacker_p = state.board[start[0]][start[1]]
                target_p = state.board[end[0]][end[1]]
                if attacker_p and target_p:
                    raw_bonus = capture_history.get_score(
                        getattr(attacker_p, "name", ""),
                        getattr(target_p, "name", ""),
                        tuple(end),
                    )
                    score += max(-500, min(500, raw_bonus))
        return score

    tactical_moves.sort(key=score_tactical, reverse=True)

    enemy_team = "pretas" if team == "brancas" else "brancas"
    for move in tactical_moves:
        clone = state.fast_clone()
        clone.execute_action(move)
        score = -quiescence_search(clone, -beta, -alpha, enemy_team, q_depth + 1, max_qdepth, evaluator, capture_history)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


class AresEngine:
    """State-of-the-art Ares AI Search Engine for RedWar."""

    def __init__(
        self,
        tt_size_power: int = 16,
        enable_threat_extension: bool = True,
        enable_threat_ordering: bool = True,
        enable_countermoves: bool = True,
        enable_capthist: bool = True,
        enable_delta_pruning: bool = True,
    ):
        self.tt = TranspositionTable(size_power_of_two=tt_size_power)
        self.killer_table = KillerMoveTable()
        self.counter_table = CounterMoveTable()
        self.capture_history = CaptureHistoryTable()
        self.history_table = HistoryTable()
        self.evaluator = RedWarDomainEvaluator()
        self.nodes_visited = 0
        self.cutoffs = 0
        self.enable_threat_extension = enable_threat_extension
        self.enable_threat_ordering = enable_threat_ordering
        self.enable_countermoves = enable_countermoves
        self.enable_capthist = enable_capthist
        self.enable_delta_pruning = enable_delta_pruning

    def reset(self) -> None:
        self.tt.clear()
        self.killer_table.clear()
        self.counter_table.clear()
        self.capture_history.clear()
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
        """Perform iterative deepening negamax search with dynamic aspiration windows."""
        start_time = time.time()
        self.nodes_visited = 0
        self.cutoffs = 0
        best_overall_move: Optional[dict[str, Any]] = None
        best_overall_score = -float("inf")
        team = "brancas" if getattr(state, "white_to_move", True) else "pretas"
        completed_depth = 0

        # Advance TT generation counter for fresh search prioritization
        self.tt.new_search()

        # Opening book probe (active in multi-piece opening formations)
        total_pieces = sum(1 for row in getattr(state, "board", []) for p in row if p is not None)
        if use_opening_book and total_pieces >= 6 and len(getattr(state, "move_log", [])) <= 8:
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

        # Iterative Deepening with Dynamic Geometric Aspiration Windows & PV extraction
        for depth in range(1, max_depth + 1):
            if time.time() - start_time >= time_limit or self.nodes_visited >= max_nodes:
                break

            pv_key = move_to_string_key(best_overall_move) if best_overall_move else None

            # Dynamic Aspiration Window for depth >= 2
            if depth >= 2 and best_overall_score > -40_000:
                delta = 75.0  # Scaled to RedWar piece evaluations (~0.4 piece value)
                alpha = best_overall_score - delta
                beta = best_overall_score + delta
                failed_attempts = 0

                while True:
                    score, move = self._negamax(
                        state=state,
                        depth=depth,
                        ply=0,
                        alpha=alpha,
                        beta=beta,
                        team=team,
                        start_time=start_time,
                        time_limit=time_limit,
                        max_nodes=max_nodes,
                        pv_best_move=pv_key,
                        prev_move_key=None,
                    )

                    if time.time() - start_time >= time_limit or self.nodes_visited >= max_nodes:
                        break

                    if score <= alpha:
                        failed_attempts += 1
                        if failed_attempts >= 2:
                            alpha = -float("inf")
                        else:
                            delta *= 1.75
                            alpha = max(-float("inf"), score - delta)
                    elif score >= beta:
                        failed_attempts += 1
                        if failed_attempts >= 2:
                            beta = float("inf")
                        else:
                            delta *= 1.75
                            beta = min(float("inf"), score + delta)
                    else:
                        break
            else:
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
                    pv_best_move=pv_key,
                    prev_move_key=None,
                )

            if move is not None:
                best_overall_move = move
                best_overall_score = score
                completed_depth = depth

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
        do_null: bool = True,
        pv_best_move: Optional[str] = None,
        prev_move_key: Optional[str] = None,
    ) -> tuple[float, Optional[dict[str, Any]]]:
        self.nodes_visited += 1

        if self.nodes_visited % 512 == 0 and (time.time() - start_time >= time_limit or self.nodes_visited >= max_nodes):
            return self.evaluator.evaluate(state, team), None

        # Detect imminent mortal stun execution threat (RedWar check-analogue)
        imminent_threat = is_under_imminent_threat(state, team)

        # Tactical Threat Extension (+1 ply):
        # When an allied stunned unit is in the direct line-of-fire or adjacent to an executioner,
        # extend depth by 1 ply so the engine sees tactical rescues/blocks before leaf evaluation
        effective_depth = (
            depth + 1
            if (self.enable_threat_extension and imminent_threat and ply < 16 and depth < 6)
            else depth
        )

        # Transposition table probe
        z_hash = getattr(state, "current_hash", 0)
        tt_best_move_str: Optional[str] = None
        tt_entry = self.tt.probe(z_hash) if z_hash else None
        if tt_entry is not None and tt_entry.depth >= effective_depth:
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
        if effective_depth <= 0:
            capthist_ref = self.capture_history if self.enable_capthist else None
            q_score = quiescence_search(
                state, alpha, beta, team, evaluator=self.evaluator, capture_history=capthist_ref
            )
            return q_score, None

        # Reverse Futility Pruning (Static Null-Move Pruning) for shallow depths (depth 1..2)
        # Strictly disabled if under imminent threat or any ally is stunned
        if effective_depth <= 2 and ply > 0 and beta < 30_000 and not imminent_threat:
            has_stunned_ally = any(
                p and p.team == team and getattr(p, "stun_timer", 0) > 0
                for row in getattr(state, "board", []) for p in row
            )
            if not has_stunned_ally:
                margin = effective_depth * 45.0
                static_eval = self.evaluator.evaluate(state, team)
                if static_eval - margin >= beta:
                    self.cutoffs += 1
                    return static_eval - margin, None

        enemy_team = "pretas" if team == "brancas" else "brancas"

        # Adaptive Null-Move Pruning (NMP) with RedWar tactical danger safeguards
        if do_null and effective_depth >= 3 and ply > 0 and not imminent_threat:
            has_stunned_ally = any(
                p and p.team == team and getattr(p, "stun_timer", 0) > 0
                for row in getattr(state, "board", []) for p in row
            )
            total_active_allies = sum(
                1 for row in getattr(state, "board", []) for p in row if p and p.team == team
            )
            if not has_stunned_ally and total_active_allies >= 2:
                # Stockfish-inspired adaptive R: R=3 for deep searches (depth >= 6), R=2 for depth 3..5
                R = 3 if effective_depth >= 6 else 2
                clone = state.fast_clone()
                clone.white_to_move = not clone.white_to_move
                null_score, _ = self._negamax(
                    state=clone,
                    depth=effective_depth - 1 - R,
                    ply=ply + 1,
                    alpha=-beta,
                    beta=-beta + 1,
                    team=enemy_team,
                    start_time=start_time,
                    time_limit=time_limit,
                    max_nodes=max_nodes,
                    do_null=False,
                    prev_move_key=None,
                )
                null_score = -null_score
                if null_score >= beta:
                    self.cutoffs += 1
                    return beta, None

        raw_actions = to_legacy_dicts(legal_actions(state))
        if not raw_actions:
            state.check_game_over()
            if getattr(state, "game_over", False):
                return -50_000.0, None  # Loss
            return 0.0, None  # Stalemate / draw

        # Move ordering with PV, TT, MVV-LVA + Capthist, Threat Responses, Killers, Countermove, History
        ordered_actions = sort_moves_ares2(
            moves=raw_actions,
            ply=ply,
            killer_table=self.killer_table,
            history_table=self.history_table,
            counter_table=self.counter_table if self.enable_countermoves else None,
            capture_history=self.capture_history if self.enable_capthist else None,
            prev_move_key=prev_move_key,
            tt_best_move=tt_best_move_str,
            pv_best_move=pv_best_move,
            state=state,
            enable_threat_ordering=self.enable_threat_ordering,
        )

        best_move = None
        best_score = -float("inf")
        initial_alpha = alpha

        killer1, killer2 = self.killer_table.get_killers(ply)
        counter_cand = (
            self.counter_table.get_countermove(prev_move_key)
            if (self.enable_countermoves and prev_move_key) else None
        )
        moves_searched = 0

        for move in ordered_actions:
            if time.time() - start_time >= time_limit or self.nodes_visited >= max_nodes:
                break

            clone = state.fast_clone()
            clone.execute_action(move)
            child_prev_key = move_to_string_key(move)
            m_type = str(move.get("type", "")).lower()
            is_tactical = (
                m_type in ("attack", "stun")
                or str(move.get("spell_name", "")).lower() in (
                    "bone_v", "spectral_strike", "aimed_shot", "sentinel_shot",
                    "chain_lightning", "arcane_blast", "sniper_shot"
                )
            )

            # Check killer move, countermove, and history safety guards
            key = child_prev_key
            is_killer = (key == killer1 or key == killer2)
            is_counter = (key == counter_cand) if counter_cand else False
            start = move.get("start")
            end = move.get("end")
            hist_score = self.history_table.get_score(tuple(start), tuple(end)) if (start and end and len(start) == 2 and len(end) == 2) else 0

            # Late Move Reductions (LMR): never reduce when in imminent threat
            do_lmr = (effective_depth >= 3 and moves_searched >= 3 and not is_tactical and not is_killer and not is_counter and not imminent_threat and hist_score < 3000)
            reduction = 2 if (do_lmr and effective_depth >= 5 and moves_searched >= 8) else (1 if do_lmr else 0)

            score, _ = self._negamax(
                state=clone,
                depth=effective_depth - 1 - reduction,
                ply=ply + 1,
                alpha=-beta,
                beta=-alpha,
                team=enemy_team,
                start_time=start_time,
                time_limit=time_limit,
                max_nodes=max_nodes,
                prev_move_key=child_prev_key,
            )
            score = -score

            # Re-search at full depth if reduced search exceeded alpha
            if do_lmr and score > alpha:
                score, _ = self._negamax(
                    state=clone,
                    depth=effective_depth - 1,
                    ply=ply + 1,
                    alpha=-beta,
                    beta=-alpha,
                    team=enemy_team,
                    start_time=start_time,
                    time_limit=time_limit,
                    max_nodes=max_nodes,
                    prev_move_key=child_prev_key,
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
                # Record killer, countermove, and history for quiet cutoffs, or capture history for tactical cutoffs
                m_type = str(move.get("type", "")).lower()
                start = move.get("start")
                end = move.get("end")
                if m_type not in ("attack", "stun") and not move.get("spell_name"):
                    key = move_to_string_key(move)
                    self.killer_table.record_killer(ply, key)
                    if self.enable_countermoves and prev_move_key:
                        self.counter_table.record_countermove(prev_move_key, key)
                    if start and end and len(start) == 2 and len(end) == 2:
                        self.history_table.record_cutoff(tuple(start), tuple(end), effective_depth)
                else:
                    if self.enable_capthist and start and end and len(start) == 2 and len(end) == 2:
                        attacker_p = state.board[start[0]][start[1]]
                        target_p = state.board[end[0]][end[1]]
                        if attacker_p and target_p:
                            self.capture_history.record_cutoff(
                                getattr(attacker_p, "name", ""),
                                getattr(target_p, "name", ""),
                                tuple(end),
                                effective_depth,
                            )
                break

        # Store in TT
        if z_hash:
            if best_score <= initial_alpha:
                flag = TTFlag.UPPERBOUND
            elif best_score >= beta:
                flag = TTFlag.LOWERBOUND
            else:
                flag = TTFlag.EXACT
            self.tt.store(z_hash, effective_depth, best_score, flag, best_move)

        return best_score, best_move


def ares_search_position(state: Any, max_depth: int = 3, time_budget: float = 1.0) -> dict[str, Any]:
    """Top-level convenience function for searching a position with AresEngine."""
    engine = AresEngine()
    return engine.search(state, max_depth=max_depth, time_limit=time_budget)
