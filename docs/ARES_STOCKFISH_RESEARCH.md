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

The codebase already contains incremental NNUE hooks for:

```text
piece change
→ accumulator delta

effect change
→ accumulator delta

side to move change
→ feature delta

twc change
→ feature delta
```

However, `evaluate.cpp` currently calls `redwar::nnue::sync_board()` before every NNUE evaluation. The source-level regression `tests/test_d_nnue_oracle_boundary.py` explicitly protects this full-sync oracle.

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

This is directly aligned with the NNUE design principle described by Stockfish: sparse features and incremental accumulator updates exist specifically to avoid rebuilding the first layer for every evaluation. Stockfish's documentation also describes storing accumulators with search-position state so the incremental representation follows the search tree.

The change must first prove:

```text
incremental evaluation == full-sync evaluation
```

on the protected corpus and across make/unmake paths, before using the faster path as the production baseline.

## 3. Stockfish-guided search priorities

The first experiments after the gameplay gate should be ordered by expected search leverage and RedWar-specific risk.

### S1 — incremental NNUE evaluation economics

First priority because it attacks evaluation overhead without changing the game-theoretic search decisions.

Measure:

- evaluations/second;
- nodes/second;
- wall-clock to fixed node budget;
- fixed-time reached depth;
- incremental/full-sync score equality;
- make/unmake parity;
- effect-heavy positions.

Do not promote based on NPS alone; compare decision quality under controlled budgets.

### S2 — Late Move Reductions (LMR)

LMR is a high-value candidate because Ares currently searches every move at essentially the full child depth.

Candidate first experiment:

- apply only after a small number of earlier moves;
- avoid the first move/PV move;
- avoid forcing RedWar actions;
- avoid moves entering special STUN-continuation contexts;
- reduce by a small depth amount;
- re-search at full depth when the reduced search raises alpha / threatens a cutoff.

The basic Stockfish principle is to spend less search on moves that move ordering predicts are unlikely to improve the node. Official Stockfish documentation identifies LMR as a core selective-search mechanism; literature also studies LMR together with null-move and futility pruning in non-chess game-tree search.

This must be treated as a hypothesis for RedWar, not copied as a constant-for-constant port from chess.

### S3 — Aspiration windows

Use the previous iterative-deepening score as a centre for a narrow alpha-beta window, widening/researching after fail-low/fail-high.

This changes search economics rather than the semantics of the game and should be relatively low-risk once root scores are stable.

Require explicit handling of:

- terminal scores;
- unstable tactical positions;
- changing best move;
- RedWar score scale.

### S4 — History / continuation information

Ares already has basic history and action-specific history. The next question is whether richer context-conditioned statistics can improve ordering:

- continuation history;
- counter-move style information;
- capture/action history separated by tactical class;
- bonuses/penalties for searched quiet alternatives.

The classic history-heuristic literature shows that dynamic move ordering can materially reduce search cost. Modern Stockfish has substantially richer history structures than a single source/destination table.

The RedWar adaptation should be semantic rather than syntactic: action type, spell identity, stun context, target relation and effect context may matter more than chess piece identities.

### S5 — Null-move pruning

Research candidate, **not default**.

RedWar may have positions where “passing” is strategically unlike chess null moves, especially because:

- every side has exactly one action per turn;
- there are stun continuation mechanics;
- effects/timers progress with turns;
- zugzwang-like situations may differ materially from chess.

Therefore first determine whether there is a sound RedWar null-move abstraction. If there is no valid semantic equivalent, do not introduce NMP merely because Stockfish uses it.

### S6 — Futility / late-move pruning / shallow pruning

These can save substantial nodes but are riskier because they actually discard candidate actions.

Only investigate after LMR and move-ordering evidence is available and only with protected tactical coverage.

Measure:

```text
nodes saved
omitted-action count
best-move changes
tactical failures
```

### S7 — Transposition-table quality

The current table is a direct indexed one-slot array. Research should compare:

- replacement policy;
- depth-preferred replacement;
- generation/age information;
- collision behaviour;
- TT move reliability;
- hit rate under RedWar's state key including TWC.

This is important because better TT usage can improve both ordering and search economy without requiring new domain heuristics.

### S8 — Quiescence / forcing frontier

The current qsearch already has a RedWar-specific forcing definition. Research whether the forcing set is complete enough and economically bounded.

Potential classes:

- attacks/captures;
- second-STUN threats;
- lethal Ignite interactions;
- immediate forced spawns;
- tactical terrain interactions.

Do not blindly copy chess's “captures + checks” frontier.

## 4. What to borrow from Stockfish — and what not to

Borrow methodology and experimentally validated architecture patterns:

```text
small atomic patch
→ deterministic bench/capability checks
→ controlled strength test
→ keep only statistically supported improvements
```

Stockfish's current contributor guidance explicitly treats search-changing patches as functional changes that require testing, and Fishtest uses sequential statistical tests to avoid promoting changes on anecdotal matches.

Do **not** borrow chess-specific semantics blindly:

- checks are not RedWar forcing actions;
- castling/en-passant/promotion logic has no direct analogue;
- null move may have a different meaning;
- chess SEE is not automatically the correct tactical filter;
- chess material values are not RedWar's stun/mortality semantics.

## 5. Research papers / primary references

### Stockfish / NNUE

- Stockfish developers, **Stockfish source / current search implementation**: https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp
- Stockfish developers, **NNUE documentation**: https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html
- Yu Nasu, **Efficiently Updatable Neural-Network-based Evaluation Functions for Computer Shogi** (2018): https://github.com/asdfjkl/nnue

### Search heuristics

- Jonathan Schaeffer, **The History Heuristic** (1983), ICGA Journal, DOI: 10.3233/ICG-1983-6305.
- Jonathan Schaeffer, **The history heuristic and alpha-beta search enhancements in practice** (1989), IEEE TPAMI 11(11), pp. 1203–1212, DOI: 10.1109/34.42858.
- Christian Donninger, **Null Move and Deep Search: Selective-search Heuristics for Obtuse Chess Programs** (1993), ICGA Journal 16(3), pp. 137–143, DOI: 10.3233/ICG-1993-16304.
- Michael Buro, **ProbCut: An Effective Selective Extension of the α-β Algorithm** (1995), ICGA Journal 18(2), pp. 71–76, DOI: 10.3233/ICG-1995-18202.
- Thomas Anantharaman, Murray Campbell & Feng-hsiung Hsu, **Singular extensions: Adding selectivity to brute-force searching** (1990), Artificial Intelligence 43(1), pp. 99–109, DOI: 10.1016/0004-3702(90)90073-9.
- **Efficiency of three forward-pruning techniques in shogi: Futility pruning, null-move pruning, and Late Move Reduction (LMR)** (2012), *Entertainment Computing* 3(3), pp. 51–57, DOI: 10.1016/j.entcom.2011.11.003.

## 6. Current conclusion

The most promising first Ares work is **not** “add every Stockfish feature”.

The rational sequence is:

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
