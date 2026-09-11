# RedWar — Project Reasoning Spine

Este documento explica a cadeia causal e as fronteiras de evidência do RedWar. Não é estado atual nem roadmap: o comportamento é autoridade do código/testes, os contratos pertencem aos documentos de domínio, e a ordem pertence a `ROADMAP.md`.

## 1. Hierarquia

```text
implementação + testes
        ↓
contrato canónico
        ↓
decisão histórica
        ↓
research / proposta
        ↓
ROADMAP
```

Não usar snapshots para determinar o estado atual.

## 2. Estados de evidência

```text
DOCUMENTED → IMPLEMENTED → TESTED → VALIDATED → PROVEN (claim-specific)
```

Uma camada não implica automaticamente a seguinte.

## 3. Linha causal

```text
problema / oportunidade
→ contrato afetado
→ evidência existente
→ hipótese
→ menor alteração útil
→ testes
→ differential/property/benchmark
→ medição independente quando aplicável
→ aceitar / rejeitar / continuar
→ atualizar contrato e roadmap
```

## 4. Dependência técnica

```text
GAME_RULES / HERO_SYSTEM
        ↓
ação e estado canónicos
        ↓
Python reference ↔ C++ Ares
        ↓
search / evaluation
        ↓
Arena / strength evidence
        ↓
balance
        ↓
produto / online
```

UI, replay e telemetria observam o estado; não substituem a autoridade das regras.

## 5. Fronteira de execução Ares

A ordem obrigatória é:

```text
canonical normalization / resolution
→ action-space membership
→ transition-domain validation
→ mutation
```

`fast_clone()` é ferramenta auxiliar de referência/replay/testes offline, nunca autoridade de legalidade ou preflight do executor.

## 6. Regra Ares

```text
semantic correctness
→ search capability
→ search efficiency
→ evaluation quality
→ competitive strength
```

NPS, benchmark táctico, training loss ou resultados descritivos de uma amostra não substituem evidência de força.

## 7. Evidência mínima

| Afirmação | Evidência mínima |
|---|---|
| regra funciona | teste de transição + regressão |
| Python/C++ concordam | differential nos estados relevantes |
| pesquisa encontra X | benchmark específico e determinístico |
| ficou mais rápido | benchmark controlado de custo |
| ficou mais forte | Arena A/B + incerteza apropriada |
| balanceamento melhorou | análise contextual + validação independente |
| UX melhorou | interação + validação visual/uso |

## 8. Onde procurar

- Regras: `GAME_RULES.md`, `HERO_SYSTEM.md`
- Arquitetura: `ARCHITECTURE.md`, `MECHANICS_TRACEABILITY_MATRIX.md`
- Ares: `AI_ENGINE.md`, `AI_BENCHMARK_PROTOCOL.md`, `STRENGTH_EVALUATION.md`
- NNUE: `NNUE.md`, `AI_ENGINE.md`
- Strength: `STRENGTH_EVALUATION.md`, `ARENA_STATISTICAL_METHODOLOGY.md`
- Balance: `BALANCE_METHODOLOGY.md`
- UI: `BATTLE_UI_SIDEBAR.md`
- decisões históricas: `DECISIONS/`

## 9. Regra anti-ficção documental

É inválido inferir:

```text
planeado = implementado
implementado = provado
benchmark verde = mais forte
CI verde = correctness total
branch = main
```

## 10. Novos documentos

Antes de criar um documento, localizar o proprietário canónico em `00_INDEX.md`. Atualizar esse proprietário quando a informação for durável. Criar um documento novo apenas para uma decisão histórica, questão de research ou contrato realmente distinto.

O objetivo é que outra IA consiga reconstruir o raciocínio sem depender da conversa original, sem criar uma segunda camada de estado.