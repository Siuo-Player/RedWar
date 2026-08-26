# Discovery / Decision — paired bootstrap aggregate semantics

**Date:** 2026-08-27  
**Area:** Ares / Strength Evaluation  
**Status:** accepted for descriptive empirical auditing only

## Discovery

The Arena uses colour-inverted A/B pairs as the experimental unit. A pair therefore contains two dependent games and must remain intact during resampling.

The first implementation of the empirical audit calculated an implied Elo delta separately inside each resampled unit. With the current Arena design, a normal two-game pair such as `win/loss` has an Elo-equivalent delta of exactly zero, while `win/win` or `loss/loss` can produce an infinite logistic estimate.

That makes pair-level Elo values a poor statistic for the bootstrap itself.

## Decision

For paired Arena evidence:

```text
pair
  ↓
resampling unit
  ↓
keep both games together
  ↓
aggregate outcomes across the sampled pairs
  ↓
compute one descriptive Elo-equivalent effect
```

The production Elo estimator remains unchanged. The paired empirical audit is explicitly descriptive and is not a calibrated confidence interval or promotion test.

Small bootstrap samples can contain only decisive wins or only decisive losses. To keep the descriptive statistic finite at those boundaries, the paired audit applies a 0.5-count boundary smoothing to wins and losses **only inside this empirical bootstrap path**. The result records this choice explicitly in `audit_status` and `boundary_smoothing`.

## Consequences

- paired dependence is preserved;
- `win/loss` pairs no longer force the bootstrap estimate to zero by construction;
- boundary bootstrap replicates remain finite;
- the generic `empirical_uncertainty_audit()` semantics remain backwards compatible;
- this code must not be presented as calibrated statistical evidence until the later sequential/pentanomial framework is implemented and validated on sufficient real experiments.

## Next validation

Run this adapter against raw Arena JSONL produced by the normal CI/manual Arena workflow. Compare its descriptive output against the existing engineering uncertainty proxy and retain the raw paired observations as the source of truth.
