# C5 — Ares Engine Protocol Contract

Status: current production contract, 2026-09-04.

This document specifies the implemented Python↔Ares subprocess protocol. It describes wire commands and observable responses; it does not redefine game rules.

## Commands

`isready` → `readyok` after native hero behaviours are loaded.

`position rwen <RWEN>` replaces native board state from canonical RWEN and synchronizes the NNUE board representation.

`go nodes <N>` performs a positive-node-bounded search with wall-clock expiry disabled. Search diagnostics precede terminal `bestmove <ACTION>`; no action is `bestmove 0000`.

`go infinite` starts search until `stop`, another state-changing command, or `quit` interrupts it.

`stop` terminates an active search and joins its thread. `quit` terminates an active search and exits.

`setoption name UseTT value true|false` toggles TT use and stops active search first. `clearhash` stops active search, clears TT, and returns `info string clearhash ok`.

`eval classical` returns `info score classical <integer>`. `eval` returns classical plus NNUE score or `info score nnue unavailable`.

`nnue info` returns an `info string nnue ...` diagnostic. `nnue load <PATH>` reports load success/failure.

## Response semantics

Search diagnostics precede `bestmove`. Consumers must read through `bestmove` rather than assuming the first line is terminal.

Command errors emit `info string command error: ...` and keep the process alive. Unknown commands emit `info string unknown command: ...`.

Search exceptions emit `info string search error: ...` followed by `bestmove 0000`.

## State identity

`SubprocessEngineBridge` derives a local SHA-256 identity from the exact UTF-8 RWEN payload sent in `position rwen`. `GameState.to_rwen()` is the canonical Python serializer.

## Action representation

Native actions use algebraic coordinates: `MOVE`, `ATTACK`, `STUN`, `SPAWN <hero>`, and `SPELL <spell>`. Python parses the wire form; `GameAction` is the typed application-level representation. FrostMage `STUN` is normalized to `SPELL`/`nevada` by the Python bot.

## Authority and compatibility

`GameState` is the Python transition authority. `SubprocessEngineBridge` owns transport lifecycle; `ActionParser` owns textual syntax; `GameAction` owns the typed action value; Ares owns native state/search.

Protocol changes require contract updates and executable conformance coverage. The current production source does not implement the historical `state canonical` A0 diagnostic; references to it are not current requirements.
