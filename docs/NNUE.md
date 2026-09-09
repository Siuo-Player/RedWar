# RedWar — NNUE

## Autoridade

Este documento define o contrato da NNUE. [`ROADMAP.md`](ROADMAP.md) define a sequência; [`PROJECT_REASONING.md`](PROJECT_REASONING.md) define a cadeia de evidência.

## Arquitetura atual

**Baseline documental:** `main` @ `f2e7155d150b4cc0be79d4b86beb5005941ef180`.

Ares possui uma NNUE opcional adaptada ao estado RPG. As features representam identidade/posição/equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move. O formato binário é versionado.

NNUE não é atualmente uma alegação de superioridade competitiva. A avaliação clássica continua disponível como baseline.

## Correção incremental

**P0 CLOSED — PR #356.** A integração incremental foi validada nos caminhos reais de mutação `make_move()` / `unmake_move()`, comparando o acumulador incremental com `sync_board()` como oracle de refresh completo. A correção incluiu o caso em que temporizadores dentro de `Piece` são alterados diretamente antes de uma atribuição; os hooks passaram a observar corretamente esse estado real de mutação.

A cadeia validada é:

```text
BoardState mutation
→ incremental hook
→ accumulator
      ≡
full sync_board()
```

para as sequências e estados persistentes cobertos pela suíte, incluindo movimento, captura, STUN, lifespan, cooldown, efeitos, TWC, side-to-move, spawn, expiração e restauração por unmake.

`sync_board()` continua permitido como oracle, recovery path e test support; não é o mecanismo oculto do hot path.

## Custo e strength

A correção incremental não constitui, por si só, prova de melhoria de performance ou strength. Medições de custo/NPS devem comparar contra baseline depois da correção, e alegações competitivas exigem Arena A/B sob protocolo definido.

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

**Estado atual verificável:** #314, que propunha deterministic grouped splitting e `audit_dataset.py`, não foi merged. #316 foi merged e mantém separada a classe estreita de manutenção metodológica da promoção de strength.

## Promotion gate

NNUE só pode tornar-se default após:

1. correção e paridade de features;
2. determinismo relevante;
3. modelo treinado e reproduzível;
4. custo/NPS comparado com baseline;
5. ausência de regressões relevantes em referências;
6. Arena A/B com evidência suficiente;
7. cumprimento do contrato de observabilidade.

`dataset validity improvement ≠ strength improvement`; `lower training loss ≠ stronger Ares`; `incremental correctness ≠ competitive superiority`.
