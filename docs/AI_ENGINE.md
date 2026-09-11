# Ares — AI Engine

## Autoridade

Este documento define o contrato durável da Ares. O comportamento realmente implementado é determinado pelo código/testes do `main`; [`ROADMAP.md`](ROADMAP.md) define a ordem dos gates.

## Engine

Ares é o engine C++ de busca do RedWar. O desenho suporta:

- alpha-beta/PVS;
- iterative deepening;
- transposition table e Zobrist hashing;
- move ordering, killer/history heuristics;
- quiescence/tactical search;
- limites por nós/tempo.

O estado relevante inclui peças, stun, lifespan, spawn cooldown, efeitos, TWC e side-to-move. Ares deve respeitar exatamente a semântica do ruleset RedWar e a informação autorizada pelo modo de jogo.

## Fronteira de execução

A ordem canónica é:

```text
input action
→ normalize / canonical resolution
→ action-space membership
→ transition-domain validation
→ mutate
```

Legalidade de action-space e validade da transição são conceitos distintos. Uma otimização de pesquisa não pode contornar a autoridade de execução.

`fast_clone()` não é hot path C++ nem preflight aceite do executor.

## Pesquisa

Alterações de search, pruning, ordering ou evaluation são hipóteses isoladas. Devem demonstrar:

```text
correção
→ capability específica
→ custo/performance controlado
→ strength independente
```

Um melhor resultado num puzzle, maior NPS ou menor custo local não constitui prova de strength global.

## Evaluation / NNUE

A avaliação clássica permanece uma referência de compatibilidade/correção. NNUE é opcional e deve manter paridade semântica com o estado observável.

O caminho incremental de NNUE é aceite apenas quando a equivalência com full resync estiver demonstrada nos caminhos reais de mutação. `sync_board()` pode permanecer como oracle/recovery path sem ser usado silenciosamente para mascarar erros incrementais.

## Evidência de força

A promoção de Ares requer evidência independente, tipicamente Arena A/B sob orçamento comparável e protocolo estatístico explícito.

```text
benchmark
≠ capability geral
≠ performance geral
≠ strength
```
