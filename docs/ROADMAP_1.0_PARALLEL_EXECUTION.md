# RedWar 1.0 — Parallel Execution Plan

**Date:** 2026-09-10  
**Status:** operational execution guide  
**Authority:** `docs/ROADMAP.md` remains the canonical phase/order document. This file defines how independent work packages can run in parallel without bypassing gates.

## 1. Objective

Reach a trustworthy RedWar 1.0 as quickly as practical without creating false dependencies between unrelated work.

The project should be executed as a **dependency DAG**, not as a single serial to-do list:

```text
                         ┌─ Gameplay correctness ─┐
                         │                         │
Foundation ──────────────┼─ Ares preparation ─────┼─ Ares strength
                         │                         │
                         ├─ Product preparation ──┤
                         │                         │
                         └─ Online preparation ───┘
                                                   │
                                                   ↓
                                              Product 1.0
                                                   ↓
                                              Online 1.0
                                                   ↓
                                              Release 1.0
```

The rule is:

> **parallelize investigation, tooling, tests, benchmarks and integration preparation whenever they do not require an upstream gate; serialize only the handoffs that genuinely depend on a stable contract.**

## 2. What may run in parallel now

While #371 Gameplay is still open:

| Lane | Work now | Blocked output |
|---|---|---|
| G — Gameplay | finish #397 and remaining ruleset regressions | #371 close |
| A0 — Ares correctness preparation | corpus, diagnostics, state-readback and TT/node-budget conformance | Ares promotion |
| A1 — NNUE | incremental/full-sync design, parity tests, microbenchmark harness | production promotion until Ares gate |
| A2 — Search | LMR/aspiration/history/TT experiment branches and benchmark design | production promotion until Ares gate |
| A3 — Evaluation | classical/NNUE ablation and feature-cost plan | evaluator promotion until evidence |
| A4 — Arena | strength protocol, paired colours, hold-out and result manifests | strength claim |
| P — Product | UI validation, replay/telemetry validation and integration preparation | Product release |
| O — Online | server/session architecture and authoritative command contract preparation | Online release |
| R — Release | CI/security/license/build/reproducibility audit preparation | Release gate |

No lane may use preparation work to declare its parent phase complete.

## 3. Gameplay lane — #371

### G1 — Finish existing integration

Immediate target: merge #397 after its Test Suite and CodeQL gates complete.

Acceptance:

```text
local Pygame draft/start
+ trainer setup
→ canonical pre-match validation
→ no invalid match starts
```

Do not redesign gameplay while closing this package.

### G2 — Rule-completeness sweep

Verify the complete 8×8 ruleset against executable scenarios:

- movement and attack classes;
- spells and passives;
- spawn/invocation;
- stun and second-stun death;
- fire/ice/terrain timing;
- lifespan/cooldown;
- surrender;
- no-legal-action termination;
- 50-turn no-permanent-capture rule;
- terminal/win semantics;
- Python/C++ differential behaviour where both backends exist.

Output: a protected gameplay corpus. This corpus later becomes part of Ares correctness and Arena preparation.

### G3 — Deterministic state/replay corpus

Freeze representative RWEN positions and short action sequences covering every critical mechanic and interaction.

Output:

```text
gameplay corpus
→ reusable by Ares / replay / telemetry / online QA
```

This is high-leverage because it removes duplicated fixture work in later lanes.

## 4. Ares lane — #372

The Ares phase is blocked for promotion until #371 closes, but preparation should proceed now.

### A0 — Baseline correctness

Before any strength experiment, establish:

```text
same input state
→ same legal actions
make/unmake
→ identical relevant state
hash
→ reproducible identity
TT ON/OFF
→ equivalent result under fixed node budget
node budget
→ deterministic stopping
reference evaluation
↔ production evaluation
```

This follows the project's existing A0 protocol. A benchmark is not enough to establish correctness.

### A1 — NNUE incremental path

First production candidate because it already has an incremental architecture in RedWar and the expensive full-sync path is still used before inference.

Work packages should be separable:

```text
A1a parity campaign
A1b incremental evaluator implementation
A1c microbenchmark
A1d fixed-node/fixed-time search comparison
A1e Arena validation if strength changes
```

Keep `sync_board()` permanently available as the oracle/recovery path.

Stockfish's NNUE documentation identifies sparse inputs and incremental accumulator updates as the mechanism for reducing repeated evaluation work. citeturn402592search3turn283942search0

### A2 — Move ordering

Run independent experiments from the same Ares baseline:

```text
A2a stronger action/history table
A2b continuation/counter-context history
A2c TT move ordering quality
```

Each experiment must be independently testable. Do not merge A2a+A2b merely because both affect ordering.

### A3 — LMR

LMR is the first selective-search candidate after the baseline ordering is measurable.

Start conservatively:

- non-first moves;
- non-PV branches where applicable;
- non-forcing actions;
- no special stun continuation;
- small reduction;
- full-depth re-search on a surprising reduced result.

The conceptual role of LMR is to search later/less-promising moves less deeply while preserving a full re-search when the reduced search indicates that a move may matter. Stockfish treats LMR as a core selective-search mechanism. citeturn412738search0turn402592search0

### A4 — Aspiration / iterative-deepening economics

Once iterative deepening is deterministic and scores are stable, add narrow root aspiration windows with widening re-search on fail-low/fail-high.

Do not couple this patch to LMR. Test it alone first.

Current Stockfish search uses aspiration around previous scores and re-searches after failures. citeturn402592search0

### A5 — TT quality

Test the current direct-index one-slot table against small, explicit alternatives:

```text
A5a depth-preferred replacement
A5b age/generation information
A5c collision diagnostics
A5d TT move usefulness
```

Only one replacement concept per experimental branch.

### A6 — Pruning

Only after A2/A3/A4 evidence exists:

```text
A6a null-move study
A6b futility study
A6c late-move pruning study
```

Each is opt-in research. A technique is rejected completely when its RedWar semantic assumptions do not hold.

Null move deserves special caution because RedWar has timers, effects, stun continuation and one-action turns. Stockfish defines NMP around the assumption that a side able to reach beta while effectively passing is unlikely to need a real move; that assumption must be demonstrated for RedWar rather than imported. citeturn412738search0

### A7 — Quiescence frontier

Independently measure whether the RedWar forcing frontier is correctly capturing the tactics that explode after a nominally quiet move.

Candidate forcing classes:

```text
attack / kill
second-STUN threat
Ignite lethal interaction
forced spawn
critical terrain interaction
```

Do not import chess check/capture definitions.

### A8 — Search/time management

After the search is correct enough for performance interpretation, compare:

```text
fixed depth
fixed nodes
fixed time
adaptive time
```

Record:

- root score stability;
- best-move stability;
- depth reached;
- nodes;
- decision latency;
- time consumed when tactics are unstable.

The goal is not “search as deep as possible”; it is best decision quality for the available product budget.

### A9 — Evaluation

Treat classical evaluation and NNUE as separate experimental lanes.

Classical:

```text
material
position
stun
lifespan/cooldown
terrain/effects
mobility/threat/objective terms
```

NNUE:

```text
feature coverage
feature sparsity
accumulator cost
network size
quantisation
training data
hold-out
```

Do not tune evaluator weights using the same positions later used as the final strength claim.

### A10 — Strength

Only after correctness and candidate search/evaluation work are stable:

```text
baseline
vs
candidate
```

with:

- colours alternated;
- identical ruleset;
- declared CPU/time/node budget;
- independent openings/seeds where appropriate;
- hold-out corpus kept separate from tuning;
- uncertainty reported with the project's Arena protocol.

Stockfish's Fishtest methodology is deliberately patch-oriented: small focused changes, controlled tests and sequential statistical evidence instead of accepting a patch after anecdotal games. citeturn283942search1turn283942search3

## 5. How to parallelize Ares safely

The fastest safe pattern is **parallel discovery, serial promotion**.

Example:

```text
                     same baseline B
                /       |       |       \
              A1       A3      A4       A5
               |        |       |        |
             test     test    test     test
               |        |       |        |
                \_______|_______|________/
                         ↓
                 promote winners one-by-one
                         ↓
                  re-run composite Arena
```

This prevents one experimental patch from making another patch appear better or worse merely because it changed the baseline.

A later stacked branch is allowed only after the individual winners are known.

## 6. Product lane — #373 preparation now

The Product phase should not begin its full integration gate before #372 closes, but preparation can continue.

### P1 — Battle UI validation

The functional sidebar architecture already exists. Remaining validation is:

- responsive layouts;
- keyboard/focus;
- selected hero persistence;
- hover/context semantics;
- invalid destination recovery;
- Encyclopedia authority;
- multi-action selection;
- colour-independent semantic cues;
- FrostMage/NEVADA stress scene;
- deterministic visual captures.

The UI renderer is not a legality authority. The game engine remains authoritative. fileciteturn131file0

### P2 — Replay/telemetry

Use the deterministic gameplay corpus as the seed for replay reconstruction and event telemetry.

The canonical flow should be:

```text
canonical gameplay action/state
→ event/replay record
→ deterministic reconstruction
→ analysis/telemetry
```

Avoid creating a second source of gameplay truth.

## 7. Online lane — #374 preparation now

### O1 — authoritative session contract

Define the server boundary before implementing network behaviour:

```text
client command
→ authentication/session validation
→ canonical action resolution
→ rules validation
→ authoritative mutation
→ event/replay output
```

The client must never be the authority for legality or final state.

### O2 — reconnect

Design reconnection around deterministic replay/state reconstruction, not ad-hoc state copying.

### O3 — time controls

Define the clock model independently from gameplay rules. Clock expiration should produce a canonical terminal outcome rather than directly mutating game semantics.

### O4 — matchmaking/rating

Keep matchmaking, rating and game outcome as separate concerns:

```text
matchmaking selection
≠ rating calculation
≠ game result
```

Start with the simplest reliable model and only add sophistication after real match data exists.

The current observability contract also means hidden information applies to draft/setup locally, while battle state is public in the current local mode; future online hidden-information variants require a separate observation model. fileciteturn132file0

## 8. Release lane — #375 preparation now

Prepare, but do not declare release-ready until Online is closed.

### R1 — Build matrix

Document reproducible builds for supported targets.

### R2 — Security

Audit:

- network command validation;
- state deserialisation;
- replay parsing;
- resource limits;
- untrusted client inputs;
- dependency vulnerabilities.

### R3 — Licensing/provenance

Audit code, assets, generated content and third-party dependencies before distribution.

### R4 — Observability

Release only with enough logs/metrics to diagnose:

- match failure;
- engine failure;
- reconnect;
- invalid command;
- replay divergence.

### R5 — Final acceptance

Use a release corpus spanning:

```text
rules
→ Ares
→ UI
→ replay
→ online
→ failure/recovery
```

No single green CI run substitutes for this acceptance.

## 9. Final 1.0 gates

The repository reaches 1.0 only after:

```text
GATE 1 — Gameplay
    all 1.0 rules executable + deterministic

GATE 2 — Ares
    correctness baseline + accepted strength improvements

GATE 3 — Product
    local game + UI + replay/telemetry validated

GATE 4 — Online
    authoritative multiplayer + reconnect + matchmaking/rating

GATE 5 — Release
    security + license + reproducible builds + final QA
```

## 10. Rules for every AI working on RedWar

Before coding:

```text
read ROADMAP.md
→ read domain contract
→ inspect main
→ identify exact issue/package
→ search existing branches/PRs
→ define one falsifiable change
```

During coding:

```text
one branch
→ one focused package
→ tests
→ benchmark if performance/capability
→ Arena if strength
```

After coding:

```text
CI
→ inspect actual result
→ document evidence
→ merge only validated work
→ update canonical state/roadmap
```

Never:

- merge a Stockfish feature because Stockfish has it;
- call NPS gain “strength gain”;
- use a tactical fixture as proof of general strength;
- stack several untested search concepts in one patch;
- bypass the active gameplay gate;
- create another roadmap to compete with `docs/ROADMAP.md`.

## 11. Expected operating rhythm

The project should progress by **short, independent packages** rather than large rewrites.

A useful rhythm is:

```text
Package discovered
→ smallest implementation
→ immediate regression
→ benchmark
→ decision
→ merge/reject
→ next package
```

When many packages are available:

```text
IA 1 → gameplay
IA 2 → Ares NNUE
IA 3 → Ares LMR research
IA 4 → Arena/benchmark tooling
IA 5 → Product/UI validation
IA 6 → Online/replay preparation
```

They may all work simultaneously, provided each starts from a documented baseline and records its exact dependency boundary.

## 12. Definition of “fast”

Fast does **not** mean skipping evidence.

It means:

```text
remove artificial dependencies
+ reuse the same corpora
+ keep patches atomic
+ benchmark continuously
+ promote only proven winners
```

That is the shortest route to a real 1.0 rather than the shortest route to a larger codebase.
