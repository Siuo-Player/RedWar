# RedWar — Current State

**Snapshot:** 2026-09-09  
**Verified `main`:** `a6e618d5ec0dc9454eeaec36da13d92371cc9564`

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

**Estado do conhecimento:** arquitetura IMPLEMENTED e contratos principais TESTED; não há alegação de STRENGTH improvement nesta tranche.

## 3. NNUE

**P0 fechado em #356.** A integração incremental foi validada nos caminhos reais de `make_move()` / `unmake_move()`, comparando o acumulador incremental com `sync_board()` como oracle de refresh completo, incluindo alterações de temporizadores.

`sync_board()` continua permitido como oracle/recovery/test support. Isto fecha correctness da integração incremental sob a cobertura validada; não demonstra superioridade competitiva, melhor NPS ou strength.

A metodologia de dataset NNUE continua separada da afirmação de strength. #314 não foi merged.

## 4. Tactical validation

**OPEN — PR #363.** A lane foi reconstruída sobre o `main` pós-#362. A suite cobre STUN, SPELL, DEFENSE, LIFESPAN_COOLDOWN, TWC e HIGH_VALUE_CAPTURE e inclui um probe para um estado RWEN realmente preservado do corpus de jogos reais.

O benchmark está semanticamente separado entre:

- capability: Ares consegue produzir uma ação válida;
- strict-choice: Ares escolhe uma referência específica, reservado a evidence semelhante a strength.

O timeout do harness também é realmente limitado e não depende de `readline()` bloqueante.

Estado: IMPLEMENTED; VALIDATION aguardando CI completo do #363.

## 5. Heróis / regras / traceability

O sistema continua híbrido: `engine/heroes_config.json` fornece estrutura declarativa e código especializado cobre mecânicas ainda não expressas integralmente no schema.

A auditoria Sprint 20 não demonstrou mismatch estrutural novo entre configuração, definições Python, comportamento C++, action generation, transição e RWEN/hash. Os testes existentes permanecem evidência representativa, não prova matemática de exaustividade.

## 6. Strength / Arena / provenance

A infraestrutura de Arena, provenance, população, Elo-compatible rating, uncertainty, paired-game/pentanomial analysis, hold-out e SPRT isolado existe.

PR #362 foi merged como `a6e618d5ec0dc9454eeaec36da13d92371cc9564`. A fronteira Arena agora preserva falhas de execução como observações inválidas auditáveis, sem as deixar entrar na agregação competitiva.

Correctness, capability, performance, competitive strength e balance permanecem classes distintas de evidência.

Calibração de strength global continua UNVERIFIED.

## 7. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, contexto Encyclopedia, geometria responsiva e tema semântico está integrada. A validação visual/UX e replay/telemetria continuam fora do gate de foundation correctness atual.

## 8. Estado operacional

A foundation **não está fechada** enquanto a validação tática crítica de #363 e a consistência documental correspondente não estiverem concluídas no `main`.

Não avançar para strength/balance tuning como substituto destes gates.
