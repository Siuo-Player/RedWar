# RedWar — Current State

**Snapshot:** 2026-09-10  
**Verified `main`:** `3a06d2edf1dc4f32b8719eb3d0da8167613424eb`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a cadeia causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Gate de produto atual

**Gate ativo: #372 Ares.**

A execução 1.0 segue **#370 Foundation → #371 Gameplay → #372 Ares → #373 Product → #374 Online → #375 Release**. #370 e #371 estão fechados; #372 é agora o gate principal em execução.

## 2. Fundação e Gameplay

A fronteira de execução consolidada permanece:

```text
input action
→ canonical normalization / resolution
→ action-space membership where applicable
→ transition-domain validation
→ only then mutate
```

A fundação e o ruleset Gameplay atualmente declarado estão fechados para os contratos aceites, incluindo pre-match validation, surrender, STUN → segundo STUN → morte, terminal no-action canónico, TWC e timing de efeitos.

`fast_clone()` continua apenas em tooling/reference Python e fora do hot path C++ e do preflight de legalidade.

## 3. Ares — estado atual

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo.

### Evidência já integrada na gate #372

| Linha | Estado | Evidência |
|---|---|---|
| Tactical capability | MERGED | #410: `second-stun-lethal` + corpus existente |
| Canonical bestmove legality | MERGED | #417 |
| Classical evaluator baseline | MERGED | #411, com fonte/versionamento |
| Native make/unmake reversibility in CI | MERGED | #421 / #418 |
| NNUE incremental cost benchmark | MERGED | #420 |
| Move-ordering baseline machine-readable | IN PROGRESS | #433 / PR #434 |

O corpus táctico usa respostas parseáveis/legalizadas pelo action-space canónico. As referências strict continuam capability/regression evidence; não constituem isoladamente prova de strength. 

O evaluator clássico está congelado como baseline de comparação e a NNUE permanece opcional. A paridade incremental/full-sync é tratada como correctness; o custo incremental já tem benchmark dedicado.

## 4. Próxima sequência Ares

```text
move-ordering baseline
        ↓
search hypothesis (isolada)
        ↓
correctness/regression
        ↓
matched-budget performance
        ↓
independent Arena strength
        ↓
accepted Ares configuration
```

Cada otimização deve ser atribuível a uma hipótese concreta. Melhor NPS, menor número de nodes, puzzle local ou alteração de training loss não são por si só promoção de strength.

## 5. Strength / Arena

A infraestrutura de Arena, provenance, rating/uncertainty e análise pareada existe. O dataset real persistido contém 100 jogos em 50 pares de inversão de cor; esses pares não equivalem a 50 condições experimentais independentes.

## 6. Product / Online / Release

#373 Product, #374 Online e #375 Release permanecem bloqueados até #372 fechar. A arquitetura UI/Battle Sidebar já existente pode ser validada em paralelo quando usar contratos estáveis, mas não pode substituir a aceitação do Ares.
