# RedWar — Project Reasoning Spine

**Estado:** operacional  
**Baseline verificado:** `main` @ `73cf14bc0861bd3d6fdb4a437fe9f433b7322a07`  
**Data:** 2026-09-08

Este é o **eixo de raciocínio transversal** do RedWar. Não substitui documentos de domínio: explica a ordem em que eles devem ser usados para tomar decisões e impede que uma tarefa futura salte diretamente de uma ideia para uma implementação sem atravessar as evidências necessárias.

## 1. Hierarquia que não pode ser confundida

Para saber **o que o sistema faz**, usar primeiro:

```text
implementação atual + testes executáveis
```

Para saber **qual é o contrato que o sistema pretende manter**, usar os documentos canónicos.

Para saber **por que uma decisão histórica foi tomada**, usar `DECISIONS/`.

Para saber **o que foi investigado ou proposto**, usar auditorias/research.

Para saber **o que fazer a seguir**, usar exclusivamente `ROADMAP.md`.

Um snapshot antigo nunca pode reabrir uma decisão já fechada. Uma proposta nunca pode ser tratada como implementação. Uma métrica nunca pode ser promovida a prova de força sem o protocolo de força.

## 2. A linha causal completa

Toda alteração material do RedWar deve poder ser reconstruída assim:

```text
problema / oportunidade
        ↓
contrato afetado
        ↓
evidência existente
        ↓
hipótese
        ↓
menor alteração que testa a hipótese
        ↓
teste de correção
        ↓
teste diferencial / property / benchmark
        ↓
medição independente de custo ou força, quando aplicável
        ↓
decisão: aceitar / rejeitar / continuar
        ↓
contrato canónico atualizado
        ↓
ROADMAP.md atualizado
```

Quando um passo não é necessário, isso deve ser explicitamente justificado pela natureza da alteração. Não se deve simplesmente saltá-lo por conveniência.

## 3. Dependência técnica do projeto

A dependência principal é:

```text
GAME_RULES / HERO_SYSTEM
        ↓
ação e estado canónicos
        ↓
Python reference
        ↕  differential contract
        C++ Ares hot path
        ↓
search / evaluation
        ↓
Arena / strength evidence
        ↓
balance decisions
        ↓
produto / online
```

A camada de UI/replay/telemetria é transversal:

```text
rules + state
   ↓
interaction / replay / telemetry
   ↓
observação do produto
```

Por isso **força da Ares**, **balanceamento** e **qualidade do produto** são problemas diferentes, embora partilhem estado e evidência.

## 4. Estado atual que limita a próxima fase

A fundação A0 está fechada como gate histórico, mas o projeto está no **A0.1 Semantic Closure** para resolver os últimos limites de autoridade semântica antes de reabrir tuning de força.

### Fechado

- geração de ações especiais: coberta por contrato explícito;
- fronteira canónica `GameAction`: consolidada nos consumidores principais;
- normalização na entrada de `execute_action()`;
- terminal differential: agora observa o `alpha_beta()` nativo real;
- repetição Python: observação idempotente;
- código FrostMage morto removido depois de cobertura;
- fixed node budget: contractualmente testado.

### Ainda aberto

- legalidade deve ser rejeitada **antes da mutação** por uma autoridade de execução única;
- Python e C++ ainda não possuem uma história de repetição nativa equivalente definida como contrato;
- a matriz differential deve continuar a crescer para cada nova fronteira semântica, especialmente quando uma mudança tocar vários estados persistentes.

Estas pendências são de correção/arquitetura. Não devem ser mascaradas por ganhos de benchmark.

## 5. Regra Ares

Ares deve ser melhorada nesta ordem:

```text
semantic correctness
    ↓
search capability
    ↓
search efficiency
    ↓
evaluation quality
    ↓
competitive strength
```

A ordem não significa que todos os níveis sejam estritamente sequenciais para sempre; significa que **uma alegação de nível superior não pode apagar uma dúvida de nível inferior**.

Exemplos:

- NPS maior sem equivalência semântica = não é progresso aceite.
- benchmark táctico melhor = capability evidence, não força global.
- loss NNUE menor = não é força global.
- maior Elo numa amostra dependente = não prova calibração geral.

## 6. Regra de evidência por afirmação

| Afirmação | Evidência mínima |
|---|---|
| “a regra funciona” | teste de transição + regressão |
| “Python e C++ concordam” | differential após cada estado relevante |
| “a pesquisa encontra X” | benchmark táctico determinístico |
| “ficou mais rápido” | benchmark controlado de custo/NPS |
| “ficou mais forte” | Arena A/B + conjunto protegido + incerteza adequada |
| “o roster está melhor balanceado” | análise contextual + validação independente |
| “a UX melhorou” | testes de interação + validação visual/uso |

## 7. Como usar os documentos

### Para regras

Começar em `GAME_RULES.md` e `HERO_SYSTEM.md`. Se houver divergência, confrontar a implementação e os testes; depois abrir uma decisão caso o contrato precise realmente de mudar.

### Para arquitetura

Usar `ARCHITECTURE.md`, `MECHANICS_TRACEABILITY_MATRIX.md` e este documento. A matriz não prova tudo sozinha; mostra onde a prova ainda tem de existir.

### Para Ares

Usar `AI_ENGINE.md` + `AI_BENCHMARK_PROTOCOL.md` + `STRENGTH_EVALUATION.md`.

### Para NNUE

Usar `NNUE.md` + `AI_ENGINE.md`. A existência de hooks incrementais não equivale à sua integração; a integração só termina quando houver paridade com rescan e benchmark de custo.

### Para balanceamento

Usar `BALANCE_METHODOLOGY.md`. O Auto-Pricer é diagnóstico, não autoridade causal.

### Para UI/replay

Usar `BATTLE_UI_SIDEBAR.md`, `REPLAY_STORAGE.md` e a documentação de telemetria. Não reabrir arquitetura já implementada como se ainda fosse design exploratório.

### Para online

Usar `WEB_MULTIPLAYER.md` somente depois de existir um contrato de estado/ação suficientemente estável no núcleo.

## 8. Regra anti-ficção documental

É proibido inferir estado do projeto por frases como:

- “planeado” = implementado;
- “documentado” = provado;
- “testado” = validado para o uso final;
- “benchmark verde” = mais forte;
- “CI verde” = correção total;
- “existe no branch” = existe no `main`.

A palavra **concluído** só deve aparecer no roadmap quando a evidência indicada na própria etapa existir no baseline alvo.

## 9. Regra para novos documentos

Antes de criar um documento novo:

1. verificar `00_INDEX.md`;
2. verificar este spine;
3. verificar o documento canónico do domínio;
4. verificar `DECISIONS/`;
5. só criar novo ficheiro se o artefacto tiver responsabilidade/lifecycle próprios.

Uma nova investigação normalmente deve acabar por produzir alterações em **um documento canónico existente + ROADMAP**, não num novo ficheiro paralelo.

## 10. Critério para a próxima IA

Uma IA que continue o RedWar deve começar por:

```text
README
 → 00_INDEX
 → PROJECT_REASONING
 → CURRENT_STATE
 → ROADMAP
 → documento canónico do domínio da tarefa
 → decisão histórica relevante, se existir
 → código + testes
```

Depois de trabalhar, deve atualizar na mesma unidade:

```text
código/testes
 + documento canónico afetado
 + ROADMAP
 + decisão, se a política mudou
```

O objetivo é que a conversa deixe de ser necessária para reconstruir **por que** a próxima tarefa vem antes da seguinte.
