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

- `passives`: list of automatic, event-driven abilities (not chosen by the player). Each entry:
  - `trigger`: one of `on_kill`, `on_attack`, `on_attacked`, `on_turn_start`, `on_turn_end`, `on_death`, `aura_passive`.
  - `effect`: one of `spawn_unit`, `aoe_damage`, `redirect_damage`, `disable_spells`.
  - `params`: object, shape depends on `effect` (see examples below).
  - New `trigger`/`effect` values are expected over time. Both are plain strings dispatched through a registry (name -> handler), not a closed enum, specifically so a new passive idea only needs one new handler, not changes to existing heroes. Lifespan-based decay (Bone/Ghoul/StoneWall) is not part of this list — it's already generic on any hero with a `lifespan` field, handled once in `update_timers()`.

- `spell`: for player-activated abilities (Purify, Swap, Barricade, Ignite, Jump, Silence). Same container as `movement`/`attack`, just player-targeted instead of event-triggered.
  - `type`: name of the spell.
  - `radius` / `range`: reach, where applicable.
  - `target_team`: `ally`, `enemy`, or `any`.

Passives — worked examples
---------------------------
`BoneLord` — currently hardcoded in `game_state.py`'s `attack` branch
(`if piece.name == "BoneLord": ...`), shown here as the declarative target:

```
"BoneLord": { "behavior": { "passives": [
  { "trigger": "on_kill", "effect": "spawn_unit",
    "params": { "unit_name": "Bone", "spawn_location": "target_square" } }
] } }
```

`Berserker` — no code today, text-only passive:

```
"Berserker": { "behavior": { "passives": [
  { "trigger": "on_attack", "effect": "aoe_damage",
    "params": { "pattern": "adjacent", "friendly_fire": false } }
] } }
```

`Templar` — needed the `on_attacked` trigger, which didn't exist until this
hero required it. Deterministic by design (no `chance`/RNG field): a
probabilistic reflect would force chance nodes into the search tree
(expectiminimax-style), which breaks the assumption behind Zobrist/TT reuse
that a given position + move always resolves to the same result. Cooldown
keeps everything reproducible:

```
"Templar": { "behavior": { "passives": [
  { "trigger": "on_attacked", "effect": "redirect_damage",
    "params": { "target": "attacker", "cooldown_turns": 3 } }
] } }
```

`Inquisitor` — already has real code (`get_aura_positions`, `get_valid_spells`,
`get_threat_area` in `pieces.py`); a migration candidate more than a new build:

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
- This schema is intentionally permissive for now; the goal is to document a clear shape so we can progressively move behavior logic out of Python classes and into data-driven interpreters.
- To fully support data-driven behavior we will implement a behavior interpreter that maps these declarative patterns into calls used by `get_valid_moves` / `get_valid_attacks` etc.
- When converting classes to data-driven `DataPiece`, preserve existing behavior for parity and implement tests comparing outputs.
- Implementation caveat found while drafting the `passives` section above: the current Zobrist hash key is `(r, c, name, team, stun_timer)` only — `lifespan` and `spawn_cooldown` are not part of it, so two positions differing only in those fields collide in the transposition table. Any new per-piece counter (e.g. Templar's `cooldown_turns`) needs to go into the hash key too, or the TT will serve stale results once passives with countdown state exist.
