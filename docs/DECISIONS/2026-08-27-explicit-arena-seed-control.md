# Decision — explicit Arena seed control

**Date:** 2026-08-27  
**Scope:** Strength/Arena experiment infrastructure  
**Status:** implementation candidate

## Discovery

The active Strength replication protocol requires seed variation between calibration runs while keeping all other frozen controls comparable. The persisted experiment plan declares distinct seed policies for runs A/B/C, but `arena_tournament.py` previously selected seeds only through the canonical opening book.

That meant a branch could claim a different seed policy without the Arena execution path actually receiving or recording a distinct declared seed set.

## Decision

Add explicit ordered opening-seed control to the Arena execution path.

The contract is:

- exactly one seed per declared opening;
- seeds are explicit integers and must be unique and non-negative;
- the ordered seed set is persisted in `experiment` metadata;
- `seed_policy` and `seed_generation_rule` are persisted with the run;
- both members of a colour-inverted pair receive the same opening seed;
- omitting the explicit option preserves the canonical opening-book behaviour;
- no game rules, estimator or promotion authority changes.

The Arena receives the seed set as an execution input rather than modifying `opening_book.py` on experiment branches. This keeps population selection separate from the production opening catalogue.

## Evidence / validation target

The correctness property to test is:

```text
game 0,1 -> seed[0]
game 2,3 -> seed[1]
...
game 30,31 -> seed[15]
```

The same seed must be visible in both raw game records of every colour-inverted pair.

The current implementation exposes this through `--opening-seeds`, `--seed-policy` and `--seed-generation-rule` and records the resulting values in Arena experiment metadata.

## Scope separation

This is experimental infrastructure only. It does not constitute strength evidence and does not authorize promotion.

The seed-B perft issue previously found under the fixed seed set is already resolved at the differential-harness level by PR #141. A new calibration run must still be executed from a frozen commit and validated before interpretation.
