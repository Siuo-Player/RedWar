# Strength dataset direct-entrypoint execution

**Date:** 2026-08-28  
**Status:** implemented in the associated fix PR

## Discovery

The frozen Run A calibration completed all 100 Arena games and produced a valid raw JSONL and Arena summary, but the plan-backed runner failed while invoking `tools/analytics/strength_dataset.py` directly.

The observed failure was:

```text
ModuleNotFoundError: No module named 'tools'
```

The direct script invocation did not guarantee that the repository root was on `sys.path`, even though repository-local imports work from the normal test entrypoint.

## Decision

Make `strength_dataset.py` establish the repository root from its own file location before importing repository-local `tools.*` modules.

This is an entrypoint compatibility fix only. It does not change dataset schema, validation semantics, independent-unit construction, bootstrap calculations, Arena behaviour, statistical thresholds, or promotion authority.

## Evidence handling

The completed Run A raw artifact remains the source observation set. The derived dataset may be rebuilt from that preserved JSONL while retaining the original workflow run ID, artifact ID, raw SHA-256, frozen engine/rules revisions, and experiment/run identifiers.

A technical rerun of the whole Arena is not a new calibration run and must not be combined with the original observations as independent evidence.
