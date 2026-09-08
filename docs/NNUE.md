# RedWar — NNUE

## Autoridade

Este documento define o contrato da NNUE. [`ROADMAP.md`](ROADMAP.md) define a sequência; [`PROJECT_REASONING.md`](PROJECT_REASONING.md) define a cadeia de evidência.

## Arquitetura atual

**Baseline:** `main` @ `b1aadb8a26d8af0e80839e0149b693d6ca710f40`.

Ares possui uma NNUE opcional adaptada ao estado RPG. As features representam identidade/posição/equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move. O formato binário é versionado.

NNUE não é atualmente uma alegação de superioridade. A avaliação clássica continua disponível como baseline.

## Baseline de correção

A infraestrutura mantém `sync_board()` como referência de ressincronização completa. Existem hooks incrementais para alterações de peça, efeito, lado e TWC.

A existência desses hooks é **IMPLEMENTED infrastructure**, não prova de integração hot-path.

A conclusão exige, no caminho real de mutação:

```text
BoardState mutation
→ incremental hook
→ accumulator
      ≡
full sync_board()
```

após sequências, `make/unmake` e alterações dos estados persistentes relevantes.

## Custo e strength

Só depois da equivalência incremental/full-resync se deve medir custo por avaliação e NPS. Uma redução do tempo de avaliação que introduza drift não é melhoria aceite.

Mesmo uma melhoria de NPS ou training loss não constitui strength evidence. Para alegações competitivas é necessária Arena A/B sob o protocolo de strength.

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

#316 foi merged e altera a classificação de CI para a classe estreita de metodologia de dataset NNUE, separando essa manutenção de uma promoção automática de strength. Isso não significa que o pipeline de dataset tenha sido magicamente promovido a validade experimental completa.

## Promotion gate

NNUE só pode tornar-se default após:

1. correção e paridade de features;
2. determinismo relevante;
3. modelo treinado e reproduzível;
4. custo/NPS comparado com baseline;
5. ausência de regressões relevantes em referências;
6. Arena A/B com evidência suficiente;
7. cumprimento do contrato de observabilidade.

`dataset validity improvement ≠ strength improvement` e `lower training loss ≠ stronger Ares`.
