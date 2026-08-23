# Ares NNUE

## Objetivo

Ares passa a suportar uma avaliação NNUE-style inspirada no modelo de desenvolvimento do Stockfish, mas adaptada às regras de RedWar. Não existe um conceito de rei equivalente ao xadrez, portanto não usamos HalfKP literalmente. Em vez disso, as features representam diretamente o estado RPG que interessa à avaliação.

## Arquitetura

```text
BoardState
   │
   ├── peças / casa / equipa relativa
   ├── stun timer
   ├── lifespan
   ├── spawn cooldown
   ├── efeitos de terreno
   ├── contador sem captura (TWC)
   └── lado a jogar
          │
          ▼
   sparse feature ids
          │
          ▼
   dois accumulators de 128
          │
          ▼
   hidden 32 + clipped ReLU
          │
          ▼
   score White-perspective
```

O primeiro estágio é atualizado de forma esparsa: uma mudança de uma peça, efeito, turno ou TWC altera apenas as features correspondentes. Isto é a propriedade fundamental do NNUE que interessa para o hot path.

## Features

O layout atual usa 12 469 features:

- peça + casa + equipa relativa;
- `stun_timer` em 6 buckets;
- `lifespan` em 6 buckets;
- `spawn_cooldown` em 5 buckets;
- efeitos por casa/equipa/tipo/timer;
- `twc` de 0–50;
- lado a jogar relativo à perspectiva.

O mesmo layout existe em `ai/cpp_engine/nnue.cpp` e `tools/nnue/features.py`. Qualquer alteração no layout tem de modificar os dois lados e os testes de paridade.

## Formato do modelo

O modelo binário é `RWNUE002`, versão 2. O header inclui feature count, tamanho dos accumulators/hidden e escalas de quantização. Os pesos usam inteiros `int16` e os biases `int32`.

O C++ aceita:

```text
REDWAR_NNUE_MODEL=<ficheiro>
```

ou, por omissão:

```text
data/nnue/ares.nnue
```

Um modelo ausente não é erro: a engine continua a usar a avaliação clássica.

## Treino

O treino opcional está em `tools/nnue/train.py` e usa PyTorch. O PyTorch não é requisito para executar o jogo ou a CI normal; é apenas ferramenta de treino.

Dataset mínimo:

```json
{"rwen": "...", "score": 42}
```

O primeiro objetivo é reproduzir a avaliação de uma teacher engine. A seguir, o dataset deve evoluir para posições de partidas/Arena com resultados e valores de pesquisa, para que o NNUE aprenda relações que a heurística manual não captura.

`tools/nnue/bootstrap_model.py` gera uma rede determinística apenas para validar o formato e o caminho C++ de inferência. Esse modelo não é considerado uma rede forte e não deve ser usado como prova de melhoria de Ares.

## Validação

A rede só deve passar de opcional a avaliação predefinida depois de demonstrar:

1. paridade Python/C++ do extractor;
2. loading e inferência determinísticos;
3. custo por avaliação aceitável;
4. `bestmove` pelo menos tão forte quanto o avaliador clássico;
5. melhoria mensurável em posições táticas de RedWar, incluindo stun/FrostMage;
6. resultado positivo na Arena contra a versão clássica sob condições equivalentes.

A prioridade é força e depois velocidade. Um modelo maior que reduz NPS sem compensação de força deve ser rejeitado.

## Desenvolvimento futuro

O próximo passo é substituir o dataset bootstrap por dados reais de Ares, self-play e Arena, mantendo pesos e arquitetura versionados por metadata e hash. Só depois disso faz sentido experimentar redes maiores, SIMD/AVX2 ou outras otimizações do caminho de inferência.
