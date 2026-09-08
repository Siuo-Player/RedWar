# RedWar — Strength Evaluation

## Authority

Este documento define como medir **força da Ares**. [`ROADMAP.md`](ROADMAP.md) define quando e em que ordem esta medição entra no desenvolvimento; [`PROJECT_REASONING.md`](PROJECT_REASONING.md) define por que strength é uma camada posterior à correção semântica.

**Current main:** `e17afcd54ad57635e222f3b3c9a5bb9966df9394`.

## Pergunta

> Esta revisão da Ares joga melhor contra o baseline sob condições controladas?

Isso é diferente de:

- encontrar um puzzle melhor;
- atingir mais NPS;
- ter menor loss de treino;
- ganhar uma amostra pequena e dependente.

## Hierarquia de evidência

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

Uma camada superior não pode apagar uma incerteza de uma camada inferior.

## Controles mínimos

Cada experiência deve identificar regras/configuração, versões dos engines, node/time budget, openings/seeds, política de cor, validade/terminação dos jogos e identidade dos dados.

Resultados inválidos não devem ser convertidos silenciosamente em resultados competitivos.

## Estado atual

Existe um baseline de rating Elo-compatible e camadas de análise paired-game/pentanomial, provenance, hold-out e SPRT.

**Estado do conhecimento:** infraestrutura `IMPLEMENTED`; metodologia `DOCUMENTED`; calibração para promoção automática ainda `UNVERIFIED`.

O SPRT permanece uma ferramenta isolada até a sua calibração/operating-characteristic validation justificar autoridade automática.

O primeiro dataset real persistido contém 100 jogos válidos em 50 pares de inversão de cor. Esses pares são unidades de resampling da análise; **não constituem 50 condições experimentais independentes** porque parte das combinações de opening/seed é reutilizada.

## Hold-out

```text
regression
≠
development
≠
protected hold-out
```

Hold-out não deve ser reutilizado para procurar parâmetros vencedores.

## Interpretação estatística

A distinção operacional é:

```text
resampling unit
≠
independent experimental condition
```

Um paired bootstrap pode fornecer um intervalo descritivo da distribuição reamostrada; não o chamar automaticamente de IC95% calibrado sem justificação para o estimador e desenho utilizados.

## Promoção

Uma alteração só pode ser promovida como **strength improvement** quando a evidência competitiva, sob condições reproduzíveis, supera as limitações conhecidas e o resultado é suficientemente robusto para a regra de decisão vigente.

Um benchmark, uma métrica de treino, um run isolado, um batch Elo ou um resultado favorável em dados dependentes não substituem a validação Arena adequada.
