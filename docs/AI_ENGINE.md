# Ares — AI Engine

## Objetivo

Ares é a inteligência artificial de RedWar. O objetivo é uma engine especializada que melhore continuamente através de alterações mensuráveis, usando sempre a versão anterior como referência.

Uma melhoria válida precisa de manter as regras e o orçamento de pesquisa comparáveis e demonstrar ganho de força, velocidade ou ambos. Código mais complexo não é automaticamente melhor.

## Estado atual confirmado — PR #47

O último PR integrado adicionou um self-test nativo de `make_move`/`unmake_move`. O teste verifica restauração do `BoardState`, peças, efeitos, timers, hash, avaliação material, contadores e turno em posições com movimento/captura, stun, spawn e efeitos temporizados.

Isto dá-nos uma fundação segura para otimizações e alterações de avaliação: primeiro preservamos reversibilidade, depois mudamos força/desempenho.

## Pesquisa

O núcleo C++ utiliza atualmente alpha-beta, ordenação de ações, transposition table, Zobrist hashing, killer moves, history heuristic, iterative deepening e pesquisa quiescente/tática.

O C++ é o hot path principal. Python/Cython continuam durante a migração e para componentes auxiliares.

## Avaliação

A avaliação atual deriva principalmente de valor material, posição, timers e estado de stun. O próximo foco é fazer com que o valor de uma posição reflita melhor ameaças específicas de RedWar, especialmente a cadeia:

```text
normal -> stun -> segundo stun = morte
```

Uma peça atordoada não tem apenas valor material reduzido: pode representar uma oportunidade tática imediata para o adversário.

### FrostMage como sanity check

`FrostMage` custa atualmente **5 pontos** no `heroes_config.json`. A unidade de 5 pontos tem capacidade de aplicar stun em área a até 3 casas de distância. Portanto, uma Ares competente não deve avaliá-la apenas como uma peça material de 5 pontos.

O objetivo não é colocar um valor arbitrário permanente no FrostMage. A avaliação deve reconhecer a **pressão real da posição**: inimigos alcançáveis por stun, especialmente peças já atordoadas que podem morrer com uma segunda aplicação.

## Plano da branch atual

Branch: `perf/ares-stun-threat-eval-2026-08-23`

Objetivo: aumentar a qualidade da avaliação perante ameaças de stun com custo por nó baixo e sem aumentar profundidade/orçamento.

Passos:

1. Medir a avaliação atual em posições pequenas com FrostMage.
2. Implementar uma estimativa barata e bounded de pressão de stun diretamente a partir do estado do tabuleiro.
3. Dar peso adicional a alvos já atordoados, porque o próximo stun pode convertê-los em morte.
4. Manter o termo simétrico para White/Black e limitar o impacto para impedir que substitua material/terminal scores.
5. Adicionar regressões determinísticas.
6. Comparar `bestmove`, tempo mediano/NPS e, quando disponível, resultados da Arena.
7. Só fazer merge se a alteração melhorar decisões táticas ou mostrar uma melhoria inequívoca sem regressão relevante.

Se a branch ficar a meio, o ponto de continuação é `ai/cpp_engine/evaluate.cpp`: a função `get_piece_value()` concentra a avaliação incremental e `compute_initial_eval()` mantém o `material_score`. O teste deve ser executado antes de qualquer alteração adicional.

## Reversibilidade e hashing

A identidade da posição inclui peças, efeitos, stun timer, lifespan, cooldowns, contador sem captura e lado a jogar. O hash incremental deve coincidir com o hash recalculado.

A relação obrigatória é:

```text
S --make(M)--> S'
S' --unmake(M)--> S
```

O self-test introduzido no PR #47 cobre uma parte importante desta propriedade; a meta futura é cobrir toda a árvore de regras.

## Testes e força

Além dos testes unitários:

- benchmark determinístico;
- `bestmove` como regressão rápida;
- NPS e tempo por nó;
- profundidade;
- TT hit rate;
- self-play/Arena;
- suite de posições de referência;
- testes diferenciais Python/C++.

Nenhuma otimização deve reduzir silenciosamente a qualidade da pesquisa apenas para apresentar números de velocidade melhores.

## Arena e balanceamento

A Arena deve comparar Ares anterior vs candidata sob condições equivalentes. O Auto-Pricer deve depender de telemetria suficiente e não ser usado como substituto de testes de força.

Depois de a avaliação de stun melhorar, FrostMage deve voltar a ser analisado explicitamente no balanceamento. O custo atual de 5 pontos é uma bandeira de sanidade, não um objetivo artificial a atingir.

## Próximos objetivos da IA

- Melhorar avaliação de ameaças e especificidades de RedWar.
- Melhorar geração/ordenação de ações.
- Melhorar quiescence.
- Aumentar NPS sem sacrificar força.
- Expandir benchmark suite.
- Medir historicamente força e desempenho.
- Melhorar a Arena para comparação estatística.
- Criar rating/ELO das engines.
- Eliminar divergências Python/C++.
