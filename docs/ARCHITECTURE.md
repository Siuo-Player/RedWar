# RedWar — Arquitetura Técnica

## Objetivo

A arquitetura deve permitir que o mesmo jogo seja executado:

- na aplicação local;
- na IA;
- em simulações massivas;
- no futuro cliente web;
- no servidor multiplayer.

A regra principal é evitar que cada camada invente a sua própria versão das regras.

## Estado atual

O projeto está numa fase de transição.

Existem implementações Python/Cython e um núcleo C++ da Ares. Algumas regras e comportamentos ainda existem em mais de uma camada, o que é uma fonte de risco.

```text
Python
├── engine/game_state.py
├── engine/pieces.py
├── engine/action_parser.py
└── ai/*.py / evaluator.pyx

C++
└── ai/cpp_engine/
    ├── types.hpp
    ├── board.cpp
    ├── movegen.cpp
    ├── evaluate.cpp
    ├── search.cpp
    ├── main.cpp
    └── SmokeTest.cpp
```

## Arquitetura alvo

A longo prazo deve existir uma definição autoritativa das regras e uma interface estável para os restantes sistemas.

```text
                     ┌────────────────┐
                     │ UI desktop/web │
                     └───────┬────────┘
                             │ ações/estado
                             ▼
                    ┌──────────────────┐
                    │    Game Core      │
                    │ estado + regras   │
                    └───────┬──────────┘
                            │
                ┌───────────┴────────────┐
                ▼                        ▼
        ┌───────────────┐       ┌────────────────┐
        │   Local Ares  │       │ Online Server  │
        │ análise / IA  │       │ valida / sync  │
        └───────────────┘       └───────┬────────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │    Ares      │
                                 │  C++ core    │
                                 └──────────────┘
```

## `engine/`

Define o jogo.

Responsabilidades:

- estado do tabuleiro;
- legalidade das ações;
- transformação do estado;
- timers;
- efeitos;
- condições de vitória;
- dados e regras dos heróis.

`engine/` não deve depender da UI.

## `ai/`

Define como procurar a melhor ação.

Responsabilidades:

- geração/ordenação eficiente de ações quando isso for parte do motor;
- avaliação;
- alpha-beta/minimax;
- transposition table;
- heurísticas de ordering;
- limites de tempo/nodes;
- benchmarking;
- integração com a Arena.

A IA pode conhecer profundamente o jogo, mas não deve redefinir regras arbitrariamente.

## C++

C++ é a direção preferida para o hot path da IA devido a desempenho e previsibilidade.

A linguagem não é um requisito ideológico. Se uma tecnologia melhor surgir para a pesquisa, poderá substituir C++ onde fizer sentido.

## Python/C++ durante a migração

Enquanto existirem os dois caminhos, devem existir testes diferenciais:

```text
mesma posição
   ↓
Python core   ─────┐
                   ├──> mesmas ações / mesmo estado / mesmo resultado
C++ core      ─────┘
```

Os testes mais importantes são:

- `make -> unmake` devolve exatamente à posição original;
- hash incremental == hash recalculado;
- mesma posição -> mesmas ações legais;
- mesma ação -> mesma transformação do estado;
- mesmos estados terminais.

## Modularidade

Um ficheiro com cerca de 1000 linhas deve ser tratado como candidato a divisão.

Exceção: a lista/configuração de heróis pode permanecer concentrada quando isso tornar novos heróis significativamente mais simples.

## Dependências

A direção desejada é:

```text
UI
 ↓
Game Core
 ↓
Ares / Online / Tools
```

Evitar:

```text
UI → AI → UI → Rules → AI → Config
```

ou dependências circulares entre regras e apresentação.

## Multiplayer

O futuro servidor deverá possuir a autoridade sobre a validade das ações.

O cliente não deve poder enviar “o resultado da jogada”; deve enviar uma intenção válida, que o servidor valide contra o estado oficial.

A solução concreta de backend, base de dados, hosting e autenticação ainda está por escolher.

## Observabilidade

Os componentes devem produzir dados suficientes para responder a:

- por que terminou uma partida;
- qual ação foi jogada;
- qual era o estado;
- qual versão da IA participou;
- quanto tempo/nodes a IA utilizou;
- por que uma Arena aceitou/rejeitou uma alteração.

## Direção de longo prazo

A melhor arquitetura não é a que contém mais módulos. É a que mantém uma única semântica de RedWar enquanto permite substituir a implementação de um componente sem reescrever o resto do produto.
