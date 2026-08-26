# RedWar Documentation Structure

## Purpose

`docs/` is the project's documentation namespace. It should describe the current system, the engineering process and the evidence used to make engineering decisions without creating competing sources of truth.

## Stable roles

The documentation is classified by role rather than by filename prefix alone.

```text
docs/
├── 00_INDEX.md                         navigation
├── canonical current-state documents   architecture, AI, testing, Arena, balance, roadmap
├── DECISIONS/                          dated historical decisions
├── audit / research documents           investigations and evidence
└── legacy documents                    retained until audited and reconciled
```

The first restructuring phase deliberately does not move existing files. Existing paths may be referenced by scripts, PRs, external notes or contributors.

## Source-of-truth hierarchy

When documents disagree, resolve them in this order:

1. Current implementation and executable tests for behaviour actually implemented.
2. A current canonical specification or methodology document for the intended contract.
3. A dated decision record for historical rationale.
4. Audit/research documents for evidence and recommendations.
5. Backlog/notes for proposals that are not yet accepted.

A research or audit document must not silently override a canonical project contract.

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
roadmap state
```

Not every change needs every stage, but changes to a project contract should not leave the documents in contradictory states.

## Current canonical domains

The main domains currently exposed by `00_INDEX.md` are:

- architecture;
- AI/Ares;
- benchmark and testing;
- competitive strength / Arena;
- CI;
- game/hero design;
- engineering workflow;
- decisions and knowledge;
- roadmap.

Balance and future research areas should be added to the index when they acquire a stable canonical document rather than creating multiple competing entry points.

## Duplication policy

Before creating a new document, check `00_INDEX.md` and the related canonical document.

Create a new document only when at least one is true:

- it records a distinct historical decision;
- it is a genuinely separate research/audit artefact;
- it defines a separate stable contract;
- its lifecycle or audience differs materially from the existing document.

Otherwise update the existing canonical document.

## Historical documents

Files in `DECISIONS/` are append-only historical records in spirit: do not rewrite old rationale to match later reality. Mark supersession explicitly and link the newer decision.

Similarly, dated audits should retain their original findings. Current truth belongs in the canonical documents they informed.

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