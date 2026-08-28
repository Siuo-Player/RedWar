# Decision — Replay analytics and incremental aggregation

**Date:** 2026-08-28  
**Status:** Adopted as engineering policy; implementation of the analytical layer remains incremental

## Discovery

The project-study audit added a math-first optimisation requirement after the initial replay-storage design. Recalculating historical aggregates from every canonical replay is unnecessary when the required statistic can be maintained from a compact aggregate state plus newly completed games.

## Decision

Keep two distinct layers:

```text
canonical replay archive
        ↓
incremental derived aggregates
```

The canonical replay remains the source of truth for sequence-level questions. Aggregates are caches and research outputs and must be rebuildable from the archive.

For arithmetic statistics, prefer online/mergeable state with an explicit correctness invariant. For a mean:

```text
μ_new = (N·μ + S_new) / (N+k)
```

or one observation at a time:

```text
μ_new = μ + (x-μ)/(N+1)
```

For variance, prefer a numerically stable Welford/Chan-style state and merge worker/batch summaries rather than repeatedly scanning the full history.

The same audit requires every incremental optimisation to document:

```text
invariant
+ update formula
+ initial/rebuild path
+ test against full recomputation
```

## Scope

The first targets are replay/telemetry aggregates such as:

- duration statistics;
- engine time statistics;
- node-count statistics;
- result counts by hero/context;
- player-vs-Ares summaries;
- derived Arena summaries where applicable.

Reservoir sampling and quantile sketches remain candidates for later use where exact replay reconstruction is unnecessary. They do not replace canonical games.

## Storage consequence

The current `compact JSON + gzip` implementation is treated as a measured candidate, not an irreversible format decision. Real-player corpus measurements should be used before changing codec or chunk sizing. The canonical schema should remain independent of the transport/storage wrapper.

## Not changed

- raw replay immutability;
- hold-out/Arena evidence policy;
- Strength thresholds;
- hero prices;
- Ares search/evaluation;
- future server or peer-assisted storage design.
