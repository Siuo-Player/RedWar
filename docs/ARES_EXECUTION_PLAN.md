# RedWar — Ares 1.0 Execution Plan

**Governing issue:** #372  
**Preparatory child:** #406  
**Governance:** #365  

Este documento define como preparar e executar a gate Ares sem criar dependências artificiais entre correctness, search, evaluation, performance e strength.

## Regra central

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

Uma métrica de uma etapa não substitui a seguinte.

## Lane A — correctness / state contract

Verificar a invariância da posição que Ares realmente pesquisa:

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

Criar um corpus determinístico e versionado cobrindo:

- movimento e ataques;
- stun e segundo-stun;
- mortes e combinações forçadas;
- spells e áreas;
- passivas;
- lifespan/cooldown;
- fogo/gelo/terreno;
- TWC;
- posições bloqueadas;
- posições quiet.

O resultado mede capability em cenários específicos, não strength global.

## Lane C — search

Investigar isoladamente:

1. move ordering/history;
2. quiescence e forcing frontier;
3. LMR;
4. aspiration windows;
5. TT replacement/aging;
6. pruning/NMP/LMP apenas onde a semântica RedWar o justificar.

Cada hipótese deve partir do mesmo baseline e ter teste/benchmark próprio.

## Lane D — classical evaluation

Fixar o evaluator clássico atual como baseline. Alterar um termo de cada vez e medir material, posição, stun, unidades temporárias, efeitos, TWC, mobilidade/ameaças e termos estratégicos.

Não ajustar pesos finais com o mesmo corpus usado para a avaliação independente de strength.

## Lane E — NNUE

A sequência é:

```text
full-sync oracle
→ incremental make/unmake parity
→ feature/update regressions
→ CPU cost
→ fixed-budget search comparison
→ Arena
```

A existência de NNUE ou uma loss menor não demonstra superioridade. `sync_board()` permanece sempre disponível como oracle/recovery path.

## Lane F — controlled performance

Comparar com orçamento equivalente e registar:

- nodes/time budget;
- NPS como métrica secundária;
- profundidade atingida;
- latência;
- melhor-jogada estabilidade;
- condições do runner;
- versão exata do executável/configuração.

Performance isolada não é strength.

## Lane G — Arena strength

Só após correctness e candidatos de search/evaluation estáveis:

```text
baseline
vs
candidate
```

com cores alternadas, regras idênticas, orçamento comparável, provenance explícita, openings/seeds conforme o protocolo, hold-out separado e incerteza reportada.

Um point estimate positivo, dataset maior ou um SPRT isolado não autoriza promoção fora do protocolo.

## Lane H — accepted configuration

Guardar commit, parâmetros de search/evaluation/NNUE, corpus, ambiente de benchmark/Arena, resultado estatístico e limitações conhecidas. Só então a configuração selecionada pode tornar-se baseline para Product.

## Paralelização segura

Enquanto #371 está fechado e #372 é a gate ativa, as lanes B–F podem avançar em paralelo a partir do mesmo baseline quando não tiverem dependências de work reais. Qualquer alteração de Gameplay que mude semântica de estado/legalidade obriga a repetir a Lane A.

```text
main baseline
   ├─ tactical corpus
   ├─ evaluator baseline
   ├─ NNUE parity/cost
   ├─ search hypotheses
   ├─ benchmark harness
   └─ Arena/provenance
             ↓
      individual evidence
             ↓
       accepted winners
             ↓
    composite revalidation
             ↓
       Ares promotion
```

Não empilhar várias ideias numa única alteração só porque parecem complementares.

## Definition of Done — #372

Ares só fecha quando:

- a correção/regressão relevante está verde;
- capability crítica está coberta por corpus determinístico;
- alterações de search/evaluation têm evidência controlada;
- a configuração selecionada tem evidência independente de strength;
- NNUE está justificada como default ou permanece opcional;
- a configuração final é reproduzível e documentada.

Preparação deste documento não fecha #372 por si só.