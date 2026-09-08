# RedWar — Balance Methodology

## Autoridade

Este documento é a metodologia canónica de balanceamento. `ROADMAP.md` define quando o tuning é autorizado; `PROJECT_REASONING.md` explica por que balanceamento depende de correctness e strength.

## Distinções fundamentais

```text
pricing heuristic
    ≠
global power estimate
    ≠
design judgement
```

O Auto-Pricer é diagnóstico. Não é oráculo causal.

## Ordem de investigação

```text
mecânica correta
→ Ares consegue explorá-la legalmente
→ efeito global/contextual
→ matchup/cor/composição
→ validade e representatividade dos dados
→ preço
→ decisão de design
```

Nunca usar alteração de preço como compensação automática para uma regra possivelmente errada.

## Contexto obrigatório

Conforme os dados disponíveis, preservar hero, opponent/matchup, composition, color, skill/engine version, budget, opening/seed, duração e condições relevantes. Intransitividade pode ser parte saudável do design.

## Desenvolvimento vs hold-out

```text
regression ≠ development ≠ protected validation
```

O hold-out não deve ser reutilizado durante tuning.

## Gate de decisão

Uma mudança material de balanceamento só avança depois de:

```text
correctness
→ controlled development evidence
→ protected validation where applicable
→ contextual analysis
→ explicit design decision
```

Consultar `BALANCE_STATE_OF_GAME_AUDIT.md` como pausa obrigatória quando a infraestrutura estiver madura; o resultado do audit deve ser documentado antes de continuar o tuning.
