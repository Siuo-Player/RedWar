# RedWar — Hero System

## Autoridade

Os dados estruturais dos heróis pertencem a `engine/heroes_config.json` e ao schema associado. A implementação pode conter código especializado enquanto o schema não representar uma mecânica de forma suficiente.

A regra transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md). Mudanças de mecânicas seguem [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md).

## Ações

A camada canónica de ações distingue `MOVE`, `ATTACK`, `STUN`, `SPAWN` e `SPELL`. Uma ofensiva implementada como spell não deve ser artificialmente duplicada como `ATTACK`.

PR #291 consolidou a análise Python sobre todo o espaço de ação canónico.

## Casos especiais já validados

- Inquisitor: apenas um Inquisitor capaz de agir aplica a condição de silêncio prevista; a exceção para Inquisitor atordoado é explicitamente testada.
- FrostMage: `NEVADA` é uma spell; o código morto que sugeria um segundo mecanismo de STUN foi removido em #300 depois de existir cobertura para o comportamento ativo.
- Special spells: a paridade de legalidade foi explicitamente coberta em #303.

## Estado data-driven

O sistema continua **híbrido**. A configuração é fonte dos dados e vocabulary, mas ainda existem comportamentos especializados em código. A redução desse hardcoding é uma refatoração futura, não uma condição para fingir que o sistema já é totalmente declarativo.

## Regra para nova mecânica

Uma nova mecânica só entra no contrato como concluída quando passa a cadeia da matriz: configuração/schema quando aplicável → Python → C++ → ações → transição → RWEN → make/unmake → hash → differential → regressão → benchmark quando altera capacidade de search.
