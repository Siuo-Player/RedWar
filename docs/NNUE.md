# RedWar — NNUE

## Autoridade

Este documento define o contrato da NNUE. A sequência de implementação está em [`ROADMAP.md`](ROADMAP.md) e a lógica transversal em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## Arquitetura atual

Ares possui uma NNUE opcional adaptada ao estado RPG. As features representam identidade/posição/equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move. O formato binário é versionado.

NNUE não é atualmente uma alegação de superioridade. A avaliação clássica continua disponível como baseline.

## Baseline de correção

A infraestrutura mantém `sync_board()` como referência de ressincronização completa. Existem hooks incrementais para alterações de peça, efeito, lado e TWC.

A existência desses hooks não significa integração concluída.

A conclusão exige:

```text
BoardState mutation
→ incremental hook
→ accumulator
      ≡
full sync_board()
```

após sequências, make/unmake e alterações dos estados persistentes relevantes.

## Custo

Só depois da equivalência incremental/full-resync se deve medir custo por avaliação e NPS. Uma redução do tempo de avaliação que introduza drift não é uma melhoria.

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

A pesquisa recente sobre datasets NNUE é uma motivação para auditar duplicação, leakage, diversidade e estabilidade das posições. **Não tratar propostas de split/filtro não integradas no `main` como implementação existente.**

## Promoção

NNUE só pode tornar-se default após:

1. correção e paridade de features;
2. determinismo;
3. modelo treinado e reprodutível;
4. custo/NPS comparado com baseline;
5. ausência de regressões relevantes em referências;
6. Arena A/B com evidência suficiente;
7. cumprimento do contrato de observabilidade.
