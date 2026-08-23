# Ares — optimization pass 2

Esta passagem continua a checklist de 100 otimizações depois do PR #17.

## Aplicado

- ✅ `ai/evaluator.pyx`: o tabuleiro é fixo em 8×8; o cálculo de índices PST foi reduzido de escalamento/clamping em ponto flutuante para indexação direta, preservando a mesma orientação.
- ✅ `setup.py`: o módulo Cython usa `-O3`, `-march=native`, `-mtune=native` e LTO no Linux; `/O2`, `/GL` e `/LTCG` no Windows.

## Próximos alvos de maior impacto

- ⏭️ `ai/cpp_engine/board.cpp`: substituir o hashing de `std::string` em `get_piece_zobrist_key()` / `get_effect_zobrist_key()` pelas tabelas Zobrist indexadas já existentes.
- ⏭️ `ai/cpp_engine/board.cpp`: alterar `update_timers()` para atualizar apenas peças/efeitos cujo estado realmente muda, evitando percorrer e reavaliar células inalteradas em cada nó.
- ⏭️ `ai/cpp_engine/movegen.cpp`: reduzir lookups por nome/string no hot path usando IDs pré-resolvidos por herói.
- ⏭️ `ai/cpp_engine/search.cpp`: reduzir o custo de comparação do best-move da TT e evitar trabalho redundante de string durante move ordering.
- ⏭️ `ai/cpp_engine/search.cpp`: avaliar reutilização de buffers de movimentos por profundidade em vez de alocação de `std::vector` por nó.

## Regra

Nenhum alvo desta passagem deve reduzir `go nodes N`, remover profundidade ou introduzir pruning que descarte deliberadamente linhas de pesquisa. Cada alteração deve ser validada por compilação, SmokeTest e comparação com posições fixas.
