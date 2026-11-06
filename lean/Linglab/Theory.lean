import Linglab.Syntax
/-! The Theory interface.

A theory says: which models exist (a finite list), how to translate the shared
syntax into its own formulas (`none` = cannot express it = out of scope), when a
formula is true / defined in a model, and its own notions of consequence
(`ent`), felicity (`felic`), consistency (`cons`) over those models.

A fact is a `Claim` over the shared syntax. For a theory `T`:
  `Holds T c`  the claim is expressible in T and true
  `Fails T c`  the claim is expressible in T and false (the negation)
Out of scope: neither `Holds` nor `Fails` is provable (no vacuous truth). -/
namespace Linglab

structure Theory where
  /-- readable name -/
  name : String
  /-- the theory's own formulas -/
  Form : Type
  /-- the models (a complete finite list; model constraints are already applied) -/
  Model : Type
  models : List Model
  /-- shared syntax -> own formula; `none` = not expressible -/
  translate : S → Option Form
  /-- the formula is true in the model -/
  trueIn : Model → Form → Bool
  /-- the formula has a truth value (is not undefined) in the model -/
  definedIn : Model → Form → Bool
  /-- vocabulary: consequence, felicity (in the null context), consistency -/
  ent : List Form → Form → Bool
  felic : List Form → Bool
  cons : List Form → Bool

/-- How a truth set relates to another: equal, within, includes. -/
inductive Rel | equals | within | includes
  deriving DecidableEq, Repr

/-- The shapes of fact (SPEC section 2). Equivalence = two `entails`. -/
inductive Claim where
  | entails (premises : List S) (conclusion : S)
  | felicitous (discourse : List S)
  | consistent (premises : List S)
  | truth (sentence : S) (rel : Rel) (target : S)
  deriving DecidableEq, Repr

namespace Theory

/-- translate a whole list; `none` if any sentence is not expressible -/
def translateAll (T : Theory) (l : List S) : Option (List T.Form) :=
  l.mapM T.translate

def truthSubset (T : Theory) (f g : T.Form) : Bool :=
  T.models.all fun m => !T.trueIn m f || T.trueIn m g

/-- The verdict of the claim: `none` out of scope, `some b` the claim is `b`. -/
def check (T : Theory) : Claim → Option Bool
  | .entails ps c => do
      let fs ← T.translateAll ps
      let f ← T.translate c
      pure (T.ent fs f)
  | .felicitous d => do
      let fs ← T.translateAll d
      pure (T.felic fs)
  | .consistent ps => do
      let fs ← T.translateAll ps
      pure (T.cons fs)
  | .truth s r t => do
      let f ← T.translate s
      let g ← T.translate t
      pure (match r with
        | .equals => T.truthSubset f g && T.truthSubset g f
        | .within => T.truthSubset f g
        | .includes => T.truthSubset g f)

end Theory

/-- The claim holds in the theory. -/
def Holds (T : Theory) (c : Claim) : Prop := T.check c = some true
/-- The claim is expressible and does not hold. -/
def Fails (T : Theory) (c : Claim) : Prop := T.check c = some false

instance (T : Theory) (c : Claim) : Decidable (Holds T c) := inferInstanceAs (Decidable (_ = _))
instance (T : Theory) (c : Claim) : Decidable (Fails T c) := inferInstanceAs (Decidable (_ = _))

end Linglab
