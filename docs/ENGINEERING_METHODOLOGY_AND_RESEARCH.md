# RedWar — Metodologia de Engenharia, IA e Investigação

## Papel deste documento

Este documento define regras metodológicas transversais. Não é um roadmap paralelo nem uma especificação de gameplay. A linha de raciocínio única está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md) e a sequência executável em [`ROADMAP.md`](ROADMAP.md).

## Cadeia obrigatória

```text
observação
→ facto/evidência
→ hipótese
→ decisão
→ implementação
→ teste
→ validação
→ resultado
→ atualização do contrato
→ ROADMAP
```

Uma decisão relevante que exista apenas na conversa é uma dependência oculta.

## Correctness vs strength

O RedWar contém Python e C++ que precisam de manter equivalência enquanto ambos forem usados para regras/engine. Por isso:

```text
regressão
→ differential
→ property/metamorphic
→ perft
→ capability benchmark
→ Arena/strength
```

Não saltar uma camada para obter uma conclusão mais apelativa.

## Ares

Ares deve separar state/rules, move generation, move ordering, search e evaluation. Uma heurística deve ser justificada pelo fenómeno de RedWar que tenta explorar e pela evidência de custo/força obtida.

## Arena

Uma alteração correta pode continuar a ser uma regressão global. O instrumento para essa pergunta é Arena A/B, com controlo experimental, provenance, hold-out e incerteza adequados.

## NNUE

O rescan completo permanece oracle de correção até a atualização incremental estar ligada ao `BoardState` real e demonstrar equivalência. NPS, loss ou tamanho de rede não são por si provas de strength.

## Balanceamento

O Auto-Pricer é um diagnóstico. Contexto, matchup, composição, cor, skill, versão e validade dos dados devem permanecer separáveis.

## Documentação

Cada work package importante deve terminar com:

```text
código/testes
+ contrato canónico atualizado
+ resultado/limitação documentado
+ ROADMAP atualizado
```

Se um documento antigo contradizer o estado atual, a correção acontece no documento canónico; o histórico fica em `DECISIONS/` ou snapshots datados.
