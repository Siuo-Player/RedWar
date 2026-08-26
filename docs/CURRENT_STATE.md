# RedWar — Current State

**Snapshot:** 2026-08-26

This document is a dated navigation snapshot. It is not a replacement for the canonical domain documents listed in `docs/00_INDEX.md`.

## Engineering baseline

- `main` contains the foundation gates established from the project-study audit.
- The repository test suite currently contains 84 tests and the latest verified local baseline is green.
- Python/C++ differential, make/unmake, move-generation, persistent-state and metamorphic coverage are part of the current regression layer.
- Arena result provenance is explicit: game validity and termination reason are retained, and invalid observations are excluded from strength inference and promotion.
- Protected hold-out validation is frozen through `data/validation/ARES_HOLDOUT_V1.json` and its canonical hash contract.

## Ares

Canonical source: `AI_ENGINE.md`.

Current architecture uses the C++ engine on the hot path with alpha-beta/PVS, transposition table, Zobrist hashing, iterative deepening, move ordering, quiescence/tactical search and bounded search. The classic evaluator remains the correctness/compatibility baseline.

NNUE infrastructure exists and is optional. Incremental NNUE primitives exist, but integration into the real `BoardState` transition hot path is still an open engineering block; full-refresh consistency remains the correctness baseline.

## Strength / Arena

Canonical sources:

- `STRENGTH_EVALUATION.md`
- `ARENA_STATISTICAL_METHODOLOGY.md`
- `ARENA_HOLDOUT_CI.md`

The current strength estimator remains an Elo-compatible engineering baseline. Paired-game/pentanomial methodology and sequential testing are part of the validation direction, but SPRT is not yet the automatic promotion authority.

The Arena now records enough provenance to distinguish valid games from invalid/blocked/max-ply observations. A strength claim must be based on valid, controlled experimental evidence rather than raw game counts alone.

## Game / heroes

Canonical sources:

- `GAME_DESIGN.md`
- `GAME_RULES.md`
- `HERO_SYSTEM.md`
- `../engine/HEROES_SCHEMA.md`

The hero system remains a hybrid declarative/runtime design: JSON data defines supported structure while specialized code is permitted where mechanics cannot yet be represented declaratively. The mechanics traceability matrix is the current guard against semantic drift across Python/C++ and state transitions.

## Observability

Canonical source: `OBSERVABILITY_CONTRACT.md`.

The current local game mode distinguishes setup/draft information from battle-state information. Ares must obey the same observability contract as the legal player model; experiments must not infer strength from an information representation that would be illegal in the product model.

## Balance

The Auto-Pricer remains a diagnostic pricing heuristic, not a causal estimator of hero power. A dedicated canonical balance methodology document is still a documentation gap; until it exists, balance claims should be treated according to the evidence rules in the existing game-design, engineering-methodology and foundation documents.

## Roadmap position

The project is in the foundation/validation phase immediately before the next major Ares performance block. The highest-value open engineering item remains incremental NNUE correctness plus performance measurement, followed by broader independent tactical/semantic validation.

No individual tactical benchmark should be interpreted as global strength evidence.
