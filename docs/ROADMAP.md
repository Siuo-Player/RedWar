# RedWar — Roadmap Operacional

**Baseline verificado:** `main` @ `73cf14bc0861bd3d6fdb4a437fe9f433b7322a07`  
**Data:** 2026-09-08

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas. A lógica que explica a ordem está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md); os contratos técnicos pertencem aos documentos canónicos referenciados em cada fase.

## Regra de execução

Uma fase só pode ser marcada como concluída quando a evidência indicada nessa própria fase existir no `main`.

```text
problema
→ contrato
→ implementação mínima
→ testes
→ differential/property/benchmark
→ validação apropriada
→ documentação
→ merge
→ próxima fase
```

### Evidência não intercambiável

`correctness ≠ capability ≠ performance ≠ generalisation ≠ strength ≠ balance ≠ UX`.

CI verde é condição necessária para mudanças de código, mas não é prova de força global. Um benchmark táctico é prova de capacidade, não de strength. Uma loss de NNUE é uma métrica de treino, não de força.

---

# Fase A — A0.1 Semantic Closure

**Objetivo:** fechar as últimas fronteiras semânticas entre regras, ações, transições e backends antes de tuning de força.

**Estado:** quase fechado; duas fronteiras arquiteturais continuam abertas.

## Evidência canónica

> `ARCHITECTURE.md`: “Mesma posição → mesmas ações legais.”

> `AI_ENGINE.md`: `S --make(M)--> S'` e `S' --unmake(M)--> S`.

> `MECHANICS_TRACEABILITY_MATRIX.md`: `configuration → Python → C++ → action generation → state transition → serializer/RWEN → make → unmake → hash → differential → tests`.

> `A01_SEMANTIC_CLOSURE_2026-09-07.md`: repetição/threefold continua uma fronteira de arquitetura, enquanto terminal, silêncio/stun e special-spell legality já têm cobertura explícita.

## Fechado no baseline atual

- [x] `GameAction` tornou-se fronteira canónica para os consumidores principais (`#291`, `#306`, `#308`).
- [x] Python analysis consome MOVE/ATTACK/STUN/SPAWN/SPELL (`#291`).
- [x] Special-spell legality parity fechada (`#303`).
- [x] Terminal contract comparado com o `alpha_beta()` nativo real (`#310`).
- [x] Repetition observation Python tornou-se idempotente (`#299`).
- [x] Código FrostMage inalcançável removido depois de cobertura (`#300`).
- [x] `go nodes N` tem teste dedicado de semântica de node budget.

## Ainda obrigatório

- [ ] Tornar a legalidade de execução uma autoridade explícita **antes da mutação**, sem duplicar a semântica das regras.
- [ ] Definir a identidade/histórico de repetição no backend nativo e provar a política escolhida. Não implementar uma “solução” sem primeiro decidir se o histórico faz parte da posição/search key e de que forma.
- [ ] Manter differential coverage para qualquer contrato fechado que seja tocado por mudanças futuras.

**Gate de saída:** execução ilegal não altera estado; repetição tem contrato explícito e não ambíguo; suite differential continua verde; roadmap atualizado.

---

# Fase B — Medição de força e calibração da Arena

**Objetivo:** transformar a infraestrutura existente numa medição de strength realmente comparável antes de promover melhorias de Ares.

**Estado:** infraestrutura existente; calibração empírica ainda não é uma autorização para tuning agressivo.

## Evidência canónica

> `AI_BENCHMARK_PROTOCOL.md`: “Regression / Development / Validation”.

> `STRENGTH_EVALUATION.md`: “Uma alteração correta pode continuar a ser uma regressão global.”

> `BALANCE_METHODOLOGY.md`: “pricing heuristic ≠ global power estimate ≠ design judgement”.

## Trabalho

- [ ] Consolidar runs reais em experiências deliberadamente replicadas, preservando commit, regras, budget, cor, seed/opening e validade.
- [ ] Separar definitivamente unidades de resampling de condições experimentais independentes; o dataset de 100 jogos/50 pares não deve ser tratado como 50 condições independentes.
- [ ] Medir estabilidade por população/contexto e detectar intransitividade.
- [ ] Calibrar a incerteza do rating contra resultados reais.
- [ ] Avaliar operating characteristics do SPRT isolado antes de o tornar gate automático.
- [ ] Manter o hold-out protegido e rastreável.

**Gate de saída:** existir uma metodologia empírica calibrada para o regime real do RedWar, com resultados reproduzíveis e regra explícita `accept / reject / continue`.

---

# Fase C — Ares: search capability e eficiência

**Objetivo:** melhorar a pesquisa sem contaminar a semântica do jogo.

**Pré-condição:** Fase A fechada e Fase B com instrumento de medição operacional.

## Evidência canónica

> `AI_ENGINE.md`: Ares usa alpha-beta/PVS, TT, Zobrist, iterative deepening, killer/history, move ordering e quiescence/tactical search.

> `ENGINEERING_METHODOLOGY_AND_RESEARCH.md`: “Uma heurística deve ser justificada pelo fenómeno de RedWar que tenta explorar e pela evidência de custo/força obtida.”

> `AI_BENCHMARK_PROTOCOL.md`: um benchmark é regression/capability evidence, não prova de força geral.

## Trabalho, nesta ordem

- [ ] Expandir benchmarks para segundo STUN, multi-stun, defesa, passivas/aura, lifespan/cooldown, spells condicionais e conflitos material/táctica.
- [ ] Medir baseline de nodes, NPS, profundidade efetiva e TT hit-rate.
- [ ] Testar move ordering refinements isoladamente.
- [ ] Testar aspiration windows/pruning apenas com equivalência de correção fechada.
- [ ] Melhorar quiescence especificamente para os fenómenos de RedWar antes de generalizar heurísticas.
- [ ] Adicionar diagnostics de primeira divergência/move-quality para explicar alterações de comportamento.

**Gate de saída:** cada otimização tem regressão de correção, benchmark de capability/eficiência e, quando alegada melhoria de força, Arena A/B independente.

---

# Fase D — NNUE

**Objetivo:** tornar a avaliação NNUE competitiva e barata sem abandonar o baseline clássico nem a verificabilidade.

**Estado:** infraestrutura existe; integração incremental ainda não é uma feature aceite de produção.

## Evidência canónica

> `NNUE.md`: “A implementação atual mantém uma sincronização completa da posição como baseline de correção.”

> `NNUE.md`: “A existência desses hooks não significa integração concluída.”

> `AI_ENGINE.md`: `sync_board()` permanece oracle de correção até existir paridade incremental provada.

## Trabalho

- [ ] Ligar `on_piece_change`/`on_effect_change`/`on_side_to_move_change`/`on_twc_change` às mutações reais do `BoardState`.
- [ ] Testar `incremental accumulator == full resync` após sequências e make/unmake.
- [ ] Manter `sync_board()` como oracle de correção/debug.
- [ ] Medir custo por avaliação e NPS contra o baseline clássico/full-resync.
- [ ] Auditar qualidade do teacher dataset antes de concluir que uma arquitetura NNUE é boa.
- [ ] Só depois estudar rede maior, quantização/SIMD e outras otimizações.
- [ ] Comparar força A/B com Arena sob condições controladas.

**Nota metodológica:** a pesquisa recente sobre datasets NNUE justifica investigar duplicação/leakage e composição do dataset, mas não justifica declarar que um filtro ou split específico já está implementado no `main`. O trabalho de dataset que permaneceu fora do baseline deve ser tratado como proposta até ser integrado e validado.

**Gate de saída:** paridade incremental/full-resync provada + benchmark de custo + rede treinada e reproduzível + evidência de força; só então avaliar tornar NNUE default.

---

# Fase E — Produto jogável: UI, replay e telemetria

**Objetivo:** terminar a camada jogável sem reabrir arquitetura já implementada.

## Evidência canónica

> `BATTLE_UI_SIDEBAR.md`: “Selected Hero” é persistente; “Hovered Cell / Context” é transitório; “Actions” é a superfície de decisão contextual.

> `BATTLE_UI_SIDEBAR.md`: “Uma ação legal executa diretamente. Quando existem várias ações legais para o mesmo contexto, o painel expõe a escolha completa.”

> `CURRENT_STATE.md`: “A Battle Sidebar inicial e o contexto Encyclopedia já estão implementados; a validação visual/responsiva continua trabalho de produto.”

## Trabalho

- [ ] Validação visual/responsiva do Battle Sidebar nos tamanhos suportados.
- [ ] Validar keyboard/focus e todos os estados de interação.
- [ ] Fazer automatic scene captures para regressão visual.
- [ ] Benchmark do replay com corpus real quando houver amostra suficiente.
- [ ] Ferramenta de inspeção/exportação de replay.
- [ ] Telemetria estruturada de jogos reais para alimentar análise de produto/balanceamento, respeitando observabilidade.

**Gate de saída:** UI validada visualmente e por interação; replay reproduzível; telemetria tem contrato e provenance.

---

# Fase F — Balanceamento

**Objetivo:** usar os dados reais para melhorar o sistema de jogo sem transformar uma heurística num oráculo.

## Evidência canónica

> `BALANCE_METHODOLOGY.md`: “pricing heuristic ≠ global power estimate ≠ design judgement”.

> `BALANCE_METHODOLOGY.md`: a sequência de investigação começa na mecânica correta e só chega ao preço depois de contexto, matchup, composição e validade dos dados.

## Trabalho

- [ ] Gerar hipóteses a partir de partidas reais válidas.
- [ ] Analisar hero × matchup × composition × color × engine/version.
- [ ] Separar sinal do Auto-Pricer de decisão de design.
- [ ] Validar propostas no hold-out e Arena quando aplicável.
- [ ] Executar `BALANCE_STATE_OF_GAME_AUDIT.md` como pausa obrigatória quando a infraestrutura de dados estiver madura.
- [ ] Depois do audit, parar tuning até existir decisão explícita.

**Gate de saída:** decisões de balanceamento têm dados, contexto, incerteza e decisão documentada.

---

# Fase G — Online / multiplayer

**Pré-condição:** núcleo semântico estável e contrato de ação/estado consolidado.

## Evidência canónica

> `WEB_MULTIPLAYER.md`: cliente envia intenção; servidor autoritativo valida/executa e produz novo estado/version.

> `OBSERVABILITY_CONTRACT.md`: a fronteira de informação deve ser definida por modo; a representação completa de batalha local não deve ser exposta automaticamente numa variante online.

## Trabalho

- [ ] Protocolo de ações/estado.
- [ ] Servidor autoritativo.
- [ ] Transporte realtime.
- [ ] Reconexão/timeout.
- [ ] Matchmaking.
- [ ] Rating com incerteza quando aplicável.
- [ ] Histórico/espectadores/rematch.

**Gate de saída:** servidor é autoridade sobre legalidade, estado, resultado e RNG relevante.

---

# Ordem global

```text
A0.1 Semantic Closure
        ↓
Strength measurement / calibration
        ↓
Ares search capability + efficiency
        ↓
NNUE incremental + evaluation quality
        ↓
UI/replay/telemetry hardening
        ↓
Balance / state-of-game audit
        ↓
Server-authoritative online
```

As fases UI/replay podem avançar em paralelo quando não atravessarem um correctness blocker, mas **não substituem** a cadeia de evidência da Ares. Um blocker de semântica tem precedência sobre otimização, força e balanceamento.

## Regra de referência para cada PR

A PR deve declarar explicitamente:

1. fase do roadmap;
2. documento canónico que define o contrato;
3. hipótese ou correção;
4. evidência de correctness/capability/performance/generalisation/strength adequada;
5. critério de saída;
6. documentos canónicos atualizados no mesmo bloco.

Não criar outro roadmap para contornar esta sequência.
