# Ares NNUE

## Objetivo

Ares suporta uma avaliação NNUE-style inspirada no desenvolvimento do Stockfish, mas adaptada ao RPG de RedWar. Não copiamos HalfKP porque RedWar não tem reis nem a mesma semântica de posição.

## Arquitetura

```text
BoardState
  -> sparse feature ids
  -> 2 accumulators x 128
  -> hidden 32 + clipped ReLU
  -> score
```

As features representam peça/casa/equipa relativa, stun, lifespan, cooldown, efeitos, TWC e lado a jogar. O layout atual tem 12 469 features e existe em Python e C++.

### Estado de atualização

A implementação atual mantém uma sincronização completa da posição como **baseline de correção**. O módulo NNUE já contém operações capazes de substituir features de uma casa/efeito e atualizar lado/TWC incrementalmente, mas essas operações ainda não estão integradas às mutações normais de `BoardState`.

Portanto, a ordem correta é:

1. provar paridade/matemática com o baseline;
2. ligar as transições reais do estado aos hooks incrementais;
3. medir NPS/custo por avaliação;
4. só então otimizar mais ou alterar a arquitetura.

## Formato do modelo

`RWNUE002`, versão 2. O header valida feature count, tamanhos e escalas. Pesos usam `int16`; biases usam `int32`.

Sem modelo, a Ares continua na avaliação clássica.

## Features

As features são discretas e determinísticas. Isto permite que Python e C++ sejam testados contra a mesma representação:

```text
PieceState -> feature ids
EffectState -> feature ids
Turn/TWC -> feature ids
```

Qualquer mudança de `FEATURE_COUNT` ou do layout deve alterar simultaneamente Python e C++ e acrescentar uma regressão de paridade.

## Treino

`tools/nnue/generate_teacher.py` gera teacher data usando explicitamente `eval classical`, evitando que o próprio NNUE contamine os targets.

`tools/nnue/train.py` usa PyTorch opcional e exporta para o formato RWNUE002.

`tools/nnue/bootstrap_model.py` cria um modelo determinístico pequeno para verificar loading/inferência. **Não é uma prova de inteligência.**

Fluxo:

```text
teacher data
  -> features
  -> treino
  -> quantização
  -> RWNUE002
  -> C++ loading
  -> benchmark
  -> Arena
```

## Validação antes de tornar NNUE default

1. Paridade Python/C++.
2. Loading/inferência determinísticos.
3. Rede realmente treinada e carregada pelo C++.
4. Custo por avaliação/NPS conhecido.
5. `bestmove` e posições de referência comparados com a clássica.
6. Testes específicos de FrostMage/stun.
7. Arena contra a avaliação clássica sob condições equivalentes.

A meta é **Elo por CPU-segundo**, não complexidade por si só.

## Próximo bloco

Depois de validar este pipeline, ligar os hooks incrementais às mutações reais do `BoardState`, remover o rescan do caminho quente e medir. Só depois experimentar redes maiores, SIMD/AVX2 ou outras otimizações.
