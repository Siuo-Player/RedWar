# Ares — AI Engine

## Objetivo

Ares é uma engine de pesquisa especializada para RedWar. O objetivo é melhorar continuamente **força e/ou velocidade**, sempre com condições comparáveis e evidência reproduzível.

A metodologia é inspirada no Stockfish: mudanças isoladas, separação clara de responsabilidades, atenção extrema ao hot path e validação estatística/benchmark antes de aceitar uma alteração funcional.

## Estado atual confirmado

- **PR #52** integrou a extensão seletiva para a continuação do segundo STUN no mesmo centro, apenas quando o primeiro STUN atingiu pelo menos um adversário, além da estabilização necessária para o trainer.
- **PR #53** integrou as melhorias de CI, cobertura de benchmarks FrostMage e a separação entre gates de CI/tooling e gates de promoção da AI.
- **PR #54** integrou o harness reutilizável de benchmarks táticos, com failure-threshold e suporte a traces, tendo o FrostMage de cinco alvos como primeiro caso de referência.
- **PR #49** foi encerrado sem merge como PR independente. A documentação e o código atual devem ser entendidos pelo estado efetivamente presente na `main`, e não pelo estado histórico dessa branch.

## Observabilidade e informação imperfeita — dependência em aberto

O README especifica que o draft e o posicionamento inicial são secretos para o adversário. Contudo, a especificação anterior da Ares não definia explicitamente se essa informação continua oculta depois do setup nem quais campos pertencem à observação legal do jogador.

A auditoria atual encontrou um facto de implementação importante: `CppEngineBot.escolher_jogada()` envia `game_state.to_rwen()` ao motor C++, e `GameState.to_rwen()` serializa o tabuleiro completo, incluindo equipa, nome da peça, stun timer, lifespan e cooldown. Assim, **a Ares recebe atualmente uma representação full-state**.

Isto ainda não determina a regra de produto correta. Existem três hipóteses que devem ser distinguidas:

1. **Perfect-information by design after setup:** o segredo só existe durante draft/placement e todas as peças relevantes tornam-se públicas quando a partida começa.
2. **Imperfect-information during play:** parte da identidade/posição adversária continua secreta e Ares deve pesquisar dentro de um information set/belief representation.
3. **Information leakage:** o design pretende manter o segredo durante a partida, mas a camada `GameState → RWEN → Ares` expõe informação proibida.

A especificação operacional está em [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md) e a descoberta/decisão está em [`DECISIONS/2026-08-25-imperfect-information-observability-audit.md`](DECISIONS/2026-08-25-imperfect-information-observability-audit.md).

### Regra de desenvolvimento

Antes de otimizações de search, NNUE ou RL que dependam da representação de estado, deve existir um contrato explícito:

```text
regras/design
    ↓
observabilidade do jogador
    ↓
information set
    ↓
estado visível à Ares
    ↓
RWEN / search root
    ↓
move generation
    ↓
evaluation / NNUE
```

Não usar resultados de força para “validar” uma engine que possa estar a utilizar informação que um jogador não possui.

### Referência externa

Perolat et al., *Mastering the Game of Stratego with Model-Free Multiagent Reinforcement Learning*, Science 378(6623), 2022, 990–996. DOI: 10.1126/science.add4679. Preprint: https://arxiv.org/abs/2206.15378.

O estudo é relevante porque Stratego combina planeamento de longo horizonte com hidden information e deployment. Ele **não** é uma recomendação para substituir Ares por DeepNash; é evidência de que a estrutura de informação é parte da definição do problema de decisão.

Ficha de estudo: `Siuo-Player/Siuo-Player-PROJECT-STUDIES/_sources/cards/perolat2022-deepnash.md`.

## Arquitetura de pesquisa

O C++ é o hot path principal e utiliza alpha-beta/PVS, transposition table, Zobrist hashing, iterative deepening, killer moves, history heuristic, move ordering, quiescence/tactical search e limites de nós/tempo.

A pesquisa deve permanecer independente da forma concreta de avaliação.

## Estado RPG

RedWar não é xadrez. O estado inclui peças, stun timer, lifespan, spawn cooldown, efeitos de terreno, TWC e lado a jogar.

A reversibilidade obrigatória continua:

```text
S --make(M)--> S'
S' --unmake(M)--> S
```

A restauração inclui peças, efeitos, hash, avaliação material, contadores e restante estado derivado coberto pelos testes.

## Avaliação clássica

A avaliação clássica usa material, PST, estado de stun, lifespan, TWC e termos específicos de RedWar. `FrostMage` custa atualmente 5 pontos e continua a ser um sanity check útil.

Termos dependentes de múltiplas casas não devem ser tratados como um acumulador incremental local sem mecanismo explícito de atualização.

## NNUE RPG

A `main` contém a infraestrutura NNUE-style adaptada ao RPG, em vez de copiar HalfKP de Stockfish. As features representam:

- peça + casa + equipa relativa;
- stun timer;
- lifespan;
- spawn cooldown;
- efeitos de terreno;
- TWC;
- lado a jogar.

O formato binário é versionado como `RWNUE002`, com validação de metadata no carregador C++.

A NNUE continua opcional durante esta fase. Sem modelo carregado, a Ares mantém a avaliação clássica.

A implementação atual usa sincronização completa como **baseline de correção**. Existem primitivas de atualização incremental no módulo NNUE, mas ainda não estão ligadas às transições de `BoardState` do hot path. O próximo bloco NNUE deve fazer essa ligação e medir o ganho real; não assumir que uma função incremental existente já produz ganho.

Se a informação imperfeita permanecer uma regra durante a partida, a visibilidade dos inputs NNUE também deverá obedecer ao `OBSERVABILITY_CONTRACT.md`; não basta restringir o search root.

## Dados e treino

O pipeline é:

```text
posições reais / self-play / Arena
        ↓
RWEN + teacher score/resultados
        ↓
features esparsas
        ↓
treino PyTorch opcional
        ↓
quantização
        ↓
RWNUE002
        ↓
benchmark + Arena
```

`tools/nnue/generate_teacher.py` cria teacher data a partir da avaliação **clássica explícita**. O bootstrap model serve apenas para compatibilidade.

## Benchmarks táticos

`tools/analytics/tactical_benchmark_suite.py` fornece um harness determinístico e independente do código de pesquisa. Cada posição deve ser validada com orçamento alto antes de entrar na suite e depois medida com orçamentos progressivamente menores.

O primeiro caso é o FrostMage de cinco alvos:

```text
10 nodes    → movimento normal (failure point conhecido)
100+ nodes  → STUN A5 D5
```

O orçamento de 10 nodes é um **marcador de progresso**, não uma condição permanente de falha. Se uma otimização encontrar corretamente o STUN abaixo desse orçamento, o resultado melhorou e a suite deve passar.

## Arena e medição

A Arena deve separar três responsabilidades:

1. executar partidas determinísticas;
2. guardar o resultado e a sequência de ações;
3. analisar os registos depois.

`tools/analytics/arena_tournament.py` faz o primeiro e o segundo. `tools/analytics/game_analyzer.py` faz o terceiro sem voltar a jogar a partida.

O objetivo final é **Elo por CPU-segundo**. NPS isolado não é suficiente e uma avaliação “mais sofisticada” não é automaticamente melhor.

Quando hidden information fizer parte do modelo final de Ares, as partidas de Arena também devem usar o mesmo observability contract, para que a força medida seja a força do agente realmente legal no jogo.

## CI e benchmarking

`auto_balancer.yml` valida o caminho de build/teste e regressões do balanceamento.

`ai_arena.yml` fornece a comparação A/B da AI e deve ser usado com o mesmo orçamento de nodes/regras quando a hipótese é desempenho/força.

A Arena de promoção não deve ser acionada por alterações apenas de tooling, documentação ou benchmarks determinísticos.

Para uma mudança de AI, comparar pelo menos:

- melhor jogada em posições de referência;
- nodes/tempo/NPS;
- memória quando relevante;
- resultado da Arena;
- validade/reversibilidade do estado;
- quando aplicável, conformidade com o observability contract.

## Critérios para promover NNUE

Uma avaliação NNUE só deve tornar-se default se:

1. testes de correção permanecerem verdes;
2. layout Python/C++ permanecer idêntico;
3. carregamento e inferência forem determinísticos;
4. existir uma primeira rede realmente treinada;
5. custo por avaliação/NPS for medido contra a clássica;
6. `bestmove` e posições de referência não piorarem de forma material;
7. Arena apoiar a alteração com dados suficientes;
8. a representação usada pelo NNUE estiver conforme o observability contract, caso a partida seja de informação imperfeita.

## Próximos passos

1. formalizar e testar o `OBSERVABILITY_CONTRACT.md` antes de assumir que perfect-information search é a especificação final;
2. expandir a suite tática com posições independentes para segundo STUN letal, alternativas de centro, spells, passivas/aura, defesa, lifespan/cooldown e capturas de alto valor;
3. melhorar move ordering RPG por impacto tático observável, sem hardcode das posições de benchmark;
4. ligar as mutações de `BoardState` aos hooks incrementais do NNUE e medir o ganho real contra o baseline de rescan completo, respeitando a visibilidade definida;
5. gerar teacher dataset maior e mais variado;
6. treinar uma primeira rede real e verificar export/import C++;
7. comparar clássica vs NNUE em benchmark e Arena;
8. voltar a LMR/aspiration/PVS e outras otimizações agressivas apenas depois de existir evidência suficiente.
