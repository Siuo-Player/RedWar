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

## Duas linhas de Ares e a Balance Lab

Ares passa a ter duas utilizações distintas, que não devem ser confundidas.

### Ares Balance Baseline

É a versão congelada utilizada pelo produto 1.0-Lite para:

- fornecer um adversário jogável;
- gerar partidas sob orçamento fixo e configuração reproduzível;
- servir como **um agente experimental controlado** dentro do Balance Lab;
- permitir reexecução de experiências de design sem alterar a população de referência a meio do ciclo.

A expressão **Ares Balance Baseline não significa “Ares validada como instrumento suficiente de balanceamento por si só”**. O baseline apenas congela o agente e as condições necessárias para executar a análise.

O Balance Lab continua separado e deve analisar valor de herói de forma contextual, preservando quando disponível:

```text
hero
× position
× allied composition
× opponent / matchup
× initiative / colour
× ruleset
× seed
× Ares policy / player-skill context
× outcome / terminal reason
```

Ares é um agente importante no laboratório, não o laboratório inteiro. Aggregate win rate de um herói é apenas uma marginalização e não é suficiente para decidir balanceamento.

### Balance intervention discipline

Quando uma mudança de balanceamento é considerada:

```text
controlled baseline
→ matched games / seeds / colours
→ selection + provenance audit
→ contextual matchup / composition / counter analysis
→ candidate intervention
→ independent hold-out
→ manual/design decision
```

Para preço, a primeira intervenção normal é custo inteiro e a procura deve ser coarse-to-fine. Uma alteração específica de mecânica só entra quando a evidência mostra que custo não resolve o defeito estratégico.

O `tools/balance/auto_pricer.py` é **diagnóstico/legado, não autoridade de balanceamento**. Os seus resíduos agregados de ocorrência/performance não modelam adequadamente posição, composição, matchup, população, contexto ou consequências no metagame. Nenhuma alteração de preço, mecânica ou roster deve ser aceite apenas porque esse script a propõe.

Para cor/iniciativa, usar condições emparelhadas, várias seeds/configurações, incerteza explícita e separação entre calibração e hold-out. A mesma amostra usada para escolher uma compensação não pode ser apresentada como validação independente dessa compensação.

Balance statistics remain descriptive and conditional on the declared baseline, population and protocol. They are not claims of intrinsic hero power, universal game balance or competitive Ares strength.

### Competitive Ares

Continua como projecto open-project sob #372:

- search/evaluation research;
- Arena A/B;
- NNUE;
- performance;
- historical evidence;
- promoção por critérios científicos.

Uma melhoria competitiva não substitui automaticamente o Lite baseline. A adopção no produto é uma decisão separada, seguida de revalidação de toda a evidência de balanceamento dependente daquele baseline.

Esta separação permite que o produto local avance sem transformar cada optimização experimental da Ares num blocker de lançamento, sem enfraquecer a metodologia científica do Balance Lab.

## Workflows isolados

Cada workflow deve medir uma responsabilidade principal e falhar por motivos que pertençam a essa responsabilidade:

- `test_suite.yml`: correção funcional e regressões gerais;
- `ai_quality_gate.yml`: única autoridade strength-sensitive para PRs;
- `codeql.yml`: análise de segurança;
- `arena_diagnostics.yml`: diagnósticos observacionais da Arena, sem decisão de promoção;
- `arena_experiments.yml`: experiências Arena manuais, datasets e holdout, sempre não-authoritativos;
- `nnue_nightly.yml`: teacher data, treino NNUE e publicação de modelos experimentais;
- `auto_balancer.yml`: regressões numéricas, trainer/pricer e telemetria;
- `strength_calibration.yml`: protocolo A/A temporário de calibração, sem autoridade de promoção.

A proteção estrutural de `main` pertence ao GitHub Ruleset `Protect main`, não a um workflow paralelo.

Assim uma falha do treino NNUE não aparece como uma falsa falha do Auto-Balancer, um diagnóstico da Arena não bloqueia promoção e experiências experimentais não duplicam a autoridade de `ai_quality_gate.yml`.

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
