# RedWar — Roadmap Operacional

## Gate chain 1.0 Full — CONCLUÍDA

Os seis gates da cadeia 1.0 estão **fechados no GitHub**. O roadmap não deve reabrir gates por existirem tarefas de evolução posteriores.

```text
#370 Foundation (CLOSED)
      ↓
#371 Gameplay (CLOSED)
      ↓
#372 Ares Competitive Track (CLOSED)
      ↓
#373 Product Full & Game Modes (CLOSED)
      ↓
#374 Online Multiplayer & Web (CLOSED)
      ↓
#375 Release Full (CLOSED)
```

O trabalho posterior é evolução RedWar 2.0 ou follow-up especializado, e deve ter issues próprias. Em particular, a issue #318 continua aberta para objetivos especializados de análise de heróis; não altera o estado fechado dos gates 1.0.

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
- **#372 Ares Competitive Track — CLOSED.** Gate 1.0 encerrado; as melhorias posteriores do motor são acompanhadas como trabalho de evolução separado, com validação empírica própria.
- **#373 Product Full & Múltiplos Modos — CLOSED.** Gate 1.0 encerrado; modos, puzzles e funcionalidades de produto aceites nesse âmbito.
- **#374 Online Multiplayer & Web — CLOSED.** Gate 1.0 encerrado; servidor autoritativo, salas, relógios, API e cliente Web integrados.
- **#375 Release Full — CLOSED.** Gate 1.0 encerrado; lançamento multiplataforma e auditoria de licenças concluídos.

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

## #374 — Online Multiplayer & Plataforma Web (IMPLEMENTADO EM PR #622 & #374)

**Objetivo Central:** Construir a infraestrutura online que suportará partidas em tempo real, rankings competitivos e a versão Web no mesmo ecossistema.

### 1. Servidor Autoritativo WebSocket e Gestão de Salas (`online/server/`)
- [x] **Salas Autoritativas (`online/server/room.py`):** Gestão isolada de partidas (`GameRoom`, `RoomManager`) com modos configuráveis (Standard 8×8, Grand 10×10) e controlos de tempo (Bullet, Blitz, Rápido).
- [x] **Relógios de Partida Sincronizados:** Gestão formal de tempo (`GameClock`) com contagem decrescente no turno ativo, adição de incrementos por lance e derrota automática por queda de bandeira (`flag_fall`).
- [x] **Integração de ELO em Partidas Concluídas:** Atualização automática de ratings e estatísticas de vitória/derrota no `LeaderboardManager` em partidas pontuadas (rated).
- [x] **Modo Espetador:** Jogadores adicionais além de Brancas e Pretas são admitidos na sala como espetadores e recebem todos os broadcasts de estado sem interferir nas jogadas.
- [x] **Protocolo WebSocket com Salas (`online/server/app.py`, `online/network/client.py`):** Suporte tanto a pedidos de sala (`join_room`, `acao`, `resign`, `pronto`) como compatibilidade total com clientes e testes legados.

### 2. Plataforma Web e REST API (`online/server/web_app.py`, `deploy/web/`)
- [x] **REST Web API:** Endpoints `/api/leaderboard`, `/api/bot_tiers`, `/api/puzzles`, `/api/rooms` e `/api/game_modes`.
- [x] **Cliente Web HTML5/Canvas (`deploy/web/`):** Interface web inspirada no Chess.com com tabuleiro interativo, auras de stun, relógios digitais, alternador de abas (Jogar, Puzzles, Leaderboard) e integração online.
- [x] **HUD de Relógios no Pygame (`online/client/multiplayer_main.py`):** Renderização visual dos relógios digitais com destaque luminoso na equipa ativa.

---

## #375 — Release Full (CONCLUÍDO)

- [x] **Unificação das Plataformas Desktop e Web (`launcher.py`, `run_redwar.bat`):** Launcher oficial multiplataforma que unifica a execução do cliente Desktop Pygame, da aplicação Web HTML5 Canvas/REST API (`deploy/web/`), do cliente multijogador em rede e da Arena diagnóstica.
- [x] **Auditoria e Formalização de Licenças (`docs/LEGAL_AND_LICENSES.md`, `docs/THIRD_PARTY_LICENSES.md`, `tests/test_licensing_audit.py`):** Auditoria rigorosa de proveniência de assets PNG (`game_icons_manifest.json` com CC BY 3.0), preservação integral das licenças de terceiros (MIT, GPL-3.0, LGPL-2.1, BSD-3-Clause, Apache-2.0) e certificação do cliente web sem dependências externas opacas.
- [x] **Lançamento do Ecossistema Competitivo:** Sistema de ELO por modo de jogo, bot tiers calibrados estilo Stockfish (Apprentice a Grandmaster), banco de puzzles táticos interativo e suporte autoritativo para partidas públicas e salas privadas com relógios sincronizados.

---

## Estado de conclusão e evolução

A cadeia operacional **RedWar 1.0 Full (#370–#375) está concluída**: todos os seis gates estão fechados no GitHub. Isto não significa que o produto deixou de ter trabalho futuro.

A evolução **RedWar 2.0 continua em curso** e é governada por `docs/ROADMAP_2_0.md` e pelas issues específicas.

**Academia de Heróis 30/30 — concluída e integrada.** A auditoria inicial encontrou 30 definições em `engine/heroes_config.json` (27 draftáveis e três não draftáveis), mas apenas 12 lições Web e seis Python. A PR [#678](https://github.com/Siuo-Player/RedWar/pull/678), associada à issue [#677](https://github.com/Siuo-Player/RedWar/issues/677), introduziu o catálogo JSON partilhado, migrou os dois consumidores, validou todas as soluções no espaço canónico de ações e gerou o selector Web a partir das 30 entradas. Foi integrada em `main` pelo commit `fe1d69a934919d8617dde663f29db46070ee558d`. Evidência CI no head integrado antes do merge: **1236 testes passaram, 4 foram ignorados; suite CPU-intensiva: 4 passaram; CodeQL Python/C++: sucesso; Windows black-box acceptance: sucesso; AI Quality Gate: sucesso.**

A auditoria detetou ainda uma discrepância independente na configuração/motor da Valkyrie (`max_steps=3` configurado, mas vetores adjacentes limitados a uma casa pelo compilador). Esta correção mecânica está isolada na issue [#679](https://github.com/Siuo-Player/RedWar/issues/679); a PR #678 não alterou regras de combate e descreve o comportamento atualmente aceite pelo motor.

A issue [#444](https://github.com/Siuo-Player/RedWar/issues/444) permanece aberta: a reprodução da partida original ainda depende do replay/RWEN e da sequência completa de ações. Fixtures sintéticas não substituem essa evidência.

Não usar “100% concluído” para descrever o produto global. O estado correto é: **gates 1.0 fechados; evolução 2.0 em progresso**.

---

## Regra Documental

Este é o único roadmap operacional do projeto. Estado transitório, SHAs, resultados de CI e notas de handoff pertencem ao Git/Issues/CI. Decisões duráveis de arquitetura pertencem a `docs/DECISIONS/`.
