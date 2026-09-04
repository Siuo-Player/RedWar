# RedWar — Autonomous Continuation Handoff

**Last updated:** 2026-09-04
**Purpose:** canonical handoff for a new developer or AI agent taking over the repository without access to the originating conversation.

> This document is an operational handoff, not a claim that the RedWar/Ares research programme is complete. It records what was verified, what was changed, why those changes were accepted, what remains open, and how to continue safely.

---

## 1. Start here

A new contributor should read, in this order:

1. `README.md` — project purpose, product boundaries, game rules and high-level Ares architecture.
2. `docs/ARCHITECTURE.md` — technical boundaries.
3. `docs/DEVELOPMENT_WORKFLOW.md` — branch/PR/validation discipline.
4. This document — current 2026-09-04 handoff and continuation state.
5. `docs/ROADMAP.md` and the latest roadmap-status document — priority order.
6. Relevant decision records in `docs/DECISIONS/` before changing semantics.

The repository is intended to contain enough information to continue development without private conversation context. Do not treat chat history as a source of truth when the repository contains a newer statement.

---

## 2. Scope and non-goals of this handoff

This handoff covers the recent autonomous RedWar work around:

- A0/C3 correctness and observability infrastructure;
- Python/C++ cross-backend agreement;
- state lifecycle/metamorphic testing;
- bridge regression isolation;
- protected holdout infrastructure;
- dependency maintenance;
- FrostMage/Nevada coverage;
- PR/CI hygiene;
- the decisions that control the next engineering steps.

It explicitly does **not** claim completion of:

- A0 acceptance as a whole;
- empirical strength acceptance/promotion;
- statistical analysis or dataset interpretation;
- NNUE superiority;
- search superiority;
- product/web/multiplayer completion.

No statistical or dataset analysis was performed as part of this handoff. Measurement infrastructure may exist in the repository, but implementation work must not be confused with evidence interpretation.

---

## 3. Repository state at this handoff

### Main branch

The current `main` includes the recent A0/C3 merges and the dependency update merged during this continuation.

The most recent explicitly verified merge commits in this cycle are:

- PR #233 → merge commit `f3c1ad30e7a97c045b5f845d93a0d79baf482214`.
- PR #234 → merge commit `f5dd851464f6b77f50a892e61fcdc3ff6bd5086d`.
- PR #235 → merge commit `75f5fe9baf52afde4d8368316ec82f3069488bbb`.

PR #231 was already merged before this cycle and is the latest important predecessor for the randomized C3 oracle campaign.

### Open work at handoff time

PR #236:

- title: `test(a0-c3): include FrostMage in randomized oracle campaign`;
- purpose: extend the existing deterministic 128-seed native-vs-independent-oracle legal-action campaign to include FrostMage;
- scope: test/evidence infrastructure only;
- production behaviour: unchanged;
- statistical claim: none.

At the moment this handoff was written, its AI Quality Gate had passed while Test Suite and CodeQL were still running. **Do not merge #236 until all required checks are green.** If a check fails, diagnose and fix the actual cause on the branch; do not bypass or weaken the gate.

The original Dependabot PR #213 and stale predecessors #219/#232 were closed rather than merged because they were based on older `main` states. Current replacements were created on the then-current `main` where needed.

---

## 4. What was done in this continuation

### 4.1 Rebased deterministic state-lifecycle metamorphic coverage

PR #232 contained useful C3 lifecycle coverage but was based on an older `main` after later merges. Instead of forcing the stale branch through conflicts, the same intended change was reconstructed on current `main` as PR #233.

The resulting tests cover three important invariants:

1. repeated legal-action generation is state-pure;
2. applying the same legal action to independent clones produces the same resulting state/hash/metadata;
3. executing on a clone does not mutate the original lifecycle state.

Why this matters:

- legal-action generation is frequently called by both gameplay and search;
- hidden mutation during move generation can corrupt search trees and invalidate differential testing;
- clone determinism provides a stronger lifecycle contract than checking only final board geometry.

No A0 acceptance was claimed. These are evidence-producing correctness tests.

### 4.2 Rebased native bridge diagnostic regression

PR #219 identified a regression in the test fixture used to verify that native engine diagnostic information is preserved when `bestmove 0000` occurs on a non-terminal state. The old fixture could itself be terminal under current rules.

The corrected version was reconstructed on current `main` as PR #234.

The fixture now constructs an explicitly non-terminal position rather than relying on the default `GameState()` starting position.

Why this matters:

- the test must exercise the **bridge error path**;
- it must not accidentally exercise the legitimate terminal-position path;
- changing production behaviour to satisfy an ambiguous fixture would be the wrong fix.

No production code was changed by #234.

### 4.3 Dependency maintenance

The repository had an old Dependabot PR #213 changing:

`websockets==17.0.1` → `websockets==17.1`

Because #213 was stale relative to the newly merged A0/C3 work, it was closed and the same one-line dependency update was recreated on current `main` as PR #235.

PR #235 changed only `requirements.txt` and passed the required validation before merge.

The lesson is general: dependency updates must be rebased/recreated from the current `main`; do not merge stale dependency branches merely because their diff is small.

### 4.4 Audited and closed already-solved correctness issues

#### Issue #189 — temporary target and TWC

The issue described a Python/C++ mismatch for `aimed_shot` against a temporary piece: Python preserved the turns-without-capture counter while the old C++ implementation reset it.

Repository history shows this was already corrected by PR #191. The current C++ implementation distinguishes permanent targets (`lifespan >= 999`) from temporary targets when deciding whether to reset TWC.

The regression tests include:

- temporary target destruction preserving TWC;
- permanent target capture resetting TWC.

After verifying that the correction was already present in current `main`, issue #189 was closed as completed.

**Important rule:** do not reintroduce a Python change merely to match an old C++ bug. Python semantics are the reference where the issue explicitly establishes them unless a deliberate game-rule decision changes the contract.

#### Issue #144 — protected holdout manifest

The issue requested a dedicated execution path for explicit `(opening_index, seed)` holdout cases rather than forcing an 8-case protected population through the normal 16-seed opening interface.

Current code already provides this via `tools/analytics/holdout_arena.py` plus `tools/analytics/holdout_validation.py` and the protected manifest:

`data/validation/ARES_HOLDOUT_V1.json`

The manifest contains eight explicit cases, with stable IDs, seeds and opening indices. The protected validator checks both set identity and canonical SHA-256 provenance.

The holdout executor:

- consumes the explicit manifest directly;
- runs two games per case;
- inverts challenger colour between the pair members;
- preserves case ID, seed and opening index in raw output;
- validates pair structure;
- records experiment provenance;
- does not alter the normal 16-opening interface.

Because the requirement was already satisfied, issue #144 was closed as completed.

---

## 5. A0/C3 infrastructure currently in the repository

### 5.1 Independent legal-action oracle

`tools/analytics/legal_action_oracle.py` is intentionally independent from the implementation under test.

It must not call `Piece.get_valid_*` methods or reuse Ares move-generation/search code to establish agreement with itself.

It encodes explicit predicates for:

- movement geometry;
- attacks;
- spells;
- spawn actions;
- silence restrictions;
- ice blocking;
- team-relative forward movement;
- special actions such as Dragoon jump and FrostMage Nevada.

The important testing principle is:

```text
implementation under test
        ↕
independent semantic reference
```

not:

```text
implementation under test
        ↕
helper that internally calls the implementation
```

### 5.2 Randomized C3 native-vs-oracle campaign

`tests/test_a0_c3_native_oracle_randomized.py` currently uses 128 deterministic seeds and compares native C++ legal-action generation against the independent oracle.

PR #231 corrected a real omission before allowing the randomized campaign to stand: Dragoon's orthogonal attack existed in the canonical hero configuration but was missing from the independent reference. The oracle was corrected rather than weakening the native implementation.

The test deliberately remained a legal-action equivalence test. It does **not** claim strength, Elo, promotion, or statistical superiority.

### 5.3 Cross-backend move-generation contract

`tests/test_cross_backend_movegen.py` provides fixed fixtures across ordinary, tactical, spell, special and effect-oriented states.

The C++ move generator is loaded from `engine/heroes_config.json`, while the Python-side contract helper extracts action semantics for comparison.

Important special cases already covered:

- FrostMage / Nevada;
- Dragoon / jump;
- spells with special action classification;
- effects such as ice/fire;
- silence-sensitive action generation.

### 5.4 Make/unmake lifecycle coverage

`tests/cpp_make_unmake_bridge_test.cpp` and related Python tests compare root metadata as well as board state. Metadata includes at least:

- Zobrist/state hash;
- TWC;
- side to move;
- material/active-piece counters where applicable.

A board that looks restored but has a different hash or TWC is a lifecycle failure.

### 5.5 State hashing

Both Python and C++ treat TWC as state, not as incidental UI information.

In the C++ engine the search-position key combines the board hash with a hash of TWC.

Therefore:

```text
same pieces + different TWC
        ≠
same search state
```

Any future stateful feature must decide explicitly whether it affects:

1. RWEN serialization;
2. canonical state hash;
3. make/unmake state;
4. search cache keys;
5. NNUE feature state.

Do not update only one representation.

---

## 6. FrostMage / Nevada: current contract and next step

FrostMage is special because Nevada is an area spell whose target is a selected centre cell rather than a normal enemy-target attack.

Current semantic contract:

- action class: `SPELL`;
- spell name: `nevada`;
- target envelope: Manhattan distance ≤ 3, excluding the caster's own square;
- an ice cell cannot be selected as a Nevada centre;
- the spell does not require an enemy on the selected centre;
- the native move generator and independent oracle use this same representation.

The native implementation creates an ice effect at the selected centre and applies the cross-shaped tactical consequences to the centre and its orthogonal neighbours according to the established rules.

The independent oracle already contains explicit Nevada generation. The C3 randomized campaign previously excluded FrostMage because a complete spell contract had not yet been trusted in the randomized reference. The fixed corpus continued to cover it.

During this continuation the code was audited and the two sides were found to encode the same legal-action envelope. PR #236 therefore removes the historical exclusion from the 128-seed randomized legal-action campaign.

**Do not interpret #236 as proving full FrostMage semantic correctness.** It proves one narrower thing when green: randomized agreement for the legal action representation. It does not by itself prove identical post-action state transitions, tactical consequences, search quality, or strength.

The next stronger FrostMage step, after #236, is therefore:

```text
legal-action equivalence
        ↓
state-transition equivalence
        ↓
make/unmake equivalence
        ↓
longer multi-step differential coverage
```

not an immediate jump to strength claims.

---

## 7. CI policy and what “green” means

The project uses three important PR gates repeatedly in this cycle:

### Test Suite

Builds the C++ differential helpers and executes the Python test suite.

A green Test Suite means the committed test suite completed successfully in the CI environment. It does not by itself establish experimental strength.

### AI Quality Gate

The AI Quality Gate detects whether the PR needs AI-specific quality work. For pure tests/documentation/dependency changes, expensive benchmark substeps may be skipped while the gate still passes.

Do not infer “AI quality improved” from a green gate on a test-only PR.

### CodeQL

C++ and Python code are analysed separately where configured.

A green CodeQL run is a security/static-analysis result, not a game-correctness or strength result.

### Merge rule

For ordinary engineering PRs in this area:

```text
implementation
  ↓
relevant tests
  ↓
required CI gates green
  ↓
merge
```

Do not bypass failing checks. If GitHub reports a stale or misleading mergeability state, recreate/rebase the branch rather than forcing a stale merge.

---

## 8. Handling stale PRs and duplicate work

This project currently has many historical PRs because work is intentionally decomposed into small, auditable blocks.

The correct procedure when an older PR is found is:

1. inspect its actual semantic purpose;
2. compare its base SHA with current `main`;
3. determine whether the change is already present;
4. if not present and still valid, recreate the change cleanly on current `main`;
5. close the stale duplicate after the replacement is available;
6. never merge an obsolete branch merely to preserve PR chronology.

A replacement PR should explain that it is a current-main reconstruction of the stale work and state exactly what was intentionally preserved.

This procedure was used for #233, #234 and #235.

---

## 9. Scientific/evidence boundaries that must not be broken

The repository intentionally separates:

```text
correctness / observability
        from
measurement infrastructure
        from
statistical interpretation
        from
promotion decisions
```

A test that enables a measurement is not itself evidence that a model is better.

A dataset being present is not itself a statistical conclusion.

A deterministic campaign is not automatically an independent sample.

A green CI job is not a strength result.

A protected holdout runner is not permission to tune against the holdout.

A same-engine A/B run measures experimental variation; it must not be reported as a model improvement.

The current roadmap deliberately keeps search/NNUE optimisation behind the empirical validation gates. Do not advance the roadmap simply because the infrastructure exists.

---

## 10. Current engineering roadmap from this point

The safe continuation order is:

### Gate A — finish #236

1. Confirm all three required checks are green.
2. Merge #236.
3. Record the merged commit in the roadmap/status documentation.

### Gate B — strengthen cross-backend state conformance

Priorities:

1. multi-step Python/C++ differential sequences;
2. state read-back after every transition;
3. make/unmake after every transition;
4. temporary effects and timers;
5. TWC transitions;
6. special spell transitions;
7. symmetry/metamorphic transformations;
8. failure minimisation for any mismatch.

A mismatch must be reduced to the smallest deterministic reproducer before changing production semantics.

### Gate C — close remaining A0 observability obligations

Use the existing explicit seams for:

- TT on/off;
- clearhash;
- node budget;
- search diagnostics;
- canonical state read-back;
- reproducible lifecycle control.

Do not claim A0 PASS until the complete acceptance contract, not merely individual seams, has been demonstrated.

### Gate D — only then empirical strength work

The Strength plan already requires explicit:

- experiment IDs;
- run IDs;
- frozen seed-generation rules;
- frozen diagnostics;
- explicit holdout policy;
- population/stratum declarations;
- dependence-aware units.

This handoff must not be used as an excuse to run ad-hoc Arena experiments without a frozen protocol.

### Gate E — only after empirical gates, move to Ares optimisation

The order remains:

```text
intrinsic / move-quality strength
        ↓
search improvements
        ↓
move ordering
        ↓
NNUE experiments
        ↓
CPU-efficiency comparisons
```

A more complicated engine is not a successful engine unless the evidence says it is better under the declared conditions.

---

## 11. How to investigate a future mismatch

When Python and C++ disagree:

### Step 1 — capture the exact state

Persist:

- canonical RWEN before the action;
- side to move;
- action text;
- relevant piece metadata;
- effects and timers;
- TWC;
- code/config revisions.

### Step 2 — classify the mismatch

Determine whether it is:

- legal-action generation;
- action parsing;
- transition semantics;
- timer lifecycle;
- state hash;
- serialization;
- make/unmake;
- engine bridge;
- independent oracle omission;
- test-fixture bug.

### Step 3 — minimise

Reduce the state until the smallest position still demonstrates the mismatch.

Avoid changing unrelated code while the semantic category is uncertain.

### Step 4 — establish the intended rule

Prefer, in order:

1. explicit current game-rule documentation;
2. existing regression tests;
3. canonical configuration;
4. existing decision records;
5. only then implementation behaviour.

If an implementation contradicts a documented rule, fix the implementation unless a deliberate design change is being made.

### Step 5 — add the regression before broadening scope

The final PR should include the minimal regression plus any broader differential coverage needed to prevent recurrence.

---

## 12. Important files and what they are for

### Rules and state

- `engine/game_state.py` — authoritative Python game-state lifecycle.
- `engine/pieces.py` — Python piece behaviour.
- `engine/heroes_config.json` — canonical hero configuration.
- `engine/HEROES_SCHEMA.md` — configuration schema.

### Native engine

- `ai/cpp_engine/board.cpp` — native board state, transitions, timers and make/unmake.
- `ai/cpp_engine/movegen.cpp` — native legal move generation.
- `ai/cpp_engine/search.cpp` — search and search-position state key.
- `ai/cpp_engine/evaluate.cpp` — classical evaluation.
- `ai/cpp_engine/nnue.cpp` / `nnue.hpp` — optional NNUE state/features.
- `ai/cpp_engine/types.hpp` — native state and undo structures.

### Ares bridge

- `ai/bot.py` — Python-facing bot integration.
- `ai/engine_bridge.py` — subprocess/native bridge and lifecycle/error handling.

### Independent references and differential tests

- `tools/analytics/legal_action_oracle.py` — independent legal-action reference.
- `tests/test_cross_backend_movegen.py` — fixed cross-backend legal-action contract.
- `tests/test_cross_backend_make_unmake.py` — lifecycle/make-unmake contract.
- `tests/test_a0_c3_native_oracle_comparison.py` — canonical oracle comparison helpers.
- `tests/test_a0_c3_native_oracle_randomized.py` — deterministic 128-seed campaign.
- `tests/test_metamorphic_properties.py` — state/action metamorphic properties.
- `tests/test_aimed_shot_twc.py` — temporary/permanent target TWC regression.
- `tests/test_engine_bridge.py` — bridge lifecycle and native diagnostic regression.

### Holdout

- `data/validation/ARES_HOLDOUT_V1.json` — protected eight-case manifest.
- `tools/analytics/holdout_validation.py` — manifest and provenance validation.
- `tools/analytics/holdout_arena.py` — protected paired execution.
- `tests/test_holdout_arena.py` — protected execution contract tests.

### Arena and measurement

- `tools/analytics/arena_tournament.py` — normal headless A/B Arena.
- `tools/analytics/arena_pairs.py` — paired result representation/validation.
- `tools/analytics/strength_calibration_protocol.py` — frozen calibration protocol checks.
- `tools/analytics/strength_calibration_report.py` — descriptive report layer.
- `tools/analytics/sprt.py` — isolated sequential-test implementation; not automatic promotion authority.

### Documentation

- `docs/ARCHITECTURE.md` — technical architecture.
- `docs/AI_ENGINE.md` — Ares architecture and optimisation principles.
- `docs/NNUE.md` — NNUE boundaries and validation.
- `docs/DEVELOPMENT_WORKFLOW.md` — development protocol.
- `docs/DECISION_AND_KNOWLEDGE_PROTOCOL.md` — knowledge-preservation protocol.
- `docs/ROADMAP.md` — long-term roadmap.
- `docs/ROADMAP_STATUS_2026-08-27.md` — strength/Arena status and experimental gates.
- `docs/DECISIONS/` — semantic and methodological decision records.

---

## 13. Local validation commands

Basic Python tests:

```bash
pytest tests/
```

Cython evaluator build:

```bash
python setup.py build_ext --inplace
```

C++ engine build:

```bash
python tools/scripts/build_cpp_engine.py
```

C++ smoke test:

```bash
python tools/scripts/build_cpp_engine.py --smoke
```

For the differential helpers, use the build modes documented by the corresponding tests/scripts. Do not assume a prebuilt local binary is trustworthy merely because it exists; rebuild it from the current checkout when diagnosing a mismatch.

---

## 14. PR documentation template for future blocks

Every substantive future PR should let a reader reconstruct the work without external context.

Recommended structure:

```markdown
## Objective

## Problem / evidence

## Decision

## Alternatives rejected

## Implementation

## Tests / CI

## What this does NOT prove

## Known limitations

## Next gate
```

For correctness bugs add:

```markdown
## Minimal reproducer
## Expected semantics
## Previous incorrect behaviour
## Regression added
```

For experimental changes add:

```markdown
## Frozen controls
## Seed policy
## Population / holdout policy
## Primary outcome
## Planned diagnostics
## Interpretation boundary
```

---

## 15. Decisions that should survive into the future

### Decision 1 — independent references stay independent

Do not make a differential oracle call the implementation under test. Otherwise the comparison can prove internal consistency without proving correctness.

### Decision 2 — fixture bugs are fixed as fixtures

When a test accidentally enters a different semantic path, correct the fixture. Do not modify production code merely to make the test pass.

### Decision 3 — current-main reconstruction beats stale-branch merging

The meaningful unit is the semantic change and its evidence, not the age or number of a pull request.

### Decision 4 — state metadata is part of correctness

Hash, TWC, turn, timers and other state must be treated as first-class state. Board visual equality alone is insufficient.

### Decision 5 — no strength claims from infrastructure

Randomized legal-action agreement is evidence of conformance for that contract. It is not evidence of stronger play.

### Decision 6 — holdout is protected by construction

The protected holdout manifest must remain distinct from development inputs. Never use it for tuning and then present it as independent validation.

### Decision 7 — no automatic promotion without declared evidence

The existence of Arena, SPRT, holdout or calibration tooling does not grant authority to promote an AI version. Promotion remains a separate policy decision requiring the declared evidence gates.

### Decision 8 — keep Ares optimisation behind correctness

Search/NNUE work should not outrun the correctness and cross-backend contracts. Optimising a semantically unstable engine creates faster evidence of the wrong behaviour.

---

## 16. Immediate continuation checklist

A fresh agent can continue from this document with the following sequence:

```text
[ ] Read README + ARCHITECTURE + DEVELOPMENT_WORKFLOW.
[ ] Verify current main SHA and open PRs.
[ ] Verify PR #236 status.
[ ] If #236 is green, merge it.
[ ] Record the merge in roadmap/status documentation.
[ ] Inspect current open issues again; do not rely on stale issue snapshots.
[ ] Continue cross-backend state-transition conformance.
[ ] Add the smallest deterministic regression before any broad refactor.
[ ] Run relevant tests locally/CI.
[ ] Create one focused PR per coherent engineering block.
[ ] Merge only after required gates pass.
[ ] Update this handoff/roadmap before starting the next conceptual block.
```

If there is no correctness blocker, do **not** invent a new production feature solely to create activity. The next task should come from the declared roadmap or a demonstrable missing contract.

---

## 17. Final status statement

As of 2026-09-04:

- the recent C3 state-lifecycle metamorphic coverage is merged;
- the native bridge non-terminal diagnostic fixture is corrected and merged;
- the websockets dependency update is rebased to current `main` and merged;
- the older TWC temporary-target issue is already fixed in production and its issue is closed;
- the explicit protected holdout execution path is already implemented and its issue is closed;
- the next active conformance improvement is FrostMage inclusion in the randomized native-vs-independent-oracle campaign (#236), pending its complete CI validation;
- no A0 acceptance or strength-promotion claim is made by these changes;
- statistical/dataset interpretation remains a separate activity and was intentionally not performed here.

The repository itself should remain the canonical source of truth. Any future agent should update this document when a material state change occurs, especially after merging #236 or discovering a new correctness boundary.
