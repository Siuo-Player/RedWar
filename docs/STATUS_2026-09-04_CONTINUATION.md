# RedWar — Current Continuation Status — 2026-09-04

This file is the compact status override for the longer `HANDOFF_2026-09-04_AUTONOMOUS_CONTINUATION.md`.

## Current main

The current `main` contains the recent A0/C3 test infrastructure, the corrected bridge fixture, the dependency update to `websockets==17.1`, and the autonomous-continuation documentation.

Verified merge commits from this work cycle:

- PR #233 → `f3c1ad30e7a97c045b5f845d93a0d79baf482214`
- PR #234 → `f5dd851464f6b77f50a892e61fcdc3ff6bd5086d`
- PR #235 → `75f5fe9baf52afde4d8368316ec82f3069488bbb`

The documentation commits themselves are documentation-only and do not change game or Ares semantics.

## Superseded PRs

- #232 was stale and was replaced by #233.
- #219 was stale and was replaced by #234.
- #213 was stale and was replaced by #235.
- #236 passed its three CI gates, but its base became stale while documentation commits moved `main`; it was closed and replaced by #238 on the then-current `main`.

Do not reopen or merge these superseded PRs.

## Active PR

### #238 — FrostMage randomized C3 legal-action coverage

Branch: `test/a0-c3-frostmage-randomized-2026-09-04-final`

It changes only `tests/test_a0_c3_native_oracle_randomized.py`:

- adds `FrostMage` to the deterministic 128-seed randomized corpus;
- updates the explanatory comment;
- leaves production code unchanged.

The purpose is to extend native C++ vs independent Python-oracle **legal-action** agreement coverage. It does not prove post-action state equality, make/unmake equality, search quality, or strength.

The current oracle and native generator both encode Nevada as `SPELL nevada` with the same Manhattan-3 action envelope and ice-cell blocking. The fixed cross-backend corpus already exercised FrostMage.

Do not merge #238 until all required CI checks are green.

## Completed correctness audits

### Issue #189

Already corrected by PR #191. Current C++ semantics preserve TWC when a temporary piece is destroyed and reset TWC for permanent-piece capture. Independent regression coverage exists. Issue #189 is closed as completed.

### Issue #144

Already implemented. `tools/analytics/holdout_arena.py` executes the eight-case protected manifest directly, preserves case identity/provenance, uses colour-inverted pairs, and validates pair structure. `tools/analytics/holdout_validation.py` protects the canonical manifest identity/SHA. Issue #144 is closed as completed.

## Continuation order

1. Finish and merge #238 if CI remains green.
2. Strengthen multi-step Python/C++ state-transition conformance.
3. Extend state read-back and make/unmake checks across timers, effects, TWC and special spells.
4. Complete the remaining A0 acceptance obligations before making any A0 PASS claim.
5. Only then execute frozen empirical strength work.
6. Keep search/NNUE optimisation behind correctness and declared measurement gates.

## Non-negotiable boundaries

- Do not change Python semantics merely to make C++ agree with an old bug.
- Do not let an independent oracle call the implementation under test.
- Do not treat CI success as evidence of strength.
- Do not treat legal-action agreement as proof of transition or strength equivalence.
- Do not tune against the protected holdout.
- Do not perform statistical/dataset interpretation as part of a correctness-only task.
- Do not merge stale PRs solely to preserve chronology.

For the complete reasoning, file-by-file map, validation procedure, and future decision rules, read `docs/HANDOFF_2026-09-04_AUTONOMOUS_CONTINUATION.md`.
