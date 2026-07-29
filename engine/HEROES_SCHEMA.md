HEROES_SCHEMA
=============

This document describes the `engine/heroes_config.json` schema used to drive unit metadata and (in future) behavior definitions.

Top-level keys
---------------
- Each unit name (e.g. `Bone`, `Ghoul`) maps to an object with metadata and optional `behavior`.

Common metadata fields
----------------------
- `cost` (int): purchase cost used by the draft system.
- `acronym` (string): short label displayed on tokens.
- `descricao` (string): human-readable description.
- `passiva` (string): short passive ability text.
- `draftable` (bool): whether the unit appears in the draft/shop.
- `lifespan` (int, optional): number of turns before the unit expires.
- `spawn_cooldown` (int, optional): cooldown used by spawners.

Behavior object (experimental)
-------------------------------
The `behavior` object describes movement/attack/stun/spawn patterns in a declarative way.
Not all fields are required; the engine will fall back to existing class logic when absent.

Supported behavior keys (examples):
- `movement`: describes how the unit may move.
  - `type`: one of `orthogonal`, `diagonal`, `adjacent`, `knight`, `ray`, `none`, `forward_cone`, `orthogonal`.
  - `max_steps`: integer (for `orthogonal`, `diagonal`, `adjacent`).
  - `deltas`: explicit list of [dr, dc] offsets for `pattern`-like movement.
  - `forward_dir_by_team`: boolean; if true the engine interprets the forward direction depending on unit `team`.

- `attack`: similar to `movement` but used to declare attack reach and patterns.

- `stun`: AoE/stun declarative definition.
  - `type`: `aoe`.
  - `radius`: integer Manhattan radius to consider for valid stun focuses.

- `spawn`: spawn definitions for units that summon other units.
  - `unit`: string, name of unit to spawn.
  - `pattern`: string describing spawn placement (e.g. `forward_row`).

Examples
--------
`Phantom` uses `knight` movement/attack:

```
"Phantom": { "behavior": { "movement": {"type": "knight"}, "attack": {"type": "knight"} } }
```

`Sentry` fires along straight rays:

```
"Sentry": { "behavior": { "attack": {"type": "ray", "dirs": [[1,0],[-1,0],[0,1],[0,-1]] } } }
```

Notes
-----
- This schema is intentionally permissive for now; the goal is to document a clear shape so we can progressively move behavior logic out of Python classes and into data-driven interpreters.
- To fully support data-driven behavior we will implement a behavior interpreter that maps these declarative patterns into calls used by `get_valid_moves` / `get_valid_attacks` etc.
- When converting classes to data-driven `DataPiece`, preserve existing behavior for parity and implement tests comparing outputs.
