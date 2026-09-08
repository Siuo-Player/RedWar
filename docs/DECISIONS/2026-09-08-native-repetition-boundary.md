# Decisão — fronteira de repetição/history nativa

**Data:** 2026-09-08  
**Estado:** ACCEPTED  
**Âmbito:** A0.1 / A.2

## Decisão

`BoardState` nativo continua a representar uma posição corrente e o estado de transição necessário à pesquisa (`pieces`, effects, side to move, TWC e hash). Não será introduzido um `state_history` mutável no `BoardState` apenas para imitar a infraestrutura de adjudicação Python.

A identidade de repetição e a contagem threefold pertencem à camada de contexto/adjudicação que possui a sequência de posições. O `BoardState::hash` é a identidade da posição corrente; `twc` continua separado e não substitui history de repetição.

Isto é uma **fronteira arquitetural deliberada**, não uma alegação de que o C++ e o Python já possuem equivalência de threefold.

## Consequências

- `make_move()`/`unmake_move()` devem preservar a posição corrente e `twc`, sem assumir ownership de um histórico de partidas.
- O search pode receber um contexto de repetição futuro sem alterar a semântica de `BoardState`.
- RWEN e replay podem transportar o estado/sequence necessário à adjudicação fora do `BoardState`.
- Qualquer futura implementação de threefold nativo deve primeiro definir o protocolo do histórico e a identidade completa da posição; não deve ser inferida apenas do `hash` ou do TWC.
- Não se afirma equivalência Python↔C++ para threefold até existir esse protocolo e uma regressão diferencial correspondente.

## Evidência

A implementação Python mantém `GameState.state_history` e `_last_history_hash` e usa a repetição como adjudicação do estado; a estrutura nativa `BoardState` contém `twc` e `hash`, mas não um histórico de posições. A diferença é conhecida e passa a ser tratada como contrato arquitetural explícito em vez de uma lacuna ambígua.

## Não decidido

Esta decisão não define ainda a API de um futuro `RepetitionContext`, nem fecha qualquer alegação de força ou paridade de terminal semantics. Essas decisões só serão tomadas quando houver um consumidor concreto e um protocolo de validação diferencial.
