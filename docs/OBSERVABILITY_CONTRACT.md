# RedWar — Observability Contract

## Purpose

This document defines what information a player and Ares are allowed to observe at each decision point.

It is a product/game rule contract, not an implementation detail. `GameState`, RWEN, the C++ search state and NNUE inputs must not silently define visibility by accident.

## Current status

**Resolved for the current local game mode.** RedWar's hidden-information rule applies to the **draft/setup phase**. Once the player finishes the draft and the game enters `BATALHA`, the starting armies and board are public game state and Ares may receive the complete battle state.

This matches the current flow in `main.py`:

```text
DRAFT
  ↓ player presses Ready
opponent draft is materialized in GameState
  ↓
fase_atual = BATALHA
  ↓
Ares may receive full GameState/RWEN
```

The implementation must not be interpreted as permitting hidden information during battle merely because the original draft was secret.

## Evidence for the current rule

- `docs/GAME_DESIGN.md`: the army and initial positioning are described as hidden during draft, with the stated purpose of preventing a perfect response **before the game starts**.
- `main.py`: the opponent's draft is inserted into `GameState` when the player presses Ready, immediately transitioning from `DRAFT` to `BATALHA`.
- `main.py`: `processar_ia()` invokes `CppEngineBot` only while `fase_atual == "BATALHA"`.
- `engine/game_state.py`: `to_rwen()` serializes the full board, including team, piece identity, stun timer, lifespan and cooldown.

Therefore the current local-mode contract is:

```text
DRAFT / setup:
    opponent army + starting positions = hidden

BATALHA:
    board state at the start of combat = public
    Ares may receive full battle state
```

## State visibility in battle

| Field | Player-visible during BATALHA | Visible to Ares | Reason |
|---|---:|---:|---|
| Own pieces | yes | yes | public board state |
| Opponent piece positions | yes | yes | public board state |
| Opponent hero identity | yes | yes | public after setup |
| Opponent stun timer | yes | yes | public board state |
| Opponent lifespan | yes | yes | public board state |
| Opponent cooldown | yes | yes | public board state |
| Terrain effects | yes | yes | public board state |
| Side to move | yes | yes | public game state |
| Turns without capture | yes/derivable | yes | game state |
| Previous actions | via game history where exposed | available through state/history as designed | deterministic battle history |

The table describes the current local game mode. A future web/multiplayer mode must define its own client observation layer rather than assuming that the local full-state representation is safe to expose over the network.

## Information-set terminology

The current local battle mode is a **perfect-information game after setup**. Information-set/belief-state search is therefore not required merely because the draft was hidden.

If a future variant retains hidden information after `BATALHA`, that variant must define a new observation contract and must not reuse the full-state Ares interface without an information-filtering layer.

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

The current local mode is now explicitly resolved by the first two layers.

## Leakage test principle

For any future hidden-information variant, if field `X` is hidden from the player, changing only `X` in two otherwise identical hidden states must not change an action selected by Ares from the same legal information state, unless `X` is inferable from the player's observation/history or intentionally represented in a belief model.

This remains a required test principle for future online/variant modes.

## Research dependency

Relevant external work:

Perolat et al., *Mastering the Game of Stratego with Model-Free Multiagent Reinforcement Learning*, Science 378(6623), 2022, 990–996. DOI: 10.1126/science.add4679. https://arxiv.org/abs/2206.15378

The result remains relevant as a warning that information structure defines the AI problem in genuinely hidden-information games. It does **not** imply DeepNash or information-set search for the current local RedWar mode.

Project Studies source: `Siuo-Player/Siuo-Player-PROJECT-STUDIES/_sources/cards/perolat2022-deepnash.md`.
