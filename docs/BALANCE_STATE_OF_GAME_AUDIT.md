# RedWar — Balance State-of-the-Game Audit

This document defines the mandatory analysis gate that follows sufficiently mature balance instrumentation and relevant game-data evidence. It is a decision pause, not another automatic tuning loop.

## Purpose

Once the balance system can reliably analyze the roster and a sufficiently broad, valid evidence population exists, RedWar should stop iterative balancing and produce one consolidated state-of-the-game report.

The report must cover:

- draft-cost fit;
- contextual Ares value;
- matchup structure;
- composition/synergy structure;
- tactical breakpoints;
- counterplay;
- roster feature-space coverage;
- cost-band distribution;
- player/game-health telemetry where available;
- data quality and uncertainty.

After the report is generated, the process stops for an explicit manual or explicitly authorized automatic balance decision.

## Entry gate

Run this audit only when:

1. the underlying Ares correctness/evidence gate is sufficiently trusted for the intended analysis;
2. valid-game provenance is enforced;
3. development and protected evidence are separated;
4. draft-cost estimation works across the current draftable roster;
5. contextual value tooling can inspect positions, phases, allies, enemies and tactical states;
6. matchup/composition data have sufficient coverage to support the intended slices.

Do not use a single arbitrary global game count as the sole entry criterion. Coverage and uncertainty must be reported per hero and per slice.

### Minimum evidence-coverage gate

The following are the default **engineering thresholds** for a full state-of-the-game audit. They are deliberately explicit so that an audit cannot be declared mature merely because the total number of games looks large.

```text
For every draftable hero:
    >= 200 valid hero exposures

For every draftable hero and colour:
    >= 75 valid exposures per colour

For every draftable hero:
    >= 4 distinct opponent heroes represented

For any pairwise hero-vs-hero conclusion:
    >= 50 valid games in that matchup cell

For contextual Ares value analysis:
    >= 500 sampled valid states per hero
    and >= 5 context strata represented per hero
```

These thresholds are **coverage gates, not claims of universal statistical sufficiency**. They may be tightened or relaxed when a later validation study demonstrates a better operating point.

A hero or slice below a threshold must be explicitly marked `INSUFFICIENT EVIDENCE` or `SPARSE SLICE`; it must not be silently pooled away.

The contextual sample should be stratified rather than drawn as a naive uniform sample over all replay states. At minimum, the sampling plan should attempt coverage across relevant combinations of:

- game phase;
- board density;
- position/deployment region;
- legal-action-set size/type;
- ally composition;
- enemy composition;
- tactical threat level;
- initiative/side to move;
- persistence/control state where applicable.

A state can contribute to multiple diagnostic dimensions, but the report must expose the achieved coverage so that abundant trivial positions cannot dominate the estimate.

### When thresholds are not met

Do not auto-balance merely to compensate for sparse evidence.

Instead:

```text
insufficient coverage
    -> collect more representative evidence
    -> preserve the protected hold-out
    -> rerun the audit gate
```

A sparse matchup matrix is acceptable for the audit to run, provided the missing cells are explicitly reported and no unsupported pairwise conclusion is drawn from them.

## Draft-cost rules

The draft resource is defined as a fixed **5–200** range and is spent only before the game.

A hero's draft cost does not dynamically change during a match.

During the match, Ares may and should assign a **contextual value** to the same piece based on the current state. Contextual value is an evaluation/search signal, not a modified draft price.

The explicit automatic-balance urgency rules are:

```text
estimated fair cost < 5
    → URGENT BALANCE

estimated fair cost > 200
    → URGENT BALANCE
```

These cases mean the estimated strategic value cannot be represented inside the legal draft-cost domain.

For estimates inside 5–200, the default diagnostic tolerance is:

```text
max(10% of estimated value, 5 points)
```

A current cost outside this band is suspiciously mispriced and requires investigation, but is not by itself an automatic balance action.

## Valor contextual da Ares

At runtime, estimate the value of a piece from the state rather than from its draft cost alone.

Relevant dimensions include:

- current position;
- movement/reachability;
- attack geometry;
- legal actions now available;
- threatened squares;
- control effects;
- area influence;
- board-altering effects;
- allies and their compatibility;
- enemies and their vulnerabilities/counters;
- current tactical phase;
- alternative actions available to the same side.

Do not introduce a universal damage, HP/life or attack-cooldown abstraction. RedWar has no damage/life system and attacks have no general cooldown. Stun, death, control and persistence remain distinct mechanics.

## Feature-space / roster geometry

Each draftable hero should be represented in a standardized feature vector built only from mechanics that actually exist in RedWar.

First-pass dimensions should include:

```text
mobility
attack geometry/reach
area influence
control
utility
board alteration
action economy
positional dependence
restrictions
persistent-effect capability
```

For analysis/visualization:

1. standardize numeric features;
2. use PCA to obtain a 2-D diagnostic projection;
3. test clustering with `k = 3..6`;
4. use silhouette score as one quantitative guide, then apply interpretability and minimum-cluster-size checks;
5. overlay current draft cost and major strategic-role labels.

Use the resulting plot to identify:

- sparse strategic regions;
- redundant clusters;
- isolated heroes;
- cost outliers inside otherwise similar clusters;
- potentially missing strategic archetypes.

A sparse region is a design hypothesis, not automatic proof that a new hero/class is required.

## Matchup analysis

Build a valid hero-vs-hero matrix and relevant hero-vs-composition slices.

Report:

- sample size;
- uncertainty;
- global results;
- pairwise asymmetries;
- strong counters;
- weak counters;
- counter cycles.

A local win-rate far from 50/50 is not automatically a balance failure when it forms part of a meaningful counter structure.

Pairwise cells below 50 valid games remain visible in the matrix but are not eligible for a strong pairwise balance conclusion.

## Synergy and anti-abuse rule

Strategic synergy is desirable because the draft should reward players for constructing combinations and thinking ahead.

The balance objective is not to eliminate synergy. It is to prevent synergy from becoming an unreasonably efficient, effectively unanswerable package.

The first diagnostic ceiling for an intrinsic synergy premium is **+15%** over the standalone combined value. Exceeding it is a review trigger, not an automatic rejection.

A high-impact package should have at least one meaningful counter whose relevant draft cost is less than or equal to the dominant package cost. The counter may be a rock-paper-scissors relationship rather than a universally superior hero.

This rule is intentionally about strategic answerability, not forced global 50/50 matchups.

## Breakpoint analysis

Search for discrete tactical thresholds where a small mechanical difference creates a large state-space consequence.

Examples:

- reaching a new area of the board;
- enabling a new attack pattern;
- affecting an additional target;
- changing whether a control effect creates a terminal tactical sequence;
- changing the number of viable responses;
- changing persistence/lifespan availability.

Breakpoints must be derived from actual RedWar mechanics. Do not use a generic damage-per-point model.

## Draft efficiency

Report:

```text
estimated strategic value / current draft cost
```

as a diagnostic.

Do not optimize the roster solely for this ratio: cheap specialized counters may intentionally have high efficiency in their niche.

## Game-health analysis

When enough reliable telemetry exists, inspect:

- game length;
- meaningful choices per turn;
- repeated action patterns;
- control/stun frequency;
- comeback frequency;
- stalemate/blocked-state frequency;
- first-player advantage;
- one-sided game frequency.

These metrics are not direct cost inputs in the first model. They identify possible systemic problems that may require design changes rather than price changes.

## Data-quality report

Every state-of-the-game audit must expose:

- total games;
- valid games;
- invalid games and provenance;
- hero exposure;
- matchup coverage;
- composition coverage;
- colour coverage;
- opening/seed coverage;
- Ares/version/config identity;
- development/hold-out designation;
- uncertainty and sparse slices;
- achieved evidence-coverage thresholds and any gate failures.

## Output classification

Each hero/interaction should receive one or more of:

```text
BALANCED / NO ACTION
LIKELY UNDERPRICED
LIKELY OVERPRICED
URGENT UNDER DOMAIN
URGENT OVER DOMAIN
CONTEXT DEPENDENT
SYNERGY RISK
COUNTERPLAY RISK
INSUFFICIENT EVIDENCE
STRUCTURAL ROSTER GAP
```

## Mandatory stop

After this report is complete, stop balance iteration.

The next operation must be explicitly selected as:

```text
manual adjustments
or
explicitly authorized automatic adjustments
or
collect more evidence
```

The report itself must not automatically become the training/development set for another immediate tuning pass.

This prevents self-reinforcing balance loops and protects hold-out evidence from repeated adaptation.
