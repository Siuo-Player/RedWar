# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `612221b88381cf740bab6d2ab9e31acfb98c6324`  
**Data:** 2026-09-10

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas.

## Vocabulário obrigatório

`DOCUMENTED` = descrito.  
`IMPLEMENTED` = existe no código alvo.  
`TESTED` = existe teste executável relevante.  
`VALIDATED` = foi submetido à validação apropriada para a alegação.  
`PROVEN` = a evidência é suficiente para a alegação específica sob o protocolo vigente.

Uma fase só pode ser `CLOSED` quando os critérios de aceitação forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e melhoria de dataset ≠ melhoria de strength.

## Estado histórico — A0.1 Semantic Closure: FECHADO

A tranche inicial encerrou a fronteira semântica que bloqueava trabalho dependente.

- **#329** — determinismo do audit emparelhado; merged `29973ffb6e7d270ab8ccc9289307ab11e2f24506`.
- **#330** — ausência de `fast_clone` no C++ da Ares; merged `d08a700864d8ed0fe9dc274f8495a01f81105641`.
- **#331** — encoding NNUE por perspetiva; merged `fdd1c3516e410b53608a95e554597a577ef6610e`.
- **#332** — isolamento replay/telemetria; merged `d07f52f981de0eb0606bef1823beabca61348ae1`.
- **#333** — bounds do Auto-Pricer; merged `71bc812d170a8556b9dfde98b4f95202f36190b9`.
- **#334** — fundação de sessão autoritativa server-side; merged `845b00a500fff7b3aab2f0c35920bace5d198cc6`.

A0.1 ficou operacionalmente encerrado com a sequência autoritativa `normalize → canonical resolution/membership → transition-domain validation → mutate`, sem usar `fast_clone()` como autoridade de legalidade.

## Ordem 1.0 — gates operacionais

A ordem oficial de trabalho é agora explicitamente governada pelos Issues:

```text
#370 — Foundation
   ↓
#371 — Gameplay
   ↓
#372 — Ares
   ↓
#373 — Product
   ↓
#374 — Online
   ↓
#375 — Release
```

Os Issues #376–#378 mantêm a ordem documental e o vínculo com a fila, mas não criam uma segunda roadmap. O Issue #379 é filho de #370 e é uma auditoria de autoridade/fundações; não é uma fase adicional.

### #370 — Foundation

**Estado: OPEN — audit/fixes em curso.**

Objetivo: fechar definitivamente as fundações de autoridade, contratos, documentação canónica e ausência de autoridade duplicada antes de permitir o gate seguinte.

**Trabalho atual:**

- **#379** — matriz canónica de autoridade e gap audit.
- **PR #381** — sincronizou referências CURRENT_STATE/NNUE e foi merged em `612221b88381cf740bab6d2ab9e31acfb98c6324`.
- **PR #380** — remove a whitelist duplicada de spells na validação de transições, fazendo a capacidade derivar de `heroes_config.json`; OPEN.
- **PR #386** — adiciona a matriz durável de autoridade da foundation; OPEN.

**Critério de saída:** #379 sem blockers `DUPLICATED_AUTHORITY`, `DOCUMENTATION_DRIFT` ou `UNPROTECTED_GAP` em aberto, respetivas correções integradas em `main`, CI relevante verde e evidência ligada ao #370.

### #371 — Gameplay

**Estado: NOT STARTED AS GATE — preparação subordinada permitida apenas sem atravessar blockers.**

Objetivo: consolidar o ciclo jogável de interação, regras de jogo e estados necessários ao produto, sem introduzir uma segunda autoridade das regras.

O trabalho especializado já existente, incluindo #318, é subordinado a esta ordem e não constitui uma fila concorrente.

### #372 — Ares

**Estado: BLOCKED BY GATE ORDER.**

Objetivo: capability e eficiência de search, sempre correctness-first. Cada otimização deve ter regressão de correctness e benchmark controlado; qualquer alegação de strength requer Arena A/B independente.

`fast_clone()` não pertence ao hot path C++ da Ares nem pode ser promovido a autoridade semântica.

### #373 — Product

**Estado: BLOCKED BY GATE ORDER.**

Objetivo: validação e consolidação de UI, replay e telemetria como produto jogável. Arquitetura existente pode ser preparada quando isso não atravessar blockers das gates anteriores.

### #374 — Online

**Estado: BLOCKED BY GATE ORDER.**

Objetivo: transformar a fundação server-authoritative existente num contrato online completo, incluindo validação, sincronização, sessão e segurança operacional.

### #375 — Release

**Estado: BLOCKED BY GATE ORDER.**

Objetivo: fechar evidência de release, documentação operacional, regressões e critérios de publicação. Não é permitido usar benchmarks parciais como substituto de critérios de release.

## Métricas de trabalho por fase

O progresso global deve ser lido pela conclusão dos gates acima, não por volume de commits.

- **Foundation:** fundações e autoridades canónicas fechadas.
- **Gameplay:** interação e regras jogáveis integradas e validadas.
- **Ares:** search correctness + eficiência + evidência de desempenho.
- **Product:** UI/replay/telemetria validados como produto.
- **Online:** contrato server-authoritative completo e validado.
- **Release:** critérios finais, regressão e publicação.

Uma área posterior pode receber trabalho preparatório, documentação ou testes independentes, mas **não pode ser declarada concluída nem usada para ultrapassar um gate predecessor**.

## Regra de referência para cada PR

Toda PR deve declarar:

1. ID/fase do roadmap;
2. documento canónico que define o contrato;
3. hipótese ou correção;
4. tipo de evidência esperada;
5. critério de saída;
6. documentos canónicos atualizados no mesmo work package.

Não criar outro roadmap para contornar esta sequência.
