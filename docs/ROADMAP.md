# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `3e8bbe9417b584b5a4208d18852070f578bb8b77`  
**Data:** 2026-09-10

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas.

## Vocabulário obrigatório

`DOCUMENTED` = descrito.  
`IMPLEMENTED` = existe no código alvo.  
`TESTED` = existe teste executável relevante.  
`VALIDATED` = foi submetido à validação apropriada para a alegação.  
`PROVEN` = a evidência é suficiente para a alegação específica sob o protocolo vigente.

Uma fase só pode ser `CLOSED` quando os critérios de aceitação forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e melhoria de dataset ≠ melhoria de strength.

## Estado atual — 1.0 gate chain

A execução corrente segue a cadeia de issues canónica:

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

## #370 — Foundation

**Estado: CLOSED — 2026-09-10.**

A matriz final classifica os contratos críticos auditados como `CANONICAL_AND_TESTED` ou `JUSTIFIED_SPECIALIZATION`; não há um `DUPLICATED_AUTHORITY`, `DOCUMENTATION_DRIFT` ou `UNPROTECTED_GAP` remanescente identificado no inventário fundacional. A matriz não constitui alegação de balance, strength ou superioridade de search.

A fronteira fundacional consolidada é:

```text
input action
→ normalize canonical action
→ canonical resolution / membership
→ transition-domain validation
→ only then mutate
```

`fast_clone()` permanece restrito a fixtures/replay/reference tooling em Python e fora do hot path C++ da Ares.

## Histórico de infraestrutura já concluído

Os lanes independentes anteriores B–G foram executados a partir do baseline comum `1f65f65d6b4827f0d403d8e6d2bb0f735eda0c42` e merged com as gates do repositório (#329–#334). Esta tranche fecha infraestrutura/regressões específicas; não equivale a declarar concluídas as fases de produto, strength, balance ou online.

## #371 — Gameplay

**Estado: CLOSED — 2026-09-10.**

Objetivo: tornar o ruleset 1.0 efetivamente jogável e estável sobre a fundação fechada.

Escopo canónico: board 8×8; orçamento draft atual de 200 pontos por cor; uma ação por turno; draft/placement secreto antes do match e sem compras durante o match; movimento, ataques, passivas, spells e invocações dos heróis; sequência STUN → segundo STUN enquanto stunned → morte; vitória/derrota/surrender; terminação sem ação legal; parâmetro de 50 turnos sem captura permanente; timing fire/ice/terrain; geração e execução determinísticas e sem autoridades duplicadas.

### Evidência de saída

- **Surrender:** #390/#391 introduziram e endureceram `ActionType.SURRENDER` como comando terminal não-board, resolvido canonicamente e sem mistura no action-space de board.
- **STUN:** #392/#394 fecharam `stun → segundo stun enquanto stunned → morte`, incluindo TWC e paridade Python/C++.
- **Spell authority:** #399/#400 eliminaram a segunda fonte de capacidade de spell e tornaram `hero.spells` a autoridade de capability; Test Suite #2031, CodeQL #725 e AI Quality Gate #732 verdes.
- **Pre-match:** #395/#396 criaram a autoridade canónica para orçamento, home rows, `draftable`, equipas e cópias; #397 ligou-a ao Pygame draft/start e trainer; PR #401 merged em `7095258388ef71e4dad2dd178c5be6f95e061337`.
- **Terminal/action-space:** #404/#405 eliminaram a segunda definição de “há ação legal?” em `check_game_over()` e passaram a consumir `engine.legal_actions.legal_actions()`; PR #405 merged em `3e8bbe9417b584b5a4208d18852070f578bb8b77`, com Test Suite #2056, CodeQL #735 e AI Quality Gate #740 verdes após correção do fixture.
- **Effects/timing:** o contrato de timers e fire/ice/terrain está documentado em `docs/DECISIONS/2026-09-10-pre-match-and-effect-timing-contract.md` e protegido por regressões dedicadas.
- **Core regression suite:** a execução validada do #405 terminou com **692 passed**, cobrindo action execution/resolution, legal-action oracle, hero schema traceability, lifecycle/TWC/specials, differential Python/C++, NNUE integration, pre-match, terminal conditions, surrender, effects, trainer e entrypoint manual.

### Julgamento da gate

A aceitação do #371 está satisfeita para o ruleset atualmente declarado: cada regra crítica possui uma autoridade de implementação/especificação única ou especialização justificada; os cenários críticos passam pela fronteira canónica; efeitos, vitória, turnos e condições terminais possuem regressões executáveis; e não permanece uma ambiguidade conhecida que bloqueie o jogo local. Parâmetros de balance permanecem explicitamente separados de alegações de strength.

## #372 — Ares

**Estado: OPEN — gate ativa.**

Objetivo: tornar Ares forte, eficiente e confiável para uso no produto, com correctness primeiro e evidência independente para capability, performance e strength.

**#406** é o child preparatório atual, organizando as lanes de correctness/state, tactical capability, search hypotheses, classical evaluator, NNUE parity/cost, matched-resource benchmarks, Arena strength e configuração aceite.

**#409** prepara `docs/ARES_EXECUTION_PLAN.md` e sincroniza a fotografia operacional. Esta preparação não substitui a aceitação de #372.

### Ordem obrigatória

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

### Lane A — correctness/state

Revalidar make/unmake, state identity/hash, side-to-move, repetition observation, TWC, stun/lifespan/spawn cooldown, terrain effects e terminal behavior contra a semântica de Gameplay já fechada. Toda otimização deve preservar o post-state e a reversibilidade.

### Lane B — tactical capability

Construir/validar corpus determinístico de fenómenos específicos: capturas, stun/segundo-stun, spells/áreas, passivas, temporários, fogo/gelo, TWC, bloqueios e quiet positions. Isto mede competência em cenários, não strength global.

### Lane C — search

Isolar hipóteses de move ordering, quiescence/tactical extensions, pruning/reductions semanticamente seguros, transposition table, node/time budgets, killer/history e tratamento dos diferentes tipos de ação. Nenhuma promoção por mais NPS, profundidade ou nodes sem orçamento comparável.

### Lane D — classical evaluation

Congelar o evaluator clássico como baseline. Medir mudanças de um termo de cada vez e separar material, posicionamento, stun, temporários, efeitos, TWC e termos estratégicos.

### Lane E — NNUE

Sequência obrigatória:

```text
full-sync oracle
→ incremental make/unmake parity
→ feature/update regressions
→ CPU cost
→ Arena
```

NNUE funcional ou com menor training loss não implica maior strength. Só passa a default se o protocolo competitivo/económico mostrar benefício sobre o baseline.

### Lane F — controlled performance

Comparar sob recursos equivalentes, registando nodes/tempo, NPS como métrica secundária, versão de código/configuração, runner e inputs de reprodução. Performance isolada não é strength.

### Lane G — Arena

Comparar baseline e candidato com cores alternadas, provenance explícita, orçamento comparável, pairing de openings/seeds quando exigido e incerteza apropriada. Dataset maior, point estimate positivo ou SPRT isolado não autoriza promoção fora do protocolo definido.

### Lane H — accepted configuration

Registar commit exato, configuração de search/eval/NNUE, corpus e versões, condições de benchmark/Arena e limitações. Só depois selecionar a configuração Ares para a fase Product.

`fast_clone()` não pertence ao C++ hot path nem ao preflight de legalidade.

## #373 — Product

**Estado: BLOCKED UNTIL #372 CLOSES.**

Abrange aplicação local, replay/telemetria e UX. UI sofisticada e polish ficam subordinados à estabilidade das regras e do núcleo de execução.

## #374 — Online

**Estado: BLOCKED UNTIL #373 CLOSES.**

Servidor authoritative, multiplayer, matchmaking, contas e contratos de sessão/rede.

## #375 — Release

**Estado: BLOCKED UNTIL #374 CLOSES.**

QA final, segurança, operação, documentação e critérios de release.

## Regras operacionais

Todo work package deve:

1. partir do `main` verificado;
2. trabalhar numa branch dedicada;
3. referenciar o issue canónico e o critério de aceitação;
4. implementar e testar antes do merge;
5. passar as gates aplicáveis do repositório;
6. atualizar a documentação canónica no mesmo pacote quando o estado mudou;
7. atualizar o issue com evidência concreta e fechar apenas após o resultado estar integrado em `main`.

A preparação de um gate futuro pode ocorrer em paralelo quando os contratos estão estáveis, mas não pode contornar um blocker de correctness nem transformar benchmark/capability em prova de strength.
