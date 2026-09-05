# C5 — Ares Engine Protocol Contract

## Purpose

This document defines the currently implemented Python↔Ares subprocess protocol. It is a compatibility contract, not a replacement for `GameState`, the independent legal-action oracle, or the canonical `GameAction` value object.

## Current command surface

The production `ai/cpp_engine/main.cpp` accepts:

- `isready` → `readyok`
- `quit`
- `stop`
- `position rwen <RWEN>`
- `go nodes <N>` where `N > 0`
- `go infinite`
- `clearhash`
- `setoption name UseTT value true|false`
- `eval classical`
- `eval`
- `nnue info`
- `nnue load <PATH>`

Search completion emits a diagnostic line followed by `bestmove <ACTION>`. An empty native move is represented as `bestmove 0000`.

## Ordering and lifecycle

`isready` is the readiness barrier. `position rwen` stops an active search before loading the position. `go` also stops any previous search before starting a new search. `stop` waits for the active search thread to join. `quit` stops the active search and exits the command loop.

The Python `SubprocessEngineBridge` owns process lifecycle and classifies transport failures. It does not interpret rules or select actions.

## Position identity

`position rwen <RWEN>` is the canonical state input. The bridge records a SHA-256 identity of the exact RWEN payload for local request provenance; this hash is not an Ares wire field.

RWEN identity includes board pieces, per-piece mutable fields represented by RWEN, tile effects, side to move, and turns-without-capture.

## Actions

Ares action text is parsed by `engine.action_parser.ActionParser` using the current grammar:

- `MOVE A2 A3`
- `ATTACK A2 B2`
- `STUN A2 B2`
- `SPAWN <Hero> A2 A3`
- `SPELL <spell> A2 A3`

The canonical Python representation is `engine.actions.GameAction`. The current bot boundary still returns legacy dictionaries, preserving compatibility while producers migrate incrementally.

FrostMage's native `STUN` representation is normalized by `CppEngineBot` into the canonical Python spell representation (`SPELL` / `nevada`) at the compatibility seam.

## Search semantics

`go nodes <N>` is node-bounded and deliberately disables the wall-clock limit so node-bounded runs remain reproducible across hosts. It reports search diagnostics containing `nodes`, `tt_probes`, `tt_hits`, and `tt_stores`.

`go infinite` removes the node limit and uses the engine's maximum search depth until interrupted by `stop`, `position`, another `go`, `clearhash`, `setoption`, or `quit`.

`clearhash` stops active search before clearing the transposition table.

## Error semantics

Malformed or unsupported commands normally produce an `info string` diagnostic rather than terminating the process. Invalid `go nodes` input is reported as a command error. A search exception is surfaced as `info string search error: ...` followed by `bestmove 0000`.

The Python bridge treats an unexpected process exit, timeout, malformed transport response, or non-terminal `0000` as an explicit bridge/engine failure rather than silently restarting the process.

## Contract boundaries

- `GameState.make_action()` remains transition authority.
- `engine.actions.GameAction` is the canonical Python action value object.
- `engine.action_parser.ActionParser` owns wire-text parsing.
- `SubprocessEngineBridge` owns process/transport lifecycle.
- Ares owns native state/search execution after `position rwen`.
- The independent legal-action oracle remains independent of the implementation under test.

## Historical note

An earlier A0 seam exposed a `state canonical` diagnostic command. The current production `main.cpp` does not expose that command; references to it in older documents describe historical tooling only and must not be treated as a current protocol requirement.

## Current conformance coverage and future evolution

The current protocol contract is backed by executable checks rather than being only a future target. The existing C5 coverage includes:

1. readiness and lifecycle ordering in `tests/test_engine_bridge.py` and `tests/test_c5_ares_protocol.py`;
2. canonical RWEN acceptance and bridge state identity in the bridge/lifecycle tests;
3. command response grammar in the C5 protocol tests and action matrix;
4. search completion ordering (`info` diagnostics before `bestmove`) in the lifecycle/action-matrix coverage;
5. node-bounded protocol behavior and deterministic node accounting in the C5/search checks;
6. option and hash lifecycle, including cancellation before stateful hash changes;
7. explicit failure semantics, including timeout, transport failure, and non-terminal `0000` handling;
8. clean close/quit behavior and restart-after-close coverage.

Protocol changes should update this contract and their executable conformance checks in the same change series. Remaining forward-looking work is limited to compatibility features that have a concrete need, notably explicit protocol/feature negotiation and RWEN versioning; those should not be added speculatively.