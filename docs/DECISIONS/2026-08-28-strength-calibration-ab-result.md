# Strength calibration A/B result

**Date:** 2026-08-28  
**Status:** evidence reviewed; no model recalibration approved

## Observed evidence

Run A and Run B are both same-engine controls using the frozen engine/rules SHA `81d018d3dd9d509e6ed1e4ba801adfab0d6fe5ef`, 100 valid games each, 50 complete colour-inverted pairs each, and zero draws/invalids.

The aggregate paired effect is exactly 0 Elo-equivalent in both runs. Descriptive paired-bootstrap ranges are approximately [-41.5, +41.5] for Run A and [-55.5, +55.5] for Run B.

The important cross-run change is structural rather than directional: Run A has 8/50 same-outcome pairs (16% sweeps), while Run B has 18/50 (36%). An exploratory Fisher exact comparison gives p≈0.039 for this difference. This is retained only as a descriptive context/dependence diagnostic, not as a preregistered inferential result.

## Decision

Do not recalibrate the production uncertainty proxy from A/B alone. The evidence supports zero mean effect for the same-engine controls but also shows context-dependent outcome repeatability under the two seed populations. More evidence is required before changing uncertainty semantics.

Continue to protected holdout and the remaining planned draw/dependence diagnostics. Promotion remains disabled.
