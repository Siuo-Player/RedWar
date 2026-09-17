# RedWar — Ares Balance Baseline 1.0-Lite

## Status

**Draft contract — not yet frozen for balance decisions.**

This document defines what must be frozen before 1.0-Lite hero/economy tuning is treated as controlled Balance Lab evidence. It does not declare Ares competitively validated and does not replace #372.

## Separation of responsibilities

```text
Ares Balance Baseline
    = reproducible execution agent/configuration

Balance Lab
    = contextual evidence + intervention + hold-out + design decision

Competitive Ares #372
    = strength / correctness / efficiency research
```

Ares is an experimental agent inside the Balance Lab; the baseline itself is not a balance certificate.

## Current code facts

The current `ai/bot.py` defines these player-facing C++ Ares profiles:

| Profile | Node budget |
|---|---:|
| StockWar Iniciante | 100,000 |
| StockWar Intermédio | 500,000 |
| StockWar Avançado | 1,000,000 |

`BotAleatorio` is deliberately not a Balance Baseline candidate because it is stochastic and does not represent the Ares policy used for controlled strength/economy evidence.

The deterministic search benchmark in `ai/BENCHMARK_SCENARIO.md` uses 150,000 nodes for performance comparison. That benchmark is a **performance/correctness instrument**, not the balance baseline.

## What must be frozen

A balance run is only baseline-valid when its provenance records all fields applicable to the experiment:

```text
repository / source SHA
engine binary identity
ruleset / game-rules version
search implementation
search budget and time controls
search/evaluation mode
selected difficulty / Ares policy
random seed and seed derivation
opening / draft / population definition
hero roster and costs
initiative / colour assignment
termination rules
record schema / provenance version
```

The exact configuration must be recorded with the produced game data, not inferred later from mutable defaults.

## Baseline selection rule

The repository currently exposes multiple Ares difficulty budgets, but **no difficulty is promoted to the canonical Balance Baseline merely because it exists or because `auto_pricer.py` uses/assumes it**.

Before the first Lite balance intervention, one exact Ares policy/profile must be explicitly selected and frozen with the fields above. Mixing 100k, 500k and 1M games inside one baseline is invalid unless the analysis explicitly models policy/skill as a context dimension.

A later Ares change does not silently replace the baseline. It starts a new baseline identity and any balance evidence dependent on the old agent must be revalidated where applicable.

## Evidence rules

Balance analysis must preserve the contextual dimensions available to the experiment:

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

`hero → global win rate` is only a marginal summary and is not sufficient authority for a balance intervention.

The reference flow is:

```text
freeze baseline
→ matched games / seeds / colours
→ selection + provenance audit
→ contextual matchup / composition / counter analysis
→ candidate intervention
→ independent hold-out
→ manual/design decision
```

Colour/first-player calibration must remain separate from its hold-out confirmation.

## Intervention hierarchy

Hero price is the normal first intervention and uses integer costs with coarse-to-fine search.

```text
Tier 0 — integer cost
Tier 1 — one existing mechanic parameter
Tier 2 — mechanic-local redesign
Tier 3 — new/replacement mechanic
Tier 4 — roster/game-rule/systemic change
```

Escalation is justified only by evidence that the lower tier cannot repair the observed defect without introducing a worse contextual/system effect.

## Auto-Pricer policy

`tools/balance/auto_pricer.py` remains available as diagnostic/legacy tooling. It may help expose telemetry or generate hypotheses, but it is **not** an authoritative balance algorithm and cannot, by itself, justify a price, mechanic, roster, or rules change.

## Freeze checklist

Before closing the baseline phase for 1.0-Lite, the project must be able to point to:

- one exact Ares profile/policy selected for baseline experiments;
- exact engine/rules/search/evaluation identity;
- reproducible seed protocol;
- frozen draft/opening/population definition;
- provenance-valid game-record schema;
- deterministic replay/termination expectations for representative runs;
- explicit calibration/hold-out split where first-player or balance tuning is involved.

Until that checklist is complete, balance results are exploratory and must not be presented as a frozen Lite Balance Baseline.
