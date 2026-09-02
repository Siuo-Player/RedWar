# RedWar — Balance Feature Schema

This document defines the first reproducible feature schema for roster geometry and contextual balance analysis.

The objective is to make hero-space analysis deterministic and comparable across tools. A feature is valid only when it can be derived from canonical RedWar rules/configuration or from explicitly identified game-state evidence.

## Principles

1. Do not invent mechanics that do not exist in RedWar.
2. Do not encode draft cost as an intrinsic mechanic feature. Cost is an outcome/diagnostic overlay.
3. Do not use damage, HP/life or a generic attack-cooldown abstraction. These are not universal RedWar mechanics.
4. Separate static mechanical features from observed contextual features.
5. Keep raw features and normalized features. Never discard the raw measurement.
6. Every feature must have a provenance key identifying its source and rules/config identity.
7. Missing observations are distinct from zero capability.

## Feature layers

The analysis should maintain two related vectors.

```text
DESIGN VECTOR
    derived from the hero definition/rules only

GAMEPLAY VECTOR
    derived from valid replay/state evidence
```

The design vector describes what a hero can do. The gameplay vector describes what that capability actually becomes in representative positions and match contexts.

Neither vector is the final draft cost.

## Design-vector schema

The initial schema is intentionally compact. Each dimension should be represented as a numeric value in raw form, with normalization performed downstream.

### Mobility

Measure movement capability from the canonical legal-move generator, not from description text.

Recommended raw fields:

```text
mobility.max_reachable_squares_open_board
mobility.max_step_distance
mobility.geometry_cardinality
mobility.ignores_occupancy
mobility.special_jump_capability
mobility.directional_restriction
```

`geometry_cardinality` is the number of distinct legal displacement vectors on an empty board from a representative central square, excluding board-edge truncation where possible.

### Attack geometry / reach

Derive from the canonical attack/action generator.

```text
attack.max_reachable_targets_open_board
attack.geometry_cardinality
attack.max_distance
attack.ray_capability
attack.minimum_distance
attack.requires_line_of_sight
attack.ignores_occupancy
attack.pattern_target_count
```

When an attack is not available, use numeric zero for capability counts and a separate presence flag where zero could otherwise be ambiguous.

### Area influence

Area influence measures the spatial footprint an action can affect without pretending all targets have equal value.

```text
area.max_cells_affected
area.max_target_slots
area.max_manhattan_radius
area.shape_count
area.can_affect_multiple_enemies
area.can_modify_multiple_cells
```

The first implementation should use legal action geometry and board effects. It must not infer “damage per cell”.

### Control

Control is represented by actual RedWar control mechanics.

```text
control.stun
control.spell_disable
control.position_swap
control.mobility_denial
control.other_rules_defined_control_count
control.max_control_footprint
control.max_control_persistence
```

A control flag is zero when the hero does not possess that mechanic. Persistence is measured in canonical turns/states where the rules define it.

### Utility

Utility captures non-damage, non-movement support capabilities.

```text
utility.purify
utility.summon
utility.spawn_on_kill
utility.reflection
utility.swap
utility.other_rule_defined_utility_count
```

Each boolean mechanic may later become a dedicated sparse feature when enough heroes exist to justify it.

### Board alteration

```text
board.alters_terrain
board.creates_ice
board.creates_barricade
board.creates_fire
board.removes_or_purifies_effects
board.spawns_units
board.max_persistent_board_effects
```

The schema records the actual effect, not a subjective strength score.

### Action economy

Action economy concerns how many distinct legal choices the hero can create and how many game-state changes can be triggered by one selected action.

```text
action.action_type_count
action.spell_count
action.max_distinct_legal_action_families
action.max_effect_fanout
action.can_trigger_secondary_effect
action.can_generate_new_unit
```

This is a structural feature. Observed choice quality belongs in the gameplay vector.

### Positional dependence

This must not be guessed from the hero name or role.

First implementation should estimate it from controlled open-board sampling:

```text
positional.mobility_variance
positional.attack_variance
positional.legal_action_count_variance
positional.effect_footprint_variance
```

Variance must be normalized by the corresponding mean or by a bounded reference when appropriate. Report the exact estimator in the generated artifact.

### Restrictions

Restrictions are mechanics that reduce availability or make capability conditional.

```text
restriction.min_attack_distance
restriction.directional_dependency
restriction.cooldown_count
restriction.requires_target_pattern
restriction.requires_state_condition
restriction.disabled_action_families
```

A missing restriction is zero. A defined but currently unimplemented mechanic must be represented as `unsupported`, not silently as zero.

### Persistence

```text
persistence.lifespan_defined
persistence.lifespan_turns
persistence.spawns_persistent_units
persistence.persistent_board_effect
persistence.persistent_control
```

Use canonical lifecycle semantics. Do not encode the historical `N -> 999` diagnostic workaround; `N` means the canonical non-expiring state where applicable.

## Gameplay-vector schema

The gameplay vector is computed from valid replay states after Ares/state reconstruction has passed its correctness gate.

For each hero, sample representative states and compute distributions rather than a single mean.

Recommended measurements:

```text
context.legal_action_count
context.reachable_square_count
context.attackable_target_count
context.threatened_square_count
context.controlled_enemy_count
context.area_influence_cells
context.board_effect_cells
context.available_counter_count
context.ally_compatibility_score
context.enemy_vulnerability_score
context.tactical_phase
```

For continuous quantities retain:

```text
mean, median, p10, p25, p50, p75, p90
```

and the number of valid sampled states.

Do not pool all states blindly. Report the same context strata used by the state-of-the-game audit.

## Context strata

At minimum, the sampling metadata should identify:

```text
phase
board_density
position_region
legal_action_bucket
ally_count
enemy_count
threat_level
initiative
control_or_persistence_state
```

Exact bucket definitions belong to the sampling implementation and must be versioned so that longitudinal comparisons remain meaningful.

## Normalization

PCA and clustering should use a documented standardized matrix:

1. remove features that are constant across the current draftable roster;
2. encode boolean capabilities as 0/1;
3. log-transform strongly skewed non-negative count features only when the transformation is recorded;
4. standardize retained numeric dimensions using training-set statistics for the current analysis epoch;
5. keep the transformation metadata with the output artifact.

Do not normalize against current draft cost. Cost must remain an external overlay.

## Missingness

The feature pipeline must distinguish:

```text
0       = verified absence / zero capability
NA      = measurement unavailable
UNSUPPORTED = mechanic exists in configuration but the analyzer cannot interpret it
```

A hero with `NA` or `UNSUPPORTED` fields must not be silently treated as a weak zero in clustering.

## Cost overlay

For visualization, expose at least:

```text
current_draft_cost
estimated_fair_cost
estimated_fair_cost_uncertainty
cost_deviation
cost_efficiency
```

These are annotations/diagnostics, not design-space inputs.

## Mechanical-vs-behavioural interpretation

A useful diagnostic should be able to distinguish:

```text
mechanically similar + behaviourally similar
    -> possible redundancy

mechanically different + behaviourally similar
    -> possible strategic convergence

mechanically similar + behaviourally different
    -> context/composition dependence

mechanically different + behaviourally different
    -> genuine diversity candidate
```

These classifications are hypotheses for investigation, not automatic balance decisions.

## Derived roster analyses

The first roster-analysis artifact should include:

1. feature coverage table;
2. PCA 2-D projection;
3. clustering candidates for `k = 3..6`;
4. silhouette scores;
5. cluster sizes;
6. current cost overlay;
7. fair-cost overlay when available;
8. nearest-neighbour hero pairs in design space;
9. nearest-neighbour hero pairs in gameplay space;
10. sparse-region candidates.

Every plot must carry the analysis epoch, source configuration identity and feature-schema version.

## Breakpoint hooks

The feature schema is also a source for breakpoint analysis. A breakpoint candidate occurs when a discrete feature changes across a legal threshold, such as:

```text
reachable_area increases
attack_geometry gains a new displacement family
area target count crosses an integer threshold
control persistence changes
new action family becomes available
board-effect persistence begins/ends
```

Breakpoint detection must compare actual legal state transitions, not arbitrary score thresholds.

## Versioning and provenance

Schema changes are breaking for longitudinal PCA/clustering unless a compatibility mapping is provided.

Each generated feature artifact should include:

```text
feature_schema_version
rules/config hash
hero config hash
Ares revision, when gameplay features are included
sampling protocol version, when gameplay features are included
analysis epoch
source evidence set identity
```

This allows later balance reports to distinguish a real roster change from a feature-definition change.
