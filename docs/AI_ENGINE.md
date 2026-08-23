# Ares — AI Engine

## Objetivo

Ares é uma engine de pesquisa especializada para RedWar. O objetivo é melhorar continuamente **força e/ou velocidade**, sempre com condições comparáveis e evidência reproduzível.

A metodologia é inspirada no Stockfish: mudanças isoladas, separação clara de responsabilidades, atenção extrema ao hot path e validação estatística/benchmark antes de aceitar uma alteração funcional.

## Estado atual confirmado

O **PR #48 está integrado na `main`**. Ele adicionou pressão tática dinâmica do FrostMage à avaliação clássica, manteve `material_score` como acumulador incremental puro e reforçou a restauração de estado derivado em `make_move`/`unmake_move`. O **PR #14** estabilizou o Auto-Pricer contra overflow de ELO.

O **PR #49** é a implementação NNUE RPG atual e continua aberto. A arquitetura está pronta para validação, mas ainda não deve ser considerada superior à avaliação clássica sem benchmark e Arena.

## Arquitetura de pesquisa

O C++ é o hot path principal e utiliza alpha-beta/PVS, transposition table, Zobrist hashing, iterative deepening, killer moves, history heuristic, move ordering, quiescence/tactical search e limites de nós/tempo.

A pesquisa deve permanecer independente da forma como a posição é avaliada.

## Estado RPG

RedWar não é xadrez. O estado inclui peças, stun timer, lifespan, spawn cooldown, efeitos de terreno, TWC e lado a jogar.

A reversibilidade obrigatória continua:

```text
S --make(M)--> S'
S' --unmake(M)--> S
```

A restauração inclui peças, efeitos, hash e acumuladores derivados do estado.

## Avaliação clássica

A avaliação clássica usa material, PST, estado de stun, lifespan, TWC e termos específicos de RedWar. `FrostMage` custa atualmente 5 pontos e é um sanity check importante.

Termos dependentes do tabuleiro inteiro não devem ser guardados num acumulador incremental local sem mecanismo explícito de atualização.

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

A implementação atual usa um caminho de sincronização completo como baseline de correção; a próxima otimização isolada deve substituir esse rescan por atualização incremental via `BoardState` e provar o ganho de NPS. Isto segue diretamente o princípio de NNUE de minimizar entradas ativas e atualizar apenas o que mudou. citeturn573908search0turn573908search7

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

`tools/nnue/generate_teacher.py` cria um pequeno dataset determinístico a partir da avaliação **clássica explícita**. O bootstrap model continua a ser apenas um teste de compatibilidade, não uma medida de força.

A metodologia segue a ideia usada no desenvolvimento do Stockfish: redes e alterações funcionais precisam de ser comparadas estatisticamente, não aceites apenas porque passam testes mecânicos. citeturn573908search2turn573908search5

## CI e benchmarking

`auto_balancer.yml` aceita tanto a engine clássica como revisões com `nnue.cpp` e executa os testes de compatibilidade NNUE quando aplicável.

`ai_arena.yml` compara agora **base vs HEAD**, em vez de recompilar todos os commits intermédios. Para PRs de performance mantém um guard de regressão de 10%.

## Critérios de aceitação

Uma avaliação NNUE só deve tornar-se default se:

1. testes de correção permanecerem verdes;
2. layout Python/C++ permanecer idêntico;
3. carregamento e inferência forem determinísticos;
4. existir uma primeira rede realmente treinada;
5. custo por avaliação/NPS for medido contra a clássica;
6. `bestmove` e posições de referência não piorarem de forma material;
7. Arena apoiar a alteração com dados suficientes.

O objetivo é **Elo por CPU-segundo**, não uma rede maior por si só. Stockfish demonstra que NNUE pode ganhar muita força mesmo com menor NPS, desde que o custo adicional compre uma melhoria de avaliação suficientemente grande. citeturn573908search1

## Próximos passos

1. Validar CI completo do PR #49.
2. Gerar teacher dataset maior e mais variado.
3. Treinar uma primeira rede real e verificar export/import C++.
4. Comparar clássica vs NNUE em benchmark de posições e custo por avaliação.
5. Comparar força na Arena.
6. Implementar atualização incremental real dos accumulators.
7. Melhorar move ordering.
8. Melhorar quiescence para stun/spells/kill chains.
9. Criar histórico de NPS, profundidade, TT hit rate e força.
10. Eliminar divergências Python/C++.
