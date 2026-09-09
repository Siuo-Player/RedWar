# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `f2e7155d150b4cc0be79d4b86beb5005941ef180`  
**Data:** 2026-09-09

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas.

## Vocabulário obrigatório

`DOCUMENTED` = descrito.  
`IMPLEMENTED` = existe no código alvo.  
`TESTED` = existe teste executável relevante.  
`VALIDATED` = foi submetido à validação apropriada para a alegação.  
`PROVEN` = a evidência é suficiente para a alegação específica sob o protocolo vigente.

Uma fase só pode ser `CLOSED` quando os critérios de aceitação forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e melhoria de dataset ≠ melhoria de strength.

## A0.1 — Semantic Closure

**CLOSED.** As fronteiras deliberadas de action-space/execução e repetição histórica foram fechadas por #338, #351 e #352. `legal_actions()` permanece autoridade da action-space; `resolve_legal_action()` é o seam de resolução; `_validate_transition()` trata restrições da transição; `execute_action()` só muta depois das validações. `fast_clone()` não é autoridade de legalidade.

## Sprint 20 — Foundation Gate

A0.1 fechado **não** implica foundation fechada. A fundação continua a exigir correctness operacional, Ares, validação crítica, provenance e documentação coerente.

### P0 — NNUE incremental correctness

**CLOSED — #356.** A integração incremental passou por CI e foi merged em `main`. A evidência valida equivalência do acumulador incremental com `sync_board()` nos caminhos reais de `make_move()`/`unmake_move()` e nos estados persistentes cobertos pela suíte, incluindo temporizadores mutáveis.

Isto é evidence de correctness da integração. Não é evidence de performance superior, strength superior ou melhor modelo.

### P0/P1 — Tactical validation breadth

**OPEN — #359.** A lane foi reconstruída sobre o `main` pós-#356. A suite cobre STUN, SPELL, DEFENSE, LIFESPAN_COOLDOWN, TWC e HIGH_VALUE_CAPTURE e inclui um probe para um estado RWEN realmente preservado do corpus de jogos reais. A execução CI deve validar o comportamento da engine antes do merge.

### P1 — Traceability

**AUDITED — no mismatch estrutural novo demonstrado nesta tranche.** O schema de heroes alimenta Python/C++ e existem testes de schema, spells declaradas, referências de comportamento e paridade representativa. Esta evidência não deve ser descrita como exaustividade de todos os estados possíveis.

### P1 — Failure provenance

**OPEN — #360.** A infraestrutura de bridge já distingue timeout, process exit e protocol errors, e a Arena exclui observações já marcadas como inválidas das agregações. Falta transportar exceções reais ocorridas dentro de `start_tournament()` para uma observação inválida por jogo com categoria semântica persistida, em vez de abortar o torneio.

### P1 — Documentation consistency

**OPEN FOR MERGE — `state20/foundation-docs-sync-2026-09-09`.** `CURRENT_STATE.md`, `NNUE.md` e este roadmap foram atualizados para refletir o `main` pós-#356 e a separação entre A0.1 e foundation. Esta lane é deliberadamente independente da execução do #359.

## Gate de fundação

A foundation só passa a `CLOSED` quando, cumulativamente:

- regras centrais e runtime não têm blockers estruturais conhecidos;
- Ares tem pipeline funcional e regression-protected;
- correctness incremental relevante está validada;
- tactical/capability regressions críticas estão validadas;
- provenance real sobrevive aos boundaries de tooling;
- configuração ↔ lógica não divergem silenciosamente nos caminhos relevantes;
- serialização/reprodução suporta os contratos existentes;
- CI/testes principais estão verdes nos heads que entram em `main`;
- não existe blocker E/D/C/B relevante.

## Depois da foundation

Quando o gate acima estiver fechado, **não continuar a expandir a foundation**.

A sequência de produto/capability passa então para:

1. **B — Strength measurement / calibration:** medir competitive strength sob protocolo controlado, sem confundir capability/performance com strength.
2. **C — Ares search capability + efficiency:** otimizações e melhorias de search somente com regressão de correctness e benchmark controlado.
3. **D — NNUE evaluation quality:** custo/NPS, qualidade do evaluator e eventual promoção a default somente após Arena A/B.
4. **E — UI / replay / telemetry validation.**
5. **F — Balance / state-of-game audit.**
6. **G — Server-authoritative online / multiplayer.**

UI/replay pode avançar em paralelo quando não atravessar correctness blockers, mas não substitui o gate da foundation.

## Regra de referência para cada PR

Toda PR deve declarar:

1. ID/fase do roadmap;
2. documento canónico que define o contrato;
3. hipótese ou correção;
4. tipo de evidência esperada;
5. critério de saída;
6. documentos canónicos atualizados no mesmo work package.

Não criar outro roadmap para contornar esta sequência.
