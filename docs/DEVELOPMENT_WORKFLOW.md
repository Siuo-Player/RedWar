# RedWar — Development Workflow

## Branches

Cada branch deve representar um **bloco de desenvolvimento completo**.

No início:

```text
main
 ↓
branch nova
 ↓
atualizar ROADMAP
 ↓
registar decisão/hipótese, quando aplicável
 ↓
desenvolver
```

O roadmap é obrigatório porque a intenção da branch deve ser recuperável sem depender do histórico da conversa.

## Regra de conhecimento

**O repositório deve conter informação suficiente para que outra pessoa ou IA continue o desenvolvimento sem acesso à conversa de origem.**

Para qualquer decisão técnica, científica, arquitetural, metodológica ou de produto:

```text
observação / problema
 ↓
documentar facto + evidência
 ↓
registar hipótese / alternativas
 ↓
tomar decisão
 ↓
implementar
 ↓
testar / experimentar
 ↓
documentar resultado
 ↓
atualizar roadmap / estado
```

Ver `DECISION_AND_KNOWLEDGE_PROTOCOL.md` para o protocolo completo.

## Durante o bloco

Um erro encontrado enquanto o bloco está ativo é corrigido na própria branch.

A documentação acompanha a implementação, mas uma decisão que orienta o código deve ser registada **antes** de a implementação depender dela:

```text
código muda
  ↓
teste muda
  ↓
documentação atualiza resultado
```

Não acumular bugs conhecidos para “depois do PR”.

## PR

O PR é a fronteira de revisão do bloco terminado. Deve conter:

- objetivo;
- problema/contexto;
- decisão ou hipótese relevante;
- resumo das alterações;
- testes executados;
- benchmarks/Arena quando aplicável;
- limitações conhecidas;
- descobertas feitas durante a implementação;
- próximo passo do roadmap.

Uma branch pode receber vários commits antes do PR. O número de commits não é o objetivo; a unidade importante é a hipótese validada e o conhecimento preservado.

## Depois do PR

Depois de merge:

1. atualizar `ROADMAP.md`;
2. fechar/apagar a branch remota;
3. criar a próxima branch a partir da `main` atual;
4. rever documentação antes de continuar;
5. confirmar que decisões/descobertas relevantes da branch continuam recuperáveis apenas pelo repositório.

## Bugs descobertos depois

Se um problema só for descoberto noutra branch, é corrigido onde foi descoberto. O novo PR deve referenciar o problema e atualizar a documentação/regressão respetiva.

Não reabrir artificialmente branches antigas só para preservar uma sequência histórica.

## Alterações experimentais

Experimentos de Ares, NNUE, Arena e balanceamento devem ser reproduzíveis:

- seed conhecida;
- inputs versionados;
- configuração explícita;
- orçamento explícito;
- saída guardada quando o resultado for relevante;
- hipótese e decisão documentadas antes da alteração experimental.

Resultados negativos também são conhecimento e devem ser preservados quando alteram a direção do projeto.

## Workflows isolados

Cada workflow deve medir uma responsabilidade principal e falhar por motivos que pertençam a essa responsabilidade:

- `auto_balancer.yml`: regressões numéricas, build mínimo do motor necessário ao trainer, telemetria e Auto-Pricer;
- `ai_arena.yml`: jogos comparativos e recolha de evidência de força;
- `ai_quality_gate.yml`: decisão de qualidade da AI nos PRs;
- `nnue_nightly.yml`: teacher data, treino NNUE e publicação de modelos experimentais;
- `main_guard.yml`: apenas validação/política de proteção, sem reescrita automática de `main`.

Assim uma falha do treino NNUE não aparece como uma falsa falha do Auto-Balancer, e uma falha da Arena não bloqueia regressões numéricas básicas.

## Dados e artefactos

Ferramentas experimentais devem preferir:

- `--output` explícito;
- escrita atómica;
- `--no-write` para cálculos de previsão;
- seeds explícitas;
- artefactos CI ou diretórios temporários para outputs gerados.

Não substituir configurações do jogo automaticamente durante validações.

## Critério de conclusão

Um bloco termina quando a alteração pretendida funciona **e** as regressões relevantes estão cobertas **e** as decisões/descobertas que explicam a alteração ficaram preservadas no repositório. Código “quase pronto” permanece desenvolvimento e não deve ser tratado como concluído pela documentação.

## Modelo de projetos grandes

A disciplina aproxima-se de práticas visíveis em Stockfish/Fishtest/Fairy-Stockfish: engine separada dos testes, experimentos separados da execução normal, CI especializada e decisões baseadas em medições reproduzíveis.

O detalhe adicional para RedWar é que cada bloco deve preservar também a cadeia de conhecimento:

```text
problema
 → evidência
 → decisão
 → implementação
 → validação
 → resultado
 → próximo passo
```
