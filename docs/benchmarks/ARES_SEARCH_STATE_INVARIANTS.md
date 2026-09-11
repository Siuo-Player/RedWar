# Ares — Search-State Invariants Audit

**Governing issue:** #413  
**Parent:** #406 → #372  
**Reconciled baseline:** `main` @ `23391d956e4712d778cbf68713766b2ccb9a4623` (2026-09-11)

Este documento regista o contrato de estado que o caminho nativo de pesquisa Ares deve preservar entre `make_move()` e `unmake_move()`. É uma baseline de correctness, não uma alegação de performance ou strength.

## Invariante necessária

Para qualquer movimento legal `m` a partir de um estado `S`:

```text
S
→ make_move(m)
→ estado visível à pesquisa
→ unmake_move(m)
→ S'
```

deve produzir `S' == S` em todos os campos relevantes para a pesquisa.

A regressão nativa de reversibilidade compara o `BoardState` completo, incluindo:

- lado a jogar;
- TWC;
- hash Zobrist;
- score material;
- contagens White/Black;
- ocupação, equipa, identidade do herói, stun timer, lifespan, spawn cooldown, cost e ID de cada peça;
- ocupação, equipa, tipo e timer de cada efeito de terreno.

## Evidência integrada

`tests/cpp_reversibility_test.cpp` exerce o caminho de produção `generate_valid_moves()` → `make_move()` → `unmake_move()` em casos representativos de:

1. movimento/captura básica;
2. estado de peça atordoada;
3. spawn/lifecycle;
4. lifespan temporário e estado de efeitos/timers.

O workflow de Test Suite já compila e executa esta regressão nativa. O resultado deve bloquear a promoção de qualquer alteração que deixe de restaurar um campo relevante.

A regressão NNUE incremental/full-sync também é independente e valida a equivalência em torno de operações reais de `make_move()` / `unmake_move()`.

## Modelo de estado nativo

`BoardState` é a posição usada pela pesquisa nativa. O histórico de repetição permanece fora do objeto de posição; o hash identifica a posição e a lógica de sequência/histórico é uma preocupação externa.

`fast_clone()` não faz parte deste contrato e não deve ser introduzido no hot path C++ nem no preflight de legalidade.

## Limite atual da auditoria

A próxima extensão de correctness deve cobrir semânticas de transição específicas que ainda não estejam representadas pela matriz existente, sobretudo spells complexas, segundo-stun e efeitos de spawn. Cada divergência concreta deve ser reduzida a um caso determinístico e promovida a regressão.

Nenhuma heurística de search deve ser afinada sobre uma regressão de invariantes falhada. Benchmarks de performance e medições de Arena só são interpretáveis depois de esta camada de correctness permanecer verde.
