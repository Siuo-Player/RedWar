# Ares — Classical Evaluation Baseline

**Governing issue:** #411  
**Parent:** #406 → #372  
**Baseline:** `main` after Gameplay #371 closure and terminal hardening #405

## Purpose

Congelar a avaliação clássica atual como referência experimental antes de alterar pesos, termos ou substituir o evaluator por NNUE.

Esta referência serve para comparação controlada. Não constitui alegação de balanceamento perfeito nem de strength global.

## Current implementation

`ai/cpp_engine/evaluate.cpp` calcula uma avaliação clássica quando NNUE não fornece uma pontuação válida.

A cadeia é:

```text
piece state
→ base piece cost
→ lifespan scaling
→ positional bonus/PST
→ stun adjustment
→ material_score
→ FrostMage tactical pressure
→ TWC bias
```

### 1. Base material

O valor inicial de uma peça vem de `PIECE_COSTS` quando o id é conhecido; caso contrário usa o custo da própria peça e, como fallback defensivo, `50`.

Os valores são limitados a um intervalo seguro antes da aritmética adicional.

### 2. Lifespan

Para peças temporárias (`lifespan != 999`), o valor é escalado por:

```text
base_value × lifespan / 5
```

com limites defensivos para o lifespan e para o resultado.

### 3. Positional bonus

O evaluator possui PSTs específicas para:

- Ghoul;
- Sentry;
- FrostMage;
- Lich;
- BoneLord;
- Phantom.

As peças restantes não recebem atualmente um PST específico e ficam com bônus posicional zero.

A orientação das PSTs considera a perspetiva da equipa.

### 4. Stun

Uma peça atordoada tem o valor base e o bônus posicional reduzidos para 40%.

Além disso, o seu custo produz um termo de ameaça equivalente a metade do custo. O sinal desse termo é orientado para representar a vantagem de explorar a peça atordoada.

### 5. FrostMage pressure

Existe um termo específico de pressão do FrostMage. Para cada alvo inimigo dentro do raio de pressão Manhattan <= 4:

- alvo já atordoado: contribuição de 50% do custo;
- alvo não atordoado: contribuição de 10% do custo, com mínimo 1.

A pressão total é limitada por FrostMage e agregada com sinal segundo a equipa.

### 6. TWC

Após `material_score + FrostMage pressure`:

- score positivo perde `twc`;
- score negativo ganha `twc` em magnitude;
- score zero permanece zero.

Isto codifica urgência crescente à medida que se aproxima o limite de 50 turnos sem captura.

### 7. Terminal states

A avaliação retorna imediatamente scores próximos de ±`INFINITO` quando um dos lados tem zero peças.

O limite TWC é tratado separadamente no search com o desempate material correspondente.

## Experimental baseline contract

Para qualquer futura alteração de evaluation:

```text
same position
+ same side-to-move
+ same TWC/effects/timers
+ same search budget
→ compare old evaluator vs candidate
```

Registar no mínimo:

- commit do baseline;
- hash/configuração do corpus;
- distribuição de posições;
- score antigo e novo por posição;
- termo alterado;
- magnitude da alteração;
- efeito em capability;
- efeito em matched-budget search;
- eventual evidência Arena independente.

## Data separation

O corpus usado para escolher ou ajustar uma alteração de evaluator não deve ser tratado automaticamente como hold-out para provar strength dessa mesma alteração.

```text
tuning corpus
≠
hold-out corpus
≠
Arena strength sample
```

## Promotion rule

Não promover uma alteração porque:

- aumenta uma pontuação local;
- melhora um puzzle isolado;
- aumenta NPS;
- reduz training loss;
- produz scores que “parecem mais corretos”.

A promoção requer regressões de correctness e, quando houver alegação competitiva, avaliação independente segundo o protocolo Arena.

## Scope boundary

Este documento não muda a implementação do evaluator. É a referência para experiências futuras e mantém a avaliação clássica como baseline explícito enquanto NNUE continua opcional.
