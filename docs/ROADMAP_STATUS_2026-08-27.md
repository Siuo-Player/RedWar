# RedWar — Roadmap Status

**Snapshot:** 2026-08-27  
**Verified main baseline:** `1e20e679a92e749c4fa4b57efcec19ce56046267`

## Estado consolidado

A fundação de correctness, provenance e observabilidade da Ares está concluída. O trabalho atual está concentrado na validação empírica do Strength antes de voltar a alterar a política de promoção ou iniciar um novo bloco agressivo de search/NNUE.

### Blocos concluídos mais recentemente

- **PR #127** — adapter executável de Arena JSONL para o auditor empírico de Strength, agrupando cada par A/B com inversão de cores como uma unidade independente.
- **PR #128** — correção do bootstrap empírico: o par continua a ser a unidade de reamostragem, mas o Elo-equivalente é calculado sobre os resultados agregados de cada amostra. A suavização de fronteira de 0,5 é usada apenas no caminho descritivo do paired bootstrap.
- **PR #129** — análise descritiva de matchup/contexto e deteção de ciclos de intransitividade. `rules_version` e `node_budget` são sempre tratados como controlos experimentais e nunca são misturados entre condições incompatíveis.

As PRs #127, #128 e #129 foram integradas em `main` após os respectivos gates de CI.

## Próxima sequência de trabalho

```text
real Arena / Strength calibration
        ↓
matchup / context validation
        ↓
SPRT validation with real Arena outcomes
        ↓
sequential promotion gate
        ↓
intrinsic / move-quality strength
        ↓
search / move-ordering / NNUE optimisation
```

### 1. Strength/Arena — prioridade imediata

Ainda falta calibrar empiricamente o Strength Rating e a incerteza com **jogos reais da Arena**, incluindo os pares completos e a estrutura pentanomial.

Requisitos para a próxima experiência:

- mesmo `rules_version`;
- mesmo `node_budget`;
- openings/seeds fixos e auditáveis;
- cores balanceadas com inversão por par;
- retenção do JSONL bruto;
- validade e motivo de terminação preservados;
- summary estatístico derivado do JSONL, nunca usado como substituto do dado bruto.

A análise não deve usar um pequeno resultado histórico como se fosse uma calibração definitiva.

### 2. Matchup/contexto

`tools/analytics/strength_matchup_context.py` já fornece a infraestrutura descritiva para agrupar resultados por direção, abertura e outros contextos, mantendo separados os controlos experimentais.

Próximo objetivo empírico: obter comparações suficientes entre mais de dois participantes/contextos para verificar se existe estrutura de matchup ou intransitividade persistente.

O resultado continua descritivo até existir uma base estatística adequada.

### 3. SPRT

`tools/analytics/sprt.py` continua isolado. Ainda não deve controlar promoção.

Antes de o ligar ao gate é necessário verificar, com resultados reais:

- escala Elo;
- tratamento de draws;
- dependência entre jogos pareados;
- inválidos e pares incompletos;
- escolha dos parâmetros do teste;
- comportamento de `accept`, `reject` e `continue` em experiências reais.

### 4. Promoção automática

A margem heurística existente não deve ser elevada a autoridade estatística simplesmente por aumentar o número de jogos.

O objetivo é substituir a decisão heurística por um teste sequencial apenas depois de o comportamento estatístico estar validado empiricamente.

## Evidência real já disponível

Existe uma Arena histórica documentada em `docs/DECISIONS/2026-08-25-action-aware-ordering-arena-result.md` com 20 jogos: Challenger 14, Baseline 6, Draws 0. O documento estima aproximadamente +147 Elo-equivalente de forma descritiva, mas explicitamente não trata esse resultado como prova estatística geral.

Esse resultado não contém, no snapshot documental, todos os jogos individuais necessários para o paired bootstrap. Não será reconstruído artificialmente.

## Bloqueio operacional identificado

A infraestrutura histórica do GitHub Actions nem sempre expõe os JSONL brutos de uma Arena antiga através do conector atual. Assim, antes de qualquer “calibração” baseada em dados antigos, deve ser garantida uma forma reprodutível de conservar e recuperar os artefactos JSONL de novas execuções da Arena.

## Regra de desenvolvimento

Cada descoberta relevante deve ser documentada antes de iniciar o próximo bloco. Qualquer alteração que mexa no estimador de força, Arena, SPRT ou política de promoção deve permanecer isolada, testada e validada antes de merge.
