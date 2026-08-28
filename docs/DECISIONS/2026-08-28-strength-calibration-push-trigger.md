# RedWar — Dedicated push trigger for frozen Strength calibration

**Date:** 2026-08-28  
**Status:** implementation decision

## Finding

The frozen Strength calibration workflow is intentionally exposed through `workflow_dispatch`, but the available repository integration used for engineering work does not expose workflow dispatch. This prevented execution of the already-approved Run A without changing the scientific protocol.

## Decision

Add a narrowly scoped `push` trigger for branches under:

```text
calibration/strength/**
```

The push path does **not** introduce new experimental parameters. It resolves the same predeclared Run A from `replication-v3` and uses the same defaults:

- run: `strength-calibration-2026-08-27-control-replication`;
- 100 games;
- `stratified-opening-scenarios-v1`;
- `Ares-v1-vs-baseline-v1`;
- `fixed-node-budget`.

The runner remains the authoritative execution path and still resolves the frozen engine/rules revision from the plan before data collection.

## Scope boundary

This trigger is an execution mechanism only. It does not change:

- the frozen engine/rules revision;
- node budget;
- seed set or seed-generation rule;
- colour pairing;
- validity/termination policies;
- primary outcome/statistic;
- holdout policy;
- promotion authority.

A branch outside `calibration/strength/**` cannot invoke the push path.

## Evidence requirement

The first triggered execution is still a calibration control, not evidence of increased Ares strength. The resulting raw JSONL, derived dataset, validation audit and provenance must be inspected before any subsequent Run B interpretation.
