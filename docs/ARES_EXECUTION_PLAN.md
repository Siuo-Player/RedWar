# RedWar — Ares 1.0 Execution Plan

**Governing issue:** #372  
**Preparatory child:** #406  
**Governance:** #365  
**Baseline reference:** `main` at the start of each work package

This document defines the dependency-safe execution order for Ares. It deliberately allows independent evidence work to proceed while Gameplay #371 is the active product gate, but it does not authorize promotion of Ares before #371 closes.

## 1. Contract gate — rules before strength

**Input:** the gameplay engine after #371.  
**Output:** a reproducible semantic interface for Ares.

Verify, before optimizing search:

```text
position
→ canonical legal action-space
→ transition validation
→ make
→ search-visible state
→ unmake
→ identical relevant state
```

Required invariants include terminal conditions, side-to-move, state hash/repetition observation, turn-without-capture, stun/lifespan/spawn cooldown and terrain effects.

`fast_clone()` remains outside the C++ hot path and is not a legality preflight mechanism.

## 2. Capability lane — deterministic tactical corpus

Build a small, versioned, deterministic suite that exercises the phenomena unique to RedWar:

- forced kills and stun chains;
- spells and area effects;
- passives that alter legal responses;
- lifespan and spawn cooldown;
- fire/ice interactions;
- TWC pressure;
- blocked/no-legal-action positions;
- representative quiet positions where search must not hallucinate tactics.

**Output:** capability scores and concrete regressions. A better puzzle score is not yet a global strength claim.

## 3. Search lane — hypotheses in isolation

Test one search hypothesis at a time:

1. move ordering;
2. quiescence/tactical extensions;
3. pruning/singular-style reductions only where semantically justified;
4. transposition-table policy;
5. time/node budgeting;
6. killer/history adaptations to RedWar action types.

Every candidate follows:

```text
correctness
→ deterministic capability regression
→ controlled benchmark
→ independent Arena strength test
```

Do not merge a search change because it merely increases depth, nodes or apparent complexity.

## 4. Evaluation lane — freeze and improve the classical baseline

Treat the current classical evaluator as a versioned baseline. Candidate changes are isolated by term so their effect can be attributed to a concrete hypothesis.

Keep separate measurements for material, position, stun state, temporary-unit value, effects, TWC and any future strategic terms.

**Output:** evaluator revisions with reproducible diffs and matched-budget comparisons.

## 5. NNUE lane — correctness first, promotion last

The existing NNUE path is optional. The sequence is:

```text
full-sync oracle
→ incremental make/unmake parity
→ feature/update regression
→ CPU-cost benchmark
→ Arena comparison
```

Lower training loss or a working export is not evidence that NNUE is stronger. NNUE becomes default only after competitive and/or efficiency evidence beats the accepted classical baseline under the agreed protocol.

## 6. Performance lane — matched resources

Use controlled benchmark conditions and report at least:

- nodes/search budget;
- wall-clock budget where applicable;
- reproducibility inputs;
- nodes/second as a secondary metric;
- capability outcomes;
- known machine/runner variance.

Performance is an engineering metric. It becomes a strength claim only through the independent Arena lane.

## 7. Arena lane — strength evidence

Compare a candidate against the accepted baseline with:

- color alternation;
- identical openings/seeds where protocol requires pairing;
- recorded version/provenance;
- matched resource budgets;
- uncertainty intervals;
- hold-out data where applicable;
- an independent decision procedure for promotion.

A larger dataset, a positive point estimate or a single SPRT result is not sufficient outside the protocol's defined stopping/acceptance conditions.

## 8. Promotion lane — one accepted Ares

Only after the previous lanes agree is a candidate promoted. Record:

- exact commit/version;
- evaluator/search/NNUE configuration;
- benchmark corpus/version;
- Arena corpus/version;
- hardware/runner assumptions;
- final evidence and limitations.

The accepted configuration becomes the reproducible Ares baseline for the Product gate.

## Parallel execution model

While #371 is active, these can run independently without changing rules:

```text
                ┌─ tactical corpus
#371 Gameplay ──┼─ evaluator baseline
                ├─ NNUE parity/cost
                ├─ benchmark harness
                └─ Arena/provenance hardening
                         ↓
                 candidate validation
                         ↓
                    Ares promotion
```

Search/evaluation experiments may be developed in parallel, but promotion remains serialized by the evidence chain. Gameplay changes that alter action legality or state semantics invalidate downstream measurements and must trigger reruns.

## Definition of done for #372

Ares is ready for Product only when:

1. correctness/regression suites are green;
2. the selected search/evaluation path has controlled evidence;
3. strength is established independently by Arena under the accepted protocol;
4. NNUE is either justified as default or explicitly retained as optional;
5. the selected configuration and evidence are reproducible from documented inputs.
