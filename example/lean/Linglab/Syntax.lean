/-! Shared syntax S: every fact is written over it, every theory translates it
(or cannot: then the fact is out of scope for that theory).
Add an operator = add a constructor; theories that do not know it return `none`
(end every `translate`/evaluator with a wildcard case `| _ => none`).

Version 2 (JSON forms in docs/INTERFACE.md section 1): predicates over terms,
`iff`, generalized quantifiers `some/every/no x R S`, first-order `exist/forall'`,
modals `must/may`, and `op1/op2 name args` for theory-defined operators (for example "exh"). -/
namespace Linglab

/-- Individual terms: constants and variables (`"?x"` in the data files is `var "x"`). -/
inductive Term where
  | const (n : String)
  | var (n : String)
  deriving DecidableEq, Repr

inductive S where
  | atom (n : String)
  | not (a : S)
  | and (a b : S)
  | or (a b : S)
  | imp (a b : S)
  | iff (a b : S)
  /-- predicate application `["Student","?x"]` -/
  | pred (n : String) (args : List Term)
  /-- generalized quantifiers: variable, restrictor, scope -/
  | some (x : String) (r s : S)
  | every (x : String) (r s : S)
  | no (x : String) (r s : S)
  /-- first-order quantifiers -/
  | exist (x : String) (a : S)
  | forall' (x : String) (a : S)
  /-- modals (flavour left to the theory) -/
  | must (a : S)
  | may (a : S)
  /-- any other operator, defined by theories (for example `op1 "exh" a`). A generic
  `op (name) (args : List S)` is a nested inductive and `DecidableEq` cannot be derived for it,
  so arities 1 and 2 get a constructor each. -/
  | op1 (name : String) (a : S)
  | op2 (name : String) (a b : S)
  deriving DecidableEq, Repr

/-- A discourse is a list of sentences. -/
abbrev Discourse := List S

end Linglab
