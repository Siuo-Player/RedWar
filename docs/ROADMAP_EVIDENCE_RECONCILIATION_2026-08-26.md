# Roadmap Evidence Reconciliation — 2026-08-26

This is a dated audit of roadmap items that were completed during the foundation/strength-validation work. It exists to prevent the roadmap from silently drifting from the implementation while the canonical roadmap is reconciled in a later documentation block.

## Strength / Arena infrastructure now present

The following capabilities are present in the current `main` baseline:

- experiment-set metadata with explicit evidence-set identity;
- protected hold-out manifest and hash validation;
- result provenance for valid/invalid games and termination reason;
- exclusion of invalid observations from strength inference;
- balanced-color/opening/seed auditing before statistical summaries;
- baseline Elo-compatible strength estimation with uncertainty;
- isolated SPRT implementation and tests;
- CI contract separating protected hold-out from promotion execution.

## Not yet completed

The following remain future work:

- calibrated SPRT against real RedWar Arena data;
- validated paired/pentanomial statistical promotion model;
- automatic promotion authority based on sequential testing;
- contextual strength/matchup analysis;
- intrinsic move-quality strength;
- full A/B experiment runner that consumes only validated evidence sets.

## Interpretation

The existence of the infrastructure above does **not** mean the final strength methodology is complete. The project currently has the machinery required to preserve evidence correctly, while the inferential model and promotion authority remain deliberately provisional.

The canonical methodology remains `STRENGTH_EVALUATION.md`; this file is a dated reconciliation note and must not become a competing source of truth.
