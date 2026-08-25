# Discovery / Decision — RedWar observability and imperfect information

Data: 2026-08-25
Estado: **resolvido para o modo local atual**
Origem: auditoria do código + README + GAME_DESIGN + Project Studies upstream alert

## Discovery

O `README.md`/`docs/GAME_DESIGN.md` especificam informação escondida no draft: a composição e o posicionamento inicial são secretos para o adversário antes do início da partida.

A auditoria encontrou que a Ares recebe `game_state.to_rwen()`, e `to_rwen()` serializa o estado completo. Inicialmente isto parecia poder representar leakage.

## Auditoria da transição

O fluxo real em `main.py` resolve a ambiguidade:

```text
DRAFT
  ↓
player presses Ready
  ↓
auto_draft_inimigo() materializes opponent pieces in GameState
  ↓
fase_atual = BATALHA
  ↓
processar_ia()
  ↓
CppEngineBot.escolher_jogada()
  ↓
game_state.to_rwen()
```

A Ares só é chamada em `BATALHA`, depois de o adversário já ter sido materializado e o jogo de combate ter começado.

## Evidence

- `main.py`: `auto_draft_inimigo()` coloca o draft adversário no `GameState` quando o jogador termina o draft e o fluxo muda de `DRAFT` para `BATALHA`.
- `main.py`: `processar_ia()` chama `CppEngineBot` apenas quando `fase_atual == "BATALHA"`.
- `engine/game_state.py`: `to_rwen()` serializa todas as peças e efeitos do tabuleiro.
- `docs/GAME_DESIGN.md`: a informação escondida é descrita como proteção durante o draft, antes de o jogo começar.

## Decision

Para o **modo local atual**, RedWar é um jogo de **informação escondida apenas durante draft/setup e informação perfeita durante a batalha**.

Portanto:

```text
DRAFT
→ adversary composition/initial placement hidden

BATALHA
→ board state is public
→ full-state Ares is legal
```

A Ares atual **não deve** ser reclassificada como uma engine de information-set/belief-state apenas por causa do draft secreto.

## Non-goal

Não implementar DeepNash, information-set search ou belief-state reasoning para o modo local atual com base nesta descoberta.

## Future constraint

Qualquer futuro modo web, variante ou regra que mantenha informação oculta durante a batalha deve criar um novo Observability Contract e uma camada de observação antes de passar estado à Ares.

## Research reference

Perolat et al., *Mastering the Game of Stratego with Model-Free Multiagent Reinforcement Learning*, Science 378(6623), 2022, 990–996. DOI: 10.1126/science.add4679. Public preprint: https://arxiv.org/abs/2206.15378

A referência continua relevante para futuras variantes genuinamente de informação imperfeita; não é uma indicação de substituir a Ares atual.

## Impact on development

A infraestrutura full-state de Ares pode continuar a ser otimizada para o modo local atual. A auditoria deixa de ser um bloqueio para search/NNUE/Arena, mas passa a ser uma dependência para qualquer variante que esconda informação durante a batalha.
