# Ares Move-Ordering Baseline — 2026-09-10

**Governing gate:** #372 Ares  
**Purpose:** freeze a reproducible pre-change search-ordering measurement on the current tactical corpus.

This is a measurement baseline only. It does not change Ares search behavior and does not establish a strength claim.

## Protocol

- Use the production Ares C++ engine built from the branch's exact commit.
- Use the deterministic tactical capability suite as the position corpus.
- Measure fixed node budgets so runner wall-clock speed cannot change the search budget.
- Record the bestmove legality through the canonical action-space.
- Record the first budget at which a case stops producing a legal/expected capability result.
- Keep trace output diagnostic; traces are not correctness fixtures.

## Current corpus

The suite currently contains the original capability families plus the validated `second-stun-lethal` case:

- FrostMage five-target Nevada spell;
- second-stun lethal via `SPELL nevada A5 D5`;
- high-value capture;
- declared ranged spell;
- defensive purify;
- lifespan/spawn cooldown;
- TWC-adjacent capture.

FrostMage's historical `STUN` action reference is obsolete: the current rules/API expose the effect through the Nevada spell, so strict-choice baselines must use the current spell action rather than the retired action form.

## Baseline runner

`tools/analytics/move_ordering_baseline.py` invokes the tactical suite at a dense fixed-node scan. Future move-ordering candidates must be compared against the same corpus and budgets before Arena testing.

## Experimental boundary

A lower node threshold or higher NPS is only an efficiency observation. A candidate is not promoted from this lane without correctness/regression evidence and independent Arena evidence under matched conditions.
