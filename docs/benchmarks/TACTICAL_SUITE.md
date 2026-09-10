# Ares Tactical Benchmark Suite

Ares is validated with deterministic RPG positions rather than only aggregate Arena results.

## Method

Each case contains:

- a canonical 8x8 RWEN position;
- the tactical action class expected from a stable high-budget reference;
- a node-budget scan.

The same position is executed at progressively smaller budgets. The useful metric is the **failure threshold**: the first budget at which Ares stops selecting the reference tactical action.

This deliberately avoids hard-coding a special search path for one position. The engine sees only the RWEN and node budget.

A strict reference test is used only for positions whose expected action has been independently chosen from the game rules and then validated at a high node budget. Strict-choice results are capability/regression evidence and are not, by themselves, Arena strength evidence.

## Current cases

### `frostmage-5-target`

Five enemies are clustered inside one FrostMage stun area. The expected tactical class is the immediate `STUN`. This is the current sanity benchmark for the two-stun lethal rule.

### `second-stun-lethal`

A single Bone on `D5` is already stunned while a White FrostMage on `A5` can apply the same stun line to `D5`. The reference is `STUN A5 D5`, exercising the lethal second-stun transition rather than an ordinary material capture.

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
2. stun that misses all enemies, proving the selective extension is not triggered;
3. same first stun target area versus a different stun area;
4. high-value spell versus material gain;
5. passive/aura tactical threat without an immediate material swing;
6. lifespan/cooldown trade-off;
7. defensive position where the strongest move is not the highest material move.

A position is not promoted to a hard regression until its reference move is stable across repeated high-budget runs.
