# Ares Tactical Capability Suite

This suite is deterministic capability/regression evidence. It is not a global strength benchmark.

## Method

Each case contains a canonical 8x8 RWEN position, a tactical reference chosen from the current game rules, and a node-budget scan.

Capability mode checks that Ares returns a non-null legal action. Strict-choice mode additionally requires the frozen reference action. Strict-choice results are capability/regression evidence and are not, by themselves, Arena strength evidence.

## Current cases

### `frostmage-5-target`

Five enemies are clustered inside one FrostMage Nevada spell area. The expected tactical class is the immediate `SPELL nevada`; this is the current sanity benchmark for the two-stun lethal rule.

### `second-stun-lethal`

A single Bone on `D5` is already stunned while a White FrostMage on `A5` can apply the Nevada spell to `D5`. The reference is `SPELL nevada A5 D5`, exercising the lethal second-stun transition rather than an ordinary material capture.

The repository regression validates this reference at a 10,000-node budget in strict-choice mode. It remains deliberately separate from global strength claims.

### Existing capability cases

The suite also contains deterministic cases covering:

- high-value capture;
- declared ranged spell;
- defensive `purify`;
- lifespan/spawn cooldown;
- TWC-adjacent capture.

## Next cases

The next positions should be independently constructed and validated at a high node budget before becoming regression references:

1. multi-stun with fewer targets;
2. spell that misses all enemies, proving the selective extension is not triggered;
3. same first spell target area versus a different spell area;
4. high-value spell versus material gain;
5. passive/aura tactical threat without an immediate material swing;
6. lifespan/cooldown trade-off;
7. defensive position where the strongest move is not the highest material move.

A position is not promoted to a hard regression until its reference move is stable across repeated high-budget runs.
