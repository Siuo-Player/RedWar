# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `7095258388ef71e4dad2dd178c5be6f95e061337`  
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

#370 foi fechado. O gate principal ativo é **#371 Gameplay**. O child técnico atual é **#404**, para eliminar a segunda autoridade de legalidade na terminação por bloqueio. Em paralelo, **#406** prepara as lanes de evidência de Ares sem alterar a ordem dos gates.

## #370 — Foundation

**Estado: CLOSED — 2026-09-10.**

### Evidência de saída

- **#386** — matriz de autoridade machine-readable + Markdown, merged em `b83e1b851911a295052802572b9fbb7369a462ff` com Test Suite #1964, CodeQL #692 e AI Quality Gate #707 verdes.
- **#381** — sincronização do estado/documentação fundacional, merged em `612221b88381cf740bab6d2ab9e31acfb98c6324` com Test Suite #1948, CodeQL #685 e AI Quality Gate #701 verdes.
- **#380** — eliminação da duplicação de vocabulário de spells em `_validate_transition()`, merged em `8534b2f59392b9e9779bb9ac8e55d7a8b3e53613` com as gates verdes.
- **#391 / #392** — surrender canónico + hardening do contrato, e segundo-STUN do Ignite com paridade Python/C++, integrados com as gates relevantes verdes.

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

Os lanes independentes anteriores B–G foram executados a partir do baseline comum `1f65f65d6b4827f0d403d8e6d2bb0f735eda0c42` e merged com as três gates do repositório:

- **#329** — determinismo do audit emparelhado; `29973ffb6e7d270ab8ccc9289307ab11e2f24506`.
- **#330** — ausência de `fast_clone` no C++ da Ares; `d08a700864d8ed0fe9dc274f8495a01f81105641`.
- **#331** — encoding NNUE por perspetiva; `fdd1c3516e410b53608a95e554597a577ef6610e`.
- **#332** — isolamento replay/telemetria; `d07f52f981de0eb0606bef1823beabca61348ae1`.
- **#333** — bounds do Auto-Pricer; `71bc812d170a8556b9dfde98b4f95202f36190b9`.
- **#334** — fundação de sessão autoritativa server-side; `845b00a500fff7b3aab2f0c35920bace5d198cc6`.

Esta tranche fecha infraestrutura/regressões específicas; não equivale a declarar concluídas as fases de produto, strength, balance ou online.

## #371 — Gameplay

**Estado: OPEN — em execução.**

Objetivo: tornar o ruleset 1.0 efetivamente jogável e estável sobre a fundação fechada.

Escopo canónico: board 8×8; orçamento draft atual de 200 pontos por cor; uma ação por turno; draft/placement secreto antes do match e sem compras durante o match; movimento, ataques, passivas, spells e invocações dos heróis; sequência STUN → segundo STUN enquanto stunned → morte; vitória/derrota/surrender; terminação sem ação legal; parâmetro de 50 turnos sem captura permanente; timing fire/ice/terrain; geração e execução determinísticas e sem autoridades duplicadas.

### Progresso atual

- **Concluído:** surrender canónico e hardening do fluxo terminal; segundo STUN do Ignite com TWC/paridade Python-C++; autoridade de spell declarations sem whitelist duplicada.
- **Concluído:** **#397** ligou a autoridade de validação canónica de pre-match draft/placement aos chamadores Pygame e treino; merged no baseline `7095258388ef71e4dad2dd178c5be6f95e061337`.
- **Ativo:** **#404 / PR #405** — fazer a terminação por ausência de ações consumir diretamente `engine.legal_actions.legal_actions()`, removendo o scan paralelo de geradores dentro de `GameState.check_game_over()`. O PR acrescenta regressões para a delegação à autoridade canónica e para uma posição realmente bloqueada.
- **Concluído no contrato:** timing de efeitos foi explicitado: a criação não consome o primeiro tick; o timer avança quando o lado proprietário se torna ativo. Fire aplica stun elegível na transição; ice impede passagem/centro Nevada. O contrato está em `docs/DECISIONS/2026-09-10-pre-match-and-effect-timing-contract.md`.

Critério de saída: cada regra declarada tem uma implementação/especificação autorizada; cenários críticos passam pela ação canónica; efeitos, vitória e edges de turnos têm regressões executáveis; não existe ambiguidade conhecida que impeça jogo local; parâmetros de balance são explícitos.

## #372 — Ares

**Estado: BLOCKED UNTIL #371 CLOSES; PREPARATORY WORK ALLOWED.**

Objetivo: correctness primeiro, depois capability/search/eval/classical baseline, optional NNUE, controlled benchmarks e Arena A/B com provenance. Benchmark ≠ strength; mais nodes ≠ strength; NNUE existente ≠ superioridade; dataset maior ≠ strength.

**#406** é o child preparatório atual e documenta as lanes que podem avançar sem alterar Gameplay: correção/invariantes, tactical capability corpus, search hypotheses, evaluator baseline, NNUE parity/cost, matched-resource benchmarks e Arena strength evidence.

Critério de promoção: apenas depois de #371 fechar e de cada alteração relevante passar correctness/regression → capability/performance → independent Arena evidence.

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
