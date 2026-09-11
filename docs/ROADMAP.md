# RedWar — Roadmap Operacional

## Gate chain 1.0

```text
#370 Foundation
      ↓
#371 Gameplay
      ↓
#372 Ares
      ↓
#373 Product
      ↓
#374 Online
      ↓
#375 Release
```

## Estado

- **#370 Foundation — CLOSED.** Contratos base e fronteira de execução fechados para o ruleset atual.
- **#371 Gameplay — CLOSED.** Ruleset 1.0 jogável fechado para o escopo declarado.
- **#372 Ares — OPEN.** Gate ativo.
- **#373 Product — BLOCKED por #372.**
- **#374 Online — BLOCKED por #372/#373.**
- **#375 Release — BLOCKED por #372/#373/#374.**

## #372 — Ares

Objetivo: tornar Ares suficientemente correto, capaz, eficiente e forte para promoção ao produto.

Ordem obrigatória:

```text
correctness
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

Regras permanentes:

- `fast_clone()` não é hot path C++ nem preflight de legalidade;
- benchmark, NPS, node count, dataset size ou training loss não são prova de strength;
- search changes devem ser hipóteses isoladas com validação própria;
- NNUE só pode ser promovida após paridade, custo e evidência competitiva adequados;
- não alterar as regras do jogo para contornar um blocker de Ares.

## Execução paralela

Trabalho posterior pode preparar-se em paralelo quando não falsifica uma dependência. Uma preparação não fecha nem ultrapassa um gate anterior.

## Regra documental

Este é o único roadmap operacional. Estado transitório, SHAs, resultados de CI e notas de handoff pertencem ao Git/Issues/CI. Decisões duráveis pertencem a `docs/DECISIONS/`.
