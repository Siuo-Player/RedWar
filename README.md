<div align="center">

# ⚔️ RedWar

### *Tactical Grid Warfare. One Engine to Rule Them All.*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5.2-FF6F00?logo=python&logoColor=white)](https://www.pygame.org/)
[![Cython](https://img.shields.io/badge/Cython-3.0+-009688?logo=c&logoColor=white)](https://cython.org/)
[![pytest](https://img.shields.io/badge/pytest-8.0-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![CI — AI Arena](https://img.shields.io/badge/CI-AI%20Arena-FF4444?logo=githubactions&logoColor=white)](.github/workflows/ai_arena.yml)
[![Contributions — ai/ only](https://img.shields.io/badge/PRs%20Welcome-ai%2F%20only-brightgreen)](ai/)

**RedWar** é um jogo de tabuleiro tático em grelha com economia de pontos, eliminação direta e mecânicas profundas — stuns, spawns, terrenos dinâmicos e feitiços (*ignite*, *purify*, *barricade*, *swap*).

**Ares Engine** é o Stockfish do RedWar: um motor de busca Minimax open-source, calibrado por ELO, pronto para ser otimizado pela comunidade global.

</div>

---

## 🎯 Visão & Filosofia

O RedWar assenta numa divisão estrita e intencional:

| Camada | Escopo | Licença / Contribuição |
|--------|--------|------------------------|
| **O Jogo & Multijogador** | UI (Pygame), regras, rede, deploy | **Closed / Owner Source** — desenvolvido e controlado pelo autor |
| **Ares Engine** (`ai/`) | Busca, avaliação, bots, calibração | **Open Source** — PRs da comunidade bem-vindos |

> *Tu não editas o tabuleiro. Tu editas o cérebro que o domina.*

A pasta `ai/` é a **única** zona do repositório aberta a Pull Requests externos. O resto do projeto — motor de jogo, interface gráfica, ferramentas de balanceamento, pipeline DevOps — permanece sob controlo do autor. Isto garante integridade das regras de jogo enquanto permite uma corrida global pela supremacia algorítmica.

---

## 🧠 Ares Engine — O Stockfish do RedWar

Inspirado na arquitetura dos motores de xadrez de elite, o Ares Engine isola a inteligência artificial num núcleo puro, testável e otimizável:

```
ai/
├── bot.py          # Orquestração de bots, presets ELO e dificuldade dinâmica
├── search.py       # Minimax + Alpha-Beta, Move Ordering, TT, Iterative Deepening
├── evaluator.pyx   # Avaliador posicional (Cython — hot path compilado)
└── cpp_engine/     # Motor C++ UCI + interface nativa de busca
```

### Stack Algorítmica

- **Minimax com Alpha-Beta Pruning** — poda agressiva para maximizar profundidade de busca
- **Move Ordering heurístico** — capturas, stuns e ameaças avaliados primeiro
- **Zobrist Hashing + Tabela de Transposição** — cache de posições com limpeza inteligente por profundidade no motor Python; a implementação de TT real em C++ ainda não está presente
- **Iterative Deepening** — profundidade crescente dentro do limite de tempo
- **Killer Moves & Quiescence** — estabilidade tática em posições voláteis
- **Avaliador Cython** (`evaluator.pyx`) — avaliação posicional compilada para NPS elevado
- **Simulação completa de Feitiços** — *ignite*, *purify*, *barricade*, *swap* integrados no `game_state.py` e na árvore de busca

### 🧩 Sistema Declarativo de Passivas

O motor suporta `behavior.passives` em `engine/heroes_config.json`, como documentado em `engine/HEROES_SCHEMA.md`. Este esquema permite definir efeitos automáticos por evento (`on_kill`, `on_attack`, `on_attacked`, `aura_passive`) sem espalhar lógica de herói em código ad hoc. O BoneLord já está migrado para `behavior.passives`; Templar, Berserker, Inquisitor e outros heróis ainda estão planeados para migração.

### Calibração ELO

O sistema de dificuldade não é arbitrário. Mede probabilidade de vitória relativa usando a curva logística FIDE:

$$E_A = \frac{1}{1 + 10^{\frac{R_B - R_A}{400}}}$$

A âncora empírica fixa o **Bot Aleatório em 100 ELO**. Bots superiores são calibrados em cadeia (*Anchored ELO Scaling*), evitando inflação estatística quando um motor de topo enfrenta oponentes fracos.

Presets oficiais da Arena:

| Bot | ELO Aproximado | Perfil |
|-----|----------------|--------|
| `BOT_ALEATORIO` | 100 | Movimentos aleatórios — baseline absoluto |
| `BOT_INICIANTE` | 140 | Entrada tática |
| `BOT_INTERMEDIO` | 200 | Desafiante padrão da Arena |
| `BOT_AVANCADO` | 250 | Campeão atual |
| `BOT_MESTRE` | 300 | Teto calibrado empiricamente |

<!-- TODO: confirmar escala de ELO -->

---

## 🏟️ A Arena — GitHub Actions

A Arena é o coliseu automatizado onde bots da comunidade provam o seu valor. Sem favoritismos. Sem merge manual por simpatia. **Só matemática.**

### Como Funciona

1. **Submetes um PR** que altera exclusivamente ficheiros em `ai/`
2. O workflow [`ai_arena.yml`](.github/workflows/ai_arena.yml) dispara automaticamente
3. Corre um torneio headless de **50 partidas** via `tools/analytics/arena_tournament.py`
4. O **Desafiante** (`BOT_AVANCADO` — a tua versão) enfrenta o **Campeão** (`BOT_INTERMEDIO` — baseline)
5. Cores alternam a cada jogo para eliminar viés de primeira jogada

### Critério de Promoção

```python
def verificar_promocao(vitorias_desafiante, vitorias_atual, margem=5):
    diferenca = vitorias_desafiante - vitorias_atual
    return diferenca >= margem
```

O Desafiante tem de vencer o Campeão por uma **margem mínima de 5 vitórias** em 50 jogos. Só então o código é promovido. Merge automático. Sem desculpas.

```
⚔️ TORNEIO DE ARENA: 50 JOGOS (Margem exigida: 5)
Resultados: Desafiante 28 | Campeão 20 | Empates 2
👑 SUCESSO: O Desafiante superou o Campeão por uma margem >= 5 vitórias!
```

> **Regra de ouro:** Se a tua IA não vence matematicamente, o teu PR não entra. Optimiza o `search.py`, refina o `evaluator.pyx`, ou volta à prancheta.

---

## 🤝 Como Contribuir (Ares Engine)

### ✅ Podes contribuir

- Otimizações de busca (`search.py`)
- Heurísticas de avaliação (`evaluator.pyx`)
- Lógica de bots e presets ELO (`bot.py`)
- Ferramentas de análise dentro de `ai/`

### ❌ Não aceites PRs externos

- `engine/` — regras de jogo, peças, feitiços
- `ui/` — interface gráfica e VFX
- `online/` — multijogador
- `tools/` — laboratório privado (Auto-Pricer, calibração, torneios)
- `deploy/`, `main.py`, configs de build

### Fluxo Recomendado

```bash
# 1. Fork & clone
git clone https://github.com/<teu-user>/RedWar.git
cd RedWar

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Compilar o avaliador Cython (se alteraste evaluator.pyx)
python setup.py build_ext --inplace

# 4. Garantir que os testes passam
pytest tests/

# 5. Testar localmente contra o campeão
python tools/analytics/arena_tournament.py --jogos 50 --margem_vitorias 5

# 6. Abrir PR com alterações exclusivamente em ai/
```

---

## 🏗️ Arquitetura do Projeto

```
RedWar/
├── ai/                 # 🟢 OPEN SOURCE — Ares Engine (comunidade)
│   ├── bot.py
│   ├── search.py
│   ├── evaluator.pyx
│   └── cpp_engine/
│
├── engine/             # 🔒 Motor de jogo — regras, estado, peças
│   ├── game_state.py   #    make/unmake, Zobrist, feitiços, stuns
│   ├── pieces.py       #    Lógica de movimento, ataque, spawn
│   ├── heroes_config.json
│   └── config.py
│
├── ui/                 # 🔒 Interface Pygame — render, VFX, HUD
│   └── renderer.py
│
├── online/             # 🔒 Multijogador (scaffolding)
│   ├── server/
│   ├── client/
│   └── network/
│
├── tools/              # 🔒 Laboratório privado
│   ├── analytics/      #    Arena, calibração ELO, geração de telemetria
│   │   ├── arena_tournament.py
│   │   ├── calibrate_elo.py
│   │   ├── trainer.py
│   │   └── game_analyzer.py
│   ├── balance/        #    Auto-Pricer, color balancer
│   └── scripts/        #    Build pipeline, hooks, utilitários
│
├── tests/              # Testes unitários (pytest)
├── docs/               # Documentação de design e esquemas
├── deploy/             # Packaging (PyInstaller specs)
├── data/               # Telemetria e estatísticas de treino
├── logs/               # Relatórios de build e gridlocks
│
├── main.py             # Entry point — Jogo local vs IA
└── requirements.txt
```

### Separação Motor ↔ UI

O motor (`engine/` + `ai/`) é **completamente headless** — pura matemática. A UI (`ui/`) apenas pergunta: *"Quais os movimentos legais?"* e desenha o resultado. Esta separação permite simulações massivas na Arena sem abrir uma janela gráfica.

---

## 🎮 RedWar — O Jogo

### Mecânicas Core

- **Eliminação Direta (Hit-Kill)** — sem HP. Captura = remoção instantânea.
- **Economia de Draft** — constrói o exército num tabuleiro vazio dentro de um orçamento de pontos.
- **Stun Tático** — atordoamentos bloqueiam turnos; stun num alvo já atordoado = morte instantânea.
- **Terrenos Dinâmicos** — Gelo (bloqueio) e Fogo (stun) alteram o campo de batalha.
- **Feitiços** — *ignite*, *purify*, *barricade*, *swap* com VFX dedicados na UI.

### Quick Start

```bash
pip install -r requirements.txt
python setup.py build_ext --inplace   # Compilar evaluator Cython
python main.py                         # Jogar vs IA localmente
```

### Multijogador (Em Desenvolvimento)

```bash
# Terminal 1 — Servidor
python online/server/app.py

# Terminal 2 — Cliente (Jogador 1)
python online/client/multiplayer_main.py localhost

# Terminal 3 — Cliente (Jogador 2, noutra máquina)
python online/client/multiplayer_main.py <IP_DO_SERVIDOR>
```

### DevOps Local

```bash
pytest tests/                                    # Testes unitários rápidos
python tools/scripts/build_pipeline.py           # Pipeline completo (testes + telemetria + balance)
python tools/analytics/arena_tournament.py       # Simular torneio da Arena localmente
python tools/analytics/game_analyzer.py           # Detetar gridlocks e anomalias
```

---

## 🗺️ Roadmap

### 🔴 Em Curso / Próximo

| Frente | Estado | Descrição |
|--------|--------|-----------|
| **Modelo Matemático de ELO** | 🟡 Pendente | Abandonar limites de tempo como proxy de dificuldade. Implementar **Miopia** (`Depth = max(1, ⌊ELO/400⌋)`) e **Roleta de Blunders** (ruído probabilístico na raiz para ELOs baixos) — modelo Stockfish/Chess.com |
| **Heróis Modulares** | 🟡 Em curso | Migrar `behavior`/`passives` para um sistema data-driven e reduzir cases hardcoded nas unidades |
| **IA completa em C++** | 🟡 Pendente | Integrar todos os ficheiros de `ai/` no motor nativo com otimizações inspiradas em Stockfish |
| **Ajustes de jogo** | 🟡 Se necessário | Ajustes no tabuleiro e nas regras apenas após a estabilidade da IA nativa |
| **Multijogador + packaging** | 🟡 Scaffolding | Cliente/servidor, `main.spec` e deployment final |

### ✅ Concluído Recentemente

- Zobrist hashing no motor Python; a implementação de Tabela de Transposição em C++ ainda está pendente
- Feitiços integrados na IA e na UI (VFX roxos, cliques corretos)
- Pipeline DevOps: pre-push hooks com pytest + simulações pesadas na CI
- Refatoração cirúrgica: separação `ai/` (cérebro) vs `tools/` (laboratório)
- Calibração ELO empírica com escala ancorada e presets oficiais da Arena
- Schema data-driven para heróis (`heroes_config.json` + `HEROES_SCHEMA.md`)

### 🔮 Horizonte

- Arena pública com leaderboard de bots da comunidade
- Integração Auto-Pricer ↔ `heroes_config.json` via CI (`auto_balancer.yml`)
- Documentação de contribution dedicada em `docs/`
- Tabuleiro 10×10 com coordenadas algébricas (A–J / 1–10)

### 💡 Game Design & Modos Alternativos (Em Análise)

| Conceito | Estado | Descrição |
|----------|--------|-----------|
| **Desempate por Material** | 🟡 Em estudo | Se o limite de turnos for atingido, vence quem tiver o maior valor (custo total) de Heróis vivos no tabuleiro. Obriga a "first blood" para quem quiser fazer *stalling*. |
| **Terrenos Especiais** | 🟡 Em estudo | Evolução do sistema de efeitos: casas que conferem `+1 Alcance` permanente, ou casas que convertem habilidades de *Stun* em *Ataque/AoE*. |
| **Modo Battle Royale** | 🔵 Planeado | Variante onde as bordas do tabuleiro começam a arder após X turnos, encolhendo a arena e forçando os exércitos para o centro (anula totalmente táticas de fuga). |

---

## 📐 Referência Rápida — Fórmulas ELO

**Probabilidade esperada de vitória:**

$$E_A = \frac{1}{1 + 10^{\frac{R_B - R_A}{400}}}$$

**Extração de ELO a partir de win-rate empírico:**

$$R_A = R_B - 400 \cdot \log_{10}\left(\frac{1 - W}{W}\right)$$

**Modelo de dificuldade planeado (Stockfish-style):**

$$Depth_{limit} = \max\left(1,\ \left\lfloor \frac{ELO}{400} \right\rfloor \right)$$

---

<div align="center">

### ⚔️ *Build the brain. Enter the Arena. dethrone the champion.*

**RedWar** — tactical warfare on a grid.
**Ares Engine** — open-source intelligence, closed-source battlefield.

</div>
