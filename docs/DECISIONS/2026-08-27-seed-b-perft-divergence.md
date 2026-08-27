# Discovery — replication seed set B exposes Python/C++ perft divergence

**Date:** 2026-08-27  
**Status:** root cause confirmed; correctness fix required  
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

The piece on `D2` is `Dragoon`. The shared hero configuration declares `jump_max: 2` and `spells: ["jump"]`. The Python `Dragoon.get_valid_spells()` implementation computes the jump destinations but returns plain two-element coordinate tuples. The common action adapter accepts tuple spells only when a third element contains the spell name; therefore those Dragoon jump results were silently omitted from the Python action list.

The C++ move generator instead reads `jump_max` and emits the corresponding `SPELL jump` actions directly.

Therefore the mismatch is a **Python reference/action-contract bug**, not an intentional C++ semantic difference and not experimental noise.

## Why the old tests missed it

The existing cross-backend move-generation test contained a Dragoon-specific compatibility fallback that inferred `jump` from a two-element tuple. That test-side workaround masked the violated action contract. The generic perft reference path did not contain that fallback and therefore exposed the divergence when seed-B placed a Dragoon at `D2`.

## Correctness decision

Keep the C++ jump semantics unchanged. Normalize the Python `Dragoon.get_valid_spells()` return value to the same spell-action representation already used by the other spell-producing implementations:

```python
{"target": (row, col), "spell_type": "jump"}
```

Remove the test-only Dragoon special case so future tests validate the common spell-action contract rather than compensating for it.

Then retain focused regression coverage for Dragoon jump actions and cross-backend move-generation/perft equivalence.

Do not:

- remove the three C++ actions;
- exclude the seed-B opening;
- weaken the differential assertion;
- change node-count semantics;
- classify the discrepancy as statistical variation.

## Scope separation

This correctness fix is separate from the direct-entrypoint CI fix merged in PR #138. The direct-entrypoint issue was a tooling failure after successful Arena validation. The Dragoon discrepancy is an actual reference/backend semantic mismatch.

## Promotion / experiment gate

Seed-B calibration remains blocked until the corrected Python/C++ action semantics pass focused and broader differential validation. Promotion authority remains disabled.
