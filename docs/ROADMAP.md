# RedWar — Roadmap Operacional

## Gate chain 1.0 Full

```text
#370 Foundation
      ↓
#371 Gameplay
      ↓
#372 Ares competitive/product-strength gate
      ↓
#373 Product Full
      ↓
#374 Online
      ↓
#375 Release Full
```

## 1.0-Lite path

RedWar now distinguishes the first **local playable release** from the longer-term competitive Ares programme.

```text
#370 Foundation
      ↓
#371 Gameplay
      ↓
#526 1.0-Lite / Ares Balance Baseline
      ↓
local Product acceptance
      ↓
local 1.0-Lite release
```

The 1.0-Lite path is not an alternative definition of competitive Ares. It establishes a frozen, reproducible Ares baseline that is sufficiently trustworthy for gameplay and controlled hero/economy balance work.

## Estado

- **#370 Foundation — CLOSED.** Contratos base e fronteira de execução fechados para o ruleset atual.
- **#371 Gameplay — CLOSED.** Ruleset 1.0 jogável fechado para o escopo declarado.
- **#372 Ares — OPEN.** Competitive/open-project AI track. It is no longer required to block a first local 1.0-Lite release.
- **#526 1.0-Lite — OPEN.** Define and validate the product-facing Ares Balance Baseline and the reduced local-release scope.
- **#373 Product — OPEN/BLOCKED for 1.0 Full by #372.** Stable local work may proceed through #526 when contracts are independent of the competitive Ares gate.
- **#374 Online — BLOCKED for the Full product sequence by #372/#373.**
- **#375 Release — BLOCKED for the Full product sequence by #372/#373/#374.**

## #372 — Ares competitive track

Objective: make Ares strong enough, fast enough and scientifically trustworthy enough for competitive/product-strength promotion.

This track remains open after 1.0-Lite and is explicitly suitable for continued open-project development.

Order:

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

Rules:

- `fast_clone()` não é hot path C++ nem preflight de legalidade;
- benchmark, NPS, node count, dataset size ou training loss não são prova de strength;
- search changes devem ser hipóteses isoladas com validação própria;
- NNUE só pode ser promovida após paridade, custo e evidência competitiva adequados;
- não alterar as regras do jogo para contornar um blocker de Ares.

## #526 — 1.0-Lite / Ares Balance Baseline

The Lite baseline is a **product and balance contract**, not a competitive strength claim.

Minimum Ares confidence for Lite:

- correctness/regression suites green;
- legal action generation and state transitions reliable;
- reliable termination with no known hangs in representative matches;
- deterministic/reproducible fixed-budget behaviour;
- stable, documented difficulty levels;
- frozen engine revision, search budget and population/context for balance experiments;
- enough consistency to produce useful hero/economy matchup statistics under the declared baseline;
- statistics interpreted as descriptive evidence conditional on the Lite baseline, not as proof of globally optimal or competitive strength.

Not required for 1.0-Lite:

- statistically significant improvement over previous Ares versions;
- NNUE as default;
- continued search optimisation such as LMR;
- historical competitive rating;
- closure of #372.

## Execution model

The Ares programme and the local product can proceed in parallel once the Lite baseline is frozen:

```text
                         Ares
                           │
               ┌───────────┴───────────┐
               │                       │
       Lite Balance Baseline     Competitive Ares
               │                       │
       product + balancing       #372 research
               │                  Arena / search /
               │                  evaluation / NNUE
               │                       │
               └──────────┬────────────┘
                          │
                    future integration
```

An Ares improvement remains open-project research until explicitly selected as the product baseline. Changing the product Ares baseline requires revalidation of the balance/statistics context; it does not automatically happen because a competitive experiment succeeded.

## Execution parallel

Trabalho posterior pode preparar-se em paralelo quando não falsifica uma dependência. Uma preparação não fecha nem ultrapassa um gate anterior.

The 1.0-Lite path is specifically allowed to progress while #372 remains open, because it uses a frozen balance baseline rather than claiming that Ares has completed the competitive-strength programme.

## Regra documental

Este é o único roadmap operacional. Estado transitório, SHAs, resultados de CI e notas de handoff pertencem ao Git/Issues/CI. Decisões duráveis pertencem a `docs/DECISIONS/`.
