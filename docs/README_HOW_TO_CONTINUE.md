# Como continuar o RedWar

O RedWar deve ser continuável sem depender da conversa que originou uma alteração.

## Ordem obrigatória de leitura

```text
README.md
  ↓
docs/00_INDEX.md
  ↓
docs/CURRENT_STATE.md
  ↓
docs/ROADMAP.md
  ↓
documento canónico do domínio da tarefa
  ↓
decisão histórica relevante, se necessária
  ↓
código + testes
```

`PROJECT_REASONING.md` pode ser consultado para reconstruir a cadeia causal transversal; não substitui `CURRENT_STATE` nem `ROADMAP`.

## O que cada camada responde

```text
00_INDEX
→ onde está a fonte de verdade e quem é o proprietário de cada domínio?

CURRENT_STATE
→ qual é o baseline verificável agora?

ROADMAP
→ qual é o próximo bloco autorizado, porquê, com que dependências e gate?

documento canónico
→ qual é o contrato técnico/design atual?

PROJECT_REASONING
→ por que esta dependência e este nível de evidência existem?

DECISIONS
→ por que uma política histórica foi escolhida?
```

## Estados de conhecimento

Ao ler ou atualizar documentação, distinguir:

```text
DOCUMENTED
IMPLEMENTED
TESTED
VALIDATED
PROVEN
```

Nunca promover uma categoria para outra apenas porque um snapshot, branch ou handoff o afirma.

## Regra de continuidade

Toda PR que altere comportamento, contrato, metodologia ou prioridade deve atualizar os artefactos correspondentes no mesmo work package:

```text
código/testes
   +
contrato canónico afetado
   +
ROADMAP
   +
decisão, quando a política muda
```

Quando uma etapa do roadmap depende de uma distinção que possa ser esquecida, o próprio bloco do roadmap deve citar o documento canónico e a passagem crítica que fixa essa regra.

## Regra contra snapshots

Handoffs, audits e snapshots datados são evidência histórica. Não são fontes operacionais alternativas ao `main`.

Um documento mais recente em nome/data não vence um documento canónico atual simplesmente por ser mais recente; a autoridade é determinada pelo tipo documental e pela verificação do código/testes.

## PROJECT-STUDIES

`Siuo-Player-PROJECT-STUDIES/REDWAR` pode conservar investigação, literatura e rationale. Não é a operational source of truth do RedWar. Uma descoberta operacionalmente relevante deve ser refletida em `RedWar/docs` e ligada ao roadmap.

## Regra final

Quando o estado não puder ser verificado, escrever **UNKNOWN / UNVERIFIED** em vez de transformar inferência em facto.
