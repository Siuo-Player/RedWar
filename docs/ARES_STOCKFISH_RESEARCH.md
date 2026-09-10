# Ares — Stockfish-guided research priorities

**Date:** 2026-09-10  
**Status:** research/preparation only  
**Canonical gate:** #372, after #371 closes

This document records the Ares search/evaluation research performed in parallel with the remaining gameplay gate. It does **not** promote the Ares phase or authorize an optimization before the #371 exit criteria are met.

## 1. Current Ares shape

The current C++ Ares search already has:

- alpha-beta/PVS;
- iterative deepening;
- transposition table;
- Zobrist position key with TWC included;
- killer/history ordering;
- action-specific history/killer ordering;
- bounded quiescence search with RedWar-specific forcing moves;
- node/time stopping;
- optional NNUE;
- special handling for consecutive STUN tactics.

The current search does **not** yet implement the major selective-search mechanisms that are standard in modern Stockfish-style search, such as LMR, null-move pruning, futility pruning and aspiration-window root iteration. This is a research observation, not a claim that each mechanism is automatically appropriate for RedWar.

## 2. Highest-priority finding: NNUE incremental path is present but evaluation still synchronizes

The codebase already contains incremental NNUE hooks for piece change, effect change, side to move and TWC. However, `evaluate.cpp` currently calls `redwar::nnue::sync_board()` before every NNUE evaluation. The source-level regression `tests/test_d_nnue_oracle_boundary.py` explicitly protects this full-sync oracle.

This creates a clear research/engineering seam:

```text
current:
search node
→ evaluate
→ scan/resynchronise board
→ NNUE inference

candidate:
root/position load
→ establish accumulator state once
→ make/unmake hooks maintain it
→ NNUE inference only
```

The change must first prove:

```text
incremental evaluation == full-sync evaluation
```

on the protected corpus and across make/unmake paths, before using the faster path as the production baseline.

## 3. Stockfish-guided search priorities

### S1 — incremental NNUE evaluation economics

Measure evaluations/second, nodes/second, fixed-node wall time, fixed-time depth, exact incremental/full-sync equality, make/unmake parity and effect-heavy positions. Do not promote based on NPS alone.

### S2 — Late Move Reductions (LMR)

Start conservatively: non-first/non-PV candidates, avoid forcing actions and special STUN-continuation contexts, use a small reduction, and full-depth re-search when a reduced search becomes relevant. This is a RedWar hypothesis, not a constant-for-constant Stockfish port.

### S3 — Aspiration windows

Use the previous iterative-deepening score as the centre of a narrow alpha-beta window, with explicit widening on fail-low/fail-high. Validate terminal scores, unstable tactics and the RedWar score scale.

### S4 — History / continuation information

Evaluate richer context-conditioned ordering using action type, spell identity, stun context, target relation and effect context rather than copying chess-specific piece semantics.

### S5 — Null-move pruning

Research candidate, **not default**. RedWar's one-action turns, timers, effects and stun continuation may invalidate the chess assumption behind a null move. First determine whether a sound semantic abstraction exists.

### S6 — Futility / late-move pruning / shallow pruning

Only after ordering/LMR evidence exists and only with protected tactical coverage. Measure nodes saved, omitted-action count, best-move changes and tactical failures.

### S7 — Transposition-table quality

Compare replacement policy, depth preference, generation/age, collision behaviour, TT-move reliability and hit rate under the RedWar state key.

### S8 — Quiescence / forcing frontier

Evaluate whether the forcing frontier captures attacks/captures, second-STUN threats, lethal Ignite interactions, forced spawns and critical terrain interactions. Do not import chess check/capture definitions blindly.

## 4. What to borrow from Stockfish — and what not to

Borrow methodology:

```text
small atomic patch
→ deterministic correctness/capability checks
→ controlled benchmark
→ independent strength test
→ keep only supported improvements
```

Do not borrow chess-specific semantics blindly: checks, castling, en-passant, promotion, chess SEE and chess material values have no direct RedWar equivalence.

## 5. Research references

- Stockfish source / current search: https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp
- Stockfish NNUE documentation: https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html
- Yu Nasu, **Efficiently Updatable Neural-Network-based Evaluation Functions for Computer Shogi** (2018).
- Jonathan Schaeffer, **The History Heuristic** (1983), DOI: 10.3233/ICG-1983-6305.
- Jonathan Schaeffer, **The history heuristic and alpha-beta search enhancements in practice** (1989), DOI: 10.1109/34.42858.
- Christian Donninger, **Null Move and Deep Search: Selective-search Heuristics for Obtuse Chess Programs** (1993), DOI: 10.3233/ICG-1993-16304.
- Michael Buro, **ProbCut: An Effective Selective Extension of the α-β Algorithm** (1995), DOI: 10.3233/ICG-1995-18202.
- Thomas Anantharaman, Murray Campbell & Feng-hsiung Hsu, **Singular extensions: Adding selectivity to brute-force searching** (1990), DOI: 10.1016/0004-3702(90)90073-9.
- **Efficiency of three forward-pruning techniques in shogi: Futility pruning, null-move pruning, and Late Move Reduction (LMR)** (2012), DOI: 10.1016/j.entcom.2011.11.003.

## 6. Current conclusion

The most promising first Ares work is **not** “add every Stockfish feature”. The rational sequence is:

```text
#371 close
    ↓
Ares correctness baseline
    ↓
NNUE incremental/full-sync equivalence + economics
    ↓
LMR experiment
    ↓
aspiration experiment
    ↓
richer history / ordering
    ↓
TT replacement study
    ↓
carefully scoped NMP / pruning studies
    ↓
independent Arena strength evidence
```

The strongest immediate engineering smell found during this review is the per-node NNUE full synchronization despite already having incremental hooks. It should be the first performance hypothesis tested once the Ares gate opens.

This sequence remains subordinate to `docs/ROADMAP.md` and #372. No Stockfish-inspired technique is accepted merely because it exists in Stockfish.
