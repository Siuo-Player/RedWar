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

RedWar distinguishes the first **local playable release** from the longer-term competitive Ares programme.

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

The 1.0-Lite path is not an alternative definition of competitive Ares. It establishes a frozen, reproducible Ares execution baseline that is sufficiently reliable to play and to serve as one controlled agent inside the Balance Lab.

## Estado

- **#370 Foundation — CLOSED.** Contratos base e fronteira de execução fechados para o ruleset atual.
- **#371 Gameplay — CLOSED.** Ruleset 1.0 jogável fechado para o escopo declarado.
- **#372 Ares — OPEN.** Competitive/open-project AI track. It is no longer required to block a first local 1.0-Lite release.
- **#526 1.0-Lite — CLOSED.** Product split and Ares Balance Baseline are closed; remaining local release acceptance is tracked by #555.
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

The Lite baseline is a **product execution contract**, not a balance certificate and not a competitive strength claim.

Minimum Ares confidence for Lite:

- correctness/regression suites green;
- legal action generation and state transitions reliable;
- reliable termination with no known hangs in representative matches;
- deterministic/reproducible fixed-budget behaviour;
- stable, documented difficulty levels;
- frozen exact engine revision, ruleset, search budget, seed policy and experimental population/context;
- sufficient capability to generate complete, provenance-valid controlled evidence for Balance Lab analysis.

### Balance methodology constraint

The baseline does not make Ares into the Balance Lab. Ares is one experimental agent used by the Balance Lab.

Hero/economy balance must not be inferred from a single marginal statistic such as:

```text
hero → global win rate
```

The evidence model must retain, where applicable:

```text
hero
× position
× allied composition
× opponent / matchup
× initiative / colour
× ruleset
× seed
× Ares policy / player-skill context
× outcome / terminal reason
```

The controlled flow is:

```text
freeze baseline
→ matched games / seeds / colours
→ selection + provenance audit
→ contextual matchup / composition / counter evidence
→ candidate intervention
→ independent hold-out
→ manual/design decision
```

For colour/first-player compensation, calibration games and hold-out games must remain separate; repeatedly selecting compensation from the same observations does not create independent confirmation.

For hero pricing, integer cost is normally the first intervention and should be explored coarse-to-fine. If cost cannot repair the observed strategic defect, escalate to the smallest hero-specific mechanic intervention justified by the evidence. Candidate evaluation must include contextual/matchup and ecosystem effects rather than only the changed hero's aggregate win rate.

`tools/balance/auto_pricer.py` is legacy diagnostic tooling, not an authoritative balance method. It must not automatically justify a price, mechanic or roster change. Its aggregate occurrence/performance heuristic does not replace contextual matchup, composition, positional, population and hold-out analysis.

Balance results remain descriptive and conditional on the frozen baseline, declared population and protocol. They are not claims of intrinsic hero power, universal game balance or competitive Ares strength.

## Local 1.0-Lite acceptance — #555

Current implementation path:

```text
#526 Lite baseline
      ↓
#557 Local 2P / hot-seat — CLOSED
      ↓
#558 Settings + audio — PR #561 / CI pending
      ↓
#555 final product acceptance
```

#557 is merged into `main` at `2c6c9e9`. PR #561 contains the remaining settings/audio scope and must pass the normal Test Suite, AI Quality Gate and CodeQL before merge. Closing #555 additionally requires the final local smoke-test and validation record; this acceptance gate does not close #372.

## Not required for 1.0-Lite

- statistically significant improvement over previous Ares versions;
- NNUE as default;
- continued search optimisation such as LMR;
- historical competitive rating;
- closure of #372;
- an authoritative automatic price change produced by `auto_pricer.py`.

## Execution model

The Ares programme and the local product can proceed in parallel once the Lite baseline is frozen:

```text
                         Ares
                           │
               ┌───────────┴───────────┐
               │                       │
       Lite Balance Baseline     Competitive Ares
               │                       │
       Balance Lab input          #372 research
       + local opponent           Arena / search /
                                  evaluation / NNUE
               │                       │
               └──────────┬────────────┘
                          │
                    future integration
```

An Ares improvement remains open-project research until explicitly selected as the product baseline. Changing the product Ares baseline requires revalidation of dependent balance evidence; it does not automatically happen because a competitive experiment succeeded.

## Execution parallel

Trabalho posterior pode preparar-se em paralelo quando não falsifica uma dependência. Uma preparação não fecha nem ultrapassa um gate anterior.

The 1.0-Lite path is specifically allowed to progress while #372 remains open, because it uses a frozen execution baseline rather than claiming that Ares has completed the competitive-strength programme.

## Regra documental

Este é o único roadmap operacional. Estado transitório, SHAs, resultados de CI e notas de handoff pertencem ao Git/Issues/CI. Decisões duráveis pertencem a `docs/DECISIONS/`.
