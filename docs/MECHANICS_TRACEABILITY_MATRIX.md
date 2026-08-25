# RedWar — Mechanics Traceability Matrix

This matrix is a foundation gate for data-driven mechanics. A mechanic is not considered complete merely because its JSON representation parses successfully.

## Required trace

Every state-changing mechanic should be traceable through:

```text
configuration
→ Python implementation
→ C++ implementation
→ action generation
→ state transition
→ serializer/RWEN
→ make
→ unmake
→ hash
→ legal-action differential
→ regression/property test
→ tactical/semantic benchmark when applicable
```

## Initial matrix

| Mechanic / state | Configuration | Python rules | C++ rules | Actions | Transition | Make | Unmake | Hash | Differential | Benchmark |
|---|---|---|---|---|---|---|---|---|---|---|
| Basic movement | heroes_config.json | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | regression |
| Basic attack | heroes_config.json | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | regression |
| STUN | hero data / behavior | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | tactical |
| Spells | hero data / spells | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | tactical |
| Lifespan | hero data | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | targeted | tactical |
| Cooldown | hero data / state | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | targeted | tactical |
| Tile effects / ice | hero data / behavior | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | targeted | tactical |
| Passive effects | behavior.passives | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | targeted | semantic |
| TWC / persistent effects | hero/state data | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | targeted | semantic |

## Status semantics

- `✓` means current project documentation/tests report an implemented path; it does not mean the path is independently proven for every mechanic variant.
- `targeted` means the project must keep explicit directed coverage because random differential sequences are insufficient for rare persistent states.
- Blank cells are not acceptable for a mechanic that changes legal actions or state.

## Required completion rule

For a new or migrated mechanic, mark the row complete only after:

1. Python and C++ action generation agree;
2. resulting state agrees after the action;
3. make/unmake returns to the exact root state;
4. serialization/RWEN remains stable and unambiguous;
5. hashes agree where hashing is part of the engine contract;
6. a regression/property case exists for the mechanic;
7. a tactical benchmark exists when the mechanic changes search capability.

This matrix is deliberately stricter than schema validation because the schema itself does not guarantee semantic completeness across backends.

## Maintenance rule

Update this matrix in the same development block in which a mechanic is discovered, changed or proven. Do not postpone the documentation until after implementation.
