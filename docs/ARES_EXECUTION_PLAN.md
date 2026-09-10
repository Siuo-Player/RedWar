# RedWar — Ares 1.0 Execution Plan

**Governing issue:** #372  
**Preparatory child:** #406  
**Governance:** #365  
**Verified baseline at plan update:** `main` @ `3a06d2edf1dc4f32b8719eb3d0da8167613424eb` (2026-09-10)

Este documento define a sequência operacional de Ares sem bloquear trabalho independente. As outras lanes podem evoluir continuamente; esta planificação deve ser reconciliada com o `main` antes de cada promoção.

## Cadeia obrigatória por candidato

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ accepted configuration
```

Uma métrica de um estágio não substitui a seguinte.

## Estado das lanes no baseline atual

- **A — correctness/state:** native make/unmake reversibility já está ligado à CI pelo #421. Isto prova o helper existente sob CI; não equivale a prova matemática de todos os estados possíveis.
- **B — tactical capability:** o corpus foi expandido pelo #410 e a validação canónica de bestmoves foi reforçada pelo #417.
- **C — search experiments:** preparação em andamento. #434 torna o baseline de move-ordering reproduzível e machine-readable; não altera o search.
- **D — classical evaluator:** #411 congelou o baseline clássico, incluindo registo machine-readable. Não deve existir um segundo baseline concorrente para o mesmo contrato.
- **E — NNUE:** #420 acrescentou benchmark controlado de custo incremental vs full-sync e exige equivalência entre caminhos. Não prova superioridade competitiva.
- **F — controlled performance:** deve usar o mesmo corpus e orçamento entre candidatos; NPS é apenas métrica auxiliar.
- **G — Arena strength:** permanece o único mecanismo para claims de strength global. Deve usar condições comparáveis, cores alternadas, provenance e separação tuning/hold-out/Arena.
- **H — accepted configuration:** só depois de A–G fechadas conforme o claim é que um candidato pode substituir o baseline de Product.

## Lane A — correctness / state contract

A invariância que importa à pesquisa é:

```text
position import
→ canonical action-space / native action representation
→ make
→ search state
→ unmake
→ same relevant state and identity
```

Cobrir side-to-move, terminal/no-action conditions, TWC, stun/lifespan/spawn cooldown, terrain/effects e state hash. `fast_clone()` não é hot-path C++ nem mecanismo de preflight de legalidade.

O #421 passou a executar `tests/cpp_reversibility_test.cpp` no workflow nativo. Qualquer alteração de regras ou de representação deve reabrir esta validação e o differential correspondente.

## Lane B — tactical capability corpus

Usar casos pequenos, versionados e determinísticos para fenómenos específicos de RedWar: segundo-STUN letal, capturas, spells/áreas, defesa, lifespan/cooldown e TWC.

A capability normal deve exigir:

```text
bestmove exists
+ parses
+ belongs to canonical legal action-space
```

`--strict-choice` continua a ser evidência mais forte, com interpretação separada de strength/capability.

## Lane C — search hypotheses

Trabalhar uma hipótese por vez:

1. move ordering;
2. quiescence/tactical extensions;
3. reductions/pruning apenas quando semanticamente seguros;
4. transposition-table policy;
5. killer/history;
6. node-budget efficiency.

O baseline de move-ordering deve ser tomado de `tools/analytics/move_ordering_baseline.py` com o corpus e budgets explicitamente registados. Um ganho de NPS ou de nodes por si só não é promoção.

## Lane D — classical evaluator

O baseline é o definido por #411. Futuras alterações devem modificar termos isolados e manter:

```text
same position/state
+ same search budget
→ baseline score / candidate score
→ capability
→ matched-budget search
→ Arena, quando houver claim competitivo
```

Não criar outro documento “canónico” para o mesmo baseline sem integração explícita.

## Lane E — NNUE

A sequência é:

```text
full-sync oracle
→ incremental make/unmake parity
→ feature/update regressions
→ controlled cost
→ matched-budget search
→ Arena
```

O #420 mede o custo de incremental vs full-sync e exige equivalência. A integração atual continua opcional. Antes de remover `sync_board()` do caminho quente, a hipótese de performance deve ser confirmada por medição e acompanhada por regressões de paridade.

## Lane F — controlled performance

Comparar candidatos com recursos equivalentes. Registar commit, compilador/runner quando relevante, orçamento de nodes/tempo, corpus e configuração. Não misturar alterações de evaluator/search/NNUE no mesmo experimento quando isso destruir a atribuição causal.

## Lane G — Arena strength

Comparar baseline e candidato com orçamento comparável, alternância de cores, openings/seeds emparelhados quando o protocolo o exigir, provenance explícita e incerteza reportada.

```text
capability ≠ performance ≠ strength
```

Dataset maior, melhor NPS, training loss menor ou um resultado isolado não autorizam promoção.

## Lane H — accepted configuration

Registar a configuração vencedora ou a decisão de manter o baseline:

- commit;
- search settings;
- evaluator;
- NNUE on/off e modelo/hash;
- corpus/versionamento;
- orçamento competitivo;
- protocolo Arena;
- limitações conhecidas.

Só então atualizar o baseline de Product.

## Paralelização segura

As lanes podem avançar em paralelo desde que cada uma declare a base exata utilizada. Quando o `main` avançar, qualquer PR antigo deve ser reavaliado contra o novo baseline antes do merge.

A regra prática é:

```text
new main
→ re-check changed contracts
→ keep independent work
→ discard/rebase duplicated work
→ rerun evidence on final head
```

Isto é especialmente importante para trabalho concorrente: a existência de dois PRs verdes não implica que a combinação dos dois seja verde.

## Definition of done — #372

Ares só pode avançar para Product quando:

```text
correctness/regressions green
→ deterministic capability established
→ controlled performance evidence
→ independent Arena strength evidence for any strength claim
→ reproducible accepted configuration
```

NNUE deve estar explicitamente justificada como default ou permanecer opcional. Nenhuma lane pode transformar o seu próprio benchmark num claim global de strength.