# RedWar — Current State

**Snapshot:** 2026-08-26  
**Verified baseline:** `main` after differential-diagnostics and experiment-provenance work.

This document is a dated navigation snapshot. It is not a replacement for the canonical domain documents listed in [`docs/00_INDEX.md`](00_INDEX.md).

## Engineering baseline

- `main` contains the foundation gates established from the project-study audit.
- The regression suite now covers 100+ tests, including Python/C++ differential, make/unmake, move-generation, persistent-state, metamorphic and per-mechanic coverage.
- Long persistent-state differential coverage exercises lifespan, spawn cooldown, stun, tile effects and TWC across multiple plies.
- Differential diagnostics now identify the first divergent transition instead of only reporting a final aggregate mismatch.
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

The current strength estimator remains an Elo-compatible engineering baseline. Paired-game/pentanomial methodology, empirical uncertainty auditing and sequential testing are part of the validation direction, but SPRT is not yet the automatic promotion authority.

The Arena records enough provenance to distinguish valid games from invalid/blocked/max-ply observations. A strength claim must be based on valid, controlled experimental evidence rather than raw game counts alone.

Population context for Strength experiments is structured and machine-validated so results can retain the population, selection policy, controller population and skill context that produced them.

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

The project has completed the main correctness/provenance foundation and is moving through the remaining validation layers before the next major Ares performance block.

Current priority order is:

```text
long differential diagnostics
→ perft / node-count differential
→ real Strength/Arena calibration
→ contextual matchup/intransitivity analysis
→ stronger sequential promotion gate
→ intrinsic/move-quality strength
→ only then broader Ares search/NNUE optimisation
```

No individual tactical benchmark should be interpreted as global strength evidence.
