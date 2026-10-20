# Strength rating order sensitivity

**Date:** 2026-08-28  
**Status:** accepted as a methodological guardrail

## Discovery

The Arena's current `strength_rating` estimator updates an Elo-compatible rating after each result in sequence. The update is not order-invariant: two result streams with the same final 50/50 score can produce different terminal rating deltas when wins and losses occur in different orders.

This was observed across the frozen same-engine calibration runs. Run A and Run B both finished 50 challenger wins / 50 baseline wins, yet the Arena's terminal `rating_delta` differs substantially between them, while the aggregate paired effect is zero in both runs.

## Decision

Do not use the Arena terminal `rating_delta` as the primary calibration statistic for the replication protocol.

The primary calibration analysis remains the declared paired effect over complete colour-inverted units. The operational Elo-compatible rating remains available as a descriptive engine-side diagnostic, with its engineering uncertainty proxy unchanged.

Changing the production estimator requires a separate methodological decision and validation block; it must not be inferred from this observation alone.

## Consequences

This guardrail prevents result ordering from being mistaken for experimental evidence and preserves separation between the production engineering proxy and the empirical calibration analysis.


## Arena output contract (#597)

The Arena summary now keeps two different quantities separate:

- `rating_delta_sequential_elo_diagnostic` (also retained under the legacy `rating_delta` key) is produced by replaying each result in order. It is deliberately order-dependent and is diagnostic only.
- `rating_delta_aggregate_score_elo_equivalent` is derived only from the final aggregate win/draw/loss score. For a fixed aggregate score it is order-invariant, but it is a descriptive Elo-equivalent transformation—not a calibrated strength estimate, uncertainty interval, or promotion criterion. It is undefined when there are no valid games or the score is exactly 0%/100%.

The console labels both quantities explicitly. Neither quantity replaces the complete colour-inverted pair analysis, the declared statistical protocol, or the authoritative `ai_quality_gate.yml` promotion gate. Experimental runs also record `promotion_authority=false` and `promotion_decision=not_authorized`; the legacy `promoted` field remains false for those runs.


The raw-data recomputation for the 100-game historical bridge is preserved in [`docs/EXECUTIONS/2026-10-20-arena-597-raw-recompute.md`](../EXECUTIONS/2026-10-20-arena-597-raw-recompute.md), including the JSONL SHA-256, paired/color audit, the sequential result, and the aggregate-score equivalent.
