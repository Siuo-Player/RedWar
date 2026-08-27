# Decision — first calibration against a real Arena JSONL artifact

**Date:** 2026-08-27  
**Source:** GitHub Actions `RedWar AI Arena`, run `32898835641`  
**Artifact:** `redwar-ai-arena-b59e0e5a131e0bf5bfaf25e22fddd9e55d11bef9` (artifact `9582276075`)  
**Challenger:** `b59e0e5a131e0bf5bfaf25e22fddd9e55d11bef9`  
**Baseline:** `a58aad8e1927d34f1fe67d1c507fa54ce89d69fb`

## Dataset observed

The retained artifact contains 20 raw Arena games and 10 complete colour-inverted pairs.

- Challenger wins: **14**
- Baseline wins: **6**
- Draws: **0**
- Challenger colour: **10 White / 10 Black**
- Observed openings: **10**, each with 2 games and the same seed inside its pair
- Pair bins: **4 WW** and **6 WD/DW-equivalent split decisive pairs** (`WL`/`LW`)
- Node budget: **10,000**

The raw JSONL therefore contains the pair structure needed for descriptive paired resampling.

## Descriptive strength estimates

For the 20 individual games, the logistic Elo-equivalent point estimate is:

```text
+147.19 Elo
```

Using the paired bootstrap policy adopted in PR #128 — resample complete pairs, keep both games together, then compute the Elo-equivalent effect from the aggregate sampled outcomes — and 20,000 bootstrap replicates with seed 0 gives:

```text
observed aggregate effect:  +139.38 Elo-equivalent
empirical 2.5 percentile:    +33.19
empirical 97.5 percentile:   +279.59
empirical half-width:        123.20
```

The bootstrap is deliberately reported as **descriptive empirical resampling**, not as a calibrated confidence interval and not as a promotion criterion. With only 10 pairs, the bootstrap distribution has only a small number of distinct pair-composition outcomes, so the interval is necessarily coarse.

## Important schema limitation

This historical JSONL predates the current strict experiment-validation contract. The individual records do **not** contain the modern `valid` and `termination_reason` fields, even though the run summary records 20 completed decisive games.

Therefore this result is classified as:

```text
legacy_real_arena_descriptive_calibration
```

It must **not** be presented as evidence that has passed the current Strength validation boundary. No missing field was inferred or silently synthesized for promotion purposes.

## Comparison with the historical summary artifact

The same run's historical summary reports a rating delta of approximately **+105.61 Elo-equivalent** and an engineering uncertainty proxy half-width of approximately **922.72 Elo**. Those values come from the older rating/output contract and are retained only for provenance. They are not treated as the calibrated uncertainty result above.

## Decision

1. The paired bootstrap implementation is now exercised against a real Arena dataset rather than fixtures only.
2. The result supports the expected qualitative finding: the 14–6 experiment is positive, but the uncertainty is broad at only 10 pairs.
3. The historical dataset is not promoted into current validated evidence because its per-game schema is incomplete relative to the current contract.
4. The next required experiment is a **current-schema** Strength experiment with a materially larger number of complete pairs, retained raw JSONL, and explicit validity/termination provenance.
5. The SPRT/promotion gate remains disconnected from these descriptive numbers.

## Next experiment target

Run the current Strength experiment workflow with at least 100 games (50 complete colour-inverted pairs) under a fixed rules version and node budget, retaining the resulting JSONL and summary artifact. Then repeat:

```text
strict validation
    ↓
paired/pentanomial audit
    ↓
empirical Strength/uncertainty audit
    ↓
SPRT validation
```

Only after those stages agree should the sequential promotion gate be considered for activation.
