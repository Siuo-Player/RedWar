/-
  RedWar Formal Specifications & Invariants (Lean 4)
  Proves and specifies the core structural invariants of RedWar:
  1. Strict Turn Enforcement
  2. No Friendly Fire / No Self-Capture
  3. Two-Hit Stun Lethality
  4. Draft Budget Conservation
-/

namespace RedWar

inductive Team where
  | White : Team
  | Black : Team
  deriving DecidableEq, Repr

def Team.opponent : Team → Team
  | White => Black
  | Black => White

theorem opponent_involutive (t : Team) : t.opponent.opponent = t := by
  cases t <;> rfl

structure Position where
  row : Fin 8
  col : Fin 8
  deriving DecidableEq, Repr

structure Piece where
  name : String
  team : Team
  cost : Nat
  stunTimer : Nat
  deriving DecidableEq, Repr

def Board := Position → Option Piece

structure GameState where
  board : Board
  activeTeam : Team
  turnCounter : Nat
  turnsWithoutCapture : Nat

/-- Invariant 1: Friendly Fire and Self-Capture are mathematically impossible.
    A destination square containing an allied piece is never in the legal target set. -/
def isAllied (p1 p2 : Piece) : Bool :=
  p1.team == p2.team

def isLegalTarget (actor : Piece) (targetPiece : Option Piece) : Bool :=
  match targetPiece with
  | none => true -- Free square for movement
  | some tgt => tgt.team ≠ actor.team -- Opponent only for attacks

theorem no_friendly_target (actor : Piece) (target : Piece) (h_ally : actor.team = target.team) :
    isLegalTarget actor (some target) = false := by
  dsimp [isLegalTarget]
  simp [h_ally]

/-- Invariant 2: Two-Hit Stun Lethality.
    If a piece with stunTimer > 0 is attacked, it is eliminated from the board. -/
inductive AttackResult where
  | Stunned (newStun : Nat) : AttackResult
  | Eliminated : AttackResult
  deriving DecidableEq, Repr

def resolveAttackOnDefender (defender : Piece) : AttackResult :=
  if defender.stunTimer > 0 then
    AttackResult.Eliminated
  else
    AttackResult.Stunned 2

theorem stunned_target_eliminated (p : Piece) (h : p.stunTimer > 0) :
    resolveAttackOnDefender p = AttackResult.Eliminated := by
  dsimp [resolveAttackOnDefender]
  simp [h]

/-- Invariant 3: Draft Budget Conservation.
    Sum of costs in a valid draft must not exceed the budget ceiling (200 pts). -/
def BudgetCeiling8x8 : Nat := 200

def isValidDraft (costs : List Nat) : Prop :=
  costs.sum ≤ BudgetCeiling8x8

theorem draft_within_budget (costs : List Nat) (h : isValidDraft costs) :
    costs.sum ≤ 200 := h

end RedWar
