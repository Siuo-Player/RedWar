HEROES_SCHEMA
=============

This document describes the `engine/heroes_config.json` schema used to drive unit metadata and the declarative movement/attack behavior compiler.

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

Behavior object
---------------
The `behavior` object describes movement/attack patterns and passive abilities in declarative form.
Missing behavior sections do not invent arbitrary movement; hero-specific classes may still provide abilities that are not yet fully data-driven.

Supported behavior keys (examples):
- `movement`: describes how the unit may move.
  - `type`: one of `orthogonal`, `diagonal`, `adjacent`, `knight`, `ray`, `none`, `forward_cone`.
  - `max_steps`: integer (for range-based movement types).
  - `deltas`: explicit list of [dr, dc] offsets for pattern-like movement.
  - `forward_dir_by_team`: boolean; if true, the engine flips the declared forward direction for White.
  - `ghost_move`: whether occupied squares can be crossed for movement.

- `attack`: similar to `movement`, but used to declare attack reach and patterns.
  - `type`: `orthogonal`, `diagonal`, `knight`, `ray`, `pattern`, `forward_cone`, or `none`.
  - `max_steps`: maximum attack distance.
  - `min_steps`: minimum attack distance.
  - `deltas` / `dirs`: explicit attack vectors.
  - `forward_dir_by_team`: boolean; interpreted independently from `movement` when present.

- `stun`: declarative AoE/stun metadata where supported by the unit.
  - `type`: `aoe`.
  - `radius`: integer Manhattan radius to consider for valid stun focuses.

- `spawn`: spawn definitions for units that summon other units.
  - `unit`: string, name of unit to spawn.
  - `pattern`: string describing spawn placement (e.g. `forward_row`).

- `passives`: list of automatic, event-driven abilities. Each entry contains:
  - `trigger`: e.g. `on_kill`, `on_attack`, `on_attacked`, `on_turn_start`, `on_turn_end`, `on_death`, `aura_passive`.
  - `effect`: e.g. `spawn_unit`, `aoe_damage`, `redirect_damage`, `disable_spells`.
  - `params`: object whose shape depends on the effect.
  - New trigger/effect values are deliberately strings so the schema can evolve without changing every hero definition.

- `spell`: player-activated ability metadata. Spell execution is still partly implemented in the game-state layer.
  - `type`: spell name.
  - `radius` / `range`: reach, where applicable.
  - `target_team`: `ally`, `enemy`, or `any`.

Passives — worked examples
---------------------------
`BoneLord`:

```
"BoneLord": { "behavior": { "passives": [
  { "trigger": "on_kill", "effect": "spawn_unit",
    "params": { "unit_name": "Bone", "spawn_location": "target_square" } }
] } }
```

`Berserker`:

```
"Berserker": { "behavior": { "passives": [
  { "trigger": "on_attack", "effect": "aoe_damage",
    "params": { "pattern": "adjacent", "friendly_fire": false } }
] } }
```

`Templar`:

```
"Templar": { "behavior": { "passives": [
  { "trigger": "on_attacked", "effect": "redirect_damage",
    "params": { "target": "attacker", "cooldown_turns": 3 } }
] } }
```

`Inquisitor`:

```
"Inquisitor": { "behavior": { "passives": [
  { "trigger": "aura_passive", "effect": "disable_spells",
    "params": { "radius": 2, "target_team": "enemy" } }
] } }
```

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
- Lifespan and spawn-cooldown are generic state fields. They are part of the Python position hash and must be treated as part of the C++ position hash as well.
- Tile effects are also part of the position identity because their type, owner and timer affect future legal moves and outcomes.
- When migrating more hero logic into `behavior`, preserve Python/C++ parity with differential tests comparing legal moves and state transitions.
- The current architecture intentionally retains a small amount of hero-specific Python/C++ logic for spells and special abilities while the data-driven behavior system is expanded.
