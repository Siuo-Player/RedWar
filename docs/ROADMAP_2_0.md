# ⚔️ RedWar 2.0 — RoadMap de Evolução e Publicação

> Este documento governa a evolução do RedWar a partir da versão 1.0, organizando as versões intermediárias (1.1, 1.2) e a transição definitiva para o **RedWar 2.0**.

---

## 🗺️ Visão Estratégica

Inspirado no modelo de ecossistema do **Chess.com** e no poder de cálculo do **Stockfish**, o RedWar evoluiu em fases complementares com rigor de engenharia:
1. **RedWar 1.1**: Roster expandido de heróis e PvP resiliente (reconexão em voo, desforras, espectadores ao vivo e reações táteis).
2. **RedWar 1.2**: Publicação gratuita na internet (deploy automático via GitHub Pages + Docker para nuvens gratuitas) e endurecimento de segurança (rate limiting, DoS mitigation, proteção de dados e integridade).
3. **RedWar 2.0**: Modos avançados (Tournament Draft & Riscos Ambientais), Motor Ares 2.0 (History Heuristic + Killer Moves, alocação dinâmica de tempo), Análise de Partidas no Browser com gráfico de precisão (Game Review), Academia de Heróis com tutoriais interativos, perfis especializados de IA por modo e framework estatístico **SPRT** (Sequential Probability Ratio Test) para garantir que apenas melhorias matematicamente comprovadas entram no motor.

---

## 📌 Fase 1: RedWar 1.1 — Expansão de Heróis e PvP Resiliente

- [x] **Expansão do Roster de Heróis (`engine/heroes_config.json`, `engine/pieces.py`)**:
  - `Paladin` (custo 55): Linha de frente resistente com avanço ortogonal até 2 casas.
  - `Shadowblade` (custo 65): Flanqueador diagonal com mobilidade fantasma (atravessa peças aliadas e inimigas) até 3 casas.
  - `Stormcaller` (custo 72): Atacante elétrico de raio direto com feitiço `chain_lightning`.
- [x] **Protocolo de Reconexão em Voo (`online/server/room.py`, `online/server/app.py`)**:
  - Geração de tokens de reconexão criptográficos (`reconnect_token`).
  - Reconexão sem reinicialização do relógio ou estado da partida.
- [x] **Desforra Bilateral (Rematch)**:
  - Proposta e aceitação de nova partida com inversão automática de lados (Brancas ⇄ Pretas).
- [x] **Espectadores e Emotes Táticos**:
  - Contagem ao vivo de espectadores transmitida em tempo real.
  - Reações rápidas de respeito e desportivismo (`gg`, `well_played`, `thinking`, `wow`).
- [x] **Síntese de Áudio no Browser (`deploy/web/app.js`)**:
  - Sons sintetizados via Web Audio API para movimentos, atordoamentos e vitória (zero dependência de ficheiros externos).

---

## 📌 Fase 2: RedWar 1.2 — Publicação Gratuita e Segurança

- [x] **Publicação Frontend no GitHub Pages (`.github/workflows/deploy_web.yml`)**:
  - Deploy automatizado e 100% gratuito do cliente web em `https://<user>.github.io/RedWar/`.
- [x] **Containerização Docker (`Dockerfile`, `docker-compose.yml`)**:
  - Imagem Docker leve e multi-stage para servidor WebSocket e API REST.
  - Compatibilidade com plataformas de nuvem gratuitas (Render.com, Fly.io, HuggingFace Spaces).
- [x] **Endurecimento de Segurança e Proteção DoS (`online/server/security.py`, `SECURITY.md`)**:
  - Rate limiting por Token Bucket (máximo de 30 mensagens/segundo por conexão).
  - Limite estrito de 64 KB por payload WebSocket para prevenir exaustão de memória.
  - Verificação de CORS e headers HTTP defensivos (CSP, X-Content-Type-Options, X-Frame-Options).
  - Validação estrita de esquemas JSON e máscara de erros internos.

---

## 📌 Fase 3: RedWar 2.0 — Plataforma Competitiva de Última Geração

### Milestone 2.1: Modos Táticos Avançados
- [x] **Tournament Snake Draft Mode (`engine/draft_tournament.py`, `tests/test_snake_draft.py`)**:
  - Seleção alternada (1-2-2-1) com banimento inicial a partir de um pool partilhado gerado aleatoriamente, estimulando contra-escolhas estratégicas.
- [x] **Hazard Arena — Terrenos Dinâmicos (`engine/hazards.py`, `tests/test_hazard_arena.py`)**:
  - Terrenos dinâmicos (`Lava`, `MagicBarrier`, `HealingSpring`) gerados de forma procedural e simétrica, com interações táticas como incineração e purificação de atordoamento.

### Milestone 2.2: Ares AI Engine 2.0
- [x] **History Heuristic & 2-Slot Killer Move Ordering (`ai/ares2.py`, `tests/test_ares2_engine.py`)**:
  - Tabela de histórico de lances calmos com pontuação quadrática por profundidade ($depth^2$) e tabela de dois slots de killer moves por ply, reduzindo a árvore de busca e antecipando podas $\beta$.
- [x] **Gestão Dinâmica de Relógio (`DynamicTimeManager` em `ai/ares2.py`)**:
  - Ajuste dinâmico de tempo e nós em função da complexidade tática, heróis ativos e tempo remanescente no relógio.

### Milestone 2.3: Análise de Partida Interativa (Game Review)
- [x] **Gráfico de Probabilidade de Vitória e Centipawns (`engine/review.py`, `deploy/web/app.js`, `deploy/web/index.html`)**:
  - Renderização no browser da curva de vantagem em centipawns ao longo dos turnos e cálculo de precisão global de cada jogador via modelo de decaimento exponencial.
- [x] **Classificação Qualitativa de Lances (`MoveClassification` em `engine/review.py`)**:
  - Classificação formal de cada jogada: Brilhante, Melhor Lance, Excelente, Bom, Imprecisão, Erro e Gaffe (Blunder).

### Milestone 2.4: Metodologia de IA Stockfish (SPRT & Perfis por Modo)
- [x] **Framework Estatístico SPRT (`ai/sprt.py`, `.github/workflows/ares_sprt.yml`)**:
  - Teste sequencial de razão de verosimilhança (Wald's SPRT) com LLR, estimativa de Elo e margens de erro de 95% de confiança, garantindo que novas versões de motor provem superioridade antes de promoção.
- [x] **Perfis de IA Especializados por Modo (`ai/profiles.py`)**:
  - `StandardAresProfile`, `GrandAresProfile`, `DraftAresProfile` e `HazardAresProfile`, cada qual com pesos de avaliação, sinergias e parâmetros de busca dedicados.

### Milestone 2.5: Academia de Heróis e Documentação Wiki

- [x] **Academia de Heróis completa — 30/30 (#677 / PR #678, integrada)**:
  - A configuração contém 30 definições: 27 heróis draftáveis e três unidades não draftáveis (Bone, Ghoul e StoneWall), todas com uma lição contextualizada e identificada.
  - Catálogo JSON versionado e partilhado por Python e Web; ambos os consumidores carregam a mesma fonte.
  - As soluções incluem o tipo de ação e metadados de feitiço/invocação, e são verificadas contra `legal_actions` do motor canónico.
  - O selector Web é gerado a partir das 30 entradas e assinala unidades não draftáveis. Foram acrescentados testes de contrato, legalidade, integração e interação real Playwright.
  - Integrada em `main` no commit `fe1d69a934919d8617dde663f29db46070ee558d`. CI: 1236 passed / 4 skipped; CPU-intensive: 4 passed; CodeQL Python/C++, Windows acceptance e AI Quality Gate passaram.
  - Follow-up #679 / PR #680 concluído: `max_steps=3` aplicado ao movimento `adjacent` em Python e C++, com browser, oráculo e Academia sincronizados.
- [x] **Documentação Wiki Oficial do GitHub (`wiki/`, `.github/workflows/deploy_wiki.yml`)**:
  - Estrutura da Wiki com seis secções (Home, Regras, Heróis, Ares/SPRT, Modos e Publicação) sincronizada com o repositório GitHub Wiki.

---

## Próximas frentes RedWar 2.0

A ordem abaixo explicita dependências e bloqueios; não transforma propostas em trabalho concluído.

A Academia 30/30 está concluída e integrada. As próximas frentes permanecem separadas, com estes pré-requisitos:

1. **FrostMage vs Inquisitor — #444 (bloqueada por evidência).** Retomar apenas com o replay/RWEN da partida original e a sequência integral de ações. Depois reproduzir deterministicamente e investigar com busca adversarial; profundidade mínima 8 é uma ferramenta de análise, não prova por si só de empate forçado.
2. **Interação Web — #681.** Auditoria inicial confirma interação do tabuleiro por clique no Canvas; não foi encontrada implementação de drag-and-drop nem política `prefers-reduced-motion` no CSS. A issue #681 governa a validação e implementação incremental, começando por testes Playwright e preservando ações autoritativas.
3. **Matchmaking.** Tratar como trabalho de produto/infraestrutura separado: critérios de emparelhamento, rating, filas, abandono, reconexão e proteção contra abuso, sem confundir matchmaking com a existência atual de salas WebSocket.
4. **Ares C++/WASM.** Criar uma fronteira de compilação e contrato de compatibilidade entre o motor C++ e o browser, com testes diferenciais Python/C++ e medições antes de substituir o caminho existente.

**Follow-up técnico descoberto pela Academia — #679 / PR #680 (CONCLUÍDO):** `max_steps=3` foi restaurado no movimento `adjacent` da Valkyrie em Python e C++, sincronizando browser, oráculo independente e lição da Academia. Integrado em `main` no commit `32fdb3ebfdd0094e7ca9b91be95117db0dd3bb5d`; validação: 1245 testes passaram, 4 ignorados; suite CPU-intensiva 4/4; CodeQL Python/C++, Windows acceptance e AI Quality Gate passaram.

## Registo de estado

- A cadeia 1.0 (#370–#375) está fechada no GitHub.
- A Academia 30/30 está concluída e integrada em #677 / PR #678 (commit `fe1d69a`).
- #444 continua bloqueada pela falta do replay original; não inferir resultados a partir de fixtures sintéticas.
- #679 / PR #680 está concluída e integrada; o contrato de movimento adjacente respeita agora `max_steps` nos dois motores.

## Regra de Governação

Cada versão segue estritamente a metodologia TDD do projeto: testes que falham criados primeiro, implementação até todos passarem localmente e em CI, verificação por Pull Request e merge em `main`.
