# RedWar — Balance Methodology

## Autoridade

Este documento é a metodologia canónica de balanceamento. `ROADMAP.md` define quando o tuning é autorizado; `docs/ARES_BALANCE_BASELINE_1_0_LITE.md` define o contrato do agente congelado para o caminho 1.0-Lite; `PROJECT_REASONING.md` explica por que balanceamento depende de correctness e strength.

Ares é um **agente dentro do Balance Lab**. Ares não é o Balance Lab e uma melhoria de força da Ares não prova que o roster esteja equilibrado.

## Distinções fundamentais

```text
Ares strength
    ≠
global hero power
    ≠
player-perceived balance
    ≠
design judgement
```

O Auto-Pricer é diagnóstico/legado. Não é oráculo causal nem autoridade de balanceamento.

## Contexto obrigatório

Conforme os dados disponíveis, preservar:

```text
hero
× position
× allied composition
× opponent / matchup
× initiative / colour
× ruleset
× seed
× Ares policy / player-skill context
× outcome / terminal reason
```

`hero → global win rate` é apenas uma marginalização grosseira e não é suficiente para decidir tuning.

## Ordem de investigação

```text
mecânica correta
→ Ares consegue explorá-la legalmente
→ baseline/control conditions frozen
→ matched games / seed / colour
→ selection + provenance audit
→ contextual matchup / composition / counter analysis
→ candidate intervention
→ protected hold-out
→ explicit design decision
```

Nunca usar alteração de preço como compensação automática para uma regra possivelmente errada.

## Desenvolvimento vs hold-out

```text
regression ≠ development ≠ calibration ≠ protected validation
```

Amostras usadas para escolher uma compensação, preço ou mecânica não podem também ser tratadas como confirmação independente da mesma decisão.

Para cor/primeiro jogador, calibração e hold-out devem ser separados, com condições emparelhadas e múltiplas seeds/configurações quando aplicável.

## Hierarquia de intervenção

Para preço, a intervenção normal começa em **custos inteiros** e usa procura coarse-to-fine. Quando o custo não resolve o defeito estratégico, escala-se para a menor alteração de mecânica suportada pela evidência, evitando mudanças sistémicas prematuras.

## Gate de decisão

Uma mudança material de balanceamento só avança depois de:

```text
correctness
→ controlled development evidence
→ contextual analysis
→ protected validation where applicable
→ explicit design decision
```

Consultar `BALANCE_STATE_OF_GAME_AUDIT.md` como pausa obrigatória quando a infraestrutura estiver madura; o resultado do audit deve ser documentado antes de continuar o tuning.

## 1.0-Lite

O 1.0-Lite usa um **Ares Balance Baseline congelado** apenas para tornar experimentos controlados reprodutíveis. O baseline não é um certificado de balanceamento global, não substitui o gate competitivo #372 e não autoriza `auto_pricer.py` a alterar o jogo automaticamente.
