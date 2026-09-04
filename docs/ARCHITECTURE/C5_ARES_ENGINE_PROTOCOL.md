# C5 — Ares Engine Protocol Contract

Status: current implementation contract
Version: `1`
Scope: Python bridge ↔ native Ares subprocess

## Purpose

This document defines the protocol currently implemented by Ares. It is a compatibility contract, not a proposal for a new engine protocol.

The protocol is line-oriented UTF-8 text over stdin/stdout. One command is sent per line. Responses are emitted as complete lines and flushed by the engine.

The protocol is intentionally independent from the higher-level `EngineBridge` transport abstraction. The bridge owns process lifecycle and transport failures; Ares owns command semantics.

## Current authority

The current native command dispatcher is `ai/cpp_engine/main.cpp`.

The Python transport boundary is `ai/engine_bridge.py`.

The Python product adapter is `ai/bot.py`.

The current battle position payload is produced by `GameState.to_rwen()` and sent as `position rwen <payload>`.

## Protocol version

`Protocol version 1` is the contract represented by the current implementation.

Version changes are required when an existing command changes grammar, required semantics, canonical state representation, response meaning, or lifecycle behavior in a way that can break an existing client.

Additive diagnostic responses that do not change existing command semantics may remain within the same protocol version.

A future protocol-version negotiation command may be introduced before version `2`; until then, clients should assume version `1` and fail explicitly when they cannot understand a response.

## Command grammar

### Lifecycle

`isready`

Response:

`readyok`

The command ensures hero behavior configuration is loaded before reporting readiness.

`quit`

Stops an active search, terminates the engine loop, and exits the process.

`stop`

Stops the active search and waits for the search thread to join. It does not itself emit a search result.

### Position

`position rwen <RWEN>`

Replaces the native board state with the supplied RWEN payload and synchronizes NNUE state.

A position command stops an active search before replacing state.

The RWEN payload is currently the complete battle representation required by Ares: board pieces, piece lifecycle fields, tile effects, side to move and TWC.

### Search

`go nodes <N>`

Starts a node-bounded search with `N > 0`.

The wall-clock time limit is disabled for node-bounded searches. Therefore the requested node budget is the controlling bound for this search mode.

Responses include an informational diagnostic line followed by exactly one terminal `bestmove` line for a completed search request:

`info string search diagnostics nodes=<...> tt_probes=<...> tt_hits=<...> tt_stores=<...>`

`bestmove <MOVE>`

When no legal move is available, the engine emits:

`bestmove 0000`

Python must distinguish legitimate terminal-position `0000` from a native diagnostic/error `0000` using the game-state contract and preceding diagnostic information.

`go infinite`

Starts a search without a wall-clock limit and with the maximum supported search depth.

This mode is intended for pondering/interactive use, not for fixed-node reproducibility.

### Transposition-table control

`setoption name UseTT value true`

Enables the transposition table.

`setoption name UseTT value false`

Disables transposition-table probes and stores for subsequent searches.

Invalid values are rejected with an informational command error.

`clearhash`

Stops active search, clears all transposition-table entries, and emits:

`info string clearhash ok`

### Evaluation / NNUE diagnostics

`eval classical`

Emits the current classical evaluation as:

`info score classical <VALUE>`

`eval`

Emits the classical evaluation and either an NNUE score or an explicit NNUE-unavailable diagnostic.

`nnue info`

Reports NNUE availability and model metadata.

`nnue load <PATH>`

Stops active search, attempts to load the model, and reports `ok` or `failed`.

## Error semantics

Malformed or unsupported commands do not terminate the engine process by themselves. The dispatcher reports an informational diagnostic line:

`info string command error: <MESSAGE>`

Unknown commands are reported as:

`info string unknown command: <COMMAND>`

Unknown `go` forms are reported as:

`info string unknown go command: <ARGS>`

Search exceptions are converted into:

`info string search error: <MESSAGE>`
`bestmove 0000`

A Python client must not silently reinterpret an error as a legal move.

## Ordering and lifecycle guarantees

Before a new `position`, `go`, `clearhash`, `setoption`, `eval`, or NNUE load operation that requires exclusive engine state, the current dispatcher stops an active search.

`isready` is a readiness barrier for the command-processing state and hero-behavior loading. The Python bridge additionally owns process startup and transport timeout behavior.

Search results are asynchronous internally, but the public command contract remains line-oriented. A caller must consume informational `info` lines until the terminal `bestmove` response for a search request.

## Canonical position identity

RWEN is the cross-layer canonical representation used by the current local Ares path.

The canonical state identity must include:

- every occupied square and empty square;
- team;
- hero/unit name;
- stun timer;
- finite lifespan or permanent marker;
- spawn cooldown;
- tile-effect presence, type, team and timer;
- side to move;
- TWC (`turns_without_capture`).

The current native canonical read-back seam also exposes the native board hash as a diagnostic identity value.

The Python side must continue treating semantic state and hash as separate assertions: equal hashes are required for equal canonical states in tested paths, but a hash match alone is not a semantic proof.

## Action representation

Ares search results are text actions parsed by `engine/action_parser.py`.

Current external action families are:

`MOVE <ORIGIN> <TARGET>`

`ATTACK <ORIGIN> <TARGET>`

`STUN <ORIGIN> <TARGET>`

`SPAWN <HERO> <ORIGIN> <TARGET>`

`SPELL <SPELL_NAME> <ORIGIN> <TARGET>`

The higher-level canonical Python representation is `engine.actions.GameAction`.

The protocol itself remains textual at the subprocess boundary in version `1`.

## Compatibility behavior

FrostMage/Nevada currently has a compatibility normalization at the Python product boundary: a native `STUN` representation from Ares may be normalized to `SPELL nevada` before becoming a `GameAction`.

This normalization is intentionally documented rather than hidden. A future protocol revision should make the native representation identical to the canonical action vocabulary so that client-side semantic conversion is no longer necessary.

## State canonicalization command

The historical A0 seam introduced `state canonical` as a native read-back diagnostic. Where present in production/A0 tooling, its output is:

`info string state canonical <RWEN> hash=<HASH>`

The command is diagnostic/read-only: it must not mutate the engine state.

## Contract boundaries

`GameState` remains the Python gameplay transition authority.

The independent legal-action oracle remains an evidence/specification layer and must not call the implementation under test.

Ares is responsible for native state parsing, move generation, search and native state transitions.

`EngineBridge` is responsible for process lifecycle, command transport, bounded waiting and transport failures.

`ActionParser` is responsible for textual action syntax.

`GameAction` is responsible for the canonical Python action value object.

No layer may infer correctness solely from the existence of a `bestmove` line.

## Required future conformance checks

Before changing the protocol version or exposing Ares to another product surface, conformance tests should cover:

1. command grammar and explicit error semantics;
2. canonical RWEN round-trip;
3. canonical state read-back and hash stability;
4. multi-step position → search → state transition sequences;
5. `stop` and `quit` lifecycle behavior;
6. TT OFF/ON/clear lifecycle behavior;
7. invalid-command non-mutation;
8. protocol action normalization without loss of semantic fields;
9. Python bridge compatibility with the exact native response ordering.

These are correctness/compatibility checks only. They do not constitute strength evaluation or statistical analysis.

## Change policy

Protocol changes must update this document and the relevant contract tests in the same PR.

A gameplay-rule change must not be smuggled into a protocol maintenance PR.

A search/evaluation change must not be used to justify a protocol-version change unless the externally observable command contract actually changes.

When the protocol becomes a network/server interface, authentication, framing, message correlation IDs, explicit version negotiation and transport-independent serialization should be designed as a new protocol layer rather than retrofitting semantics into the current line protocol.
