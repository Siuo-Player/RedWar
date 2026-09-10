# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `5c5b09f32fad3769764ea449a673790a02ab552c`  
**Data:** 2026-09-10

## Estado atual — 1.0 gate chain

```text
#370 Foundation
      ↓
#371 Gameplay
      ↓
#372 Ares
      ↓
#373 Product
      ↓
#374 Online
      ↓
#375 Release
```

#370 e #371 Gameplay estão fechados em 2026-09-10. O trabalho principal autorizado é agora #372 Ares. Preparação anterior de Ares não constitui promoção nem fecho de #372.

## #370 — Foundation

**Estado: CLOSED — 2026-09-10.**

Os contratos críticos auditados estão classificados como `CANONICAL_AND_TESTED` ou `JUSTIFIED_SPECIALIZATION`. A fronteira consolidada é `input → normalize → canonical resolution/membership → transition validation → mutate`. `fast_clone()` permanece fora do hot path C++.

## #371 — Gameplay

**Estado: CLOSED — 2026-09-10.**

### Evidência de saída

- Surrender canónico: #390/#391.
- STUN → segundo STUN → morte: #392/#394, com TWC e paridade Python/C++.
- `hero.spells` como autoridade única: #399/#400; Test Suite #2031, CodeQL #725 e AI Quality Gate #732 verdes.
- Pre-match canónico e integração Pygame/trainer: #395/#396/#397; #401 merged em `7095258388ef71e4dad2dd178c5be6f95e061337`.
- No-legal-action terminal usa `engine.legal_actions.legal_actions()`: #404/#405; #405 merged em `3e8bbe9417b584b5a4208d18852070f578bb8b77`, com Test Suite #2056, CodeQL #735 e AI Quality Gate #740 verdes.
- Effects/timing: contrato documentado em `docs/DECISIONS/2026-09-10-pre-match-and-effect-timing-contract.md` e protegido por regressões.
- Core Suite: #405 terminou com **692 passed**.

A aceitação do #371 está satisfeita para o ruleset atualmente declarado. Parâmetros de balance continuam separados de alegações de strength.

## #372 — Ares

**Estado: OPEN — gate ativa.**

Objetivo: tornar Ares forte, eficiente e confiável para uso no produto, com correctness primeiro e evidência independente para capability, performance e strength.

Preparação: #406 e `docs/ARES_EXECUTION_PLAN.md`.

### Ordem obrigatória

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

`fast_clone()` não pertence ao C++ hot path nem ao preflight de legalidade. Benchmark/NPS/dataset growth não são prova de strength.

#373 Product, #374 Online e #375 Release permanecem bloqueados até #372 cumprir a sua aceitação.

## Regras operacionais

Todo work package parte do `main` verificado, usa branch dedicada, refere o Issue canónico, implementa e testa antes do merge, passa as gates aplicáveis e sincroniza documentação quando o estado muda. Preparação futura pode ocorrer em paralelo, mas nunca contorna uma gate anterior.
