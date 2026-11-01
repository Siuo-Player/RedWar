# RedWar — Roadmap Operacional

## Gate chain 1.0 Full

```text
#370 Foundation (CLOSED)
      ↓
#371 Gameplay (CLOSED)
      ↓
#372 Ares Competitive Track (OPEN - Foco Stockfish-like AI & Avaliação de Balanceamento)
      ↓
#373 Product Full & Game Modes (OPEN - Modos balanceados, Leaderboards e Puzzles)
      ↓
#374 Online Multiplayer & Web (OPEN - Chess.com model: WebSocket, ELO, Web app)
      ↓
#375 Release Full
```

## 1.0-Lite path (CONCLUÍDO)

RedWar completou com sucesso a primeira versão **local 1.0-Lite**, que estabelece um produto desktop jogável, regras canónicas estáveis e um baseline congelado para a IA Ares.

```text
#370 Foundation — CLOSED
      ↓
#371 Gameplay — CLOSED
      ↓
#526 1.0-Lite / Ares Balance Baseline — CLOSED
      ↓
#557 Local 2P / Hot-seat — CLOSED
      ↓
#558 Settings & Audio — CLOSED
      ↓
#555 Windows Acceptance & E2E — CLOSED (PR #587)
```

---

## Estado Geral dos Gates

- **#370 Foundation — CLOSED.** Contratos base, normalização de ações e fronteira de execução fechados.
- **#371 Gameplay — CLOSED.** Ruleset jogável fechado (stun, morte, turnos sem captura, efeitos de fogo/gelo).
- **#526 1.0-Lite — CLOSED.** Baseline local e produto desktop com aceitação real no Windows.
- **#372 Ares Competitive Track — EM PROGRESSO (FOCO ATUAL).** Evolução competitiva contínua inspirada no **Stockfish** (busca alfa-beta otimizada, LMR, ordenação de lances, quiescence, TT e NNUE) servindo também como oráculo para o Balance Lab.
- **#373 Product Full & Múltiplos Modos — EM DESENVOLVIMENTO PARALELO.** Implementação de múltiplos modos balanceados (8×8, 10×10, controlos de tempo Bullet/Blitz/Rápido, puzzles táticos e variantes de draft) e leaderboards.
- **#374 Online Multiplayer & Web — EM PREPARAÇÃO.** Transição para o modelo **Chess.com**: servidor WebSocket autoritativo, matchmaking baseado em ELO/Glicko-2, relógios sincronizados e cliente Web.
- **#375 Release Full — PLANEADO.** Lançamento multiplataforma unificado (Desktop + Web).

---

## #372 — Ares Competitive Track (Stockfish-like AI Core)

**Objetivo Central:** Tornar o Ares o motor definitivo de RedWar, aplicando as técnicas consolidadas do Stockfish adaptadas à mecânica de combate por stun/morte e utilizando a sua força de cálculo para auditar e balancear o jogo de forma contínua.

### 1. Algoritmos de Busca Avançada (Stockfish-like) - IMPLEMENTADO EM PR #622
- **Late Move Reductions (LMR):** [x] Redução seletiva de profundidade em lances calmos (quiet moves) para `depth >= 4` e `move_count >= 6`, preservando lances táticos (ataques de stun, ataques letais de segundo stun, feitiços ofensivos diretos).
- **Move Ordering Aperfeiçoado:** [x]
  1. *PV Move / Hash Move* proveniente da Transposition Table (TT) com score 1.000.000.
  2. *Lethal Captures:* Segundo stun letal ordenado por valor da peça capturada (MVV-LVA: score 100.000 + victim*100 - attacker).
  3. *Tactical Stuns:* Primeiro stun em alvos de alto custo (score 50.000 + victim*50 - attacker).
  4. *Spells Ofensivas:* Feitiços de área (`ignite`, `nevada`, `aimed_shot`) com bónus de alvo central direto (+20 pts).
  5. *Killer Moves:* Heurística de dois lances assassinos por nível de profundidade ply (scores 10.000 e 5.000).
  6. *History Heuristic:* Tabela de histórico por equipa e por tipo de ação (score até 2.000).
  7. *Lances Calmos restantes.*
- **Quiescence Search (Busca de Tranquilidade):** [x] Extensão tática para resolver trocas pendentes e ameaças iminentes de morte antes de avaliar folhas estáticas, eliminando o efeito horizonte.
- **Transposition Table (TT) Otimizada:** [x] Hashing Zobrist dinâmico incluindo timers de stun, cooldowns e terreno com observabilidade de warmup/reutilização comprovada em testes nativos.

### 2. Avaliação e NNUE
- **Avaliação Clássica Heurística:** Calibração contínua de mobilidade de heróis, controlo das casas centrais, linhas de visão, suporte defensivo mútuo e evasão de perigos de terreno (fogo).
- **NNUE (Efficiently Updatable Neural Network):** Manutenção do caminho incremental validado; promoção para avaliação padrão apenas quando demonstrar ganho de força comprovado por CPU-segundo na Arena.

### 3. Validação por Arena Automatizada
- Validação empírica rigorosa com emparelhamento de sementes e alternância de cores (evitando viés de primeiro jogador).
- Adoção de métricas descritivas invariantes à ordem (modelo pentanomial de pares de jogos) para promoção de código sensível à força.

---

## #373 — Product Full, Múltiplos Modos & Balance Lab

**Objetivo Central:** Garantir que RedWar oferece uma experiência rica com múltiplos modos de jogo equilibrados, apoiando-se no motor Ares como oráculo analítico de balanceamento.

### 1. Pipeline de Balanceamento Orientado por IA (Balance Lab)
- **Ares como Oráculo Analítico:** Simulação de milhares de partidas self-play e confrontos de composições para alimentar matrizes de desempenho herói × posição × composição × adversário.
- **Calibração de Custos de Draft:**
  - Ajuste iterativo e progressivo em números inteiros (coarse-to-fine) no orçamento de draft (200 pts padrão).
  - Prevenção de "metas" estagnados: heróis hiperdominantes têm o custo aumentado; heróis pouco viáveis têm o custo reduzido.
- **Balanceamento de Regras e Mecânicas:**
  - Compensação empírica de iniciativa (primeiro jogador / Brancas vs Pretas).
  - Calibração de durações de terreno (fogo e gelo), alcance de feitiços e cooldowns.

### 2. Múltiplos Modos de Jogo Balanceados (Chess.com-like) - IMPLEMENTADO EM PR #622
1. **Modo Clássico 8×8 (Padrão):** [x] Orçamento de 200 pontos, regras normais, 50 turnos de TWC (`GameMode.standard_8x8()`).
2. **Modo Grand RedWar 10×10:** [x] Tabuleiro 10×10 expandido para manobras de flanco e maior profundidade tática; orçamento de 300 pontos, 60 turnos de TWC, hash Zobrist e clonagem dinâmica (`GameMode.grand_10x10()`).
3. **Modos com Controlo de Tempo:** [x]
   - **Bullet:** 1 min + 0s por lance (`TimeControl.bullet_1_0()`).
   - **Blitz:** 3 min + 2s ou 5 min + 0s (`TimeControl.blitz_3_2()`, `TimeControl.blitz_5_0()`).
   - **Rápido:** 10 min + 0s ou 15 min + 10s (`TimeControl.rapid_10_0()`, `TimeControl.rapid_15_10()`).
   - **Relógio de Partida Autorizado:** `GameClock` com decremento por lance, incremento e deteção de bandeira caída.
4. **Modo Puzzles & Táticas:** [x] Runner de problemas táticos (`TacticalPuzzle`, `PuzzleRunner`, `PUZZLE_BANK`) para treino e avaliação de soluções jogada a jogada.
5. **Bot Difficulty Tiers & ELO Calibrado:** [x]
   - *Ares Apprentice:* ELO 800, profundidade 2, taxa de erro/inaccuracy de 25%.
   - *Ares Intermediate:* ELO 1400, profundidade 4, taxa de erro de 8%.
   - *Ares Advanced:* ELO 1900, profundidade 6, taxa de erro de 1%.
   - *Ares Master:* ELO 2500+, sem ruído intencional, busca máxima.
6. **Sistema de Classificação e Leaderboard:** [x]
   - Cálculo de Elo FIDE/Glicko adaptativo (K=40 provisório, K=20 padrão, K=10 mestre).
   - Histórico e ranking por modo de jogo com persistência em JSON (`LeaderboardManager`, `PlayerRatingProfile`).
5. **Variantes de Draft:**
   - *Draft Espelho (Mirror Draft):* Ambos os jogadores partilham a mesma composição de heróis.
   - *Draft às Cegas (Blind Draft):* Escolhas em tempo real sem conhecimento antecipado da equipa inimiga.

### 3. Bots com Níveis de Dificuldade Calibrados
- Roster de Bots com personalidades e ratings simulados:
  - *Bot Iniciante (ELO ~800):* Profundidade 1-2, ruído de busca introduzido intencionalmente.
  - *Bot Intermédio (ELO ~1400):* Profundidade 3-4, busca tática básica.
  - *Bot Avançado (ELO ~1900):* Profundidade 5-6 com TT e avaliação clássica completa.
  - *Bot Mestre Ares (ELO ~2500+):* Full nodes, avaliação NNUE e busca máxima.

---

## #374 — Online Multiplayer & Plataforma Web

**Objetivo Central:** Construir a infraestrutura online que suportará partidas em tempo real, rankings competitivos e a versão Web no mesmo ecossistema.

### 1. Servidor Autoritativo WebSocket (`online/server/`)
- Servidor autoritativo que valida cada ação legal antes de mutar o estado, impossibilitando batota via cliente.
- Gestão de sessões, salas privadas com código e fila de matchmaking automático baseado em ELO/MMR por modo de jogo.
- Gestão formal de relógios de jogo (tempo por turno e relógio global) com derrota por timeout e tolerância a reconexões breves.

### 2. Plataforma Web e Aplicação Unificada
- Transição/portabilidade para versão Web jogável diretamente no browser.
- Perfis de jogador: registo de partidas, histórico de ELO, gráficos de precisão e estatísticas de utilização de heróis.
- Modo Espetador ao vivo e análise pós-jogo interativa no browser com o Ares WebAssembly/servidor.

---

## #375 — Release Full

- Unificação das plataformas Desktop e Web.
- Auditoria e substituição/formalização de licenças de assets gráficos e sonoros (incluindo game-icons.net).
- Lançamento público da temporada competitiva com rankings e temporadas de balanceamento periódicas.

---

## Regra Documental

Este é o único roadmap operacional do projeto. Estado transitório, SHAs, resultados de CI e notas de handoff pertencem ao Git/Issues/CI. Decisões duráveis de arquitetura pertencem a `docs/DECISIONS/`.
