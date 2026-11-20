# Deterministic Audit: FrostMage vs Inquisitor Endgame Dynamics

**Issue:** #444  
**Date:** 2026-11-20  
**Scope:** Authoritative game-rules audit of the 16 FrostMages vs 1 Inquisitor endgame.

---

## 1. Context and Problem Statement

Manual play on `main` exposed a perplexing scenario: a player commanding 16 FrostMages against a single enemy Inquisitor was unable to win or finish the position.

Issue #444 posed three deterministic questions:
1. Is this position **legally winnable** with correct FrostMage play?
2. Is it a **legitimate losing/stalemate position** under authoritative rules?
3. Or is it an **actual interaction/ice-placement deadlock**?

---

## 2. Deterministic Findings

### A. Is it legally winnable with FrostMages against a lone Inquisitor?
**No.** Under authoritative rules, the position cannot be won by White (FrostMages):
- FrostMage has no basic attack (`behavior.attack.type == "none"`).
- The only offensive mechanism available to FrostMage is the `NEVADA` spell, which applies a 2-turn stun on the first hit and captures on a second stun during an active stun window.
- When Black has only a single piece (the Inquisitor), stunning the Inquisitor immediately leaves Black with zero legal moves on their turn (`can_act() == False`).
- The authoritative transition engine calls `check_game_over()` at turn switch. When the active player has zero legal moves, the `Oponente Bloqueado` terminal rule triggers immediately.
- In `check_game_over()`:
  ```python
  adversario_vencedor = "Brancas" if self.white_to_move else "Pretas"
  ```
  On Black's turn (`white_to_move == False`), `adversario_vencedor` evaluates to `"Pretas"`.
  The game terminates instantly with:
  ```text
  Pretas Vencem (Oponente Bloqueado)
  ```
- Thus, stunning the lone Inquisitor immediately causes Black to win.

---

### B. Is it a legitimate losing position?
**Yes, authoritative rules classify this endgame as a definitive loss for White:**
1. **If White stuns Inquisitor:** Black wins immediately via `Pretas Vencem (Oponente Bloqueado)`.
2. **If White refuses to stun Inquisitor:** FrostMage cannot capture without stunning. The game reaches 50 turns without capture (`twc == 50`). At `twc == 50`, `resolver_por_material()` compares piece costs:
   - 1 Inquisitor: **128 points** (`HERO_DEFS["Inquisitor"]["cost"]`)
   - 16 FrostMages: **80 points** ($16 \times 5 = 80$, `HERO_DEFS["FrostMage"]["cost"] = 5`)
   - Since $128 > 80$, Black wins on material tiebreak:
     ```text
     Desempate por Material (128 vs 80) - Pretas Vencem no Desempate
     ```
3. **If Inquisitor approaches:** Inquisitor has adjacent movement and attack (`cost 128`), and projects a silence aura of Chebyshev radius 2 (`aura_radius = 2`). Any FrostMage within radius 2 is silenced and unable to cast `NEVADA`. Inquisitor can systematically eliminate FrostMages one by one.

---

### C. Is there an interaction/ice-placement deadlock?
**Yes, whenever direct targeting is used:**
1. When `NEVADA` is targeted directly on the Inquisitor's tile `(r, c)`:
   - The tile `(r, c)` receives an ice tile effect (`timer: 3`).
   - The Inquisitor receives `stun_timer = 2`.
2. On White's subsequent turn:
   - `_install_frostmage_nevada_rules()` explicitly forbids targeting any tile that already contains ice:
     ```python
     if tile_effects and tile_effects[focus_r][focus_c].get("type") == "ice":
         continue
     ```
   - Adjacent `NEVADA` casts aimed at neighboring tiles skip `(r, c)` from splash/cross-AOE because `(r, c)` has ice:
     ```python
     if tile and tile.get("type") == "ice" and (fr, fc) != (end_row, end_col):
         continue
     ```
   - This creates an **"ice shield"**: while sitting on ice, the Inquisitor is completely immune to further stuns.
   - The ice persists for 3 turns, whereas the stun lasts 2 turns. By the time the ice melts, the stun has already expired.

### D. The Indirect Splash Execution Technique (When Auxiliary Enemies Exist)
If Black possesses at least one auxiliary piece (e.g. a Cleric or Bone) so that Black is not blocked when Inquisitor is stunned, White **can** eliminate Inquisitor using indirect splash targeting:
1. **Turn 1:** FrostMage centers `NEVADA` on an adjacent square $(r, c-1)$.
   - Tile $(r, c-1)$ receives ice.
   - The cross-AOE reaches $(r, c)$, stunning Inquisitor without placing ice on $(r, c)$.
2. **Black Turn:** Black moves their auxiliary piece (Inquisitor remains stunned).
3. **Turn 2:** A second FrostMage targets $(r, c)$ directly with `NEVADA`.
   - Since $(r, c)$ has no ice, the action is legal.
   - The stunned Inquisitor is captured and removed from the board.

---

## 3. Policy and Product Impact

In accordance with Issue #444 guidance:
> *"Do not change combat semantics merely to make the reported position easier. First reproduce with a focused state-level regression/fixture and document the conclusion."*

1. **Combat Semantics Preserved:** Combat and terminal contracts are strictly preserved.
2. **Player Feedback:** PR #615 implemented dedicated sidebar feedback explaining Inquisitor silence and aura radius so players understand tactical constraints.
3. **Regression Suite:** Added `tests/test_frostmage_inquisitor_endgame_audit.py` covering all 5 key dynamics:
   - Immediate terminal block when stunning a lone enemy piece.
   - Ice shield immunity from direct targeting.
   - Indirect splash execution with auxiliary enemy pieces.
   - 50-turn material tiebreak (128 vs 80).
   - Inquisitor silence radius boundary vs FrostMage casting range.
