# RedWar — Ares Balance Baseline 1.0-Lite

## Status

**Frozen operational baseline: StockWar-Iniciante (100,000 nodes).**

The selection is frozen for 1.0-Lite Balance Lab work. This is an operational/reproducibility decision, not a competitive-strength claim and not a declaration that the roster is balanced.

## Frozen selection record

The final controlled experiment was run by GitHub Actions run `35415022596` from `main` at source SHA `bf9955c26db58cf08c39f939f96317ed4a7be7c1`.

| Provenance | Value |
|---|---|
| Rules version | `8610c07c19b078cc73393880d034fd1780e773b0` |
| Engine SHA-256 | `8f5799e646af7f0917e6e29afc9a24d764f7498609668215ba8c0c46ef482bcc` |
| Compiler | `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` |
| Controlled main games | 16 per candidate / 48 total |
| Colour pairing | 8 white + 8 black per candidate |
| Main-game seeds | `101, 211, 307, 401, 503, 601, 709, 809` |
| Replay checks | 1 per candidate / 3 total |
| Intervention | none |

All three candidates completed 16/16 valid main games, with every main game terminating as `game_over`; no invalid actions, timeout/failure records, or unresolved hangs occurred. All three replay checks reproduced the complete action digest exactly.

| Candidate | Nodes | Main-game elapsed | Reliability result |
|---|---:|---:|---|
| StockWar-Iniciante | 100,000 | 282.75 s | passed |
| StockWar-Intermedio | 500,000 | 1,197.43 s | passed |
| StockWar-Avancado | 1,000,000 | 1,983.84 s | passed |

**Frozen baseline:** `StockWar-Iniciante` at **100,000 nodes**. The other two candidates were not rejected for correctness or determinism; they passed the same reliability boundary but required substantially more execution time for the same controlled schedule. The selection therefore freezes the lowest-cost candidate that demonstrated the required operational/reproducibility behaviour. This decision must not be interpreted as a strength ranking.

The evidence artifact is `redwar-lite-ares-baseline-selection-35415022596` (artifact `10576413639`).

## Separation of responsibilities

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

`tools/analytics/trainer.py` is also **not** a Balance Baseline source. Its telemetry deliberately mixes `BotAleatorio` with 1k/5k/10k training bots and generates random drafts. This is useful diagnostic/training infrastructure, but it does not define one fixed Ares policy, one fixed skill context, or one controlled draft population for Lite balance evidence.

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

The 1.0-Lite baseline phase is now complete. The project can point to:

- one exact Ares profile/policy selected for baseline experiments;
- exact engine/rules/search/evaluation identity;
- reproducible seed protocol;
- frozen draft/opening/population definition;
- provenance-valid game-record schema;
- deterministic replay/termination expectations for representative runs;
- explicit calibration/hold-out split where first-player or balance tuning is involved.

Balance evidence may now be collected under this frozen context. This freeze does not close or replace competitive Ares #372.
