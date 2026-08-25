# RedWar — Ares Strength Evaluation Framework

## Objetivo

Este documento define como medir **a força geral da Ares** sem confundir melhoria num pequeno conjunto de posições com melhoria global.

A pergunta central é:

> "Esta revisão da Ares joga melhor, em média, contra a mesma população de estados e adversários, sob condições controladas, e quão certa estamos dessa conclusão?"

A **Arena é o instrumento principal para medir a força da Ares**. Benchmarks tácteis, differential tests e hold-out servem para proteger, explicar e complementar essa medição; não a substituem.

## 1. Inspiração: desenvolvimento do Stockfish

O modelo de desenvolvimento do Stockfish/Fishtest é a principal inspiração operacional:

```text
Ares revision A
      vs
Ares revision B
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

O RedWar não deve copiar literalmente todos os pressupostos do xadrez. Deve reutilizar o princípio: **a força da Ares é medida por comparação experimental repetida, não por inspeção nem por poucos puzzles seleccionados**.

Referência prática principal: Stockfish Fishtest.

- https://github.com/official-stockfish/fishtest
- https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html
- https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html

## 2. O que o rating representa

Para duas revisões da Ares queremos estimar:

```text
R_Ares,new - R_Ares,baseline
```

A força absoluta é arbitrária; a diferença entre revisões é o que importa operacionalmente.

A primeira implementação no repositório está em `tools/analytics/strength_rating.py`. É um baseline Elo-compatible, com resultados explícitos de partidas e uma estimativa conservadora de incerteza. **Ainda não é um SPRT nem um modelo Bradley–Terry/Bayesiano completo.**

Um resultado futuro deverá poder ser expresso como:

```text
Ares revision X
rating = 1678
uncertainty = ±18
```

A incerteza é parte do resultado.

## 3. Arena = medição de força geral

A função dos diferentes mecanismos é:

```text
correctness / differential
        ↓
regression benchmarks
        ↓
hold-out validation
        ↓
Ares Arena
        ↓
Strength Rating + uncertainty
        ↓
SPRT / sequential decision
```

### Differential / correctness

> A Ares continua semanticamente correta?

### Benchmarks tácticos

> Capacidades específicas importantes continuam a funcionar ou melhoraram?

### Hold-out

> A alteração generaliza para casos não usados durante o desenvolvimento?

### Arena

> **A nova revisão da Ares é realmente mais forte no jogo global?**

### Strength Rating

> Qual é o tamanho estimado da diferença?

### SPRT / teste sequencial

> Existe evidência suficiente para aceitar, rejeitar ou continuar?

Assim, uma melhoria da Ares **não é promovida apenas porque passou FrostMage ou outros puzzles dirigidos**. A Arena é a medição competitiva global.

## 4. Modelo de comparação

Uma formulação inicial compatível com Elo pode usar:

```text
P(B vence A) = logistic((R_B - R_A + context_effects) / scale)
```

Em evolução posterior pode ser usado Bradley–Terry:

```text
P(B > A) = strength_B / (strength_A + strength_B)
```

com tratamento explícito de empate.

Os dados devem ser guardados de forma suficientemente rica para permitir a evolução do modelo sem repetir todas as partidas.

## 5. Dados mínimos por partida da Arena

Cada partida de medição de força entre revisões da Ares deve guardar, no mínimo:

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
- validade da partida.

Quando possível:

- hardware class;
- tempo total;
- nodes pesquisados;
- search statistics;
- tactical metadata.

O JSONL bruto da Arena deve continuar a ser a fonte de dados; os resumos estatísticos devem ser derivados dele.

## 6. Controlo experimental

Comparações de força da Ares devem controlar ou equilibrar:

```text
same rules
same budget
same openings/seeds
balanced colours
same game termination policy
same invalid-game policy
```

O challenger não pode receber sistematicamente uma cor ou família de openings que o favoreça.

Para uma comparação A/B:

```text
Ares-new as White vs Ares-old as Black
Ares-new as Black vs Ares-old as White
```

O book/opening set deve ser fixado antes da análise.

## 7. Development, regression e hold-out

### Regression set

Casos que nunca podem quebrar. Servem para detectar regressões conhecidas.

### Development set

Casos usados durante o desenvolvimento para testar hipóteses de engenharia.

### Hold-out set

Casos que não orientam a alteração corrente e só são abertos na validação.

Uma alteração que melhora development mas piora consistentemente hold-out **não é uma melhoria geral da Ares**.

O hold-out não deve ser reciclado continuamente para development; caso contrário deixa de ser independente.

O hold-out é uma protecção contra overfitting; **a Arena continua a ser o teste principal da força global**.

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

sem que isso corresponda a uma regra real do jogo.

O guardrail actual de 10.000 plies é uma protecção experimental. Caso ocorram partidas sem vencedor, o `GameState` deve ser investigado antes de interpretar o resultado como empate legítimo.

A execução manual `main vs main` introduzida no workflow é um **experimento de infraestrutura/comportamento da Arena** (por exemplo, observar draws/terminação). Isso não substitui a utilização normal da Arena para comparar duas revisões da Ares.

## 9. Elo não é suficiente sozinho

O rating global pode esconder intransitividade:

```text
Ares A > Ares B
Ares B > Ares C
Ares C > Ares A
```

Isto pode surgir em RedWar por composição, matchup, cor ou estilo.

Devemos preservar análises condicionais para explicar resultados:

```text
strength global
strength por matchup
strength por composição
strength por cor
strength por classe táctica
```

Essas análises explicam o rating global; não o substituem.

Referência académica sobre limitações do Elo em presença de intransitividade:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12742789/

## 10. Intrinsic / move-quality strength

Resultado de jogo e qualidade de decisão são dimensões diferentes.

A investigação de **Intrinsic Chess Ratings** mostra uma linha de trabalho que estima força pela qualidade das decisões, além do resultado bruto.

No RedWar, isto pode tornar-se uma segunda métrica experimental:

```text
posição
  ↓
ação escolhida
  ↓
perda de avaliação / tactical regret
  ↓
move-quality score
```

Pode incluir, no futuro:

- oportunidade de stun perdida;
- spell forçante ignorado;
- captura de alto valor perdida;
- dano/risco evitável;
- perda material;
- alteração inesperada de TWC/lifespan/cooldown.

Isto **não substitui a Arena**. Serve para explicar por que uma revisão parece mais forte ou mais fraca.

Referências:

- Regan & Haworth, *Intrinsic Chess Ratings*, AAAI 2011: https://ojs.aaai.org/index.php/AAAI/article/view/7951
- Ferreira, *Determining the Strength of Chess Players Based on Actual Play*: https://journals.sagepub.com/doi/pdf/10.3233/ICG-2012-35102

## 11. Modelo estatístico futuro

A primeira implementação pode manter Elo, mas o desenho deve permitir evoluir para:

1. Elo-compatible paired comparison;
2. Bradley–Terry;
3. rating + uncertainty;
4. dynamic/Bayesian rating;
5. SPRT ou teste sequencial equivalente.

Referências académicas:

- Joe, *Rating systems based on paired comparison models*: https://www.sciencedirect.com/science/article/abs/pii/016771529190046T
- *A Bayesian approach to time-varying latent strengths in pairwise comparisons*: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0251945
- *Rating players by Laplace's approximation and dynamic modeling*: https://www.sciencedirect.com/science/article/pii/S0169207023001036

## 12. Critérios de promoção da Ares

Uma alteração que pretende melhorar a força da Ares deve satisfazer:

```text
regression suite = obrigatória
hold-out = obrigatório
Arena = obrigatória
rating = guardar quando disponível
uncertainty = não omitir
manual investigation = necessária em resultados anómalos
```

Quando o sistema estatístico estiver maduro:

```text
ACCEPT
    evidência suficiente de aumento de força na Arena

REJECT
    evidência suficiente de regressão na Arena

CONTINUE
    dados insuficientes / intervalo demasiado largo
```

**CONTINUE é uma decisão válida.** Não se deve forçar uma promoção por falta de dados.

## 13. Anti-overfitting

Não é permitido desenhar uma melhoria da Ares para passar apenas:

- FrostMage;
- um único tactical puzzle;
- uma única abertura;
- um único seed;
- uma única composição;
- uma única faixa de nodes.

Esses casos continuam importantes como capability/regression probes.

A força geral deve aparecer na **Arena**, usando uma população suficientemente variada de partidas e controlo experimental.

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
[ ] integrar rating na Arena Ares-vs-Ares
[ ] comparar revisões por rating delta
[ ] adicionar matchup/intransitivity analysis
[ ] adicionar SPRT/teste sequencial
[ ] estudar intrinsic move-quality score
```

## 15. Regra central

> **Nenhum benchmark individual define a força da Ares. A Arena mede a força competitiva geral; benchmarks, differential tests e hold-out tornam essa medição segura, explicável e resistente a overfitting.**
