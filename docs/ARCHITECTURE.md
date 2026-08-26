# RedWar — Technical Architecture

## 1. Central principle

RedWar should have **one game semantics**. UI, AI, Arena and server-facing components must not invent their own rules.

The current boundary is:

```text
                      Product / interfaces
                ┌────────────┬────────────┐
                ▼            ▼            ▼
               UI         Online        CLI/tools
                │            │            │
                └────────────┼────────────┘
                             ▼
                      Game Core / Rules
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
             Ares                      Services
          search/eval                telemetry/data
```

`engine/` is the reference for game rules. `ai/` consumes the state and rules; duplicated rule semantics require an explicit performance/portability reason and differential coverage.

## 2. Current architecture state — 2026-08-26

The project is no longer represented accurately by a dated 2026-08-23 snapshot. The current architecture is a Python game/rules layer with a C++ Ares hot path, differential bridges/tests, Arena/analysis tooling and a separate online surface under active development.

```text
engine/
  state, rules, heroes and action semantics

ai/
  bot integration + C++ Ares

ui/
  presentation/local product surface

online/
  client/network/server components under development

tools/
  Arena, analysis, balance, NNUE, build and audit tooling

tests/
  regression, cross-backend, property/metamorphic and experimental validation

data/
  validation datasets and generated experiment material

docs/
  canonical contracts, methodology, decisions, audits and roadmap
```

The historical NNUE PR #49 is **not** part of the current architecture contract; it was closed without merge. The current truth is the code and tests present on `main`, with NNUE infrastructure present but incremental BoardState hot-path integration still an open engineering block.

## 3. Boundaries

### `engine/`

Responsible for:

- position representation;
- legal actions;
- state transitions;
- timers and effects;
- terminal conditions;
- hero configuration/data semantics.

It must not depend on UI.

### `ai/`

Responsible for:

- search-side action generation/ordering;
- alpha-beta/PVS search;
- TT and search heuristics;
- classical and NNUE evaluation;
- node/time limits;
- bot/engine protocol integration.

Search remains independent from presentation.

### `tools/`

Responsible for processes outside a normal game:

```text
tools/
├── analytics/     # Arena, deterministic openings, game analysis, trainer
├── balance/       # auto-pricer and balance analysis
├── nnue/          # features, teacher data, training/export
└── scripts/       # build and development audits
```

Tools must not duplicate `engine/` rules merely for convenience.

### `tests/`

Tests verify invariants rather than becoming a second game implementation.

Current priorities include:

- make/unmake;
- hash consistency;
- legal/illegal actions;
- timers/effects/stun;
- Python/C++ differential behaviour;
- boundary/overflow cases;
- NNUE feature parity;
- Arena result/evidence contracts.

## 4. Long-term direction

The stable boundary remains:

```text
                    Game Core
                ┌───────┼────────┐
                ▼       ▼        ▼
              Ares    Server      UI
                │       │
                ▼       ▼
              Tools / telemetry
```

Implementation details can change; interfaces between these areas should change much less.

## 5. Python and C++

During the migration, equivalent positions must remain comparable:

```text
RWEN / BoardState
      │
      ├── Python
      └── C++
            │
            ▼
      equivalent state
```

Core invariants:

1. same position → same legal actions;
2. `make → unmake` → original position;
3. incremental hash remains consistent;
4. same terminal states;
5. same interpretation of timers/effects;
6. identical NNUE features for the same position.

## 6. Observability

The current local game-mode contract is defined by [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md): hidden information applies to draft/setup, while the battle state is public and Ares may receive the complete battle state. This is resolved for the current local mode and must not be treated as an open Ares dependency.

Future online/variant modes require a separate client observation contract; the local full-state RWEN representation must not be assumed safe for network exposure.

## 7. Reproducible evidence boundary

Important experiments must preserve enough information to answer:

- which engine/rules versions were tested;
- which dataset/opening/seed was used;
- node/time budget;
- result and termination reason;
- whether each game/observation was valid;
- what evidence class it belongs to (regression, development or protected hold-out);
- why a change was accepted or rejected.

The evidence-set policy is documented through `docs/00_INDEX.md` and the current validation/hold-out contracts.

## 8. Modularity

Production files above approximately 1000 lines are candidates for division. Large hero configuration may be an exception when concentration simplifies maintenance.

Do not create modules merely to reduce line count. Each module needs an identifiable responsibility.

## 9. Documentation and safe restructuring

Architecture is canonicalized by this document. Historical snapshots and audits must not present themselves as current architecture.

Documentation and directory restructuring should happen in small, reviewable blocks. Structure tooling must audit by default and never delete/replace files automatically. Directory moves that require imports/workflow changes are separate engineering blocks with reference checks before and after migration.
