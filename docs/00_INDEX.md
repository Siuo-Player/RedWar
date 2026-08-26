# RedWar Documentation Index

This file is the navigation entry point for the `docs/` tree.

## Canonical project documents

| Area | Current source of truth | Purpose |
|---|---|---|
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) | System/component architecture |
| AI engine | [AI_ENGINE.md](AI_ENGINE.md) | Ares architecture and implementation contract |
| AI benchmarks | [AI_BENCHMARK_PROTOCOL.md](AI_BENCHMARK_PROTOCOL.md) | Capability/regression benchmark methodology |
| Strength evaluation | [STRENGTH_EVALUATION.md](STRENGTH_EVALUATION.md) | Competitive-strength measurement methodology |
| Arena statistics | [ARENA_STATISTICAL_METHODOLOGY.md](ARENA_STATISTICAL_METHODOLOGY.md) | Statistical treatment of Arena results |
| Hold-out CI | [ARENA_HOLDOUT_CI.md](ARENA_HOLDOUT_CI.md) | Protected validation execution contract |
| CI methodology | [CI_WORKFLOW_METHODOLOGY.md](CI_WORKFLOW_METHODOLOGY.md) | CI evidence and gate semantics |
| Development workflow | [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) | Engineering workflow and branch/PR process |
| Decisions/knowledge | [DECISION_AND_KNOWLEDGE_PROTOCOL.md](DECISION_AND_KNOWLEDGE_PROTOCOL.md) | How decisions and knowledge are recorded |
| Roadmap | [ROADMAP.md](ROADMAP.md) | Current engineering sequence and priorities |
| Hero system | [HERO_SYSTEM.md](HERO_SYSTEM.md) | Hero mechanics/data contract |
| Game design | [Documento_Design_Jogo.md](Documento_Design_Jogo.md) | Game-design reference |

## Evidence and research

- `DECISIONS/` contains dated engineering decisions. These are historical records; when superseded, the replacement document is the operational source of truth.
- Research/audit documents should identify their evidence status and should not silently override implementation contracts.
- `FOUNDATION_BASELINE_2026-08-26.md` and `MECHANICS_TRACEABILITY_MATRIX.md` record the current foundation gates established from the project-study audit.

## Document roles

### Normative / canonical
Defines a rule, contract, architecture, methodology or current project state. Future changes must update the canonical document rather than creating a competing document.

### Historical decision
Explains why a decision was made. It should not be rewritten to reflect later changes; a later decision should supersede it explicitly.

### Audit / research
Records investigation, evidence and findings. It may recommend changes but does not itself redefine implementation truth.

### Index / navigation
Provides links and classification. It should remain lightweight and should not duplicate large sections of canonical documents.

## Synchronisation rule

When implementation changes a documented contract, update the relevant canonical document in the same development block. When a decision changes the contract, add/update a decision record and then update the affected canonical document and roadmap references.

Do not create parallel documents for the same subject merely because the existing document is long. Prefer improving its structure and adding cross-links.

## Transitional rule

Existing paths are retained for compatibility in this phase. Physical directory moves are postponed until the documentation audit identifies an unambiguous target and all links/references can be migrated safely.
