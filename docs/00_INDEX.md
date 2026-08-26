# RedWar Documentation Index

This is the navigation entry point for `docs/`. It identifies the current source of truth for each domain without duplicating those documents.

## Current state

- [CURRENT_STATE.md](CURRENT_STATE.md) — dated snapshot of the current engineering state. It is informative, not a replacement for canonical domain documents.

## Canonical project documents

| Area | Current source of truth | Purpose |
|---|---|---|
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) | System/component boundaries and invariants |
| Game design | [GAME_DESIGN.md](GAME_DESIGN.md) | Design intent, identity and balancing philosophy |
| Game rules | [GAME_RULES.md](GAME_RULES.md) | Operational game rules and terminal conditions |
| Hero system | [HERO_SYSTEM.md](HERO_SYSTEM.md) | Hero mechanics and data/implementation contract |
| AI engine / Ares | [AI_ENGINE.md](AI_ENGINE.md) | Ares architecture, evaluation and search contract |
| NNUE | [NNUE.md](NNUE.md) | NNUE architecture, data and promotion criteria |
| AI benchmarks | [AI_BENCHMARK_PROTOCOL.md](AI_BENCHMARK_PROTOCOL.md) | Capability/regression benchmark methodology |
| Strength evaluation | [STRENGTH_EVALUATION.md](STRENGTH_EVALUATION.md) | Competitive-strength measurement and promotion evidence |
| Arena statistics | [ARENA_STATISTICAL_METHODOLOGY.md](ARENA_STATISTICAL_METHODOLOGY.md) | Statistical treatment of Arena results |
| Hold-out CI | [ARENA_HOLDOUT_CI.md](ARENA_HOLDOUT_CI.md) | Protected validation execution contract |
| Balance | [BALANCE_METHODOLOGY.md](BALANCE_METHODOLOGY.md) | Interpretation of pricing, contextual balance and roster evidence |
| Observability | [OBSERVABILITY_CONTRACT.md](OBSERVABILITY_CONTRACT.md) | Legal information visible to the agent in each game phase |
| Mechanics traceability | [MECHANICS_TRACEABILITY_MATRIX.md](MECHANICS_TRACEABILITY_MATRIX.md) | Cross-backend mechanic/data coverage |
| CI methodology | [CI_WORKFLOW_METHODOLOGY.md](CI_WORKFLOW_METHODOLOGY.md) | CI evidence and gate semantics |
| Development workflow | [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) | Engineering workflow and branch/PR process |
| Project methodology | [PROJECT_DEVELOPMENT_METHODOLOGY.md](PROJECT_DEVELOPMENT_METHODOLOGY.md) | Planning, dependencies and development blocks |
| Engineering/research methodology | [ENGINEERING_METHODOLOGY_AND_RESEARCH.md](ENGINEERING_METHODOLOGY_AND_RESEARCH.md) | Cross-cutting engineering/research method |
| Decisions/knowledge | [DECISION_AND_KNOWLEDGE_PROTOCOL.md](DECISION_AND_KNOWLEDGE_PROTOCOL.md) | How decisions, evidence and discoveries are recorded |
| Roadmap | [ROADMAP.md](ROADMAP.md) | Current engineering sequence and priorities |
| Tooling | [TOOLING.md](TOOLING.md) | Development and analysis tooling |
| Multiplayer / online | [WEB_MULTIPLAYER.md](WEB_MULTIPLAYER.md) | Online product/protocol documentation |
| Legal | [LEGAL_AND_LICENSES.md](LEGAL_AND_LICENSES.md) | Licensing and legal constraints |
| Inspirations | [INSPIRATIONS_AND_HOMAGE.md](INSPIRATIONS_AND_HOMAGE.md) | External inspirations and homage record |

## Supporting, historical and transitional documents

- `DECISIONS/` contains dated engineering decisions. These are historical records; a later decision may supersede them but old rationale is not rewritten.
- `FOUNDATION_BASELINE_2026-08-26.md` is a foundation snapshot, not a permanent source of truth.
- Dated audit/research documents record evidence and recommendations; they do not silently override canonical contracts.
- `Documento_Design_Jogo.md`, if retained, is transitional/legacy documentation and should not be treated as the authoritative source when `GAME_DESIGN.md` or `GAME_RULES.md` applies.

## Evidence hierarchy

For behaviour actually implemented, use:

```text
implementation + executable tests
        ↓
current canonical contract
        ↓
decision rationale
        ↓
audit / research
        ↓
proposal / backlog
```

A research note or historical decision does not override current implementation or a current canonical contract unless the decision explicitly changes that contract and the canonical document is updated in the same development block.

## Synchronisation rule

When implementation changes a documented contract, update the relevant canonical document in the same development block. When a decision changes the contract, update the decision record, canonical document and roadmap references together.

Do not create a parallel document for an existing subject merely because the canonical document is long. Prefer improving its structure and adding cross-links.

## Transitional migration rule

Existing paths are retained for compatibility in this phase. Physical directory moves are postponed until classification, inbound-link analysis and content reconciliation are complete.
