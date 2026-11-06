import Linglab.Theory
/-! Toy presupposition fragment: models, values and the evaluator shared by all
toy theories. The theories differ only in the principles they plug in. -/
namespace Linglab.Toy
open Linglab

/-- 1, 0 or # (undefined) -/
inductive Val | one | zero | und
  deriving DecidableEq, Repr

/-- Valuation of s (there is a king), p, q, and a (the king is bald). -/
structure Model where
  s : Bool
  p : Bool
  q : Bool
  a : Val
  deriving DecidableEq, Repr

/-- All valuations before any model constraint (24). -/
def allModels : List Model :=
  [false, true].flatMap fun s => [false, true].flatMap fun p =>
  [false, true].flatMap fun q => [Val.one, Val.zero, Val.und].map fun a => ⟨s, p, q, a⟩

def Model.lookup (m : Model) : String → Val
  | "s" => if m.s then .one else .zero
  | "p" => if m.p then .one else .zero
  | "q" => if m.q then .one else .zero
  | "a" => m.a
  | _ => .und

/-- A theory's connectives: `none` = the theory has no such connective. -/
structure Conns where
  neg : Option (Val → Val)
  and : Option (Val → Val → Val)
  or : Option (Val → Val → Val)

/-- Value of a sentence in a model. -/
def eval (c : Conns) (m : Model) : S → Option Val
  | .atom n => some (m.lookup n)
  | .not a => do let f ← c.neg; let x ← eval c m a; pure (f x)
  | .and a b => do let f ← c.and; let x ← eval c m a; let y ← eval c m b; pure (f x y)
  | .or a b => do let f ← c.or; let x ← eval c m a; let y ← eval c m b; pure (f x y)
  | _ => none

/-- Everything a toy theory is made of: the principles it switches on. -/
structure Bundle where
  name : String
  conns : Conns
  /-- model constraint (auxiliary) -/
  constraint : Model → Bool
  /-- vocabulary: consequence / felicity, given the models and the evaluator -/
  ent : List Model → (Model → S → Val) → List S → S → Bool
  felic : List Model → (Model → S → Val) → List S → Bool

def Bundle.val (b : Bundle) (m : Model) (f : S) : Val := (eval b.conns m f).getD .und

/-- Build the generic `Theory` from a bundle. Forms are the shared sentences
themselves; `translate` fails when a connective is missing. -/
def Bundle.toTheory (b : Bundle) : Theory :=
  let ms := allModels.filter b.constraint
  { name := b.name
    Form := S
    Model := Model
    models := ms
    translate := fun f => (eval b.conns ⟨true, true, true, .one⟩ f).map fun _ => f
    trueIn := fun m f => b.val m f == .one
    definedIn := fun m f => b.val m f != .und
    ent := b.ent ms b.val
    felic := b.felic ms b.val
    cons := fun ps => ms.any fun m => ps.all fun f => b.val m f == .one }

end Linglab.Toy
