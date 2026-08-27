# Discovery — Strength context direct-entrypoint import failure

**Date:** 2026-08-27  
**Status:** confirmed  
**Origin:** CI workflow execution

## Fact observed

`ai_strength_experiment.yml` invokes `tools/analytics/strength_context_artifacts.py` as a file path. In that execution mode Python places the script directory (`tools/analytics`) on `sys.path`, but not the repository root. The script imports `tools.analytics.strength_context_effects` and `tools.analytics.strength_population`, so the direct invocation can fail with `ModuleNotFoundError: No module named 'tools'`.

The failure was observed after a successful Arena execution and validation phase; it is therefore a CI/tooling entrypoint failure, not evidence that the Arena experiment or its raw data were invalid.

## Evidence

CI run `33087013329` reached:

- Arena: 100/100 valid games;
- validation: 100 valid, 0 invalid, 50 complete pairs;
- failure at context attachment with `ModuleNotFoundError: No module named 'tools'`.

The current `main` implementation imports the `tools.analytics` package directly from `strength_context_artifacts.py` without establishing the repository root when the module is executed as a script.

## Decision

Make the script safe as both:

```text
python -m tools.analytics.strength_context_artifacts ...
python tools/analytics/strength_context_artifacts.py ...
```

by inserting the repository root into `sys.path` before the package imports.

This is a tooling/entrypoint fix only. It must not alter raw Arena records, context semantics, statistical calculations or promotion policy.

## Separate finding: seed-replication branch

A separate experimental branch changes the opening-book seed set for replication run B. That branch exposes a Python/C++ perft mismatch for `opening-1` (Python 1000, C++ 1099 at depth 2). This is a distinct correctness/semantic finding and must not be bundled with the direct-entrypoint fix.

The new-seed experiment therefore remains blocked until that differential result is investigated and either explained as an intentional semantic difference or corrected.

## Validation

The focused validation for this decision is:

1. direct script invocation succeeds from the repository root;
2. existing `tests/test_strength_context_artifacts.py` remains green;
3. no production Arena/statistical semantics change;
4. CI reaches the context-attachment step without the import failure.
