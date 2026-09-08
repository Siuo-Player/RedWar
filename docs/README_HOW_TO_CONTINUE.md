# Como continuar o RedWar

O RedWar deve ser continuável sem depender da conversa que originou uma alteração.

## Ordem obrigatória de leitura

1. [`README.md`](README.md)
2. [`00_INDEX.md`](00_INDEX.md)
3. [`PROJECT_REASONING.md`](PROJECT_REASONING.md)
4. [`CURRENT_STATE.md`](CURRENT_STATE.md)
5. [`ROADMAP.md`](ROADMAP.md)
6. documento canónico do domínio da tarefa
7. `DECISIONS/` apenas para recuperar a motivação histórica necessária

## O que cada camada responde

```text
PROJECT_REASONING
→ por que a sequência e as regras de evidência são estas?

CURRENT_STATE
→ qual é o baseline comprovado agora?

ROADMAP
→ qual é o próximo trabalho autorizado?

documento canónico
→ qual é o contrato técnico/design?

DECISIONS
→ por que uma decisão histórica foi tomada?
```

## Regra de continuidade

Toda PR que altere comportamento, contrato, metodologia ou prioridade deve atualizar os artefactos correspondentes no mesmo work package.

```text
código/testes
   +
contrato canónico afetado
   +
ROADMAP
   +
decisão, quando a política muda
```

Não criar outro “current state”, roadmap ou backlog para contornar o estado existente.
