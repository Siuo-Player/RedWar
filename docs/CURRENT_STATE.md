# RedWar — Current State

**Snapshot:** 2026-09-09  
**Verified `main`:** `f2e7155d150b4cc0be79d4b86beb5005941ef180`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a explicação causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Fase atual

**A0 histórico: CLOSED. A0.1 Semantic Closure: CLOSED. Foundation: OPEN.**

A fronteira de legalidade consolidada continua a ser:

```text
input action
        ↓
canonical normalization / resolution
        ↓
action-space membership where applicable
        ↓
transition-domain validation
        ↓
only then mutate
```

`legal_actions()` é a autoridade canónica da action-space; `resolve_legal_action()` é o seam de resolução canónica/legacy; `_validate_transition()` mantém as restrições de transição; `execute_action()` só entrega uma ação resolvida à mutação depois dessas fronteiras. `fast_clone()` não é preflight nem autoridade de legalidade e permanece fora do hot path C++ da Ares.

A0.1 permanece fechado apenas para as afirmações específicas já validadas por #351/#352/#338; não representa prova exaustiva de todos os estados possíveis.

## 2. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo.

**Estado do conhecimento:** arquitetura IMPLEMENTED e contratos principais TESTED; não há alegação de melhoria de STRENGTH nesta tranche.

## 3. NNUE

**P0 fechado em #356.** A integração incremental passou a demonstrar equivalência entre o estado incremental e `sync_board()` nos caminhos reais de `make_move()`/`unmake_move()`, incluindo alterações de temporizadores e os estados persistentes cobertos pela suíte.

`sync_board()` continua permitido como oracle/recovery/test support. Isto fecha correctness da integração incremental sob a cobertura validada; não demonstra superioridade competitiva, melhor NPS ou strength.

A metodologia de dataset NNUE continua separada da afirmação de strength. #314 não foi merged.

## 4. Tactical validation

**P1/P0 em progresso — PR #359.** A tranche foi reconstruída sobre o `main` pós-#356 porque o #358 estava baseado no baseline antigo e falhava com RWEN malformado.

O #359 cobre explicitamente STUN, SPELL, DEFENSE, LIFESPAN_COOLDOWN, TWC e HIGH_VALUE_CAPTURE, e usa apenas estados RWEN preservados/legítimos para o probe de corpus real. O harness também passou a impor um timeout real de leitura para não ficar bloqueado num `readline()` indefinido.

Estado: IMPLEMENTED; VALIDATION aguardando conclusão de CI.

## 5. Heróis / regras

O sistema continua híbrido: `engine/heroes_config.json` fornece estrutura declarativa e código especializado cobre mecânicas ainda não expressas integralmente no schema.

Os testes de traceability cobrem schema, spells declaradas, referências de comportamento e paridade representativa entre Python e C++. Isto é evidência de cobertura contratual representativa, não prova de exaustividade matemática.

## 6. Strength / Arena / provenance

A infraestrutura de Arena, provenance, população, Elo-compatible rating, uncertainty, paired-game/pentanomial analysis, hold-out e SPRT isolado existe.

Os resultados competitivos continuam sujeitos à validade do protocolo. Correctness, capability, performance, competitive strength e balance permanecem classes distintas de evidência.

Foi identificado o **P1 #360**: exceções reais de transporte/engine/transição ainda podem sair de `start_tournament()` antes de serem persistidas como observações inválidas por jogo. Os testes existentes asseguram que observações já marcadas como inválidas são excluídas das agregações, mas não cobrem ainda esta fronteira de exceção real.

## 7. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, contexto Encyclopedia, geometria responsiva e tema semântico está integrada. A validação visual/UX e replay/telemetria continuam fora do gate de foundation correctness atual.

## 8. Estado operacional

A fundação **não está fechada** enquanto #359 não tiver validação CI completa e enquanto os blockers estruturais P1 relevantes, incluindo provenance #360, não estiverem resolvidos ou formalmente reclassificados.

Não avançar para strength/balance tuning como substituto destes gates.
