# Ares — AI Engine

## 1. Objetivo

Ares é a inteligência artificial de RedWar.

O objetivo final é semelhante ao espírito do Stockfish:

> uma engine especializada que melhora continuamente através de alterações mensuráveis e que pode ser testada por uma comunidade.

Ares deve servir tanto como:

- adversário do jogador;
- ferramenta de análise de posições;
- ferramenta de análise de partidas;
- componente de bots com diferentes forças;
- objeto de benchmarking entre versões.

## 2. O que significa “melhor”

Uma alteração na Ares é melhor quando, sob condições controladas, consegue jogar melhor que a versão anterior.

Elegância, quantidade de código ou complexidade da heurística não são suficientes.

A unidade de avaliação é uma comparação:

```text
Ares anterior
    vs
Ares proposta
```

com:

- mesmas regras;
- mesmos limites de pesquisa;
- condições equivalentes;
- cores alternadas;
- número estatisticamente suficiente de partidas.

## 3. Pesquisa

O núcleo atual utiliza conceitos como:

- minimax/negamax;
- alpha-beta pruning;
- move ordering;
- transposition table;
- Zobrist hashing;
- killer moves;
- history heuristic;
- iterative deepening;
- pesquisa quiescente/tática onde suportada.

A lista não deve ser interpretada como prova de que cada técnica está perfeita ou sequer concluída. O estado real da implementação deve ser validado pelo código e pelos testes.

## 4. Avaliação

A avaliação atual deriva principalmente do valor material e de informação posicional/estado.

Futuras componentes podem incluir:

- mobilidade;
- ameaça imediata;
- controlo do tabuleiro;
- valor do stun;
- valor de cooldowns;
- valor de efeitos de terreno;
- potencial de invocação;
- segurança de posições;
- fatores específicos das condições de vitória.

A expansão da avaliação deve ser acompanhada de testes de força. Uma avaliação teoricamente mais sofisticada pode piorar a engine.

## 5. Stun e morte

Ares precisa compreender que:

```text
normal -> stun
stun   -> novo stun = morte
```

Isto é diferente de um jogo tradicional onde captura e dano são praticamente a mesma operação.

Uma posição com uma peça atordoada pode ser muito mais perigosa do que o seu valor material sugere.

## 6. Timers e estado temporal

A posição inclui informação temporal.

Faz parte da identidade da posição:

- stun timer;
- lifespan;
- cooldown;
- efeitos da casa;
- contador de turnos sem captura;
- lado a jogar.

Uma transposition table não pode tratar duas posições que diferem nesses valores como sendo a mesma posição.

## 7. C++

O caminho principal para o hot path é C++.

A pasta `ai/cpp_engine/` contém atualmente:

```text
board.cpp      # estado, hash e transições
movegen.cpp    # geração de ações
search.cpp     # pesquisa
 evaluate.cpp  # avaliação
main.cpp       # interface/protocolo
 types.hpp     # tipos e limites partilhados
SmokeTest.cpp  # testes nativos
```

O projeto ainda possui componentes Python/Cython durante a migração.

## 8. Reversibilidade

Uma propriedade essencial da engine é:

```text
S --make(M)--> S'
S' --unmake(M)--> S
```

A posição deve voltar exatamente ao estado anterior, incluindo:

- peças;
- efeitos;
- timers;
- turno;
- contador sem captura;
- hash;
- avaliação incremental.

## 9. Hashing

O hashing de posição deve distinguir qualquer informação relevante para a pesquisa.

Também deve existir uma forma de recalcular o hash a partir do estado e verificar que o hash incremental coincide com esse resultado.

## 10. Arena

A Arena é o futuro mecanismo de contribuição aberta.

Idealmente, um Pull Request de IA será comparado com o estado anterior do Ares, não contra um bot fixo arbitrário.

O pipeline atual é experimental e está a ser calibrado.

O workflow atual executa um torneio headless de 100 jogos com uma margem configurada de 10 vitórias. Estes valores podem mudar conforme a experiência e a velocidade da engine.

## 11. ELO

Os números existentes de 100/140/200/250/300 não devem ser tratados como ratings oficiais.

O projeto pretende futuramente criar um rating válido para:

- versões da Ares;
- bots de diferentes configurações;
- eventualmente jogadores humanos.

Para uma engine, o rating deve incluir metodologia, controlo de condições e amostra suficiente.

## 12. Testes de força

Além dos testes unitários, o Ares deve ser validado através de:

- self-play;
- posições de referência;
- regressão de resultados;
- benchmarks de NPS;
- profundidade média;
- taxa de acerto da TT;
- resultados da Arena;
- testes diferenciais Python/C++.

## 13. Objetivos futuros

- tornar o C++ o único hot path da pesquisa;
- eliminar regras duplicadas entre Python e C++;
- aumentar NPS sem sacrificar correção;
- melhorar quiescence para as formas de volatilidade próprias de RedWar;
- construir benchmark suite reproducível;
- tornar a Arena estatisticamente mais semelhante ao espírito do Fishtest;
- guardar histórico de versões e resultados;
- produzir análise útil para o jogador, não apenas `bestmove`.
