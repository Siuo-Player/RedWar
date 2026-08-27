# RedWar — Current State

**Snapshot:** 2026-08-27  
**Verified baseline:** `main` after provenance, Strength context, matchup/intransitivity diagnostics, real Arena report support and dedicated Strength experiment triggering.

This document is a dated navigation snapshot. It is not a replacement for the canonical domain documents listed in [`docs/00_INDEX.md`](00_INDEX.md).

## Engineering baseline

- `main` contains the foundation gates established from the project-study audit.
- The regression suite now covers 100+ tests, including Python/C++ differential, make/unmake, move-generation, persistent-state, metamorphic and per-mechanic coverage.
- Long persistent-state differential coverage exercises lifespan, spawn cooldown, stun, tile effects and TWC across multiple plies.
- Differential diagnostics identify the first divergent transition instead of only reporting a final aggregate mismatch.
- Python/C++ perft/node-count differential is now part of the regression layer for deterministic positions.
- Arena result provenance is explicit: game validity and termination reason are retained, and invalid observations are excluded from strength inference and promotion.
- Protected hold-out validation is frozen through `data/validation/ARES_HOLDOUT_V1.json` and its canonical hash contract.

## Ares

Canonical source: [`AI_ENGINE.md`](AI_ENGINE.md).

Current architecture uses the C++ engine on the hot path with alpha-beta/PVS, transposition table, Zobrist hashing, iterative deepening, move ordering, quiescence/tactical search and bounded search. The classic evaluator remains the correctness/compatibility baseline.

NNUE infrastructure exists and is optional. Incremental NNUE primitives exist, but integration into the real `BoardState` transition hot path is still an open engineering block; full-refresh consistency remains the correctness baseline.

## Strength / Arena

Canonical sources:

- [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md)
- [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md)
- [`ARENA_HOLDOUT_CI.md`](ARENA_HOLDOUT_CI.md)
- [`ARENA_STRENGTH_DATASET.md`](ARENA_STRENGTH_DATASET.md)
- [`DECISIONS/2026-08-27-strength-replication-calibration-protocol.md`](DECISIONS/2026-08-27-strength-replication-calibration-protocol.md)

The current strength estimator remains an Elo-compatible engineering baseline. Paired-game/pentanomial methodology, empirical uncertainty auditing and sequential testing are validation layers; SPRT is not yet the automatic promotion authority.

The Arena records enough provenance to distinguish valid games from invalid/blocked/max-ply observations. A strength claim must be based on valid, controlled experimental evidence rather than raw game counts alone.

Population context for Strength experiments is structured and machine-validated so results can retain the population, selection policy, controller population and skill context that produced the games.

The first persistent real-Arena control dataset is now stored under `data/arena/strength/`. It contains 100 valid games grouped into 50 complete colour-inverted pairs and is consumed by the existing paired empirical uncertainty audit. This is the first empirical calibration observation in the repository, not a completed calibration programme: the 50 pairs are resampling units for the paired audit, but they are not 50 independent experimental conditions because opening/seed combinations are reused.

The next evidence block is therefore replication across intentional experiment runs and population/context variation. The engineering uncertainty proxy remains unchanged until repeated-run evidence supports recalibration. Legitimate draws, invalid/incomplete games, dependence from repeated conditions and a predeclared hold-out must be represented in the calibration programme.

## Game / heroes

Canonical sources:

- [`GAME_DESIGN.md`](GAME_DESIGN.md)
- [`GAME_RULES.md`](GAME_RULES.md)
- [`HERO_SYSTEM.md`](HERO_SYSTEM.md)
- [`../engine/HEROES_SCHEMA.md`](../engine/HEROES_SCHEMA.md)

The hero system remains a hybrid declarative/runtime design: JSON data defines supported structure while specialized code is permitted where mechanics cannot yet be represented declaratively. The mechanics traceability matrix is the current guard against semantic drift across Python/C++ and state transitions.

Directed differential fixtures cover rare mechanics including Dragoon jump, BoneLord on-kill spawning and Berserker area damage.

## Observability

Canonical source: [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md).

The current local game mode distinguishes setup/draft information from battle-state information. Ares must obey the same observability contract as the legal player model; experiments must not infer strength from an information representation that would be illegal in the product model.

## Balance

Canonical source: [`BALANCE_METHODOLOGY.md`](BALANCE_METHODOLOGY.md).

The Auto-Pricer remains a diagnostic pricing heuristic, not a causal estimator of hero power. Balance analysis is explicitly contextual: hero, skill, matchup, composition, colour, pick-rate and other available evidence must be separated rather than reduced to global win-rate alone.

## Roadmap position

The project has completed the main correctness/provenance foundation and is moving through the remaining Strength validation layers before the next major Ares performance block.

Current priority order is:

```text
real Strength dataset persistence
→ multi-run replication + population variation
→ contextual / matchup stability
→ uncertainty calibration + hold-out
→ SPRT operating-characteristic validation
→ sequential promotion gate
→ intrinsic/move-quality strength
→ broader Ares search/NNUE optimisation
```

The previously planned long persistent differential, first-divergence diagnostics and perft/node-count differential layers are implemented in `main`.

No individual tactical benchmark or single control experiment should be interpreted as global strength evidence.
