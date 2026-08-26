# RedWar Documentation Structure

## Purpose

`docs/` is the project's documentation namespace. It should describe the current system, the engineering process and the evidence used to make engineering decisions without creating competing sources of truth.

## Stable roles

Documentation is classified by role, not by filename prefix alone.

```text
docs/
├── 00_INDEX.md                         navigation and source-of-truth map
├── CURRENT_STATE.md                    dated project snapshot
├── canonical domain documents          current contracts/methodology
├── DECISIONS/                          dated historical decisions
├── audit / research documents          investigations and evidence
└── legacy / transitional documents    retained while being reconciled
```

`CURRENT_STATE.md` is intentionally time-stamped. It tells a reader where the project is now, but it must not become a competing architecture/specification document.

The first restructuring phase does not move existing files. Existing paths may be referenced by scripts, PRs, external notes or contributors.

## Source-of-truth hierarchy

When documents disagree, resolve them in this order:

1. Current implementation and executable tests for behaviour actually implemented.
2. A current canonical specification or methodology document for the intended contract.
3. A dated decision record for historical rationale.
4. Audit/research documents for evidence and recommendations.
5. Backlog/notes for proposals that are not yet accepted.
6. Dated snapshots for temporal context only.

A research, audit or snapshot document must not silently override a canonical project contract.

## Required relationships

Important engineering changes should form a traceable chain:

```text
problem / finding
      ↓
research or audit
      ↓
decision (when policy changes)
      ↓
canonical specification / methodology
      ↓
implementation
      ↓
tests / CI evidence
      ↓
roadmap / current-state snapshot
```

Not every change needs every stage, but changes to a project contract should not leave the documents in contradictory states.

## Current canonical domains

The main domains exposed by `00_INDEX.md` are:

- architecture;
- game design and rules;
- hero system;
- AI/Ares and NNUE;
- benchmark and testing;
- competitive strength / Arena;
- observability;
- CI;
- engineering workflow/methodology;
- decisions and knowledge;
- roadmap;
- tooling;
- online/multiplayer.

Balance is currently a documented gap: do not create multiple competing balance entry points until a canonical balance methodology is established.

## Duplication policy

Before creating a new document, check `00_INDEX.md` and the related canonical document.

Create a new document only when at least one is true:

- it records a distinct historical decision;
- it is a genuinely separate research/audit artefact;
- it defines a separate stable contract;
- its lifecycle or audience differs materially from the existing document.

Otherwise update the existing canonical document.

## Historical and legacy documents

Files in `DECISIONS/` are append-only historical records in spirit: do not rewrite old rationale to match later reality. Mark supersession explicitly and link the newer decision.

Dated audits retain their original findings. Current truth belongs in the canonical documents they informed.

Legacy/transitional documents may remain for compatibility while their content is reconciled. They must be clearly identified as non-authoritative from the navigation layer and should eventually either be superseded or absorbed into the correct canonical document.

## Synchronisation rule

When implementation changes a documented contract, update the relevant canonical document in the same development block. When a decision changes the contract, update the decision record, canonical document and roadmap references together. Update `CURRENT_STATE.md` only when the resulting project state materially changes; do not use it as a substitute for canonical documentation.

## Migration policy

Physical reorganisation is a separate change from content reconciliation.

Before moving a document:

1. classify it;
2. identify its canonical owner;
3. identify inbound links/references;
4. reconcile its content with current code/tests;
5. update indexes and links;
6. only then move or archive it.

This keeps documentation restructuring reviewable and prevents a large move from hiding semantic changes.
