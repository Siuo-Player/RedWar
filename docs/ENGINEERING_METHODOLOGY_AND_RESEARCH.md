# RedWar — Metodologia de Engenharia, IA e Investigação

## Papel deste documento

Este documento define regras metodológicas transversais. Não é um roadmap paralelo nem uma especificação de gameplay. A linha de raciocínio está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md) e a sequência executável em [`ROADMAP.md`](ROADMAP.md).

## Estados de conhecimento

Usar explicitamente:

```text
DOCUMENTED
IMPLEMENTED
TESTED
VALIDATED
PROVEN
```

Estas categorias não são sinónimas. Um item documentado pode não existir no código; um teste pode provar apenas uma propriedade local; uma validação de capability não prova strength; uma decisão de design não é prova causal.

## Cadeia obrigatória

```text
observação
→ facto/evidência
→ hipótese
→ decisão
→ implementação
→ teste
→ validação apropriada
→ resultado
→ atualização do contrato
→ ROADMAP
```

Uma decisão relevante que exista apenas na conversa é uma dependência oculta.

## Correctness vs strength

O RedWar contém Python e C++ que precisam de manter equivalência enquanto ambos forem usados para regras/engine. Por isso, de forma geral:

```text
regressão
→ differential
→ property/metamorphic
→ perft ou coverage dirigida
→ capability benchmark
→ Arena/strength
```

A sequência não autoriza saltar uma camada para obter uma conclusão mais forte do que a evidência suporta.

## Ares

Ares deve separar state/rules, move generation, move ordering, search e evaluation. Uma heurística deve ser justificada pelo fenómeno de RedWar que tenta explorar e pela evidência de custo/capability/strength apropriada.

## Arena

Uma alteração correta pode continuar a ser uma regressão global. O instrumento para essa pergunta é Arena A/B com controlo experimental, provenance, hold-out e incerteza adequados.

O dataset inicial de 100 jogos/50 pares não deve ser reinterpretado como 50 condições independentes.

## NNUE

O rescan completo permanece oracle de correção até a atualização incremental estar ligada ao `BoardState` real e demonstrar equivalência. NPS, training loss, dataset hygiene ou tamanho de rede não são por si provas de strength.

#316 alterou apenas a classificação CI de uma classe estreita de metodologia de dataset para que não disparasse automaticamente um gate de promoção de strength. #314 não foi merged e não representa o estado do `main`.

## Balanceamento

O Auto-Pricer é diagnóstico. Contexto, matchup, composição, cor, skill, versão, budget, opening/seed e validade dos dados devem permanecer separáveis quando relevantes.

## Documentação

Antes de criar um artefacto para um assunto existente, localizar o proprietário canónico em [`00_INDEX.md`](00_INDEX.md). Um novo documento só é justificado se tiver responsabilidade própria e não duplicar current state, roadmap, contrato ou decisão.

Cada work package importante termina com:

```text
código/testes
+ contrato canónico atualizado
+ resultado/limitação documentado
+ ROADMAP atualizado
```

Quando o código muda um contrato ou a política, não basta atualizar um snapshot antigo.

## PROJECT-STUDIES

Material de `Siuo-Player-PROJECT-STUDIES/REDWAR` pode conservar research, rationale e literatura. Não é operational source of truth do RedWar. Uma conclusão operacional relevante deve ser refletida em `RedWar/docs` e ligada ao roadmap.

## Regra anti-ficção

É inválido inferir:

- `planned` = implemented;
- `documented` = proven;
- `tested` = validated for all states;
- benchmark improvement = strength improvement;
- CI green = total correctness;
- branch artifact = `main` state.
