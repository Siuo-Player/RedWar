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

As features representam peça/casa/equipa relativa, stun, lifespan, cooldown, efeitos, TWC e lado a jogar. O layout atual tem 12 469 features e é duplicado em Python e C++.

**Estado desta branch:** o carregamento e a inferência usam uma sincronização completa como baseline de correção. A atualização incremental dos accumulators ainda é trabalho futuro. Essa distinção é intencional: primeiro validamos formato, paridade e matemática; depois medimos o ganho do update incremental. A propriedade central do NNUE é explorar entradas esparsas e alterações pequenas entre posições para evitar recalcular a parte cara da rede. citeturn573908search0turn573908search7

## Formato do modelo

`RWNUE002`, versão 2. O header valida feature count, tamanhos e escalas. Pesos usam `int16`; biases usam `int32`.

Sem modelo, a Ares continua na avaliação clássica.

## Treino

`tools/nnue/generate_teacher.py` gera teacher data usando explicitamente `eval classical`, evitando que o próprio NNUE contamine os targets.

`tools/nnue/train.py` usa PyTorch opcional e exporta para o formato RWNUE002. O bootstrap model só serve para testar compatibilidade; não é prova de força.

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

A meta é **Elo por CPU-segundo**, não complexidade por si só. O desenvolvimento do Stockfish trata alterações funcionais e redes como hipóteses que precisam de comparação estatística antes de serem aceites. citeturn573908search2turn573908search5

## Próximo bloco

Depois de validar este pipeline, substituir o rescan por hooks incrementais ligados a `BoardState`. Só então experimentar redes maiores ou SIMD/AVX2.
