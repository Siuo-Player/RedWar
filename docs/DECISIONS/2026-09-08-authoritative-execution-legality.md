# RedWar — Authoritative execution legality — 2026-09-08

## Context

`GameState.execute_action()` now consumes every accepted input through the canonical `GameAction` normalization boundary. The remaining A0.1 gap is execution legality: a structurally valid action must not bypass the authoritative legal-action enumeration before mutating state.

## Decision

`GameState.execute_action()` must validate the normalized `GameAction` against `engine.legal_actions.legal_actions(self)` before calling the existing `make_action()` transition path.

The rule generators remain the primitives. `execute_action()` does not duplicate hero-specific legality checks; it delegates membership to the canonical action-space adapter.

## Compatibility boundary

Legacy mappings remain accepted as input. They are normalized once to `GameAction`, validated using the canonical action space, then converted to the existing primitive argument shape for `make_action()`.

## Explicit non-goals

This change does not alter individual hero rules, action generation, search strength, evaluation, balance, datasets, statistics, or NNUE/search tuning.

## Required regression evidence

- a legal canonical action still executes;
- an equivalent legal legacy mapping still executes;
- a structurally valid but illegal canonical action is rejected before state mutation;
- the same illegal action expressed as a legacy mapping is rejected identically;
- STUN/SPAWN/SPELL legality remains governed by the canonical action enumeration;
- existing transition and differential tests remain green.
