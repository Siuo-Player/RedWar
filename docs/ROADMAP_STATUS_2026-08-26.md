# Roadmap status reconciliation — 2026-08-26

This note records the roadmap items that are demonstrably implemented in `main` and therefore must not be described as future work in `ROADMAP.md`.

## Strength / Arena infrastructure now implemented

The following roadmap items are complete at the infrastructure level:

- [x] game/result data model with explicit validity and termination provenance;
- [x] commit/version and experiment metadata sufficient to identify an A/B run;
- [x] explicit colour/seed/opening/budget metadata and balance audit;
- [x] regression/development/hold-out experiment-set definitions and protected hold-out manifest;
- [x] baseline Elo-compatible strength rating with uncertainty;
- [x] rating summary integration into Arena results;
- [x] explicit invalid-game exclusion from strength inference/promotion;
- [x] paired-game/pentanomial support and integration tests;
- [x] isolated SPRT implementation and tests.

These do **not** imply that the final statistical promotion system is complete.

## Strength work that remains open

- [ ] calibrate the strength model with real Arena observations;
- [ ] validate colour/opening/seed effects on real experiments;
- [ ] add contextual strength analysis for matchup/intransitivity;
- [ ] validate the sequential test against real Arena data;
- [ ] replace the provisional promotion heuristic with a validated sequential gate;
- [ ] study intrinsic/move-quality strength as a second explanatory axis.

## Interpretation rule

A roadmap checkbox should mean that the corresponding capability exists and is tested in `main`. A capability may be `[x]` while its statistical validation, production policy, or later refinement remains `[ ]`.

The dated note is evidence/navigation only. `ROADMAP.md`, the canonical domain documents, and the executable implementation/tests remain authoritative for current project behaviour and policy.
