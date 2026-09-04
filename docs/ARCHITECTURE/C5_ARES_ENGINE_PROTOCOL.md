# C5 — Ares Engine Protocol Contract

Status: implemented production contract as of 2026-09-04.

## Scope

This document specifies the currently implemented Python↔Ares subprocess protocol. It describes wire commands and observable responses; it does not redefine RedWar game rules.

## Commands

### Readiness

`isready` must produce `readyok` after native hero behaviours have been loaded.

### Position

`position rwen <RWEN>` replaces the native board state from the canonical RWEN payload and synchronizes the NNUE board representation.

### Search

`go nodes <N>` performs a node-bounded search. `N` must be positive. Wall-clock expiry is disabled for this mode. Search diagnostics precede `bestmove <ACTION>`; an empty native action is represented as `bestmove 0000`.

`go infinite` starts an unbounded search until `stop`, another state-changing command, or `quit` interrupts it.

### Search control

`stop` terminates an active search and waits for its thread to join.

`quit` terminates an active search and exits the process.

### Transposition table

`setoption name UseTT value true|false` toggles transposition-table use and stops an active search first.

`clearhash` stops an active search, clears the transposition table, and returns `info string clearhash ok`.

### Evaluation / NNUE

`eval classical` returns `info score classical <integer>`.

`eval` returns the classical score and either an NNUE score or `info score nnue unavailable`.

`nnue info` returns one `info string nnue ...` diagnostic containing model metadata.

`nnue load <PATH>` attempts to load a model and reports `info string nnue load ok` or `info string nnue load failed`.

## Response and error ordering

For node-bounded search, `bestmove ...` is terminal and search diagnostics precede it. Consumers must continue reading until `bestmove`.

Command errors emit `info string command error: ...` and keep the process alive. Unknown commands emit `info string unknown command: ...`.

Search exceptions emit `info string search error: ...` followed by `bestmove 0000`.

## State identity

The Python subprocess bridge derives a local SHA-256 identity from the exact UTF-8 RWEN payload sent in `position rwen`. This is request provenance and is not an extra wire field.

`GameState.to_rwen()` is the canonical Python serializer. The native parser reconstructs pieces, effects, side to move and turns-without-capture from that payload.

## Action representation

Native actions use algebraic coordinates such as `MOVE A2 A3`, `ATTACK A2 B3`, `STUN A2 B3`, `SPAWN <hero> A2 B3`, and `SPELL <spell> A2 B3`. Python parses these at the bridge boundary and exposes the legacy dictionary form; `GameAction` is the typed application-level value object.

FrostMage `STUN` output is normalized by the Python bot to `SPELL`/`nevada` for compatibility with the Python rules model.

## Authority boundaries

`GameState` remains the Python transition authority. The independent legal-action oracle is used for differential validation. Ares owns native board/search state; `SubprocessEngineBridge` owns process/transport lifecycle; `ActionParser` owns textual action syntax; `GameAction` owns the typed Python action value.

## Compatibility policy

Protocol changes must update this contract and add conformance tests. New commands should be additive where practical; response-shape changes require explicit migration notes.

The current production source does **not** implement the historical `state canonical` A0 diagnostic. Historical references to it are not current production requirements.
