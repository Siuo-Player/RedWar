# 2026-11-06 - Política Anti-Involução e Preservação de Invariantes Fundamentais

## Estado
**Aprovado & Implementado** (Validado formalmente via Lean 4 e suites de testes automatizados).

## Contexto & Motivação
Durante o desenvolvimento do RedWar 2.0, identificaram-se desvios críticos e regressões ("involução") em refatorações anteriores:
1. **Sobrescrita/Remoção de Funcionalidades Válidas**: Recursos requeridos (autenticação com Raio de Explosão Zero, novas abas de Academia, Puzzles, Game Review e Analytics) correram risco de regressão quando refatorações simplistas tentaram reverter alterações benéficas.
2. **Bug de Auto-captura de Peças Aliadas**: No cliente web, a movimentação desprovida de validação permitia clicar numa peça e aterrar sobre um aliado, sobrescrevendo-o ("auto-captura").
3. **Bug de Controlo das Peças da IA**: Durante o turno das Pretas, a interface permitia ao utilizador humano interagir com peças do oponente em vez de acionar a tomada de decisão autónoma do Ares Bot.
4. **Suposição de Teto Fixo de 19 Peças**: Testes legados continham asserções rígidas (`assert len(assets) == 19`), quebrando quando o catálogo de heróis foi legitimamente expandido para 24 heróis para colmatar papéis táticos.

Esta ADR estabelece uma **política perpétua de anti-involução**, garantindo que a qualidade, as regras canónicas e as funcionalidades progridam sempre de forma acumulativa e auditada.

---

## Decisões Arquiteturais & Invariantes Canónicos

### 1. Princípio da Anti-Involução (Não-Regressão Aditiva)
- **Regra de Ouro**: Nenhuma funcionalidade requerida ou aprovada (como o subsistema de autenticação segura, abas analíticas, puzzles e academia de heróis) pode ser removida em iterações de correção.
- Modificações de código devem focar-se exclusivamente na eliminação de defeitos, na melhoria de ergonomia e na fidelidade das regras, preservando intacto todo o valor construído.

### 2. Conversão Obrigatória de Bugs em Testes Automatizados (Zero Recorrência)
- Todo e qualquer bug reportado ou identificado em ambiente de desenvolvimento, web ou nativo deve ser **imediatamente traduzido num teste automatizado** antes do encerramento da tarefa.
- A suite de testes passa a cobrir tanto a camada nativa/Python quanto a camada web JavaScript (via Node.js headless em `tests/test_web_client_invariants.py`).

### 3. Identidade Canónica: Jogo Abstrato de Tabuleiro (Anti-RPG)
- O RedWar é um jogo de tabuleiro de estratégia abstrata contemporânea.
- **Proibição Estrita de Atributos de RPG**: O estado do tabuleiro não armazena pontos de vida (HP), mana (MP), armadura, ataque numérico ou tabelas de dano.
- **O Tempo/Turno é a Única Métrica**: O combate apoia-se em estados discretos:
  $$\text{Ativo} \xrightarrow{\text{Ataque em Área / Feitiço}} \text{Atordoado (Stun: 2 turnos)} \xrightarrow{\text{Segundo Golpe}} \text{Eliminado}$$
- Ataques diretos em combate próximo eliminam de imediato. Ataques à distância e feitiços aplicam atordoamento para balancear alcance.
- **Invariante dos Dois Golpes**: "Um segundo enquanto atordoado mata" — Qualquer ataque ou feitiço direto/área que atinja uma peça com `stun_timer > 0` elimina-a sumariamente.

### 4. Invariante da Impossibilidade de Fogo Amigo e Auto-captura
- Peças aliadas constituem obstáculos físicos intransponíveis (exceto para heróis com habilidade *fantasma* como `Shadowblade` ou saltadores como `Dragoon`).
- Nenhum movimento ou ataque pode aterrar ou ter como alvo uma casa ocupada por uma peça da mesma cor:
  $$\forall p_1, p_2 \in \text{Peças}, \quad \text{team}(p_1) = \text{team}(p_2) \implies p_2 \notin \text{AlvosLegais}(p_1)$$
- No cliente web, clicar numa peça aliada deve alternar a seleção ativa de forma amigável (semelhante ao Chess.com).

### 5. Invariante de Estrita Alternância de Turnos e Autonomia da IA
- Quando é o turno das Brancas, apenas as Brancas têm ações legais. O utilizador está impedido de manipular peças Pretas.
- Quando o turno muda para as Pretas, o tabuleiro bloqueia para o jogador, a IA Ares assume deterministicamente a decisão, avalia os lances com base na heurística tática do Stockfish, executa o lance e devolve o turno às Brancas.

### 6. Escalabilidade Dinâmica do Catálogo ($\ge 24$ Heróis)
- O marco de 19 peças foi um marco de desenvolvimento preliminar. O RedWar 2.0 suporta 24 heróis com paridade visual completa (512×512 RGBA) e o motor aceita expansões dinâmicas adicionais via configuração declarativa JSON (`heroes_config.json`) e fallback dinâmico `DataPiece`.

---

## Verificação Formal & Camadas de Teste

A integridade do jogo é garantida através de uma pirâmide de verificação em quatro níveis:

```
        ▲
       / \       1. Lean 4 Formal Theorems (specs/RedWarInvariants.lean)
      /---\      2. Python Invariant Suite (tests/test_game_invariants.py)
     /-----\     3. Headless Web Client Suite (tests/test_web_client_invariants.py)
    /-------\    4. Full CI Matrix (1024+ tests: C++ smoke, reversibility, GUI journey)
```

1. **Lean 4 ([`specs/RedWarInvariants.lean`](file:///c:/Users/ASUS/Documents/RedWar/specs/RedWarInvariants.lean))**:
   - Provas matemáticas de involução de turnos (`opponent_involutive`), impossibilidade de alvo aliado (`no_friendly_target`), letalidade de peças atordoadas (`stunned_target_eliminated`) e teto orçamental de 200 pts (`draft_within_budget`).
2. **Suite de Invariantes Python ([`tests/test_game_invariants.py`](file:///c:/Users/ASUS/Documents/RedWar/tests/test_game_invariants.py))**:
   - 12 testes de propriedade verificando ausência de RPG stats, auto-captura zero em 100% dos heróis, letalidade de feitiços e ataques, temporizadores e extensibilidade ilimitada.
3. **Suite Web Headless ([`tests/test_web_client_invariants.py`](file:///c:/Users/ASUS/Documents/RedWar/tests/test_web_client_invariants.py))**:
   - 5 testes automatizados em Node.js simulando o tabuleiro de `deploy/web/app.js` e assegurando que nenhum bug de interface ou auto-captura volte a surgir.
4. **Pipeline de CI GitHub Actions**:
   - Portões de qualidade bloqueantes: `ai-quality-gate`, `codeql-cpp`, `codeql-python`, `windows-blackbox-acceptance` e `tests`.
