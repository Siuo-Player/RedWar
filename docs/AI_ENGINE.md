# Ares — AI Engine

## Objetivo

Ares é uma engine de pesquisa especializada para RedWar. O objetivo é melhorar continuamente **força e/ou velocidade**, sempre com condições comparáveis e evidência reproduzível.

A metodologia é inspirada no Stockfish: mudanças isoladas, separação clara de responsabilidades, atenção extrema ao hot path e validação estatística/benchmark antes de aceitar uma alteração funcional.

## Estado atual confirmado

O **PR #48 está integrado na `main`**. Ele adicionou pressão tática dinâmica do FrostMage à avaliação clássica, manteve `material_score` como acumulador incremental puro e reforçou a restauração de estado derivado em `make_move`/`unmake_move`.

O **PR #28** consolidou a proteção do Auto-Pricer para ELOs finitos extremos e a regressão correspondente.

O **PR #49** é a implementação NNUE RPG atual e continua aberto. A arquitetura está pronta para validação, mas ainda não deve ser considerada superior à avaliação clássica sem benchmark e Arena.

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

O PR #49 introduz uma NNUE-style adaptada ao RPG, em vez de copiar HalfKP de Stockfish. As features representam:

- peça + casa + equipa relativa;
- stun timer;
- lifespan;
- spawn cooldown;
- efeitos de terreno;
- TWC;
- lado a jogar.

O primeiro modelo usa dois accumulators de 128 entradas, hidden de 32 e inferência quantizada. O formato binário é versionado como `RWNUE002`, com validação de metadata no carregador C++.

O NNUE continua opcional durante esta fase. Sem modelo carregado, a Ares mantém a avaliação clássica.

A implementação atual usa sincronização completa como **baseline de correção**. Existem primitivas de atualização incremental no módulo NNUE, mas ainda não estão ligadas às transições de `BoardState` do hot path. O próximo bloco deve fazer essa ligação e medir o resultado; não assumir que uma função incremental existente já produz ganho.

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

## Arena e medição

A Arena deve separar três responsabilidades:

1. executar partidas determinísticas;
2. guardar o resultado e a sequência de ações;
3. analisar os registos depois.

`tools/analytics/arena_tournament.py` faz o primeiro e o segundo. `tools/analytics/game_analyzer.py` faz o terceiro sem voltar a jogar a partida.

O objetivo final é **Elo por CPU-segundo**. NPS isolado não é suficiente e uma avaliação “mais sofisticada” não é automaticamente melhor.

## CI e benchmarking

`auto_balancer.yml` valida o caminho de build/teste e regressões do balanceamento.

`ai_arena.yml` fornece a comparação A/B da AI e deve ser usado com o mesmo orçamento de nodes/regras quando a hipótese é desempenho/força.

Para uma mudança de AI, comparar pelo menos:

- melhor jogada em posições de referência;
- nodes/tempo/NPS;
- memória quando relevante;
- resultado da Arena;
- validade/reversibilidade do estado.

## Critérios para promover NNUE

Uma avaliação NNUE só deve tornar-se default se:

1. testes de correção permanecerem verdes;
2. layout Python/C++ permanecer idêntico;
3. carregamento e inferência forem determinísticos;
4. existir uma primeira rede realmente treinada;
5. custo por avaliação/NPS for medido contra a clássica;
6. `bestmove` e posições de referência não piorarem de forma material;
7. Arena apoiar a alteração com dados suficientes.

## Próximos passos

1. fechar o bloco de tooling/documentação sem misturar correções não relacionadas;
2. validar integralmente a pipeline NNUE do PR #49;
3. gerar teacher dataset maior e mais variado;
4. treinar uma primeira rede real e verificar export/import C++;
5. comparar clássica vs NNUE em benchmark e Arena;
6. implementar atualização incremental real dos accumulators através de `BoardState`;
7. voltar a move ordering/quiescence/avaliação após essa medição.
