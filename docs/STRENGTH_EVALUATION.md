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
uncertainty / confidence
      ↓
sequential test (SPRT)
      ↓
accept / reject / continue
```

O RedWar não deve copiar literalmente todos os pressupostos do xadrez. Deve reutilizar o princípio: **força é medida por comparação experimental repetida, não por inspeção nem por poucos puzzles seleccionados**.

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
5. A/B self-play
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

### A/B

A alteração melhora efectivamente o comportamento competitivo?

### Strength estimate

Qual é o tamanho estimado da melhoria/regressão?

### Statistical test

Temos evidência suficiente para tomar uma decisão?

## 8. Arena e draws

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

## 9. Elo não é suficiente sozinho

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

## 10. Intrinsic / move-quality strength

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

Isto **não substitui A/B strength**. Serve para explicar por que uma versão parece mais forte.

Referência:

- Regan & Haworth, *Intrinsic Chess Ratings*, AAAI 2011: https://ojs.aaai.org/index.php/AAAI/article/view/7951
- Ferreira, *Determining the Strength of Chess Players Based on Actual Play*: https://journals.sagepub.com/doi/pdf/10.3233/ICG-2012-35102

## 11. Modelo estatístico futuro

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

## 12. Critérios de promoção

Até existir uma implementação estatística completa, **não usar um limiar arbitrário de vitórias como prova de melhoria geral**.

A política provisória é:

```text
regression suite = obrigatória
hold-out = obrigatório para alterações de força
Arena = obrigatória para alegar aumento de força
rating = guardar quando disponível
uncertainty = não omitir
manual investigation = necessária em resultados anómalos
```

Quando o sistema de rating estiver implementado:

```text
ACCEPT
    efeito positivo suficientemente suportado

REJECT
    evidência suficiente de regressão

CONTINUE
    dados insuficientes / intervalo demasiado largo
```

O terceiro resultado é importante: **não forçar uma decisão quando não existe evidência suficiente**.

## 13. Anti-overfitting

Não é permitido desenhar uma melhoria para passar apenas:

- FrostMage;
- um único tactical puzzle;
- uma única abertura;
- um único seed;
- uma única composição;
- uma única faixa de nodes.

Os benchmarks dirigidos continuam importantes, mas como testes de capacidade/regressão.

A força geral deve ser demonstrada num conjunto experimental suficientemente variado e com um hold-out protegido.

## 14. Roadmap de implementação

```text
[x] definir data model de partida e resultado emparelhado
[x] criar StrengthRating data model / baseline Elo-compatible
[x] calcular rating incremental a partir de resultados
[x] expor rating + incerteza e intervalo relativo
[ ] ligar o modelo diretamente ao JSONL da Arena
[ ] guardar version/commit metadata em cada jogo
[ ] equilibrar cores/openings/seeds
[ ] separar development/regression/hold-out
[ ] criar hold-out congelado
[ ] integrar rating na Arena
[ ] comparar versões por rating delta
[ ] adicionar matchup/intransitivity analysis
[ ] adicionar SPRT/teste sequencial
[ ] estudar intrinsic move-quality score
```

## 15. Regra central

> **Nenhum benchmark individual define a força da Ares. A força é uma propriedade emergente de muitas partidas controladas e de uma medição estatística com incerteza conhecida.**
