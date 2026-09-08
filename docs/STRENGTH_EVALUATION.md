# RedWar — Strength Evaluation

## Authority

Este documento define como medir **força da Ares**. [`ROADMAP.md`](ROADMAP.md) define quando e em que ordem esta medição entra no desenvolvimento; [`PROJECT_REASONING.md`](PROJECT_REASONING.md) define por que strength é uma camada posterior à correção semântica.

## Pergunta

> Esta revisão da Ares joga melhor contra o baseline sob condições controladas?

Isso é diferente de:

- encontrar um puzzle melhor;
- atingir mais NPS;
- ter menor loss de treino;
- ganhar uma amostra pequena e dependente.

## Hierarquia

```text
correctness
→ regression
→ capability
→ independent validation
→ Arena A/B
→ strength estimate
→ uncertainty
→ decision
```

## Controles mínimos

Cada experiência deve identificar regras/configuração, versões dos engines, node/time budget, openings/seeds, política de cor, validade/terminação dos jogos e identidade dos dados.

Resultados inválidos não devem ser convertidos silenciosamente em resultados competitivos.

## Estado atual

Existe um baseline de rating Elo-compatible e camadas de análise paired-game/pentanomial, provenance, hold-out e SPRT. O SPRT continua uma ferramenta isolada até a sua calibração/operating-characteristic validation justificar autoridade automática.

O primeiro dataset real persistido contém 100 jogos válidos em 50 pares de inversão de cor. Esses pares são unidades de resampling da análise; não constituem 50 condições independentes.

## Hold-out

```text
regression
≠
development
≠
protected hold-out
```

Hold-out não deve ser reutilizado para procurar parâmetros vencedores.

## Promoção

Uma alteração só pode ser promovida como **strength improvement** quando a evidência competitiva, sob condições reproduzíveis, supera as limitações conhecidas e o resultado é suficientemente robusto para a regra de decisão vigente.

Um benchmark, uma métrica de treino ou um run isolado não substituem Arena.
