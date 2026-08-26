# Ares — AI Engine

## Objective

Ares is a search engine specialized for RedWar. The objective is to improve **strength and/or speed** under comparable conditions and reproducible evidence.

The methodology is inspired by Stockfish: isolated changes, clear responsibility boundaries, attention to the hot path and validation through tests, benchmarks and statistical evidence before accepting a strength claim.

## Current-state authority

This document describes the current Ares architecture and implementation contract. Dated decisions and audits explain why individual changes happened; they do not override the current contract.

The current `main` contains the Ares search/evaluation infrastructure after the post-#54 development sequence. Historical PR #49 was closed without merge and is not part of the current architecture.

## Observability and information model

The current local game-mode contract is **resolved**, not an open dependency.

The authoritative specification is [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md). It defines:

```text
DRAFT / setup
    opponent army + starting positions are hidden

BATALHA
    battle board state is public
    Ares may receive the complete battle state
```

This matches the current local flow: the opponent draft is materialized into `GameState` before battle begins, and Ares is invoked during `BATALHA`. `GameState.to_rwen()` therefore provides the complete battle representation used by the current local Ares path.

Do not reinterpret the implementation as information leakage during battle: under the current local rules, the battle state is public. Conversely, a future online/variant mode must define a separate observation boundary and must not expose the local full-state representation over the network by accident.

The historical discovery and decision remain in [`DECISIONS/2026-08-25-imperfect-information-observability-audit.md`](DECISIONS/2026-08-25-imperfect-information-observability-audit.md). It is rationale, not a competing contract.

## Search architecture

The C++ engine is the main hot path and uses alpha-beta/PVS, transposition table, Zobrist hashing, iterative deepening, killer/history heuristics, move ordering, quiescence/tactical search and bounded node/time search.

Search remains independent from the concrete evaluation implementation.

## RPG state

RedWar is not chess. State includes pieces, stun timer, lifespan, spawn cooldown, terrain effects, TWC and side to move.

The mandatory reversibility property remains:

```text
S --make(M)--> S'
S' --unmake(M)--> S
```

Restoration covers pieces, effects, hash, evaluation material, counters and the derived state covered by tests.

## Classical evaluation

The classical evaluation uses material, PST, stun state, lifespan, TWC and RedWar-specific terms. `FrostMage` remains a useful tactical sanity check.

Terms depending on multiple squares must not be treated as a local incremental accumulator without an explicit update mechanism.

## NNUE RPG

The `main` contains an NNUE-style infrastructure adapted to the RPG rather than copying Stockfish HalfKP. Features represent:

- piece + square + relative team;
- stun timer;
- lifespan;
- spawn cooldown;
- terrain effects;
- TWC;
- side to move.

The binary format is versioned as `RWNUE002`, with metadata validation in the C++ loader.

NNUE remains optional in this phase. Without a loaded model, Ares retains classical evaluation.

The current implementation uses full synchronization as the **correctness baseline**. Incremental update primitives exist in the NNUE module, but they are not yet connected to real `BoardState` transitions in the hot path. The next NNUE block must make that connection and measure the actual gain against full refresh; existence of an incremental function is not itself evidence of a performance gain.

Any future information-hidden variant must also enforce the relevant observation contract in NNUE inputs; restricting only the search root is insufficient.

## Data and training

The pipeline is:

```text
real positions / self-play / Arena
        ↓
RWEN + teacher scores/results
        ↓
sparse features
        ↓
optional PyTorch training
        ↓
quantization
        ↓
RWNUE002
        ↓
benchmark + Arena
```

`tools/nnue/generate_teacher.py` derives teacher data from the explicit classical evaluator. The bootstrap model exists for compatibility only.

## Tactical benchmarks

`tools/analytics/tactical_benchmark_suite.py` provides a deterministic harness independent of search implementation. Each position should be validated at a high budget before entering the suite and then measured at progressively smaller budgets.

FrostMage remains a reference case, not a definition of global strength.

Benchmark coverage must expand across the mechanics taxonomy and include independent/randomized or real-game-derived states to avoid overfitting a single action distribution.

## Arena and strength evidence

Arena has three distinct responsibilities:

1. execute controlled games;
2. store raw results/provenance;
3. analyse the records afterwards.

`tools/analytics/arena_tournament.py` performs execution/storage. Analysis tools operate on recorded games without silently replaying them.

The current strength estimator is an **Elo-compatible engineering baseline**. Paired-game/pentanomial analysis, protected hold-out validation and sequential testing are part of the measurement framework, but the isolated SPRT implementation is not yet the automatic promotion authority.

Arena evidence must distinguish:

```text
regression
  development
  protected hold-out
```

Game validity and termination provenance are part of the evidence contract. Invalid, blocked or max-ply observations must not silently become draws or contaminate strength inference.

The current Arena workflow also keeps hold-out execution separate from promotion Arena execution.

## CI and benchmarking

`auto_balancer.yml` validates balance tooling/build/test paths. `ai_arena.yml` provides A/B AI comparison under controlled rules and node budgets.

Arena promotion must not be inferred from documentation, tooling-only changes or deterministic benchmark capability alone.

For a meaningful AI change, compare at least:

- reference best moves;
- nodes/elapsed time/NPS;
- relevant memory cost;
- valid Arena result;
- state reversibility/correctness;
- observability compliance where applicable.

## Promotion criteria for NNUE

NNUE should only become default when:

1. correctness tests remain green;
2. Python/C++ feature layout remains identical;
3. loading and inference are deterministic;
4. a real trained network exists;
5. evaluation cost/NPS is measured against the classical baseline;
6. reference positions and best moves do not regress materially;
7. Arena supports the change with sufficient valid evidence;
8. the representation complies with the applicable observability contract.

## Next engineering priorities

The documented research priority remains:

1. incremental NNUE correctness + performance;
2. broader independent tactical/semantic validation;
3. teacher-data diversity/bias measurement;
4. population payoff analysis when sufficient Arena data exists;
5. intrinsic move-quality diagnostics;
6. broader opponent-population robustness.

These are engineering/research priorities, not automatic promotion claims. The authoritative sequence remains `ROADMAP.md`.
