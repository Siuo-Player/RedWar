# Decision: execution boundary does not use `fast_clone()`

Data: 2026-09-08  
Estado: aceite

## Contexto

A A0.1 precisa fechar a autoridade de execução sem criar uma segunda semântica entre a referência Python e a Ares. O estado canónico é `GameState`; a pesquisa nativa usa o hot path C++ e o modelo relevante para evolução de search é `make → unmake`.

## Problema

Uma abordagem proposta para validar uma ação seria:

```text
fast_clone()
→ execute_action() especulativamente
→ observar se falha
→ executar novamente no estado real
```

Esta abordagem mistura validação com execução, depende de uma cópia Python do estado e poderia divergir em metadata/history/timers ou transformar o executor em mecanismo de preflight especulativo.

## Opções consideradas

1. Usar `fast_clone()` para preflight do executor.
2. Duplicar regras de cada herói num validador paralelo.
3. Separar explicitamente action-space resolution de transition validation, mantendo `GameState` como autoridade de transição.

## Decisão

A opção 3 é a arquitetura aceite.

`fast_clone()` **não é autoridade de legalidade**, não é mecanismo de preflight de `execute_action()` e não entra no hot path C++ da Ares.

A fronteira de execução deve ser:

```text
input action
→ normalize canonical action
→ canonical action-space resolution
→ transition-domain validation
→ only then mutate state
```

A resolução usa `resolve_legal_action()` sem duplicar regras de heróis. A validação de transição preserva as condições e erros específicos já existentes em `GameState`. Uma rejeição não pode deixar mutação observável.

## Escopo de `fast_clone()`

`fast_clone()` permanece permitido como ferramenta auxiliar em testes de referência Python, replay, fixtures/transformações offline, stateful/property tests e comparação de estados, desde que não se torne parte da autoridade de execução nem do hot path Ares.

A existência de `fast_clone()` em código de referência não constitui motivo para removê-lo globalmente.

## Evidência

- PR #315 foi encerrado sem merge porque `legal_actions()` não representava todo o contrato de execução aceito por fixtures/compatibilidade.
- Issue #317 exige separar action-space coverage de transition validity e preservar erros de domínio.
- PR #321, merged em `e17afcd54ad57635e222f3b3c9a5bb9966df9394`, introduziu `resolve_legal_action()` como seam de resolução canónica/legacy.
- O C++ atual em `ai/cpp_engine/` não usa `fast_clone()`.

## Consequências

### Positivas

- não introduz cópia especulativa no executor;
- preserva `GameState` como referência semântica de transição;
- mantém search nativo separado da referência Python;
- permite fechar A.1 sem transformar `legal_actions()` num segundo `make_action()`.

### Negativas / custos

- algumas validações de transição terão de ser reorganizadas para ocorrerem antes de `gerar_notacao()`, `last_move` e mutações;
- o contrato continua a distinguir claramente ação enumerada de ação efetivamente executável.

## Como validar

- testes de legal/illegal para MOVE, ATTACK, STUN, SPAWN e SPELL;
- regressões para special spells e STUN legacy;
- testes que comparem todos os campos observáveis antes/depois de rejeições;
- differential relevante quando a alteração atravessar rules → action generation → transition;
- ausência de `fast_clone()` no executor e no código C++ da Ares.

## Quando rever

Rever apenas se `GameState` deixar de ser a autoridade semântica de transição ou se surgir um contrato explícito e provado para um backend nativo de make/unmake. Mesmo nessa situação, `fast_clone()` não deve voltar a ser o mecanismo de preflight do executor.
