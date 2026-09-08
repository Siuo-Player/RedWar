# RedWar Documentation Index

## Where is current truth?

A ordem operacional de leitura é:

1. [`README.md`](README.md)
2. [`00_INDEX.md`](00_INDEX.md)
3. [`CURRENT_STATE.md`](CURRENT_STATE.md)
4. [`ROADMAP.md`](ROADMAP.md)
5. documento canónico do domínio da tarefa
6. [`PROJECT_REASONING.md`](PROJECT_REASONING.md) quando for necessária a cadeia causal transversal
7. `DECISIONS/` apenas para recuperar a motivação histórica relevante

`CURRENT_STATE.md` responde **onde estamos**. `ROADMAP.md` responde **o que vem a seguir, porquê, dependente de quê e com que gate**. Os documentos de domínio definem **o contrato**. `PROJECT_REASONING.md` explica **por que a ordem de dependências existe**.

## Documentos canónicos por domínio

| Área | Fonte de verdade operacional |
|---|---|
| Arquitetura | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Regras | [`GAME_RULES.md`](GAME_RULES.md) |
| Design | [`GAME_DESIGN.md`](GAME_DESIGN.md) |
| Heróis | [`HERO_SYSTEM.md`](HERO_SYSTEM.md) + `engine/heroes_config.json` |
| Ares | [`AI_ENGINE.md`](AI_ENGINE.md) |
| NNUE | [`NNUE.md`](NNUE.md) |
| Benchmarks | [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md) |
| Strength | [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md) |
| Arena estatística | [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md) |
| Hold-out | [`ARENA_HOLDOUT_CI.md`](ARENA_HOLDOUT_CI.md) |
| Balanceamento | [`BALANCE_METHODOLOGY.md`](BALANCE_METHODOLOGY.md) |
| Observabilidade | [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md) |
| Traceability | [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md) |
| CI | [`CI_WORKFLOW_METHODOLOGY.md`](CI_WORKFLOW_METHODOLOGY.md) |
| Desenvolvimento | [`PROJECT_DEVELOPMENT_METHODOLOGY.md`](PROJECT_DEVELOPMENT_METHODOLOGY.md) + [`DEVELOPMENT_WORKFLOW.md`](DEVELOPMENT_WORKFLOW.md) |
| Decisões | [`DECISION_AND_KNOWLEDGE_PROTOCOL.md`](DECISION_AND_KNOWLEDGE_PROTOCOL.md) + `DECISIONS/` |
| UI | [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md) |
| Online | [`WEB_MULTIPLAYER.md`](WEB_MULTIPLAYER.md) |
| Licenças | [`LEGAL_AND_LICENSES.md`](LEGAL_AND_LICENSES.md) |

## Hierarquia de evidência

```text
implementação atual + testes executáveis
        ↓
contrato canónico atual
        ↓
decisão histórica
        ↓
auditoria / investigação
        ↓
proposta / backlog
        ↓
snapshot histórico
```

Nenhum documento histórico, audit, research ou roadmap pode alterar silenciosamente o comportamento implementado no `main`.

## Estados de conhecimento

Estas categorias são distintas e não devem ser usadas como sinónimos:

```text
DOCUMENTED   = descrito num artefacto documental
IMPLEMENTED  = presente no código alvo
TESTED       = coberto por teste executável
VALIDATED    = submetido ao tipo de validação apropriado para a alegação
PROVEN       = evidência suficiente para a alegação específica sob o protocolo vigente
```

Exemplos: uma regra pode estar `DOCUMENTED` sem estar `PROVEN`; uma mudança pode estar `TESTED` sem constituir evidência de `STRENGTH`; um PR merged pode ser `IMPLEMENTED` sem justificar uma alegação de generalização.

## Regra contra duplicação

Antes de criar documentação para um assunto existente, localizar o proprietário canónico e atualizá-lo. Só criar um novo artefacto quando tiver responsabilidade própria de lifecycle e não for uma duplicação de current-state, roadmap, contrato ou decisão.

`DECISIONS/` é histórico. Não se reescreve para fazer o passado parecer o presente.

## Regra de sincronização

Quando uma decisão ou alteração material muda um contrato:

```text
código/testes
+
documento canónico afetado
+
ROADMAP
```

Se a política mudou, acrescentar também a decisão histórica relevante. `CURRENT_STATE.md` é atualizado para refletir o baseline verificável, mas não substitui os contratos.

No `ROADMAP.md`, toda dependência consequente deve apontar diretamente para os documentos canónicos que justificam o gate e citar a passagem crítica quando a interpretação futura puder ser ambígua.

## Baseline atual

O `main` verificado em **2026-09-08** é:

`e17afcd54ad57635e222f3b3c9a5bb9966df9394`

O PR #321 foi merged nesse SHA e introduziu/testou `engine.legal_actions.resolve_legal_action()` como seam de resolução canónica, mantendo A0.1 aberto para a autoridade de legalidade em tempo de execução.

Um documento datado pode continuar válido como histórico. A data ou o nome do ficheiro nunca substituem a verificação do `main`.
