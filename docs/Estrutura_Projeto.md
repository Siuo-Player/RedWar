# Estrutura e Arquitetura do Projeto RedWar

Este documento descreve a **estrutura atual** e a arquitetura pretendida. Não é uma proposta genérica de como organizar um jogo: caminhos apresentados aqui devem corresponder à árvore real do repositório ou ser explicitamente marcados como alvo futuro.

## 1. Divisão conceptual

O projeto tem quatro grandes zonas:

```text
RedWar/
├── engine/       # estado e regras do jogo
├── ai/           # Ares e ferramentas diretamente ligadas à IA
├── ui/           # aplicação visual atual
├── online/       # infraestrutura de multiplayer em desenvolvimento
├── tools/        # analytics, balanceamento, Arena e tooling
├── tests/        # testes
├── docs/         # documentação
├── deploy/       # packaging
├── data/         # dados gerados/estatísticas
└── main.py       # entrada da aplicação local
```

A separação atual ainda não é perfeita. O objetivo é tornar `engine/` a definição autoritativa das regras e `ai/` uma camada de inteligência que consome esse jogo sem redefinir as suas regras por conta própria.

## 2. `engine/`

É a camada que deve responder à pergunta:

> **“O que é uma posição legal de RedWar e o que acontece quando uma ação é executada?”**

Responsabilidades principais:

- `game_state.py` — estado do tabuleiro e transições de estado;
- `pieces.py` — definição e comportamento dos heróis;
- `heroes_config.json` — dados dos heróis;
- `action_parser.py` — interpretação/validação de ações;
- `config.py` — constantes do jogo;
- `HEROES_SCHEMA.md` — formato da configuração de heróis.

Esta camada não deve depender de UI para saber se uma jogada é legal.

## 3. `ai/`

Contém o **Ares**, que deve idealmente tornar-se uma engine de IA independente da apresentação do jogo.

```text
ai/
├── bot.py
├── search.py
├── evaluator.pyx
└── cpp_engine/
    ├── types.hpp
    ├── board.cpp
    ├── movegen.cpp
    ├── evaluate.cpp
    ├── search.cpp
    ├── main.cpp
    └── SmokeTest.cpp
```

A implementação Python/Cython ainda existe durante a migração. O objetivo é que o caminho de pesquisa quente migre para uma implementação mais rápida, atualmente C++.

A longo prazo, Python deve permanecer principalmente como camada de integração, ferramentas e testes quando o C++ for a melhor opção para a pesquisa.

## 4. `ui/`

É a aplicação visual atual.

A UI deve:

- apresentar o estado do jogo;
- receber input do jogador;
- pedir ao core as ações legais;
- mostrar animações/VFX;
- reproduzir som;
- permitir menus, análise e histórico.

A UI não deve reimplementar as regras do jogo para “decidir” se uma ação é válida.

## 5. `online/`

Contém o trabalho em progresso relacionado com multiplayer.

Estrutura atual:

```text
online/
├── client/
├── network/
└── server/
```

A arquitetura final ainda não está escolhida. O objetivo é criar partidas 1v1 com servidor capaz de validar ações, matchmaking, tempos, reconexão e ranking.

## 6. `tools/`

Ferramentas para:

- Arena;
- análise de partidas;
- calibração de ELO;
- treino/self-play;
- auto-pricer/balanceamento;
- build e CI local.

As ferramentas não devem ser confundidas com a definição das regras do jogo.

## 7. `tests/`

Os testes devem verificar principalmente:

- validade de ações;
- transições do estado;
- efeitos e timers;
- hashing;
- equivalência incremental/recomputada;
- comportamento dos heróis;
- equivalência Python/C++ durante a migração;
- casos extremos e regressões.

## 8. `docs/`

A documentação está dividida por público:

```text
README.md
  → visão geral

GAME_RULES.md
  → jogador/desenvolvedor que precisa saber as regras atuais

GAME_DESIGN.md
  → filosofia e decisões de design

ARCHITECTURE.md
  → implementação e fronteiras entre módulos

AI_ENGINE.md
  → Ares, search, avaliação e Arena

HERO_SYSTEM.md
  → sistema de heróis e configuração

WEB_MULTIPLAYER.md
  → aplicação, web, contas e multiplayer

CONTRIBUTING.md
  → política de contribuições

ROADMAP.md
  → estado atual e trabalho futuro
```

## 9. Regra de modularidade

O projeto pretende evitar ficheiros gigantes.

Como regra prática:

> ficheiros acima de aproximadamente 1000 linhas devem ser considerados candidatos a divisão em módulos.

A principal exceção é a configuração/lista de heróis quando a concentração num único ficheiro torna a adição de novos heróis significativamente mais simples.

Mesmo nessa exceção, o código de regras não deve crescer indefinidamente dentro de uma única classe.

## 10. Arquitetura alvo

A arquitetura futura desejada pode ser resumida como:

```text
                 ┌───────────────────┐
                 │      UI / Web      │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  Game Core/Rules  │
                 └─────────┬─────────┘
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
 ┌───────────────────┐             ┌───────────────────┐
 │   Local Ares      │             │   Online Server   │
 │   / Analysis      │             │   / Validation    │
 └───────────────────┘             └─────────┬─────────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │    Ares      │
                                      │    C++       │
                                      └──────────────┘
```

O objetivo central é não ter duas definições incompatíveis das regras.
