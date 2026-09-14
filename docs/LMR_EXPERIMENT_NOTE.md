# Ares LMR experiment note

This document records the first implementation shape for issue #494.

## Scope

The candidate changes only `ai/cpp_engine/search.cpp` and applies a single-ply reduction to late `MOVE` actions inside non-root alpha-beta nodes.

The candidate deliberately excludes the first move, TT principal move, all non-`MOVE` actions, forcing contexts, active STUN continuations, shallow nodes, and tactical/safety-sensitive paths.

## Validation rule

This is an experiment only. It cannot be promoted from node-count or NPS gains alone. The acceptance chain remains correctness/regression → controlled performance → independent matched-budget Arena strength.

The protected holdout `ARES_HOLDOUT_V1` must remain untouched during implementation/tuning.
