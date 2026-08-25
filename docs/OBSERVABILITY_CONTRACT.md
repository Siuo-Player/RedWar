# RedWar — Observability Contract

## Purpose

This document defines what information a player and Ares are allowed to observe at each decision point.

It is intentionally a contract, not an implementation detail. `GameState`, RWEN, the C++ search state and NNUE inputs must not silently define visibility by accident.

## Current status

**Open specification.** The repository currently confirms that draft and initial positioning are secret to the opponent, but does not yet explicitly establish whether those facts remain hidden once the match begins.

Until this is resolved, no claim should be made that Ares is a legally fair imperfect-information agent or that its strength is directly comparable to a human player under hidden-information rules.

## Required model

For every state field, record:

| Field | Public to player? | Visible to Ares? | Reason | Search/eval impact | Test |
|---|---|---|---|---|---|
| Own pieces | TBD | TBD | | | |
| Opponent piece positions | TBD | TBD | | | |
| Opponent hero identity | TBD | TBD | | | |
| Opponent stun timer | TBD | TBD | | | |
| Opponent lifespan | TBD | TBD | | | |
| Opponent cooldown | TBD | TBD | | | |
| Terrain effects | TBD | TBD | | | |
| Side to move | TBD | TBD | | | |
| Turns without capture | TBD | TBD | | | |
| Previous actions | TBD | TBD | | | |

The table is deliberately `TBD` until the game design is resolved. Do not infer a product rule from what the current implementation happens to expose.

## Information-set terminology

If hidden information remains during play, a concrete player observation must be represented as an **information set**: the set of full game states that are indistinguishable to that player from the information they have observed.

A belief-state implementation may later assign a probability distribution over those states, but RedWar does not currently commit to a particular probabilistic representation.

If all relevant state becomes public when the match starts, this document must explicitly say so and the game becomes a perfect-information decision problem after setup.

## Audit path

```text
Game rules
    ↓
observable information
    ↓
player observation
    ↓
AI-visible state
    ↓
RWEN / state serialization
    ↓
search root
    ↓
move generation
    ↓
evaluation / NNUE
```

Every transition must preserve the visibility contract.

## Leakage test principle

If field `X` is hidden from the player, changing only `X` in two otherwise identical hidden states must not change an action selected by Ares from the same legal information state, unless `X` is inferable from the player's observation/history or is intentionally included in the model's belief representation.

This should eventually become a differential regression test.

## Research dependency

Relevant external work:

Perolat et al., *Mastering the Game of Stratego with Model-Free Multiagent Reinforcement Learning*, Science 378(6623), 2022, 990–996. DOI: 10.1126/science.add4679. https://arxiv.org/abs/2206.15378

The result is relevant because Stratego combines long-horizon board-game planning with hidden information. It does not prescribe DeepNash for RedWar; it establishes that the information structure is part of the AI problem definition.

Project Studies source: `_sources/cards/perolat2022-deepnash.md`.
