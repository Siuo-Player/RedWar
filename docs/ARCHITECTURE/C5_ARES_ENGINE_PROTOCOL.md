# C5 — Ares Engine Protocol Contract

Status: implemented production contract as of 2026-09-04.

## Scope

This document specifies the currently implemented Python↔Ares subprocess protocol. It describes the wire commands and observable responses; it does not redefine RedWar game rules.

## Commands

### Readiness

`isready` must produce `readyok` after hero behaviours required by the native engine have been loaded.

### Position

`position rwen <RWEN>` replaces the native board state from the canonical RWEN payload and synchronizes the NNUE board representation.

### Search

`go nodes <N>` performs a node-bounded search. `N` must be a positive unsigned integer. The command disables the wall-clock timeout and returns a search diagnostic line followed by `bestmove <ACTION>`; an empty native action is represented as `bestmove 0000`.

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

`nnue info` returns a single diagnostic line beginning with `info string nnue available=` and containing model metadata.

`nnue load <PATH>` attempts to load a model and reports `info string nnue load ok` or `info string nnue load failed`.

## Response ordering

For a node-bounded search, the terminal response is `bestmove ...`; search diagnostics precede it. Python bridge consumers must continue reading until `bestmove` rather than assuming the first line is terminal.

For command errors, the engine emits an `info string command error: ...` line and remains alive. Unknown commands emit `info string unknown command: ...`.

Search exceptions are converted into `info string search error: ...` followed by `bestmove 0000`.

## State identity

The Python subprocess bridge derives a local SHA-256 identity from the exact UTF-8 RWEN payload sent in `position rwen`. This identity is provenance for requests; it is not an additional wire field.

The canonical Python serializer is `GameState.to_rwen()`. The native parser consumes that payload and reconstructs pieces, tile effects, side to move, and turns-without-capture.

## Action representation

Native actions use algebraic coordinates such as `MOVE A2 A3`, `ATTACK A2 B3`, `STUN A2 B3`, `SPAWN <hero> A2 B3`, and `SPELL <spell> A2 B3`. Python converts those strings at the bridge boundary into the legacy action dictionary shape, with the typed `GameAction` value object available as the canonical application-level representation.

FrostMage `STUN` output is normalized by the Python bot to the `SPELL`/`nevada` action representation for compatibility with the Python rule model.

## Authority boundaries

`GameState` remains the Python transition authority. The independent legal-action oracle is used for differential validation and must not reuse the implementation under test. Ares owns native board/search state; `SubprocessEngineBridge` owns process/transport lifecycle; `ActionParser` owns textual action syntax; `GameAction` owns the typed Python action value.

## Compatibility policy

Protocol changes must update this document and add conformance coverage before being relied upon by higher-level callers. New commands should be additive where practical; changing an existing response shape requires explicit tests and migration notes.

## Conformance baseline

The executable C5 contract checks must cover readiness, RWEN position loading, bridge identity tracking, evaluation, TT controls, search diagnostics and ordering, malformed command handling, unknown commands, and explicit shutdown/lifecycle.

The production source currently has no `state canonical` command; any historical documentation of that A0 diagnostic must not be treated as a current production requirement.
