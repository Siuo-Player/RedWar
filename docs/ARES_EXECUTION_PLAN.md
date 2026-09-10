# RedWar — Ares 1.0 Execution Plan

**Governing issue:** #372  
**Preparatory child:** #406  
**Governance:** #365  

Este documento prepara a gate Ares em paralelo com #371 sem alterar o ruleset e sem permitir a sua promoção antes do fecho de Gameplay.

## Cadeia obrigatória por candidato

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

Uma métrica de um estágio não substitui a seguinte.

## Lane A — correctness / state contract

Antes de otimizar search, verificar a invariância da posição que Ares realmente pesquisa:

```text
position
→ canonical legal action-space
→ validated transition
→ make
→ search state
→ unmake
→ same relevant state
```

Cobrir side-to-move, terminal conditions, repetition observation, TWC, stun/lifespan/spawn cooldown, terrain effects e state hash. `fast_clone()` não é hot-path C++ nem preflight de legalidade.

## Lane B — tactical capability corpus

Criar um corpus pequeno, versionado e determinístico que cubra fenómenos específicos de RedWar: stun/segundo-stun, kills, spells/áreas, passivas, lifespan/cooldown, fogo/gelo, TWC, posições bloqueadas e posições quiet.

Saída: capability/regression scores reproduzíveis. Isto mede competência em cenários, não strength global.

## Lane C — search hypotheses

Avaliar isoladamente:

1. move ordering;
2. quiescence/tactical extensions;
3. pruning/reductions apenas quando semanticamente seguros;
4. transposition-table policy;
5. node/time budgeting;
6. killer/history adaptados aos tipos de ação.

Nenhuma alteração é promovida por simplesmente aumentar nodes, profundidade ou complexidade.

## Lane D — classical evaluator

Fixar a avaliação clássica atual como baseline. Alterar um termo por hipótese e medir separadamente material, posição, stun, unidades temporárias, efeitos, TWC e termos estratégicos futuros.

Saída: candidatos de evaluator com diffs e orçamento controlado.

## Lane E — NNUE

A sequência é:

```text
full-sync oracle
→ incremental make/unmake parity
→ feature/update regressions
→ CPU cost
→ Arena
```

Training loss menor ou integração funcional não provam strength. NNUE só passa a default se superar o baseline clássico pelo protocolo competitivo/eficiência aceite.

## Lane F — controlled performance

Comparar sob recursos equivalentes e registar orçamento de nodes/tempo, NPS como métrica secundária, inputs de reproducibilidade e variação do runner. Performance isolada não é strength.

## Lane G — Arena strength

Comparar candidato e baseline com cores alternadas, provenance explícita, orçamento comparável, emparelhamento de openings/seeds quando exigido pelo protocolo, incerteza e critérios de decisão pré-definidos.

Dataset maior, point estimate positivo ou um resultado SPRT isolado não autorizam promoção fora do protocolo.

## Lane H — accepted configuration

Registar commit, configuração de search/eval/NNUE, versões dos corpus, condições de benchmark/Arena e limitações conhecidas. Só então o Ares selecionado passa a baseline para Product.

## Paralelização

Enquanto #371 estiver ativo, as lanes B, D, E, F e partes de G podem trabalhar com o baseline atual. A lane A deve ser revalidada se Gameplay alterar semântica de legalidade/estado. Nenhuma lane pode declarar #372 fechado antes de #371.

```text
                   ┌─ tactical corpus
                   ├─ evaluator baseline
#371 Gameplay ─────┼─ NNUE parity/cost
                   ├─ benchmark harness
                   └─ Arena/provenance
                              ↓
                    candidate validation
                              ↓
                       Ares promotion
```

## Definition of done — #372

Ares só está pronto para Product quando correctness/regressions estiverem verdes, o candidato selecionado tiver evidência controlada de capability/performance, strength independente pela Arena e uma configuração reproduzível e documentada. NNUE deve estar explicitamente justificada como default ou mantida opcional.