# ⚔️ RedWar 2.0 — RoadMap de Evolução e Publicação

> Este documento governa a evolução do RedWar a partir da versão 1.0, organizando as versões intermediárias (1.1, 1.2) e a transição definitiva para o **RedWar 2.0**.

---

## 🗺️ Visão Estratégica

Inspirado no modelo de ecossistema do **Chess.com** e no poder de cálculo do **Stockfish**, o RedWar evoluiu em 3 fases complementares:
1. **RedWar 1.1**: Roster expandido de heróis e PvP resiliente (reconexão em voo, desforras, espectadores ao vivo e reações táteis).
2. **RedWar 1.2**: Publicação gratuita na internet (deploy automático via GitHub Pages + Docker para nuvens gratuitas) e endurecimento de segurança (rate limiting, DoS mitigation, proteção de dados e integridade).
3. **RedWar 2.0**: Modos avançados (Tournament Draft & Riscos Ambientais), Motor Ares 2.0 (History Heuristic + Killer Moves, alocação dinâmica de tempo) e Análise de Partidas no Browser com gráfico de precisão (Game Review).

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

---

## Regra de Governação

Cada versão segue estritamente a metodologia TDD do projeto: testes que falham criados primeiro, implementação até todos passarem localmente e em CI, verificação por Pull Request e merge em `main`.
