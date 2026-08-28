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
