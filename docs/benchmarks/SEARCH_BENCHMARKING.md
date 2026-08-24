# Search Benchmarking — Ares

## Objetivo

Medir força de pesquisa sem depender de milhares de partidas do Auto-Balancer.

Cada posição de referência representa uma situação tática concreta. A mesma posição é executada com vários orçamentos de nodes.

## Método

1. Selecionar uma posição adversarial reproduzível.
2. Executar a posição com um orçamento elevado o suficiente para obter uma solução estável.
3. Tratar essa solução como referência experimental, não como verdade matemática absoluta.
4. Reexecutar a mesma posição com orçamentos progressivamente menores.
5. Registar o menor orçamento em que a Ares ainda encontra a mesma classe de jogada.
6. Alterar apenas uma técnica de pesquisa por vez.
7. Repetir exatamente os mesmos testes.

A métrica principal é o **failure threshold**: o ponto em que a solução de referência deixa de ser encontrada quando o orçamento diminui.

## Exemplo FrostMage

A posição `FrostMage` já demonstrou:

```text
10k nodes   -> MOVE -> falha
100k nodes  -> MOVE -> falha
500k nodes  -> STUN -> sucesso
```

Isto permite perguntar se uma alteração de move ordering, quiescence ou selective extension faz a mesma posição passar a:

```text
10k nodes   -> STUN
100k nodes  -> STUN
500k nodes  -> STUN
```

ou, pelo menos, desloca o failure threshold para baixo.

## O benchmark não deve codificar a solução na engine

A posição, a expectativa experimental e os orçamentos pertencem à infraestrutura de benchmark. O C++ deve continuar genérico e desconhecer que uma posição específica é o FrostMage.

## Classes de posições a adicionar

- multi-target stun;
- segundo stun potencialmente letal;
- spell com insta-kill condicional;
- aura/passive que altera a legalidade ou o valor das ações;
- captura de alto valor;
- defesa contra ameaça tática;
- estado com lifespan/cooldown relevante;
- posição em que material simples contradiz o resultado tático.

## Alterações que devemos testar separadamente

### Move ordering
Priorizar capturas, stun de múltiplos alvos, spells de elevado impacto e movimentos que ativem uma ameaça imediata.

### Quiescence
Não limitar `STUN` forçante apenas ao caso em que já existe uma peça atordoada. Um stun que afeta múltiplos inimigos pode criar uma obrigação tática para a pesquisa seguinte.

### Selective extensions
Quando uma jogada cria uma ameaça tática muito forte (por exemplo, múltiplos alvos atordoados), pesquisar um ply adicional apenas nessa linha.

### Passives e spells
O seu valor deve aparecer primeiro como **sinal de pesquisa**: ordenação, extensão ou ameaça futura. Não devemos inflacionar automaticamente o valor material da peça apenas porque possui uma passiva forte.

## Regra experimental

Uma alteração de pesquisa só deve ser considerada melhoria se:

- baixar ou manter o failure threshold das posições de referência;
- não introduzir regressões nas restantes posições;
- não degradar significativamente NPS/tempo;
- preservar make/unmake e resultados determinísticos.

O benchmark serve para orientar o desenvolvimento; a Arena continua a ser a validação final de força.
