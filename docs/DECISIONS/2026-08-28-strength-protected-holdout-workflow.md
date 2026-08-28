# Strength protected holdout execution workflow

**Date:** 2026-08-28  
**Status:** accepted

## Decision

Use a dedicated push-triggered workflow for the protected Ares holdout rather than the configurable promotion Arena workflow.

The workflow validates the authoritative `data/validation/ARES_HOLDOUT_V1.json`, resolves the frozen engine/rules SHA `81d018d3dd9d509e6ed1e4ba801adfab0d6fe5ef`, uses a 10,000-node budget, executes one colour-inverted pair per protected case, and validates all 8 cases / 16 games before retaining the artifact.

The holdout is run as `python -m tools.analytics.holdout_arena` so repository-local imports are resolved from the repository package root. No production game, Ares search/evaluation, rating, uncertainty, or promotion semantics are modified.

## Evidence boundary

The holdout manifest is authoritative and must remain unchanged during execution. It is a measurement population separate from the calibration seed sets and must not be used for tuning before analysis is complete.

Promotion remains disabled by methodology: the holdout is evidence for generalisation and validation, not an automatic promotion gate.
