# Decision: Internal Arena Elo calibration without human players

**Date:** 2026-09-12  
**Status:** Proposed architecture; implementation follows only after statistical validation.

## Context

The Arena promotion gate estimates a **relative** challenger-vs-baseline strength effect. The current binary Bradley-Terry estimator reports that effect as Elo-equivalent `delta_elo`. This is suitable for answering:

> Is the challenger demonstrably stronger than the current champion?

It is not, by itself, an absolute rating for the champion.

This distinction matters because promotion history can contain results such as:

```text
V0 = first champion
V1 vs V0 = +512 Elo
V2 vs V1 = +519 Elo
```

Blindly defining `V2 = 1031 Elo` and propagating every previous error would make the rating depend on the path through the champion chain. It also creates a second problem: an extreme matchup such as 100-0 has an infinite two-system Bradley-Terry maximum-likelihood Elo difference.

The project therefore needs two separate statistical products:

```text
Promotion strength
    challenger vs current champion
    → decision

Historical internal rating
    all retained Arena comparisons
    → relative Elo scale + uncertainty
```

The first is operational. The second is descriptive and historical.

## Decision

### 1. Use an internal, human-independent Elo scale

The first tested champion that establishes the historical series is assigned:

```text
internal Elo = 0
```

This is only an identification constraint. Adding any constant to every rating leaves every pairwise strength difference unchanged.

Later, when human players or another trusted external reference exist, the internal scale can be calibrated to the external scale. Human calibration is therefore **not a prerequisite** for maintaining a coherent internal progression.

The internal scale must never be described as an absolute measurement of human player strength until that external calibration exists.

### 2. Never construct the official historical rating by summing promotion deltas

Do **not** use:

```text
R(V1) = R(V0) + Δ(V1,V0)
R(V2) = R(V1) + Δ(V2,V1)
R(V3) = R(V2) + Δ(V3,V2)
```

and do not propagate uncertainty by adding historical error bars.

Instead, retain the raw paired results and re-estimate the historical ratings from the complete comparison graph. A direct `V0 vs V2` experiment must be allowed to influence both ratings together with the existing `V0-vs-V1` and `V1-vs-V2` observations.

This is consistent with how paired-comparison models treat competitor strengths as latent parameters estimated from a collection of comparisons, rather than as a sum along an arbitrary path.

### 3. Use a global Bradley-Terry-family model for historical rating

The target model is a global Bradley-Terry model or Bayesian/regularized extension of it, with one rating fixed to the anchor:

```text
R(first_champion) = 0
```

Conceptually:

```text
       V1
      /  \
    V0    V2
      \  /
       V3
```

Every retained Arena comparison contributes information to the same global fit.

This means that adding a new direct comparison between old versions can correct a previous chain estimate instead of creating a second cumulative rating path.

### 4. Do not expose infinite Elo from decisive separation as the official rating

The current two-system binary MLE has a known boundary behaviour:

```text
100 challenger wins, 0 baseline wins
→ p = 1
→ delta Elo = +∞
```

This is mathematically correct for the unregularized MLE, but is not a useful historical rating.

The historical rating implementation must therefore use a **finite regularized/Bayesian model** with an explicit proper prior or an equivalent finite estimator. The purpose is not to impose an arbitrary Elo cap; it is to represent correctly that an extreme result establishes direction strongly but does not identify an exact finite distance from only that matchup.

The promotion gate must remain separate from this historical model. A challenger is not rejected merely because its global rating is uncertain.

### 5. Keep the original champion as a permanent anchor, but do not force every experiment against it

The first champion remains `0 Elo` in the internal scale and remains a useful historical reference.

However, the calibration system should **not** require every new version to play a fixed number of games against that original baseline. Once versions become much stronger, those comparisons can become highly imbalanced and provide poor information about the exact rating distance.

Instead, the system should retain a comparison graph containing:

- mandatory challenger-vs-current-champion matches used by the promotion gate;
- selected historical control matchups against older versions;
- additional calibration matchups chosen when the rating uncertainty is too large or when the graph has weak connectivity.

### 6. Use adaptive calibration comparisons when more precision is needed

The number of calibration games must not be treated as a universal fixed constant.

After each calibration batch:

```text
fit rating distribution
        ↓
inspect uncertainty
        ↓
uncertainty acceptable?
   ├─ yes → calibrated
   └─ no  → select more informative comparisons
                 ↓
               Arena
```

The preferred additional opponents are versions close to the current rating estimate or versions that connect otherwise weakly connected parts of the comparison graph. Highly imbalanced matchups still provide directional evidence, but are less efficient for locating the exact latent strength.

This follows the general principle of adaptive paired-comparison design: prior information can be used to choose subsequent pairings in order to increase expected information.

### 7. Define a precision target instead of allowing uncertainty to accumulate forever

A rating is not considered fully calibrated merely because a point estimate exists.

The eventual protocol must define an explicit maximum acceptable uncertainty (for example, a configurable Elo half-width) and validate that threshold through simulation before making it authoritative.

The important rule is:

```text
uncertainty too high
→ collect more informative games
→ re-estimate globally
```

not:

```text
uncertainty too high
→ carry it into the next generation forever
```

There is no need to force every version to reach the exact same number of games. A highly informative comparison graph may require fewer games than an imbalanced one.

### 8. Use all historical games when recalculating uncertainty

Uncertainty belongs to the current fitted rating model, not to the age of the engine version or to the number of promotion steps traversed.

Therefore:

```text
old data + new data
→ one global fit
→ one uncertainty estimate per version
```

Do not compute:

```text
σ(V3) = σ(V0) + σ(V1) + σ(V2) + σ(new test)
```

This is the main protection against uncertainty “exploding” generation after generation.

## Relationship to promotion

The production gate remains local to the current champion:

```text
challenger vs champion
        ↓
paired statistical evidence
        ↓
lower_bound_elo > 0
        ↓
PROMOTE
```

The global internal rating is informational:

```text
all historical Arena data
        ↓
global rating model
        ↓
R(version) ± uncertainty
```

The two systems must not silently substitute for one another.

For example, `+9 ± 7` against the current champion has lower bound `+2` and can be a valid promotion under the current gate. It should not be rejected because a global rating interval happens to overlap the champion's interval.

## What similar systems support this design?

### Stockfish/Fishtest: fixed references, repeated testing, and explicit uncertainty

Stockfish's public Fishtest methodology separates Elo estimation from sequential acceptance testing. Fishtest uses paired/pentanomial statistics and GSPRT for sequential testing rather than treating a single Elo point estimate as the decision rule. Its historical progression tests compare development versions against a fixed Stockfish release using large repeated samples, producing an Elo estimate with an error bar.

Most importantly for RedWar, the Fishtest FAQ explicitly warns that Elo estimates of individual patches have substantial error and that summing accepted-patch Elo estimates is not an unbiased way to reconstruct total progression because passed tests are selected by their success. This is direct evidence against implementing the RedWar historical rating as a running sum of promotion deltas.

Fishtest also demonstrates the practical value of increasing the sample when precision matters: current regression/progression series use tens of thousands of games under a controlled testing protocol, rather than assuming a small fixed sample remains equally informative as the engine evolves.

### TrueSkill: explicit uncertainty and arbitrary internal scale

TrueSkill models skill as a distribution with both mean and uncertainty, rather than only a point estimate. The official Microsoft documentation also notes that the underlying calculations can start from an arbitrary numerical scale and then be rescaled. This is strong support for using an internal RedWar anchor such as `0` without pretending that the number is externally calibrated.

TrueSkill is not being adopted wholesale for the Arena gate. It is evidence for the architectural principle that uncertainty should be a first-class state of a rating system.

### Bradley-Terry and adaptive paired comparisons

Bradley-Terry is a standard model for latent strength inferred from paired comparisons. The adaptive paired-comparison literature explicitly studies how prior information can guide which pairs to compare next so that subsequent observations yield more information.

That supports RedWar's proposed separation between:

```text
fixed promotion comparison
+
adaptive historical-calibration comparisons
```

rather than repeatedly testing every new version only against the original baseline.

## Important distinction from human calibration

Without players, the system can still answer:

> “How strong is this Ares relative to the first RedWar champion and to previous Ares versions, on the fixed Arena population?”

It cannot yet answer:

> “This Ares is approximately 2200 human Elo.”

The first is an internally identified relative scale. The second needs external calibration.

When human data becomes available, the preferred approach is to fit an explicit mapping using several Ares states, rather than overwriting the historical internal ratings with one human comparison.

## Implementation constraints

This decision is documentation-first. Before production implementation, the following must be validated by deterministic simulation and real Arena data:

1. finite Bayesian/regularized Bradley-Terry estimator for extreme 100–0 results;
2. uncertainty calibration and coverage under the actual paired Arena design;
3. graph-connectivity requirements for stable ratings;
4. adaptive opponent-selection rule;
5. stopping criterion for the target uncertainty;
6. interaction with opening/seed population effects;
7. compatibility with the existing promotion gate and raw provenance.

The existing promotion gate remains unchanged by this decision.

## References

- Stockfish/Fishtest — Statistical Methods and Algorithms in Fishtest: https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html
- Stockfish/Fishtest — FAQ: https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-FAQ.html
- Stockfish — Progression / Regression Tests: https://official-stockfish.github.io/docs/stockfish-wiki/Regression-Tests.html
- Herbrich, Minka & Graepel — *TrueSkill: A Bayesian Skill Rating System*: https://www.microsoft.com/en-us/research/publication/trueskilltm-a-bayesian-skill-rating-system/
- Glickman & Jensen — *Adaptive paired comparison design*: https://doi.org/10.1016/j.jspi.2003.09.022
- Liu et al. — *Model-Based Learning from Preference Data*: https://doi.org/10.1146/annurev-statistics-031017-100213
