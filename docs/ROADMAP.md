# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `3e8bbe9417b584b5a4208d18852070f578bb8b77`  
**Data:** 2026-09-10

Este é o **único documento que define a ordem operacional do trabalho**.

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

## Vocabulário obrigatório

`DOCUMENTED` = descrito. `IMPLEMENTED` = existe no código alvo. `TESTED` = existe teste executável relevante. `VALIDATED` = foi submetido à validação apropriada. `PROVEN` = a evidência é suficiente para a alegação específica.

Uma fase só pode ser `CLOSED` quando os critérios de aceitação forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e crescimento de dataset ≠ melhoria de strength.

## #370 — Foundation

**Estado: CLOSED — 2026-09-10.**

Os contratos críticos auditados estão classificados como `CANONICAL_AND_TESTED` ou `JUSTIFIED_SPECIALIZATION`. A fronteira consolidada é `input → normalize → canonical resolution/membership → transition validation → mutate`. `fast_clone()` permanece fora do hot path C++.

## #371 — Gameplay

**Estado: CLOSED — 2026-09-10.**

### Evidência de saída

- **Surrender:** #390/#391 estabeleceram `ActionType.SURRENDER` como comando terminal não-board, com resolução e execução canónicas.
- **STUN:** #392/#394 fecharam `stun → segundo stun enquanto stunned → morte`, com TWC e paridade Python/C++.
- **Spell authority:** #399/#400 tornaram `hero.spells` a autoridade única de capability; Test Suite #2031, CodeQL #725 e AI Quality Gate #732 verdes.
- **Pre-match:** #395/#396 criaram a autoridade canónica de orçamento/home rows/`draftable`/equipas/cópias; #397 ligou-a ao Pygame e treino; PR #401 merged em `7095258388ef71e4dad2dd178c5be6f95e061337`.
- **Terminal/action-space:** #404/#405 fizeram `check_game_over()` consumir `engine.legal_actions.legal_actions()`; PR #405 merged em `3e8bbe9417b584b5a4208d18852070f578bb8b77`, com Test Suite #2056, CodeQL #735 e AI Quality Gate #740 verdes.
- **Effects/timing:** contrato documentado em `docs/DECISIONS/2026-09-10-pre-match-and-effect-timing-contract.md` e protegido por regressões dedicadas.
- **Core regression suite:** a execução validada do #405 terminou com **692 passed** e cobriu execution/resolution, legal-action oracle, schema traceability, lifecycle/TWC/specials, differential Python/C++, NNUE, pre-match, terminal, surrender, effects, trainer e entrypoint manual.

### Julgamento da gate

A aceitação do #371 está satisfeita para o ruleset atualmente declarado: regras críticas com autoridade única ou especialização justificada, cenários críticos na fronteira canónica, regressões para effects/victory/turns/terminal e nenhuma ambiguidade conhecida que bloqueie o jogo local. Parâmetros de balance permanecem separados de alegações de strength.

## #372 — Ares

**Estado: OPEN — gate ativa.**

Objetivo: tornar Ares forte, eficiente e confiável para uso no produto, com correctness primeiro e evidência independente para capability, performance e strength.

**#406** organiza as lanes de correctness/state, tactical capability, search, classical evaluator, NNUE parity/cost, matched-resource benchmarks, Arena strength e accepted configuration.

**#409** prepara `docs/ARES_EXECUTION_PLAN.md` e a fotografia operacional. A preparação não substitui a aceitação de #372.

### Ordem obrigatória

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

### Lane A — correctness/state

Revalidar make/unmake, state identity/hash, side-to-move, repetition observation, TWC, stun/lifespan/spawn cooldown, terrain effects e terminal behavior contra a semântica de Gameplay fechada. Toda otimização deve preservar post-state e reversibilidade.

### Lane B — tactical capability

Construir/validar corpus determinístico de capturas, stun/segundo-stun, spells/áreas, passivas, temporários, fogo/gelo, TWC, bloqueios e quiet positions. Capability não é strength global.

### Lane C — search

Isolar move ordering, quiescence/tactical extensions, pruning/reductions semanticamente seguros, TT policy, node/time budget, killer/history e tratamento dos diferentes tipos de ação. Não promover por NPS, profundidade ou nodes isoladamente.

### Lane D — classical evaluation

Congelar o evaluator clássico como baseline e alterar um termo de cada vez, separando material, posição, stun, temporários, efeitos, TWC e termos estratégicos.

### Lane E — NNUE

```text
full-sync oracle
→ incremental make/unmake parity
→ feature/update regressions
→ CPU cost
→ Arena
```

NNUE só passa a default se demonstrar benefício competitivo/eficiência pelo protocolo aceite.

### Lane F — controlled performance

Comparar com recursos equivalentes e registar orçamento, runner, versão/configuração e inputs de reprodução. Performance isolada não é strength.

### Lane G — Arena

Comparar baseline/candidato com cores alternadas, provenance explícita, orçamento comparável, pairing de openings/seeds quando exigido e incerteza apropriada. Dataset maior ou SPRT isolado não autoriza promoção fora do protocolo.

### Lane H — accepted configuration

Registar commit exato, configuração search/eval/NNUE, corpus/versões, condições de benchmark/Arena e limitações antes de selecionar a configuração para Product.

`fast_clone()` não pertence ao C++ hot path nem ao preflight de legalidade.

## #373 — Product

**Estado: BLOCKED UNTIL #372 CLOSES.**

## #374 — Online

**Estado: BLOCKED UNTIL #373 CLOSES.**

## #375 — Release

**Estado: BLOCKED UNTIL #374 CLOSES.**

## Regras operacionais

Todo work package deve partir do `main` verificado, usar branch dedicada, referenciar o Issue canónico, implementar/testar, passar as gates aplicáveis, sincronizar documentação quando o estado muda e fechar o Issue apenas após integração e evidência. Gates futuras podem preparar-se em paralelo quando os contratos estão estáveis, mas não podem contornar blockers anteriores nem converter capability/benchmark em prova de strength.
