# RedWar — Project Development & Work Decomposition Methodology

## Why this document exists

RedWar has grown beyond a single-program feature project. It now contains a game rules engine, a native C++ AI engine, Python/C++ differential-testing infrastructure, tactical benchmarks, an Arena for Ares strength measurement, NNUE tooling, balance analytics, CI workflows, a local UI and a planned web/multiplayer layer.

This does **not** mean RedWar should be called a "large-scale software project" in the same organizational sense as studies involving dozens of teams or hundreds of developers. It is better described as a **small-team project with large system complexity and multiple interacting subsystems**. Nevertheless, many principles studied in large software projects are useful for its decomposition, coordination and dependency management.

This document records the project's development model and the research supporting it.

## Research basis

### Work Breakdown Structure

Tausworthe's *The Work Breakdown Structure in Software Project Management* describes WBS as a way to decompose an engineering project into subprojects, tasks, subtasks and work packages while linking objectives, resources and activities and providing a mechanism for tracking completion. DOI: https://doi.org/10.1016/0164-1212(79)90018-9

For RedWar, the equivalent hierarchy is:

```text
Project objective
    ↓
Subsystem / strategic area
    ↓
Roadmap block
    ↓
PR-sized development unit
    ↓
Implementation + tests + documentation
    ↓
Validation / experiment
```

The important point is that a roadmap item is not merely a feature name. It should have a bounded objective, a reason for existing, validation criteria and a clear completion state.

### Incremental and iterative development

Greer & Conradi's empirical study of software project initiation and planning found that iterative/incremental development creates additional planning difficulties and that documentation of project scoping varies considerably between organizations. The study also found evidence that deciding the architecture deliberately is preferable to allowing it to emerge entirely accidentally.

Reference: https://doi.org/10.1049/iet-sen.2008.0093

RedWar therefore uses a deliberately documented architecture and an incremental roadmap instead of treating the repository history itself as the only project plan.

### Coordination and dependencies

Research on large-scale software development repeatedly identifies coordination and dependency awareness as major challenges. Dingsøyr et al.'s longitudinal case study reports numerous coordination mechanisms in a very large agile programme and emphasizes the difficulty of coordinating work across teams and dependencies. https://doi.org/10.1007/s10664-022-10230-6

Bick et al. found that lack of dependency awareness was a key explanation for ineffective coordination in a 13-team software organization. https://doi.org/10.1109/TSE.2017.2730870

Even though RedWar is not a 13-team organization, the same failure mode exists in miniature: a search change may depend on move generation, which depends on rules and state representation, while Arena and CI depend on reproducible builds and experimental metadata.

### Modularity and technical debt

Research on architectural modularity and technical debt supports treating decomposition as an engineering property rather than only an administrative convenience. A module should have a coherent responsibility and a limited dependency surface, because changes that cross many boundaries are harder to validate and more likely to create architectural debt.

Reference example: Liang, Li & Guelfi, *An Empirical Investigation of Modularity Metrics for Indicating Architectural Technical Debt*. https://www.cs.rug.nl/~paris/papers/QOSA14.pdf

## RedWar development model

### 1. The roadmap is the project-level WBS

`docs/ROADMAP.md` is the top-level decomposition of work. It should answer:

- What is the next strategic objective?
- Why is it being done now?
- What dependencies must already be stable?
- What evidence is required to call it complete?
- What follows after it?

The roadmap is intentionally ordered. A later optimization should not quietly become a substitute for an unfinished correctness or measurement layer.

### 2. A PR is a controlled work package

A normal PR should correspond to a bounded unit of work. This does not mean every PR must contain only one file; it means the changes should have one coherent purpose.

A good PR should have:

```text
single objective
    +
small dependency surface
    +
tests
    +
documentation where behavior changes
    +
validation result
```

Large PRs are justified when the change is intrinsically atomic, such as a schema migration or a coordinated cross-language compatibility change. Otherwise, splitting work makes failures easier to localize and merges easier to reason about.

### 3. Branches represent isolated development streams

Branches are used to protect the stability of `main` while a roadmap block is developed.

Normal flow:

```text
main
  ↓
feature branch
  ↓
implementation
  ↓
tests / benchmarks / local validation
  ↓
PR
  ↓
CI / review
  ↓
merge
  ↓
main becomes the integration baseline
```

After merge, new branches should normally start from the current `main`. Long-lived branches are avoided unless there is a concrete reason to keep a development stream isolated.

### 4. Dependencies should be explicit

Each block should distinguish three kinds of dependency:

**Semantic dependency** — a change relies on the game rules or state representation being correct.

**Measurement dependency** — a strength claim relies on Arena, benchmarks, hold-out data or statistical infrastructure being trustworthy.

**Tooling dependency** — a workflow or script depends on a particular file format, executable, environment or artifact.

For example:

```text
C++ search optimization
    ↓
move generation correctness
    ↓
Python/C++ differential testing
    ↓
Arena traceability
    ↓
Strength Rating
    ↓
promotion decision
```

This prevents a lower-level dependency from being silently bypassed because a higher-level feature is more interesting.

### 5. Development, regression and validation are different roles

Not every test exists to prove the same thing.

```text
Regression tests
    → prevent known bugs from returning

Development cases
    → investigate a hypothesis while implementing a change

Hold-out / validation cases
    → measure generalization without exposing the full set during development

Arena
    → primary measurement of Ares strength
```

This distinction is critical for avoiding overfitting the engine to a handful of hand-picked positions.

### 6. Correctness before optimization

When two implementations exist, the canonical semantic implementation and the optimized implementation should be compared before using the optimized version for scientific conclusions.

For RedWar:

```text
Python game rules
       ↕
differential testing
       ↕
C++ engine implementation
```

Only after this relationship is stable should a C++ search or evaluation change be interpreted as an AI improvement.

### 7. Measurement before promotion

An implementation can be correct and still be a regression in overall playing strength.

Therefore the project uses:

```text
correctness
   ↓
regression protection
   ↓
independent validation
   ↓
Arena A/B games
   ↓
Strength Rating + uncertainty
   ↓
statistical decision
```

The Arena is the main instrument for measuring Ares strength. Benchmarks are supporting evidence, not a replacement for playing-strength measurement.

### 8. Documentation is part of the work package

Documentation should explain decisions while they are still fresh, not reconstruct them months later from commit history.

A completed roadmap block should normally leave behind:

- implementation;
- tests;
- experiment/benchmark results when applicable;
- a concise explanation of the design decision;
- roadmap status;
- references if an academic or external method motivated the choice.

## RedWar-specific decomposition

The project currently decomposes naturally into these strategic areas:

```text
Game semantics
 ├─ GameState
 ├─ action parser
 ├─ rules
 └─ state serialization

Ares
 ├─ move generation
 ├─ search
 ├─ evaluation
 ├─ move ordering
 └─ NNUE

Validation
 ├─ unit/regression tests
 ├─ Python/C++ differential testing
 ├─ metamorphic properties
 ├─ tactical benchmarks
 └─ hold-out validation

Strength measurement
 ├─ Arena
 ├─ experiment metadata
 ├─ Strength Rating
 ├─ uncertainty
 └─ future SPRT

Tooling / balance
 ├─ trainer
 ├─ analytics
 ├─ Auto-Pricer
 └─ CI workflows

Product
 ├─ local UI
 └─ future web/multiplayer
```

Each area may evolve independently, but interfaces between them are contracts. A change that crosses several areas should explicitly document why the coupling is necessary.

## How to decide whether to split work

Split a block when one or more of these are true:

- it has more than one independent validation criterion;
- one part can merge safely without the others;
- a failure would otherwise be hard to localize;
- it mixes experimental infrastructure with game behavior;
- it combines correctness work with optimization work;
- it crosses a subsystem boundary without needing to be atomic.

Keep work together when splitting it would temporarily leave the repository in an unusable or semantically inconsistent state.

## What not to optimize for

The project should not optimize for:

```text
number of PRs
number of commits
number of roadmap checkboxes
amount of code changed
benchmark score on a tiny fixed suite
```

The useful optimization target is:

```text
smallest coherent change
    ×
strongest validation
    ×
lowest unnecessary coupling
```

## Relationship with the rest of the documentation

- `docs/ROADMAP.md` — ordered project plan and current development sequence.
- `docs/ENGINEERING_METHODOLOGY_AND_RESEARCH.md` — engineering/scientific methodology.
- `docs/STRENGTH_EVALUATION.md` — measuring Ares playing strength.
- `docs/AI_BENCHMARK_PROTOCOL.md` — preventing benchmark overfitting.
- `docs/INSPIRATIONS_AND_HOMAGE.md` — projects, methods and ideas that influenced RedWar.

The goal is not to claim that RedWar follows a formal industrial methodology perfectly. The goal is to make its development process explicit, testable and improvable.
