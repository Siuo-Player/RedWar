# RedWar — NNUE

## Contrato

NNUE é uma avaliação opcional da Ares. Este documento define apenas o contrato durável; o código/testes determinam o estado efetivamente integrado.

As features devem representar o estado observável relevante para a avaliação, incluindo identidade/posição/equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move. O formato do modelo deve ser versionado e reproduzível.

## Correção incremental

`sync_board()` é a referência de ressincronização completa e pode funcionar como oracle/recovery path. O caminho incremental deve produzir o mesmo resultado nas sequências de mutação cobertas:

```text
board mutation
→ incremental update
→ accumulator
      ≡
full resync
```

Correção incremental e eficiência são critérios distintos. Uma redução de custo que introduza drift não é aceite.

## Treino e dataset

O pipeline conceptual é:

```text
positions
→ RWEN + target/teacher
→ features
→ training
→ quantization
→ model
→ validation
→ Arena
```

A validação deve controlar leakage, duplicação, composição, diversidade e reprodutibilidade quando relevantes.

## Promotion gate

NNUE só pode substituir a avaliação clássica como default após:

1. paridade de features;
2. determinismo relevante;
3. treino reproduzível;
4. custo/NPS medido;
5. regressões relevantes ausentes;
6. Arena A/B com evidência suficiente;
7. observabilidade e regras do produto respeitadas.

```text
incremental correctness ≠ strength superiority
lower training loss ≠ stronger Ares
higher NPS ≠ strength proof
```
