# RedWar — Estado, crítica e correção de rumo

**Snapshot:** 2026-09-06  
**Main observado:** `ed21686cdcd6d377bbf426cf7198e112bda5f3de`

## Fotografia

A base de engenharia está forte: contratos C0–C5, diferencial Python/C++, oracle independente, replay/provenance, Arena/Strength e UI contextual com Encyclopedia canónica.

## Críticas e correções

### 1. Produto avançou enquanto A0 ainda tinha obrigações residuais
Isto aumenta a superfície de mudança antes de a equivalência estar totalmente fechada.

**Correção:** novas alterações substantivas de Ares ficam bloqueadas até existir `A0 PASS`. UI pode continuar apenas quando não altera regras, transições ou contratos do engine.

### 2. Snapshots documentais ficaram atrás do `main`
`CURRENT_STATE.md` mantinha uma data anterior à evolução real do repositório.

**Correção:** cada novo marco exige snapshot datado + reconciliação do roadmap no mesmo bloco.

### 3. C3 foi corretamente implementado, mas é fácil sobreinterpretá-lo
Concordância de legal actions não prova estado pós-ação, make/unmake, search quality ou strength.

**Correção:** toda a evidência deve declarar explicitamente a camada demonstrada.

### 4. Falta de um gate agregador de A0 visível
Há muitos testes individuais, mas não um único critério de saída.

**Correção:** `A0 PASS` só pode existir quando C0+C1+C2+C3+C4+C5 e o contrato de node-budget estiverem suficientemente demonstrados.

### 5. Optimização pode produzir ganhos locais sem ganho global
Benchmarks dirigidos e CI não são prova de força competitiva.

**Correção:** search/move ordering/NNUE devem usar baseline congelada, testes de regressão, hold-out independente e strength evidence antes de promoção.

## Gate A0

```text
C0 state identity
→ C1 canonical action
→ C2 validation/execution
→ C3 independent legal-action oracle
→ C4 cross-backend post-state equivalence
→ C5 bridge/protocol
→ pure node-budget semantics
→ A0 PASS
```

Estados possíveis: `PASS`, `PARTIAL`, `BLOCKED`.

## Antes do próximo marco

1. completar gaps C4 nas transições raras: timers, lifecycle, TWC, effects, spawn/cooldown, special spells e terminal states;
2. demonstrar que `go nodes N` não depende secretamente de wall-clock;
3. reconciliar snapshots/roadmaps com o `main` após cada marco;
4. só depois executar Strength calibration;
5. manter NNUE/search optimization atrás do gate científico de strength.

## Regra permanente

```text
DOCUMENTADO ≠ IMPLEMENTADO ≠ TESTADO ≠ VALIDADO ≠ COMPROVADO
```
