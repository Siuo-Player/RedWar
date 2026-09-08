# RedWar — Project Reasoning Spine

**Estado:** operacional  
**Baseline verificado:** `main` @ `e17afcd54ad57635e222f3b3c9a5bb9966df9394`  
**Data:** 2026-09-08

Este é o eixo de raciocínio transversal do RedWar. Não substitui documentos de domínio nem `ROADMAP.md`: explica a cadeia de dependências e o nível de evidência necessário para cada tipo de afirmação.

## 1. Hierarquia que não pode ser confundida

Para saber **o que o sistema faz agora**, usar primeiro:

```text
implementação atual + testes executáveis
```

Para saber **qual é o contrato operacional atual**, usar os documentos canónicos.

Para saber **por que uma decisão histórica foi tomada**, usar `DECISIONS/`.

Para saber **o que foi investigado/proposto**, usar audits/research.

Para saber **o que fazer a seguir**, usar exclusivamente [`ROADMAP.md`](ROADMAP.md).

Snapshots antigos são contexto histórico; não vencem o `main` nem um contrato canónico atual.

## 2. Estados de conhecimento

```text
DOCUMENTED
    ↓
IMPLEMENTED
    ↓
TESTED
    ↓
VALIDATED
    ↓
PROVEN (para uma alegação específica)
```

A sequência é conceptual, não uma promoção automática. Uma implementação pode existir sem estar suficientemente testada; um teste pode existir sem validar generalização; uma validação de capability não prova strength.

## 3. Linha causal completa

Toda alteração material deve poder ser reconstruída como:

```text
problema / oportunidade
        ↓
contrato afetado
        ↓
evidência existente
        ↓
hipótese
        ↓
menor alteração que testa a hipótese
        ↓
teste de correção
        ↓
differential / property / benchmark
        ↓
medição independente de custo ou força, quando aplicável
        ↓
decisão: aceitar / rejeitar / continuar
        ↓
contrato canónico atualizado
        ↓
ROADMAP atualizado
```

Quando um passo não se aplica, a razão deve ser explícita.

## 4. Dependência técnica

```text
GAME_RULES / HERO_SYSTEM
        ↓
ação e estado canónicos
        ↓
Python reference
        ↕ differential
        C++ Ares hot path
        ↓
search / evaluation
        ↓
Arena / strength evidence
        ↓
balance decisions
        ↓
produto / online
```

UI/replay/telemetria é transversal ao estado observado:

```text
rules + state
   ↓
interaction / replay / telemetry
   ↓
product evidence
```

Por isso **correctness, capability, performance, strength, balance e UX** são alegações distintas.

## 5. Estado atual que limita a sequência

A0 é um gate histórico fechado. O baseline atual permanece em **A0.1 Semantic Closure**.

### Fechado e evidenciado

- Inquisitor silence/stun: regressão explícita em #292;
- Python repetition observation: idempotência em #299;
- FrostMage unreachable code: removido e protegido por AST regression em #300;
- special-spell legality parity: #303;
- canonical `GameAction` boundary: #306;
- `execute_action()` normalization: #308;
- terminal contract contra o `alpha_beta()` real: #310;
- canonical action resolution seam: #321;
- fixed node-budget contract: cobertura dedicada existente.

### Ainda aberto

- `GameState.execute_action()` ainda não tem, no `main`, a autoridade completa de execution legality que una action-space membership a transition-domain validation antes da mutação; #317 permanece aberto;
- native repetition/history ainda não é um contrato equivalente ao `state_history` Python;
- future semantic changes continuam a exigir differential evidence conforme a matriz.

Estas pendências não podem ser anuladas por benchmark, dataset, Elo ou uma CI verde.

Para A.1 a separação arquitetural é obrigatória:

```text
normalização/resolução canónica
        ↓
action-space membership
        ↓
transition-domain validation
        ↓
mutation
```

`fast_clone()` não é parte desta fronteira. Não deve ser usado para preflight nem para authority de execução; permanece ferramenta auxiliar de referência/replay/testes offline.

## 6. Regra Ares

Ares deve evoluir conceptualmente como:

```text
semantic correctness
    ↓
search capability
    ↓
search efficiency
    ↓
evaluation quality
    ↓
competitive strength
```

Uma alegação superior não pode mascarar uma dúvida inferior.

- NPS maior sem equivalência semântica ≠ progresso aceite;
- benchmark táctico melhor = capability evidence;
- lower NNUE loss = training evidence;
- batch Elo de amostra dependente = efeito descritivo, não calibragem global automática.

## 7. Regra de evidência por afirmação

| Afirmação | Evidência mínima |
|---|---|
| regra funciona | teste de transição + regressão |
| Python/C++ concordam | differential nos estados relevantes |
| pesquisa encontra X | benchmark determinístico específico |
| ficou mais rápido | benchmark controlado de custo |
| ficou mais forte | Arena A/B + protocolo de incerteza apropriado |
| roster está melhor balanceado | análise contextual + validação independente |
| UX melhorou | testes de interação + validação visual/uso |

## 8. Como usar os documentos

- **Regras:** `GAME_RULES.md` + `HERO_SYSTEM.md`.
- **Arquitetura:** `ARCHITECTURE.md` + `MECHANICS_TRACEABILITY_MATRIX.md`.
- **Ares:** `AI_ENGINE.md` + `AI_BENCHMARK_PROTOCOL.md` + `STRENGTH_EVALUATION.md`.
- **NNUE:** `NNUE.md` + `AI_ENGINE.md`; hooks ≠ integração concluída.
- **Strength:** `STRENGTH_EVALUATION.md` + `ARENA_STATISTICAL_METHODOLOGY.md` + hold-out.
- **Balance:** `BALANCE_METHODOLOGY.md`; Auto-Pricer é diagnóstico.
- **UI:** `BATTLE_UI_SIDEBAR.md`; arquitetura já implementada não deve ser reaberta por snapshots antigos.

## 9. Regra anti-ficção documental

É inválido inferir:

- “planeado” = implementado;
- “documentado” = provado;
- “testado” = validado para qualquer uso;
- “benchmark verde” = mais forte;
- “CI verde” = correctness total;
- “existe num branch” = existe no `main`.

## 10. Regra para novos documentos

Antes de criar um ficheiro:

1. procurar o proprietário canónico no `00_INDEX.md`;
2. verificar `CURRENT_STATE.md` e `ROADMAP.md`;
3. verificar o documento do domínio;
4. consultar `DECISIONS/` apenas quando a rationale histórica for necessária.

Uma nova investigação normalmente termina com atualização do documento canónico + roadmap, e não com outro snapshot paralelo.

## 11. Unidade mínima de continuidade

Quando código/testes alterarem um contrato ou prioridade:

```text
código/testes
 + contrato canónico
 + ROADMAP
 + decisão histórica, se a política mudou
```

O objetivo é que a próxima IA consiga reconstruir **onde estamos, o que está provado, o que não está provado e por que o próximo bloco vem a seguir**, sem depender da conversa original.
