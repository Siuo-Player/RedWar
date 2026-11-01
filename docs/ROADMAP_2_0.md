# ⚔️ RedWar 2.0 — RoadMap de Evolução e Publicação

> Este documento governa a evolução do RedWar a partir da versão 1.0, organizando as versões intermediárias (1.1, 1.2) e a transição definitiva para o **RedWar 2.0**.

---

## 🗺️ Visão Estratégica

Inspirado no modelo de ecossistema do **Chess.com** e no poder de cálculo do **Stockfish**, o RedWar evolui em 3 fases complementares:
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

- [ ] **Publicação Frontend no GitHub Pages (`.github/workflows/deploy_web.yml`)**:
  - Deploy automatizado e 100% gratuito do cliente web em `https://<user>.github.io/RedWar/`.
- [ ] **Containerização Docker (`Dockerfile`, `docker-compose.yml`)**:
  - Imagem Docker leve e multi-stage para servidor WebSocket e API REST.
  - Compatibilidade com plataformas de nuvem gratuitas (Render.com, Fly.io, HuggingFace Spaces).
- [ ] **Endurecimento de Segurança e Proteção DoS (`online/server/security.py`, `SECURITY.md`)**:
  - Rate limiting por Token Bucket (máximo de 30 mensagens/segundo por conexão).
  - Limite estrito de 64 KB por payload WebSocket para prevenir exaustão de memória.
  - Verificação de CORS e headers HTTP defensivos (CSP, X-Content-Type-Options, X-Frame-Options).
  - Validação estrita de esquemas JSON e máscara de erros internos.

---

## 📌 Fase 3: RedWar 2.0 — Plataforma Competitiva de Última Geração

### Milestone 2.1: Modos Táticos Avançados
- [ ] **Tournament Snake Draft Mode**:
  - Seleção alternada (1-2-2-1) a partir de um pool partilhado gerado aleatoriamente, estimulando contra-escolhas estratégicas.
- [ ] **Hazard Arena (Terrenos Dinâmicos)**:
  - Fissuras de lava e barreiras mágicas geradas proceduralmente para enriquecer a navegação no tabuleiro.

### Milestone 2.2: Ares AI Engine 2.0
- [ ] **History Heuristic & 2-Slot Killer Move Ordering**:
  - Tabela de histórico de lances calmos que geraram cortes beta na pesquisa alpha-beta, acelerando a poda em 15–25%.
- [ ] **Gestão Dinâmica de Relógio**:
  - Ajuste dinâmico do orçamento de nós em função da complexidade tática da posição e do tempo restante no relógio.

### Milestone 2.3: Análise de Partida Interativa (Game Review)
- [ ] **Gráfico de Probabilidade de Vitória e Centipawns**:
  - Renderização no browser da barra de avaliação ao longo dos turnos da partida.
- [ ] **Classificação Qualitativa de Lances**:
  - Classificação no cliente Web de cada jogada: Brilhante, Melhor Lance, Excelente, Imprecisão, Erro e Gaffe.

---

## Regra de Governação

Cada versão segue estritamente a metodologia TDD do projeto: testes que falham criados primeiro, implementação até todos passarem localmente e em CI, verificação por Pull Request e merge em `main`.
