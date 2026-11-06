import Linglab.Theory
import Linglib.Semantics.Exhaustification.Finite
/-! Adapter: Fox (2007) innocent exclusion, via linglib's decidable Finset layer.
Model = a world; a world is a Fin 16 coding which of the 4 valuations (p,q) are accessible
(bit i set = valuation i accessible; valuation bit0 = p, bit1 = q).
Form = a proposition `Finset W` (the set of worlds where the sentence is true). -/
namespace Linglab.FoxIE
open Exhaustification

abbrev W := Fin 16
def acc (w : W) (v : Fin 4) : Bool := Nat.testBit w.val v.val
def U : Finset W := Finset.univ
def prop (f : W → Bool) : Finset W := U.filter fun w => f w = true
/-- valuation v satisfies atom n -/
def atomAt (n : String) (v : Fin 4) : Bool :=
  if n = "p" then Nat.testBit v.val 0 else if n = "q" then Nat.testBit v.val 1 else false

/-- Inner (non-modal) formulas denote sets of valuations; modals quantify over accessible ones.
Form here is the set of worlds; inner is a Finset (Fin 4) of valuations. -/
def inner : S → Option (Finset (Fin 4))
  | .atom n => some (Finset.univ.filter fun v => atomAt n v)
  | .not a => (inner a).map (Finset.univ \ ·)
  | .and a b => do pure ((← inner a) ∩ (← inner b))
  | .or a b => do pure ((← inner a) ∪ (← inner b))
  | _ => none

/-- may A: some accessible valuation in A; must A: all accessible valuations in A (and some). -/
def mayP (A : Finset (Fin 4)) : Finset W := prop fun w => decide (∃ v ∈ A, acc w v = true)

/-- Structural (Sauerland) alternatives of a disjunction, applied under the operator `O`. -/
def altsOf : S → Option (Finset (Finset W))
  | .may (.or a b) => do
      let A ← inner a; let B ← inner b
      pure {mayP (A ∪ B), mayP A, mayP B, mayP (A ∩ B)}
  | _ => none

def tr : S → Option (Finset W)
  | .may a => (inner a).map mayP
  | .not a => (tr a).map (U \ ·)
  | .and a b => do pure ((← tr a) ∩ (← tr b))
  | .or a b => do pure ((← tr a) ∪ (← tr b))
  | .op1 "exh" a => do pure (innocent.exh (← altsOf a) (← tr a))
  | .op1 "exh2" a => do   -- Fox's second layer (exhIter 2)
      let ALT ← altsOf a; let φ ← tr a
      pure (innocent.exh (ALT.image fun q => innocent.exh ALT q) (innocent.exh ALT φ))
  | _ => none

def T : Theory where
  name := "Fox 2007 (linglib innocent exclusion)"
  Form := Finset W
  Model := W
  models := List.finRange 16
  translate := tr
  trueIn m f := decide (m ∈ f)
  definedIn _ _ := true
  ent ps c := (List.finRange 16).all fun m => !(ps.all fun f => decide (m ∈ f)) || decide (m ∈ c)
  felic ps := (List.finRange 16).any fun m => ps.all fun f => decide (m ∈ f)
  cons ps := (List.finRange 16).any fun m => ps.all fun f => decide (m ∈ f)

open S
def pq : S := may (or (atom "p") (atom "q"))
def mp : S := may (atom "p")
def mq : S := may (atom "q")
/-- one exhaustification layer: no free choice (the sentence does not entail "may p") -/
example : Fails T (.entails [op1 "exh" pq] mp) := by decide
/-- one layer denies the conjunctive alternative -/
example : Holds T (.entails [op1 "exh" pq] (not (may (and (atom "p") (atom "q"))))) := by decide
/-- Fox's second layer yields free choice -/
example : Holds T (.entails [op1 "exh2" pq] mp) := by decide
example : Holds T (.entails [op1 "exh2" pq] mq) := by decide
example : Holds T (.felicitous [op1 "exh2" pq]) := by decide
end Linglab.FoxIE
