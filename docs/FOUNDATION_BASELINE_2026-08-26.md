# RedWar — Foundation Baseline — 2026-08-26

## Purpose

This document records the foundation decisions imported from the external `Siuo-Player-PROJECT-STUDIES/REDWAR` audit before the next Ares implementation block.

It is intentionally a **foundation gate**, not a future-feature backlog.

## Confirmed risks

### P0 — Incremental NNUE is not yet the real BoardState hot path

The project has incremental NNUE primitives, but the documented correctness baseline still relies on full synchronization. Until accumulator updates are connected to real state transitions and checked against full refresh, NNUE work is infrastructure rather than a measured performance improvement.

Gate:

```text
make/unmake transition
        ↓
incremental accumulator
        ↓
full refresh
        ↓
exact agreement
        ↓
only then NPS/performance measurement
```

Required state coverage includes pieces, stun, lifespan, cooldown, effects, TWC and side to move.

### P0 — Tactical validation is not broad enough to justify global-strength claims

The existing tactical suite is useful and deterministic, but it is centred on known tactical phenomena. It must expand across STUN, spells, defence, lifespan/cooldown, TWC, high-value captures and states sampled from complete games.

Directed tactical tests are therefore classified as regression/capability evidence, not as standalone global-strength evidence.

### P0 — Auto-Pricer is a pricing heuristic, not a causal balance estimator

The current Auto-Pricer corrects match outcomes using opponent/player ELO residuals and aggregates hero occurrence volume. It does not identify hero × player skill, matchup/composition, repeated-player dependence, colour effects independent of ELO, draft position, co-occurrence/synergy or non-linear effects.

Decision:

```text
Auto-Pricer = diagnostic / pricing heuristic
Auto-Pricer != causal estimate of hero power
```

It may propose a price change, but its result must not be presented as proof that a hero has a particular intrinsic power level.

### P1 — JSON schema validity does not prove semantic completeness

`engine/heroes_config.json` is the source of hero data, but a schema-valid field can still be missing from one backend or from a state-transition path.

The protected boundary is:

```text
heroes_config.json
    ↓
Python rules ←→ C++ rules
    ↓
actions / state transitions
    ↓
serialization / make / unmake / hash
```

Decision: every state-changing mechanic must be traceable across that boundary before being treated as complete.

### P1 — Failure provenance must survive tooling boundaries

An invalid result is not a single category. At minimum, RedWar distinguishes:

- genuine game result;
- invalid action;
- timeout;
- process/engine failure;
- malformed result/schema;
- diagnostic failure;
- stale or mismatched artifact.

A report that merely drops an observation without a machine-readable reason creates research debt.

### P1 — Evidence classes must remain separated

A successful test belongs to a specific evidence class:

```text
correctness
performance
capability
competitive strength
balance/metagame
product UX
```

No class silently substitutes for another.

## Foundation order

Before major new Ares heuristics or automated balance optimization:

1. maintain mechanics traceability;
2. preserve failure provenance;
3. validate the Auto-Pricer as a diagnostic baseline;
4. expand differential/property coverage by mechanic;
5. prove incremental NNUE correctness against full refresh;
6. only then perform stronger performance/strength experiments.

## Relation to the main roadmap

This baseline gates the existing roadmap rather than replacing it. In particular:

- tactical benchmark expansion remains active;
- differential/property testing remains active;
- Strength Evaluation remains the authority for global-strength claims;
- search optimization waits for a trustworthy validation baseline;
- incremental NNUE waits for exact full-vs-incremental agreement;
- richer auto-balancing waits for better data and causal diagnostics.

## Source

Research/audit repository: `Siuo-Player/Siuo-Player-PROJECT-STUDIES/REDWAR`.

Key audits consulted on 2026-08-26:

- `VULNERABILITIES_2026-08-25.md`
- `REVERSE_ROADMAP_AUDIT_2026-08-26.md`
