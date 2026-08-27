# Discovery — replication seed set B exposes Python/C++ perft divergence

**Date:** 2026-08-27  
**Status:** confirmed / investigation required  
**Origin:** CI on experiment branch

## Fact observed

The experiment branch for Strength replication changes the opening-book seeds from the canonical `main` set to the declared seed set B. Under that population, the existing Python/C++ perft differential test reports:

```text
case: opening-1
depth: 2
Python: 1000
C++:    1099
```

The canonical `main` opening set did not expose this mismatch in the existing perft cases; the diagnostic PR #137 based directly on `main` completed the Test Suite successfully.

## Interpretation

The new seed set does not by itself invalidate the experiment. It does, however, expose an unverified part of the Python/C++ semantic surface. Because the strength calibration protocol requires trustworthy state/action semantics, real replication using the new population must not be interpreted as strength evidence until the differential result is explained.

This is a **correctness/semantic validation issue**, not a statistical result, not an Arena draw, and not a CI-only failure.

## Scope separation

Do not solve this by:

- weakening the perft assertion;
- excluding `opening-1`;
- changing Python node-count semantics;
- changing C++ semantics without identifying the discrepancy;
- treating the 99-node excess as experimental noise.

The correct next action is to identify the first state/action transition at which the backends diverge.

## Investigation target

Compare, for the seed-B `opening-1` position:

1. root legal actions in Python vs C++;
2. each root child after the exact same action;
3. child legal-action counts;
4. first mismatching action/state;
5. relevant action type and affected squares;
6. `make/unmake` and derived state if the mismatch appears after transition.

Use the Python implementation as the semantic reference while the exact source of divergence is still unknown.

## Promotion / experiment gate

Until the divergence is resolved or explicitly proven to be an intentional representation difference that does not affect legal game semantics:

```text
seed-B calibration execution = blocked
promotion authority = disabled
```

The direct-entrypoint CI fix is separate and must not be bundled with this investigation.
