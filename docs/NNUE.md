# RedWar — NNUE

## Autoridade

Este documento define o contrato da NNUE. [`ROADMAP.md`](ROADMAP.md) define a sequência; [`PROJECT_REASONING.md`](PROJECT_REASONING.md) define a cadeia de evidência.

## Arquitetura atual

**Baseline verificável:** `main` @ `218fd115864629a79c82c72c729fa0faff831664`.

Ares possui uma NNUE opcional adaptada ao estado RPG. As features representam identidade/posição/equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move. O formato binário é versionado.

NNUE não é atualmente uma alegação de superioridade competitiva. A avaliação clássica continua disponível como baseline.

## Baseline de correção

A infraestrutura mantém `sync_board()` como referência de ressincronização completa e oracle de correção. Existem hooks incrementais para alterações de peça, efeito, lado e TWC.

O **PR #356** integrou esses hooks no caminho nativo real de mutação e adicionou regressão de `make_move()` / `unmake_move()` comparando a avaliação incremental com um full resync. O PR foi merged como `f2e7155d150b4cc0be79d4b86beb5005941ef180`.

Assim, o estado atual é **IMPLEMENTED / TESTED para a integração incremental de correção** nos cenários cobertos. `sync_board()` permanece explícito como oracle/recovery path; a sua existência não é escondida dentro do hot path como mecanismo silencioso de correção.

O contrato exercido é:

```text
BoardState mutation
→ incremental hook
→ accumulator
      ≡
full sync_board()
```

após sequências `make/unmake` e alterações dos estados persistentes relevantes cobertos pela regressão.

## Custo e strength

Só depois de a equivalência incremental/full-resync estar estabelecida se deve medir custo por avaliação e NPS. Uma redução do tempo de avaliação que introduza drift não é melhoria aceite.

Mesmo uma melhoria de NPS ou training loss não constitui strength evidence. Para alegações competitivas continua necessária Arena A/B sob o protocolo de strength, com orçamento comparável, alternância de cores e incerteza explicitamente tratada.

## Dataset / treino

O pipeline conceptual é:

```text
positions
→ RWEN + target/teacher
→ features
→ training
→ quantization
→ RWNUE model
→ validation
→ Arena
```

A metodologia de dataset deve auditar, conforme aplicável, duplicação, exact-position leakage, composição, diversidade e estabilidade.

**Estado atual verificável:** #314, que propunha deterministic grouped splitting e `audit_dataset.py`, **não foi merged**. Portanto essas alterações não podem ser descritas como funcionalidades existentes no `main`.

#316 foi merged e altera a classificação de CI para a classe estreita de metodologia de dataset NNUE, separando essa manutenção de uma promoção automática de strength. Isso não significa que o pipeline de dataset tenha sido promovido a validade experimental completa.

## Promotion gate

NNUE só pode tornar-se default após:

1. correção e paridade de features;
2. determinismo relevante;
3. modelo treinado e reproduzível;
4. custo/NPS comparado com baseline;
5. ausência de regressões relevantes em referências;
6. Arena A/B com evidência suficiente;
7. cumprimento do contrato de observabilidade.

`incremental correctness ≠ strength superiority`, `dataset validity improvement ≠ strength improvement` e `lower training loss ≠ stronger Ares`.
