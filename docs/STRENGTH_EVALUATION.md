# RedWar — Strength Evaluation Framework

## Objetivo

Este documento define como medir **força geral da Ares** sem confundir melhoria num pequeno conjunto de posições com melhoria global.

A pergunta que o framework deve responder é:

> "Esta revisão da Ares joga melhor, em média, contra a mesma população de estados e adversários, sob condições controladas, e quão certa estamos dessa conclusão?"

Um benchmark táctico conhecido pode provar que uma capacidade funciona. Não prova, sozinho, que a engine ficou mais forte.

## 1. Inspiração: desenvolvimento do Stockfish

O modelo de desenvolvimento do Stockfish/Fishtest é a principal inspiração operacional:

```text
engine version A
      vs
engine version B
      ↓
controlled self-play
      ↓
paired game results
      ↓
strength estimate (Elo-like)
      ↓
uncertainty estimate
      ↓
sequential test (SPRT)
      ↓
accept / reject / continue
```

O RedWar não deve copiar literalmente todos os pressupostos do xadrez. Deve reutilizar o princípio: **força da Ares é medida principalmente pela Arena através de comparação experimental repetida**, não por inspeção nem por poucos puzzles seleccionados.

Benchmarks, differential tests e hold-outs existem para garantir correção, generalização e diagnóstico; a Arena é o instrumento principal para medir se uma revisão da Ares ficou globalmente mais forte.

Referência prática principal: Stockfish Fishtest, incluindo a utilização de paired games, ratings e SPRT.

- https://github.com/official-stockfish/fishtest
- https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html
- https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html

## 2. O que o rating representa

Para uma comparação A vs B, queremos estimar uma variável latente de força:

```text
R_A - R_B
```

A força absoluta é arbitrária; o que interessa operacionalmente é a diferença entre versões.

A escala pode começar compatível com Elo, mas a implementação deve ser modelada como **paired-comparison strength**, permitindo evoluir para Bradley–Terry ou uma formulação bayesiana.

A primeira implementação no repositório está em `tools/analytics/strength_rating.py`. Ela fornece um baseline Elo-compatible, com resultados de partidas explícitos e uma estimativa conservadora de incerteza. Esta implementação é deliberadamente provisória: **não é ainda o SPRT nem um modelo Bradley–Terry/Bayesiano completo**.

A Arena integra esse baseline no resumo experimental. O `.summary.json` passa a guardar, além de vitórias/derrotas/empates:

- `strength_model`;
- `rating_challenger`;
- `rating_baseline`;
- `rating_delta`;
- `rating_delta_uncertainty_proxy_half_width`;
- `rating_delta_uncertainty_type`.

O último campo identifica a semântica da estimativa. Atualmente o tipo é `engineering_uncertainty_proxy_v1`.

Esses valores são uma **medição estatística adicional**; o intervalo derivado do proxy não é um intervalo de confiança estatístico calibrado. Eles não substituem ainda o gate de promoção nem devem ser interpretados como um SPRT.

Um resultado futuro deve poder ser expresso como:

```text
Ares-v42
rating = 1678
uncertainty = ±18
```

em vez de apenas:

```text
Ares-v42 = 1678
```

A incerteza é parte do resultado.

## 3. Modelo de comparação

Para uma baseline A e challenger B, uma formulação inicial compatível com Elo pode usar:

```text
P(B vence A) = logistic((R_B - R_A + context_effects) / scale)
```

Em evolução posterior pode ser usado um modelo Bradley–Terry completo:

```text
P(B > A) = strength_B / (strength_A + strength_B)
```

com tratamento explícito de empate.

Não é necessário escolher já a implementação definitiva. O requisito é guardar dados suficientemente ricos para permitir esta evolução sem repetir todas as partidas.

A implementação inicial usa `MatchResult(left, right, outcome)` e suporta `win`, `draw` e `loss`; o módulo é independente da search/evaluation para que o modelo estatístico possa evoluir sem tocar na Ares.

## 4. Dados mínimos por partida

Cada partida de medição de força deve guardar, no mínimo:

- versão/commit do challenger;
- versão/commit da baseline;
- resultado: challenger / baseline / draw;
- cor do challenger;
- seed;
- opening/posição inicial;
- node budget ou time budget;
- número de plies;
- motivo de terminação;
- versão das regras;
- resultado de validade da partida.

Quando possível guardar também:

- hardware class;
- tempo total;
- nodes pesquisados;
- search statistics;
- tactical metadata.

O JSONL bruto da Arena deve continuar a ser a fonte de dados; os resumos estatísticos devem ser derivados dele.

## 5. Controlo experimental

Comparações de força devem controlar ou equilibrar:

```text
same rules
same budget
same openings/seeds
balanced colours
same game termination policy
same invalid-game policy
```

O challenger não pode receber sistematicamente uma cor ou família de openings que o favoreça.

Para uma comparação A/B, o ideal é que cada configuração relevante apareça de forma aproximadamente simétrica:

```text
A as White vs B as Black
A as Black vs B as White
```

O book/opening set deve ser fixado antes da análise.

A Arena agora também grava uma auditoria derivada das partidas para tornar esta hipótese verificável antes da inferência estatística. O contrato é implementado em `summarize_experiment_balance()` e os resultados ficam no `summary.json`.

## 6. Três conjuntos diferentes

O RedWar deve separar claramente:

### Regression set

Casos que nunca podem quebrar.

Exemplos: bugs corrigidos, regras específicas e invariantes do engine.

Objetivo:

```text
não regressar
```

### Development set

Casos usados durante o desenvolvimento para observar se uma hipótese está a produzir o efeito esperado.

Objetivo:

```text
orientar engenharia
```

### Hold-out set

Casos que não devem ser usados para orientar a alteração corrente e que só são abertos para validação.

Objetivo:

```text
generalização
```

Uma alteração que melhora apenas o development set mas piora consistentemente o hold-out **não é uma melhoria geral**.

O hold-out não deve ser reciclado continuamente para development; caso contrário deixa de ser independente.

## 7. Pipeline de evidência

A decisão de promover uma alteração deve evoluir para:

```text
1. correctness
   ↓
2. known regressions
   ↓
3. development evidence
   ↓
4. hold-out evidence
   ↓
5. Ares A/B Arena
   ↓
6. strength estimate + uncertainty
   ↓
7. sequential statistical test
   ↓
8. promotion decision
```

Cada etapa responde a uma pergunta diferente.

### Correctness

A implementação faz aquilo que deveria fazer?

### Regression

Coisas anteriormente corretas continuam corretas?

### Development

A hipótese de engenharia parece produzir o efeito desejado?

### Hold-out

O efeito generaliza para casos não utilizados durante a alteração?

### Ares A/B Arena

A revisão melhora efectivamente o comportamento competitivo da Ares?

### Strength estimate

Qual é o tamanho estimado da melhoria/regressão?

### Statistical test

Temos evidência suficiente para tomar uma decisão?

## 8. SPRT: primeira implementação experimental

O repositório agora contém `tools/analytics/sprt.py` como uma **camada estatística isolada**. Ela não altera a Ares, a Arena nem o gate de promoção.

A implementação compara duas hipóteses explícitas:

```text
H0: melhoria = elo0
H1: melhoria = elo1
```

e acumula o **log-likelihood ratio (LLR)** à medida que chegam os resultados:

```text
LLR_n = Σ log( P(resultado_i | H1) / P(resultado_i | H0) )
```

O processo termina quando o LLR atravessa uma das fronteiras:

```text
LLR >= log((1-beta)/alpha)  → accept H1
LLR <= log(beta/(1-alpha))   → reject H1
caso contrário               → continue
```

A primeira versão usa um modelo deliberadamente simples: vitórias/derrotas seguem a probabilidade logística implícita na diferença Elo, enquanto a taxa de draws é um parâmetro fixo partilhado entre H0/H1. Neste modelo, um draw acrescenta LLR zero.

**Isto ainda não é Fishtest-equivalent.** Antes de ligar o SPRT ao gate, precisamos de validar:

- calibração da escala de Elo para RedWar;
- tratamento adequado de draws;
- impacto de cor/opening/seed;
- independência efectiva das observações;
- comportamento em jogos inválidos;
- múltiplos testes/peças em paralelo;
- escolha de `elo0`, `elo1`, `alpha` e `beta` apropriada ao custo da Arena.

A implementação tem testes sintéticos para `accept_h1`, `reject_h1`, `continue`, draws e parâmetros inválidos. A próxima etapa é testar o comportamento contra resultados reais da Arena **sem ainda usar o SPRT para promoção automática**.

## 9. Arena e draws

Draws devem permanecer dados explícitos.

Não transformar:

```text
max plies reached
```

automaticamente em:

```text
draw
```

sem que isso represente uma regra real do jogo.

O guardrail actual de 10.000 plies é uma protecção experimental. Caso ocorram partidas sem vencedor, o `GameState` deve ser investigado antes de o resultado ser interpretado como empate legítimo.

## 10. Elo não é suficiente sozinho

O rating global pode esconder intransitividade:

```text
A > B
B > C
C > A
```

Isto pode surgir em RedWar por composição, matchup, cor ou estilos de jogo.

O sistema deve portanto preservar a possibilidade de análises condicionais:

```text
strength global
strength por matchup
strength por composição
strength por cor
strength por classe táctica
```

Estas análises não substituem o rating global; servem para explicar o resultado e detectar regressões localizadas.

Referência académica sobre limitações do Elo em presença de intransitividade:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12742789/

## 11. Intrinsic / move-quality strength

Resultado de jogo e qualidade de decisão são dimensões diferentes.

A investigação de **Intrinsic Chess Ratings** mostra uma linha de trabalho em que a força pode ser estimada pela qualidade das decisões, além do resultado bruto das partidas.

No RedWar, esta ideia deve ser adaptada para uma segunda métrica experimental, por exemplo:

```text
posição
  ↓
ação escolhida
  ↓
perda de avaliação / tactical regret
  ↓
move-quality score
```

Pode posteriormente incluir:

- oportunidade de stun perdida;
- spell forçante ignorado;
- captura de alto valor perdida;
- dano/risco evitável;
- perda material;
- alteração inesperada de TWC/lifespan/cooldown.

Isto **não substitui a Ares A/B Arena**. Serve para explicar por que uma versão parece mais forte.

Referência:

- Regan & Haworth, *Intrinsic Chess Ratings*, AAAI 2011: https://ojs.aaai.org/index.php/AAAI/article/view/7951
- Ferreira, *Determining the Strength of Chess Players Based on Actual Play*: https://journals.sagepub.com/doi/pdf/10.3233/ICG-2012-35102

## 12. Modelo estatístico futuro

A primeira implementação pode manter a simplicidade de Elo, mas o desenho de dados deve permitir evoluir para:

1. Elo-compatible paired comparison;
2. Bradley–Terry;
3. rating + uncertainty;
4. dynamic/Bayesian rating;
5. SPRT ou teste sequencial equivalente.

Referências académicas:

- Joe, *Rating systems based on paired comparison models*: https://www.sciencedirect.com/science/article/abs/pii/016771529190046T
- *A Bayesian approach to time-varying latent strengths in pairwise comparisons*: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0251945
- *Rating players by Laplace's approximation and dynamic modeling*: https://www.sciencedirect.com/science/article/pii/S0169207023001036

## 13. Critérios de promoção

Até existir uma implementação estatística completa, **não usar um limiar arbitrário de vitórias como prova de melhoria geral**.

A política provisória é:

```text
regression suite = obrigatória
hold-out = obrigatório para alterações de força
Ares Arena = obrigatória para alegar aumento de força
rating = guardar quando disponível
uncertainty proxy = não omitir quando calculado
manual investigation = necessária em resultados anómalos
```

Quando o sistema de rating + teste sequencial estiver validado:

```text
ACCEPT
    efeito positivo suficientemente suportado

REJECT
    evidência suficiente de regressão

CONTINUE
    dados insuficientes / incerteza demasiado larga
```

O terceiro resultado é importante: **não forçar uma decisão quando não existe evidência suficiente**.

## 14. Anti-overfitting

Não é permitido desenhar uma melhoria para passar apenas:

- FrostMage;
- um único tactical puzzle;
- uma única abertura;
- um único seed;
- uma única composição;
- uma única faixa de nodes.

Os benchmarks dirigidos continuam importantes, mas como testes de capacidade/regressão.

A força geral deve ser demonstrada num conjunto experimental suficientemente variado e, finalmente, pela Ares A/B Arena com um hold-out protegido a apoiar a generalização.

## 15. Roadmap de implementação

```text
[x] definir data model de partida e resultado emparelhado
[x] criar StrengthRating data model / baseline Elo-compatible
[x] calcular rating incremental a partir de resultados
[x] expor rating + engineering uncertainty proxy
[x] ligar o baseline ao resumo JSONL da Arena
[x] guardar metadata suficiente para reconstruir cada experiência
[x] auditar cores/openings/seeds antes da inferência
[ ] separar development/regression/hold-out em infraestrutura executável
[ ] criar hold-out congelado
[ ] comparar revisões de Ares por rating delta
[ ] adicionar comparação de força por contexto para detetar intransitividade/matchup
[x] implementar SPRT como biblioteca/teste isolado
[ ] calibrar SPRT com resultados reais da Arena
[ ] substituir a margem heurística pelo teste sequencial, depois de validado
[ ] estudar intrinsic move-quality score
```

## 16. Regra central

> **Nenhum benchmark individual define a força da Ares. A força é uma propriedade emergente de muitas partidas controladas da própria Ares e de uma medição estatística com incerteza conhecida.**
