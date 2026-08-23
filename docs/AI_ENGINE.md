# Ares — AI Engine

## Objetivo

Ares é uma engine de pesquisa especializada para RedWar. O objetivo é melhorar continuamente **força e/ou velocidade**, sempre com condições comparáveis e evidência reproduzível.

A metodologia é inspirada no Stockfish: mudanças pequenas, separação clara de responsabilidades, atenção extrema ao hot path e validação estatística/benchmark antes de aceitar uma alteração funcional.

## Estado atual confirmado

O PR #47 tornou `make_move`/`unmake_move` verificável por self-test. O PR #14 estabilizou o Auto-Pricer contra overflow ELO. O trabalho #48 está a consolidar a reversibilidade e a avaliação de stun/FrostMage antes de merge.

## Arquitetura de pesquisa

O C++ é o hot path principal e utiliza atualmente:

- alpha-beta;
- PVS/zero-window search;
- transposition table;
- Zobrist hashing;
- iterative deepening;
- killer moves;
- history heuristic;
- move ordering;
- quiescence/tactical search;
- node/time limits.

A pesquisa deve permanecer independente da forma como a posição é avaliada.

## Estado RPG

Ao contrário do xadrez, RedWar tem regras temporais e efeitos. O estado relevante inclui peças, stun timer, lifespan, spawn cooldown, efeitos de terreno, TWC e lado a jogar.

A reversibilidade obrigatória continua:

```text
S --make(M)--> S'
S' --unmake(M)--> S
```

A restauração inclui peças, efeitos, hash e todos os acumuladores derivados do estado.

## Avaliação clássica

A avaliação clássica usa material, PST, estado de stun, lifespan, TWC e termos específicos de RedWar. `FrostMage` custa atualmente 5 pontos e é um sanity check importante.

Termos dependentes do tabuleiro inteiro não devem ser guardados num acumulador incremental local sem mecanismo explícito de atualização.

## NNUE RPG

A próxima grande etapa é uma avaliação **NNUE-style**. Não copiamos HalfKP literalmente porque RedWar não tem reis nem a mesma semântica de posição. Usamos features esparsas que representam:

- peça + casa + equipa relativa;
- stun timer;
- lifespan;
- spawn cooldown;
- efeitos de terreno;
- TWC;
- lado a jogar.

O primeiro estágio usa dois accumulators de 128 entradas, hidden de 32 e inferência quantizada. O layout está documentado em `docs/NNUE.md` e deve ser idêntico em Python e C++.

O NNUE é opcional durante o desenvolvimento. Sem modelo carregado, `evaluate_board()` continua no avaliador clássico.

## Treino NNUE

`tools/nnue/train.py` é o treinador opcional baseado em PyTorch. O fluxo esperado é:

```text
posições reais / self-play / Arena
        ↓
RWEN + teacher score/resultados
        ↓
features esparsas
        ↓
treino
        ↓
quantização
        ↓
RWNUE002
        ↓
benchmark + Arena
```

O bootstrap model serve apenas para verificar compatibilidade do formato e do caminho C++. Não é prova de força.

## Critérios de aceitação

Uma alteração de avaliação só deve entrar na configuração principal se:

1. os testes de correção permanecerem verdes;
2. não houver regressão relevante de NPS/custo por nó;
3. `bestmove` e posições de referência não piorarem de forma material;
4. houver ganho reproduzível em posições táticas relevantes;
5. a Arena apoiar a alteração quando houver dados suficientes.

Uma rede maior não é melhor por definição. O objetivo é **Elo por CPU-segundo**, não complexidade.

## Próximos passos

1. Terminar e medir PR #48.
2. Completar NNUE C++/Python/CI.
3. Criar dataset teacher e primeiras redes treinadas.
4. Comparar NNUE vs clássico em benchmark e Arena.
5. Melhorar move ordering.
6. Melhorar quiescence específica para stun/spells/kill chains.
7. Criar histórico de força/NPS/TT hit rate.
8. Eliminar divergências Python/C++.
