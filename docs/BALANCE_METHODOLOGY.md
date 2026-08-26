# RedWar — Balance Methodology

## Purpose

This document defines how RedWar should reason about balance without reducing hero value to a single raw win-rate or Auto-Pricer number.

The central distinction is:

```text
pricing heuristic
        ≠
global power estimate
        ≠
design judgement
```

Balance decisions should combine game rules, competitive evidence, context and explicit uncertainty.

## 1. What is being balanced?

A hero's draft cost is intended to approximate its **strategic value under the game's normal conditions**. That value is contextual:

```text
hero
  × composition
  × opponent
  × color
  × player/engine skill
  × tactical context
  × board state
  × rules/version
```

Therefore a balanced roster does not require every hero to have identical win-rate, and a hero with an extreme cost is not automatically incorrect.

The goal is to prevent persistent, exploitable mismatches between:

- cost;
- practical competitive value;
- strategic role;
- roster interactions.

## 2. Evidence hierarchy

Balance evidence should be interpreted in layers:

```text
rule correctness
    ↓
mechanic-specific regressions
    ↓
controlled development experiments
    ↓
protected / independent validation
    ↓
competitive games with strong Ares
    ↓
contextual balance analysis
    ↓
design decision
```

A benchmark can show that a mechanic works. An Arena can show that an Ares revision changes competitive strength. Neither alone proves that a hero's price is correct.

## 3. Auto-Pricer role

The Auto-Pricer is a **diagnostic pricing heuristic**.

It is useful for:

- identifying suspiciously expensive or cheap heroes;
- proposing coarse price adjustments;
- detecting strong directional signals in controlled data;
- prioritising which heroes deserve manual investigation.

It is not sufficient to claim causal hero power because observed outcomes can be confounded by:

- matchup;
- composition;
- color;
- player/engine strength;
- opening position;
- sample selection;
- invalid/terminated games;
- changes in the rules or Ares version.

A price suggestion should therefore record its evidence population and validity constraints.

## 4. Color and matchup

Balance analysis must explicitly preserve context that can create intransitivity:

```text
A beats B
B beats C
C beats A
```

The following slices should remain available when enough data exists:

- global hero results;
- hero × color;
- hero × opponent hero;
- hero × composition;
- hero × rules/version;
- hero × engine/revision;
- hero × budget/node regime where relevant.

A strong global result with a severe localized weakness may indicate a healthy strategic niche rather than a pricing failure.

## 5. What a balance experiment must freeze

A reproducible balance experiment should identify at least:

- rules/version;
- hero configuration/version;
- candidate prices;
- baseline prices;
- Ares versions;
- node/time budget;
- opening/seed population;
- color balancing policy;
- invalid-game policy;
- termination policy;
- dataset/evidence-set identity.

Without these controls, apparent balance changes can be implementation or sampling changes.

## 6. Development vs hold-out

Balance experiments follow the same evidence separation as Ares strength evaluation:

```text
regression
    ≠
development
    ≠
hold-out
```

Development data can guide a price change. Hold-out data must remain protected from repeated tuning.

A balance change that wins on development evidence but fails on protected evidence should be treated as **unconfirmed or negative evidence**, not as automatic success.

## 7. Hero-level investigation

When a hero appears mispriced, investigate in this order:

1. verify that the underlying mechanic is correct;
2. verify that the Ares can exploit the mechanic legally;
3. check whether the effect is global or contextual;
4. check color and matchup asymmetries;
5. check composition effects;
6. check whether the observed sample is valid and representative;
7. only then change price;
8. if the required price is extreme, reconsider the mechanic itself.

This prevents the cost from becoming a permanent compensation mechanism for a broken rule.

## 8. Roster-level analysis

Once the evidence population is sufficiently large, move beyond isolated hero pricing.

Useful questions include:

- Which heroes are strategically redundant?
- Which combinations create dominant regions of the roster?
- Which heroes form meaningful counter-cycles?
- Which tactical roles are missing?
- Which heroes are only viable because of one narrow matchup?
- Does the price ladder create degenerate draft incentives?

Future tools may include matrix factorisation, trade-off analysis, embeddings or Quality-Diversity methods, but these are **analysis tools**, not substitutes for the evidence contract.

## 9. Design judgement

The designer may intentionally retain asymmetry or a non-50/50 local matchup.

Balance is therefore not defined as:

```text
win-rate = 50%
```

A decision should instead consider:

```text
competitive evidence
+ strategic role
+ counterplay
+ roster diversity
+ cost efficiency
+ game-health implications
```

Any deliberate exception should be recorded as a decision rather than silently embedded in a price.

## 10. Required output of a pricing experiment

A reproducible pricing experiment should produce:

```text
experiment id
rules/version
hero configuration/version
baseline prices
candidate prices
evidence-set identity
Ares identities
budget
colour/opening/seed policy
valid-game counts
summary statistics
contextual slices
uncertainty
final decision
```

The raw games remain the source data. Summaries are derived artifacts.

## 11. Promotion policy

No automatic promotion should occur solely because:

- a hero gained raw win-rate;
- the Auto-Pricer suggested a lower/higher cost;
- one matchup improved;
- one benchmark improved;
- a single Arena batch was favourable.

A material balance change should survive:

```text
correctness
→ controlled development evidence
→ protected validation where applicable
→ contextual analysis
→ documented decision
```

## 12. Relationship to Strength Evaluation

Strength Evaluation asks:

> Did Ares become stronger?

Balance asks:

> Given a sufficiently strong and controlled evaluator, does the roster/cost system produce a healthy strategic distribution?

These questions are related but not interchangeable.

The Ares strength framework is canonical in `STRENGTH_EVALUATION.md`.
The Arena statistical framework is canonical in `ARENA_STATISTICAL_METHODOLOGY.md`.
This document is the canonical methodology for interpreting those results for balancing decisions.

## 13. Current limitations

The project is not yet ready for a fully automated causal balance optimiser.

Known limitations include:

- limited population of controlled games;
- contextual/intransitive matchups;
- player-skill effects;
- evolving Ares strength;
- incomplete long-horizon roster analysis;
- evolving game-rule semantics.

The correct response is to improve evidence quality, not to hide these uncertainties behind a single score.
