# RedWar 1.0 — Parallel Execution Plan

**Date:** 2026-09-10  
**Status:** operational execution guide  
**Authority:** `docs/ROADMAP.md` remains the canonical phase/order document. This file defines how independent work packages can run in parallel without bypassing gates.

## Objective

Reach a trustworthy RedWar 1.0 as quickly as practical without creating false dependencies between unrelated work.

The project should be executed as a **dependency DAG**, not as a single serial to-do list:

```text
Foundation ─────┬─ Gameplay correctness ───┐
                ├─ Ares preparation ──────┼─ Ares strength
                ├─ Product preparation ───┤
                └─ Online preparation ────┘
                                             ↓
                                        Product 1.0
                                             ↓
                                         Online 1.0
                                             ↓
                                        Release 1.0
```

> **Parallelize investigation, tooling, tests, benchmarks and integration preparation whenever they do not require an upstream gate; serialize only the handoffs that genuinely depend on a stable contract.**

## Current parallel lanes

While #371 Gameplay is open:

| Lane | Work now | Promotion blocked by |
|---|---|---|
| G — Gameplay | #404/#405 and remaining rule-completeness regressions | #371 exit |
| A0 — Ares correctness | corpus, diagnostics, state readback, TT/node-budget conformance | #372 promotion |
| A1 — NNUE | incremental/full-sync parity and economics harness | #372 promotion |
| A2 — Search | LMR/aspiration/history/TT experiments from same baseline | #372 promotion |
| A3 — Evaluation | classical/NNUE ablation and feature-cost plan | #372 evidence |
| A4 — Arena | paired-colour protocol, hold-out and result manifests | strength claim |
| P — Product | UI/replay/telemetry validation | #373 promotion |
| O — Online | authoritative session/reconnect architecture | #374 promotion |
| R — Release | reproducible build, security and licensing preparation | #375 promotion |

Preparation never closes a later gate and never bypasses #371.

## Gameplay lane

### G1 — Close current correctness children

Finish #404/#405 so no-legal-action termination obtains its board-action answer from the canonical action-space and preserves all existing terminal precedence.

### G2 — Rule-completeness sweep

Exercise movement, attack, spells, passives, spawn/invocation, stun and second-stun death, fire/ice/terrain timing, lifespan/cooldown, surrender, no-legal-action, 50-turn TWC and terminal/win semantics.

Where Python and C++ implement the same rule, keep differential evidence.

### G3 — Deterministic gameplay corpus

Freeze representative RWEN positions and short action sequences for every critical mechanic. Reuse this corpus for Ares correctness, replay, telemetry and later online QA instead of duplicating fixtures.

## Ares preparation lane

### A0 — correctness baseline

Before strength experiments establish:

```text
same input state → same legal actions
make/unmake → identical relevant state
hash → reproducible identity
TT ON/OFF → equivalent result at fixed node budget
node budget → deterministic stopping
reference evaluation ↔ production evaluation
```

### A1 — NNUE incremental path

The first performance hypothesis is to remove the per-evaluation `sync_board()` scan while retaining it as an oracle. Split the work into:

```text
A1a parity campaign
A1b incremental evaluator implementation
A1c microbenchmark
A1d fixed-node/fixed-time comparison
A1e Arena validation when decision quality changes
```

Do not promote on NPS alone.

### A2 — move ordering

Run independent branches for stronger history, continuation/counter-context and TT-move quality. Never combine them before their individual effect is known.

### A3 — LMR

Start conservatively: later/non-PV/non-forcing moves, avoid special STUN continuation contexts, small reduction, and full-depth re-search when the reduced result becomes relevant.

### A4 — aspiration

Test iterative-deepening aspiration independently from LMR, with correct fail-low/fail-high widening and explicit terminal handling.

### A5 — TT quality

Evaluate replacement policy, depth preference, age/generation, collision diagnostics and TT-move usefulness one concept per branch.

### A6 — pruning

Investigate null-move, futility and late-move pruning only after ordering/LMR evidence exists. Null-move is not assumed valid for RedWar because turns advance effects/timers and stun continuation differs from chess semantics.

### A7 — quiescence

Measure the RedWar forcing frontier: attacks/captures, second-STUN threats, lethal Ignite interactions, forced spawns and critical terrain interactions.

### A8 — time management

Compare fixed-depth, fixed-node and fixed-time decision quality. Record best-move stability, depth, nodes and latency.

### A9 — evaluator

Keep classical evaluation and NNUE experiments separate. Never tune on the final hold-out corpus.

### A10 — strength

Only after correctness and candidate changes are stable:

```text
baseline vs candidate
+ colours alternated
+ identical ruleset
+ matched CPU/time/node budget
+ independent seeds/openings where appropriate
+ hold-out separation
+ uncertainty-aware Arena analysis
```

## Product preparation

The Battle UI architecture already exists. Validate responsive layouts, keyboard/focus, selected-hero persistence, hover/context semantics, illegal-destination recovery, Encyclopedia sourcing, multi-action choice, semantic non-colour cues and FrostMage/NEVADA stress scenes.

Replay/telemetry should remain a projection of authoritative canonical state:

```text
canonical action/state
→ event/replay record
→ deterministic reconstruction
→ analysis/telemetry
```

## Online preparation

Define the authority boundary before production networking:

```text
client command
→ authentication/session validation
→ canonical action resolution
→ rules validation
→ authoritative mutation
→ event/replay output
```

Design reconnect from deterministic replay/state reconstruction. Keep matchmaking, rating and game result as separate concerns.

## Release preparation

Prepare reproducible build documentation, dependency/security checks, licensing/provenance, failure/recovery observability and a release corpus covering rules, Ares, UI, replay and online failure paths.

## Safe parallelism

The fastest safe pattern is **parallel discovery, serial promotion**:

```text
same verified baseline
├── package A
├── package B
├── package C
└── package D

→ test independently
→ accept/reject independently
→ integrate winners one by one
→ revalidate the composition
```

Never stack unvalidated search concepts, and never let a preparation branch become a competing roadmap.

## Operating rule for autonomous agents

Before coding:

```text
read ROADMAP.md
→ read governing Issue
→ inspect current main
→ identify exact package
→ search existing branches/PRs
→ define one falsifiable change
```

After coding:

```text
tests
→ benchmark when relevant
→ Arena when claiming strength
→ inspect CI on exact head
→ document evidence
→ merge only validated work
```

Fast means removing artificial dependencies, reusing corpora and keeping patches atomic—not removing evidence.
