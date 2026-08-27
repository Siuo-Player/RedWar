# Discovery — replication seed set B exposes Python/C++ perft divergence

**Date:** 2026-08-27  
**Status:** root cause confirmed; differential-harness fix required  
**Origin:** CI on experiment branch

## Fact observed

The experiment branch for Strength replication changes the opening-book seeds from the canonical `main` set to the declared seed set B. Under that population, the existing Python/C++ perft differential test reports:

```text
case: opening-1
depth: 2
Python: 1000
C++:    1099
```

The canonical `main` opening set did not expose this mismatch in the existing perft cases; diagnostic PR #137 based directly on `main` completed the Test Suite successfully.

## Investigation result

The first divergence is at the **root legal-action set**, not after a root transition.

For seed-B `opening-1`, the diagnostic found:

```text
Python-only: []
C++-only:
  SPELL jump D2 B4
  SPELL jump D2 D4
  SPELL jump D2 F4
```

The piece on `D2` is `Dragoon`. The shared hero configuration declares `jump_max: 2` and the `jump` spell. The Python `Dragoon.get_valid_spells()` implementation computes the jump destinations as two-element coordinate tuples.

A repository-level move-generation test already handled that representation explicitly as `jump`. However, the shared `actions_for()` helper used by the perft reference did not contain the same normalization. Consequently the Python perft path silently omitted the three valid Dragoon jump actions, while C++ emitted them.

Therefore the mismatch is a **differential-test/reference-adapter bug**, not a C++ engine defect and not experimental noise.

## Why the old tests missed it

The cross-backend move-generation test had a Dragoon-specific compatibility path that inferred `jump` from a two-element tuple. The perft helper did not. The two reference paths therefore disagreed about how to interpret the same Python engine action.

The seed-B population exposed the inconsistency because it placed a Dragoon at D2 in a position where all three forward two-square jump destinations were legal.

## Correctness decision

Keep the Python engine representation and C++ jump semantics unchanged. Align the shared differential-test action adapter with the already-existing Dragoon compatibility rule:

```text
2-element Dragoon spell tuple → spell_name = "jump"
```

Add regression coverage proving that `actions_for()` exposes the eight legal jump targets from a central Dragoon position. Re-run the existing Python/C++ move-generation and perft differential suites.

Do not:

- remove the three C++ actions;
- modify `Dragoon.get_valid_spells()` solely to satisfy a test adapter;
- exclude the seed-B opening;
- weaken the differential assertion;
- classify the discrepancy as statistical variation.

## Scope separation

This correctness-of-validation fix is separate from the direct-entrypoint CI fix merged in PR #138. The direct-entrypoint issue was a tooling failure after successful Arena validation. The Dragoon discrepancy is a mismatch between two existing representations in the differential reference harness.

## Promotion / experiment gate

Seed-B calibration remains blocked until the corrected differential validation passes on focused and broader coverage. Promotion authority remains disabled.
