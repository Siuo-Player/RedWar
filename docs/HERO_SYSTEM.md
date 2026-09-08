# RedWar — Hero System

## Autoridade

Os dados estruturais dos heróis pertencem a `engine/heroes_config.json` e ao schema associado. A implementação pode conter código especializado enquanto o schema não representar uma mecânica de forma suficiente.

A regra transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md). Mudanças de mecânicas seguem [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md).

## Ações

A camada canónica de ações distingue `MOVE`, `ATTACK`, `STUN`, `SPAWN` e `SPELL`. Uma ofensiva implementada como spell não deve ser artificialmente duplicada como `ATTACK`.

PR #291 consolidou a análise Python sobre o espaço de ação canónico; #306 tornou a fronteira explícita e #308 normaliza `execute_action()` através dela. PR #321 acrescentou `resolve_legal_action()` como seam de resolução canónica/legacy. **Isto não prova ainda que qualquer ação estruturalmente válida seja rejeitada por membership antes da mutação:** esse bloco continua aberto porque #317 documenta a diferença entre action-space e transition validation; #309/#315 não foram merged.

## Casos especiais já validados

- **Inquisitor:** a condição de silêncio e a exceção de Inquisitor atordoado têm regressão explícita em #292.
- **FrostMage:** `NEVADA` é `SPELL`; o código morto que sugeria um segundo mecanismo de STUN foi removido em #300 depois de cobertura para o comportamento ativo.
- **Special spells:** a paridade de legalidade é coberta em #303 para as ações especiais declaradas no contrato desse PR.

## Estado data-driven

O sistema continua **híbrido**. A configuração é fonte dos dados e vocabulary, mas ainda existem comportamentos especializados em código. A redução desse hardcoding é trabalho futuro, não evidência de que o sistema já seja totalmente declarativo.

## Níveis de evidência

Para evitar sobreinterpretação:

```text
DOCUMENTED
≠
IMPLEMENTED
≠
TESTED
≠
VALIDATED
≠
PROVEN para qualquer estado possível
```

As regressões de ações especiais provam os casos e condições que exercitam; não constituem por si só prova de semantic closure universal.

## Regra para nova mecânica

Uma nova mecânica só entra no contrato como concluída quando passa a cadeia relevante da matriz: configuração/schema quando aplicável → Python → C++ → ações → transição → RWEN → make/unmake → hash → differential → regressão → benchmark quando altera capacidade de search.
