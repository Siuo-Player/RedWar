# RedWar — A0.1 Semantic Closure

**Baseline verificado:** `main` @ `73cf14bc0861bd3d6fdb4a437fe9f433b7322a07`  
**Data de reconciliação:** 2026-09-08

A0.1 é o gate de correção/arquitetura que vem imediatamente depois do A0 histórico e **antes de tuning de strength/search** quando uma alteração depender da semântica destas fronteiras.

## Fechado

### Inquisitor silence/stun

O contrato foi explicitamente comparado entre o C3 oracle, Python e native move generation: um Inquisitor inimigo atordoado não fornece silêncio. PR #292 transformou esta descoberta numa regressão explícita.

### Terminal semantics

PR #310 faz a regressão observar o score do `alpha_beta()` real, cobrindo mutual annihilation, one-side annihilation, blocked side, TWC=50 e o controlo TWC=49. O contrato externo de root terminal continua `bestmove 0000`.

### Special-spell legality

PR #303 fechou a paridade de legalidade das special spells sob a fronteira canónica. FrostMage `NEVADA` é `SPELL`, não um segundo mecanismo escondido de `STUN`.

### Canonical action boundary

PR #291 consolidou a análise sobre MOVE/ATTACK/STUN/SPAWN/SPELL. PR #306 tornou `engine.legal_actions` a fronteira canónica e #308 passou `execute_action()` pela normalização canónica antes da transição existente.

### Repetition observation

PR #299 corrigiu a observação repetida do mesmo hash em Python para que chamadas idempotentes de `check_game_over()` não fabriquem ocorrências.

### Legacy code

PR #300 removeu o bloco FrostMage inalcançável depois de a implementação ativa ter regressões suficientes.

### Node budget

PR #285 estabeleceu o teste dedicado da semântica `go nodes N`: o search bounded por nodes não deve exceder o budget e a execução repetida em processo novo permanece determinística sob o teste definido.

## Ainda aberto

### 1. Autoridade de execução

A normalização canónica já existe, mas a garantia forte desejada é:

```text
input action
   ↓
canonical legal-action membership
   ↓
only then mutate state
```

Não considerar este ponto fechado apenas porque `execute_action()` aceita `GameAction`.

### 2. Repetition / threefold nativo

Python mantém história para repetição. O `BoardState` nativo não possui ainda um equivalente definido no mesmo nível de contrato. Antes de implementar uma solução é necessário decidir:

- o que constitui identidade de repetição;
- se TWC faz parte dessa identidade;
- se a história faz parte do contexto da pesquisa;
- como `make/unmake`, RWEN e search interagem com a história;
- como provar paridade sem criar uma segunda semântica.

## Regra de saída

A0.1 só fecha quando os pontos abertos estiverem resolvidos **ou explicitamente transformados em uma fronteira contratual deliberada e testada**.

A existência deste documento não autoriza search tuning, NNUE tuning, strength claims ou balance changes.

Fonte de execução: [`ROADMAP.md`](ROADMAP.md). Linha de raciocínio transversal: [`PROJECT_REASONING.md`](PROJECT_REASONING.md).
