# Decision: make search-ordering history aware of RedWar action types

Data: 2026-08-25
Estado: proposta

## Contexto

A análise de `ai/cpp_engine/search.cpp` na `main` mostra que `history_table` e `killer_moves` só são atualizados quando `move.type == "MOVE"`. As mesmas estruturas, porém, são usadas pela pesquisa de RedWar, que também gera `ATTACK`, `STUN`, `SPELL` e `SPAWN`.

A ordenação atual já atribui prioridades específicas às ações RPG (captura, stun, spell e spawn). A history/killer heuristic funciona como memória de pesquisa entre nós e deveria complementar essas prioridades, não ficar limitada ao movimento normal.

## Facto observado

- `update_history()` retorna imediatamente para qualquer ação que não seja `MOVE`.
- `update_killers()` faz o mesmo.
- `score_moves()` consulta `history_table` apenas no ramo residual de movimentos.

Logo, uma ação `ATTACK`, `STUN`, `SPELL` ou `SPAWN` nunca beneficia de aprendizagem local de ordenação causada por cutoffs anteriores.

## Hipótese

Uma memória de ordenação que inclua a taxonomia de ações de RedWar pode reduzir nós pesquisados ou melhorar estabilidade da ordenação, especialmente quando várias ações da mesma classe têm scores heurísticos próximos.

Isto **não prova** que a força da Ares melhora. É uma hipótese de eficiência/ordenação.

## Opções consideradas

1. Manter history/killer apenas para `MOVE`.
2. Dar history/killer separados por tipo de ação, mantendo as prioridades táticas existentes.
3. Remover as prioridades específicas RPG e usar apenas history/killer.

## Decisão

Testar a opção 2.

A memória de ordenação terá uma pequena dimensão adicional por classe de ação. Os scores heurísticos existentes continuam a dominar a ordem de magnitude; history/killer serão sinais de desempate/ordenação dentro dessas classes.

## Razão

Isto aproveita informação real da pesquisa sem substituir o modelo RPG existente. Também evita atribuir valor material artificial a uma ação apenas porque apareceu muitas vezes em cutoffs.

## Validação

- suite C++/Python existente;
- testes do search/engine;
- benchmarks táticos como regressões, sem os tratar como prova de melhoria geral;
- comparação futura da Ares na Arena, quando houver uma branch experimental pronta.

## Critério de sucesso

A alteração deve preservar correção e não introduzir regressões nos testes. Qualquer afirmação de melhoria de força será adiada até validação A/B geral com a metodologia de Strength Evaluation.

## Fontes

A decisão é uma adaptação local das heurísticas clássicas de move ordering à taxonomia de ações do RedWar. A implementação seguirá a documentação metodológica do projeto; nenhuma fonte externa é tomada como prova de que esta alteração específica aumenta a força da Ares.
