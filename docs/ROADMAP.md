# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `3e8bbe9417b584b5a4208d18852070f578bb8b77`  
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

#370 e **#371 Gameplay estão fechados em 2026-09-10**. O trabalho principal autorizado é agora **#372 Ares**. Preparação anterior de Ares não constitui promoção nem fecho de #372.

## #371 — Gameplay

**Estado: CLOSED — 2026-09-10.**

### Evidência de saída

- Surrender canónico: #390/#391.
- STUN → segundo STUN → morte: #392/#394, com TWC e paridade Python/C++.
- `hero.spells` como autoridade única: #399/#400; gates verdes.
- Pre-match canónico e integração Pygame/trainer: #395/#396/#397; #401 merged em `7095258388ef71e4dad2dd178c5be6f95e061337`.
- `check_game_over()` consume o action-space canónico: #404/#405; #405 merged em `3e8bbe9417b584b5a4208d18852070f578bb8b77`, com Test Suite #2056, CodeQL #735 e AI Quality Gate #740 verdes.
- Effects/timing documentados e testados.
- Test Suite #2056 terminou com **692 passed**.

A aceitação do #371 está satisfeita para o ruleset atualmente declarado. Parâmetros de balance continuam separados de alegações de strength.

## #372 — Ares

**Estado: OPEN — gate ativa.**

Preparação: #406 e `docs/ARES_EXECUTION_PLAN.md`. A sequência obrigatória é:

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

`fast_clone()` não pertence ao C++ hot path nem ao preflight de legalidade. Benchmark/NPS/dataset growth não são prova de strength.

## Gates seguintes

#373 Product → #374 Online → #375 Release permanecem bloqueados até #372 cumprir a sua aceitação.

## Regras operacionais

Trabalho sempre a partir de `main` verificado, em branch dedicada, com Issue canónico, testes/gates e documentação sincronizada. Preparação futura pode ocorrer em paralelo, mas não contorna gates anteriores.
