# RedWar — Roadmap Status

**Snapshot:** 2026-08-27  
**Verified main baseline:** `34d7904e54935cf1bc9cc6de48e1e16c184042f3`  
**Current work branch:** `feat/real-arena-scientific-dataset-2026-08-27`

## Estado consolidado

A fundação de correctness, provenance e observabilidade da Ares está concluída. O trabalho atual está concentrado na validação empírica do Strength antes de alterar a política de promoção ou iniciar um novo bloco agressivo de search/NNUE.

A documentação de pesquisa foi entretanto atualizada com um protocolo executável de **replicação e calibração**. A principal consequência é que uma segunda tranche não deve ser apenas “mais jogos”: deve introduzir runs e variação experimental suficientes para avaliar estabilidade, dependência e generalização.

### Blocos concluídos mais recentemente

- **PR #127** — adapter executável de Arena JSONL para o auditor empírico de Strength, agrupando cada par A/B com inversão de cores como uma unidade independente.
- **PR #128** — correção do bootstrap empírico: o par continua a ser a unidade de reamostragem, mas o Elo-equivalente é calculado sobre os resultados agregados de cada amostra. A suavização de fronteira de 0,5 é usada apenas no caminho descritivo do paired bootstrap.
- **PR #129** — análise descritiva de matchup/contexto e deteção de ciclos de intransitividade. `rules_version` e `node_budget` são sempre tratados como controlos experimentais e nunca são misturados entre condições incompatíveis.
- **PR #134** — persistência do primeiro dataset real da Arena, com provenance, schema científico, unidades pareadas independentes para resampling e auditoria empírica descritiva.

As conclusões metodológicas posteriores estão registadas em [`DECISIONS/2026-08-27-strength-replication-calibration-protocol.md`](DECISIONS/2026-08-27-strength-replication-calibration-protocol.md).

## Próxima sequência de trabalho

```text
real Arena dataset persistence
        ↓
replication across experiment runs
        ↓
population/context variation
        ↓
paired effect + between-run stability
        ↓
draw / invalid / dependence analysis
        ↓
uncertainty calibration
        ↓
hold-out validation
        ↓
SPRT operating-characteristic validation
        ↓
sequential promotion gate
        ↓
intrinsic / move-quality strength
        ↓
search / move-ordering / NNUE optimisation
```

### 1. Strength/Arena — prioridade imediata

A primeira experiência persistida contém **100 jogos em 50 pares completos de inversão de cor**. Os 50 pares são unidades adequadas para a análise pareada desta experiência, mas **não são 50 condições experimentais independentes**, porque combinações de opening/seed são reutilizadas.

A experiência deve portanto ser tratada como evidência condicionada à população descrita pelo manifest.

A próxima tranche deve preferir vários runs intencionais, por exemplo:

```text
Run A — controlo replicado
Run B — novos seeds
Run C — openings/scenarios estratificados
Run D — população mais ampla
```

Cada run deve congelar antes da execução:

- challenger/baseline/rules versions;
- compute/node budget;
- opening/scenario sampling;
- seed-generation rule;
- colour pairing;
- validity/termination policy;
- primary outcome/statistic;
- diagnostics;
- hold-out policy.

A análise deve preservar a hierarquia:

```text
raw game → paired unit → experiment run → population/stratum
```

Resampling e incerteza devem respeitar a dependência real. O JSONL bruto continua a ser a fonte de verdade; o dataset derivado é uma vista analítica.

### 2. Matchup/contexto

`tools/analytics/strength_matchup_context.py` fornece a infraestrutura descritiva para agrupar resultados por direção, abertura e outros contextos.

O objetivo agora não é apenas encontrar um ciclo, mas verificar se diferenças de matchup/contexto permanecem quando repetidas em novos runs e populações. Um ciclo observado continua a ser diagnóstico; não prova, sozinho, intransitividade estratégica estável.

### 3. Draws, inválidos e dependência

O primeiro dataset real teve zero draws. Isso significa que a implementação de draw handling continua sem validação empírica real.

Novas experiências devem reter explicitamente:

- draws legítimos;
- jogos inválidos;
- jogos incompletos;
- termination reason;
- pares incompletos quando existirem.

Não converter `max plies` em draw sem que isso represente a regra real do jogo.

A dependência de condições repetidas deve ser contabilizada antes de interpretar o número de jogos como informação independente.

### 4. Calibração da incerteza

O `engineering_uncertainty_proxy_v1` permanece como baseline de produção.

Antes de o substituir, a evidência de múltiplos runs deve responder:

1. se a incerteza acompanha a variação observada;
2. se muda por contexto/população;
3. se o comportamento é alterado por draws;
4. se a dependência de condições repetidas reduz materialmente a informação efectiva;
5. se uma alternativa melhora a calibração fora dos dados usados para a escolher.

Nenhuma alteração do proxy é autorizada apenas porque uma única experiência produziu uma largura diferente.

### 5. Hold-out

Para qualquer refinamento do modelo, deve existir pelo menos um run, estrato ou subconjunto previamente declarado como hold-out.

A sequência exigida é:

```text
calibration data
→ model choice frozen
→ hold-out data
→ validation
```

O mesmo dado não pode servir simultaneamente para descobrir o efeito, escolher o modelo e declarar a validação final.

### 6. SPRT

`tools/analytics/sprt.py` continua isolado e sem autoridade de promoção.

Antes de o ligar ao gate, validar no mínimo:

- known-null experiments;
- known-positive-effect experiments;
- draws;
- invalid/incomplete games;
- repeated-condition dependence;
- stopping behaviour;
- false-positive / false-negative behaviour.

O simples facto de o SPRT existir ou passar testes sintéticos não é suficiente para activar promoção automática.

## Evidência real já disponível

Existe uma experiência persistida em `data/arena/strength/2026-08-27-control-100.json`, com 100 jogos válidos, 50 vitórias Challenger, 50 Baseline, 0 draws e 50 pares completos. O seu audit é explicitamente descritivo e usa 50 unidades emparelhadas.

O audit actualmente registado usa `bootstrap_samples=20000`, `seed=0` e reporta `empirical_half_width=41.475...`; este valor não é um IC95% calibrado e não autoriza substituir o uncertainty proxy nem alterar a promoção. O dataset e o audit preservam o hash canónico correspondente.

Existe também uma Arena histórica documentada em `docs/DECISIONS/2026-08-25-action-aware-ordering-arena-result.md` com 20 jogos. Esse resultado permanece evidência histórica descritiva e não será reconstruído artificialmente como paired dataset.

## Regra de desenvolvimento

Cada descoberta relevante deve ser documentada antes de iniciar o próximo bloco. Qualquer alteração que mexa no estimador de força, Arena, SPRT ou política de promoção deve permanecer isolada, testada e validada antes de merge.

O protocolo de replicação/calidação é agora o contrato operacional para o próximo bloco; o Roadmap só deve avançar para search/NNUE depois de este gate produzir evidência suficiente ou uma decisão explícita de `COLLECT MORE DATA` / `KEEP PROMOTION DISABLED`.
