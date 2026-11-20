# RedWar — Architecture

## Papel

Este documento define fronteiras e invariantes arquiteturais do sistema. O estado implementado é autoridade do código e dos testes; [`ROADMAP.md`](ROADMAP.md) define a sequência de evolução.

## Núcleo e Fronteiras

```text
               rules / state (canonical)
                          ↓
                  canonical actions
                          ↓
      ┌───────────────────┴───────────────────┐
      ↓                                       ↓
Python reference                        C++ Ares Engine
(Product Semantics & UI)               (Search, Eval & NNUE)
      ↓                                       ↓
Game Modes / Timers                     Arena / Strength Benchmark
(8x8, 10x10, Blitz/Bullet)                    ↓
      ↓                               Balance Lab Oracle
Authoritative Server (WebSocket)        (Hero Costs & Rules Balance)
      ↓
Web & Desktop Clients
```

Python e C++ coexistem como backends de referência e de produção de alto desempenho. Qualquer mudança que atravesse a fronteira deve preservar a semântica comum e usar validação diferencial.

## Invariantes Fundamentais

1. **Determinismo:** Mesma posição → exatamente as mesmas ações legais geradas.
2. **Reversibilidade:** `make → unmake` restaura o tabuleiro e metadados de forma idêntica.
3. **Condições Terminais:** Aniquilação, ausência de lances legais e limite de TWC (50 turnos) mantêm semântica idêntica em Python e C++.
4. **Ciclo de Efeitos:** Timers de stun, lifespan de invocações, cooldowns de feitiços e terreno (fogo/gelo) seguem contratos estritos de temporização.
5. **Serialização Canónica (RWEN):** A representação em string é estável, determinística e reversível.
6. **Autoridade de Rede:** O cliente nunca dita estado; o servidor autoritativo valida cada lance antes da mutação.

## Limites de Execução

A fronteira de execução é:

```text
input action
→ canonical normalization / resolution
→ action-space membership (legal_actions)
→ transition validation
→ mutation
```

`legal_actions()` descreve o espaço de ações possíveis; a execução valida a transição concreta antes de mutar o estado. `fast_clone()` é ferramenta auxiliar de simulação em Python e não é hot path C++ nem preflight de execução.

## Modelo Stockfish & Balance Lab

1. **Ares como Motor Stockfish-like:** A IA é otimizada com foco em profundidade, velocidade e acerto tático (LMR, ordenação de lances por capturas letais/stuns, Quiescence Search e NNUE).
2. **Ares como Oráculo de Balanceamento:** O Balance Lab utiliza o Ares para simulações massivas de partidas emparelhadas, determinando empiricamente os custos ideais de draft dos heróis, viabilidade de composições e equilíbrio entre primeiro/segundo jogador em múltiplos modos.

## Estados de Evidência

```text
IMPLEMENTED → TESTED → VALIDATED → PROVEN
```

Uma propriedade documentada não se torna automaticamente provada sem a respetiva suite de testes ou evidência da Arena.
