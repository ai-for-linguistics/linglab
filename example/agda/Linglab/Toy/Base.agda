{-# OPTIONS --safe --without-K #-}
-- Toy presupposition fragment: models, values and the evaluator shared by all
-- toy theories. The theories differ only in the principles they plug in.
module Linglab.Toy.Base where

open import Linglab.Prelude
open import Linglab.Theory

-- 1, 0 or # (undefined)
data Val : Set where
  one zero und : Val

eqVal : Val → Val → Bool
eqVal one one = true
eqVal zero zero = true
eqVal und und = true
eqVal _ _ = false

-- Valuation of s (there is a king), p, q, and a (the king is bald).
record Model : Set where
  constructor mk
  field
    vs vp vq : Bool
    va : Val
open Model

-- All valuations before any model constraint (24).
allModels : List Model
allModels =
  concatMap (λ s → concatMap (λ p → concatMap (λ q →
    map (λ a → mk s p q a) (one ∷ zero ∷ und ∷ [])) (false ∷ true ∷ [])) (false ∷ true ∷ [])) (false ∷ true ∷ [])

fromBool : Bool → Val
fromBool true = one
fromBool false = zero

lookupAtom : Model → String → Val
lookupAtom m n =
  if eqString n "s" then fromBool (vs m) else
  if eqString n "p" then fromBool (vp m) else
  if eqString n "q" then fromBool (vq m) else
  if eqString n "a" then va m else und

-- A theory's connectives: `nothing` = the theory has no such connective.
record Conns : Set where
  field
    neg : Maybe (Val → Val)
    and : Maybe (Val → Val → Val)
    or  : Maybe (Val → Val → Val)

-- Value of a sentence in a model.
eval : Conns → Model → S → Maybe Val
eval c m (atom n) = just (lookupAtom m n)
eval c m (¬ₛ a) = do
  f ← Conns.neg c
  x ← eval c m a
  just (f x)
eval c m (a ∧ₛ b) = do
  f ← Conns.and c
  x ← eval c m a
  y ← eval c m b
  just (f x y)
eval c m (a ∨ₛ b) = do
  f ← Conns.or c
  x ← eval c m a
  y ← eval c m b
  just (f x y)
eval c m _ = nothing

-- Everything a toy theory is made of: the principles it switches on.
record Bundle : Set where
  field
    name       : String
    conns      : Conns
    constraint : Model → Bool                                         -- model constraint (auxiliary)
    ent        : List Model → (Model → S → Val) → List S → S → Bool   -- consequence
    felic      : List Model → (Model → S → Val) → List S → Bool       -- felicity

bval : Bundle → Model → S → Val
bval b m f with eval (Bundle.conns b) m f
... | just v = v
... | nothing = und

-- Build the generic `Theory` from a bundle. Forms are the shared sentences
-- themselves; `translate` fails when a connective is missing.
toTheory : Bundle → Theory
toTheory b = record
  { name      = Bundle.name b
  ; Form      = S
  ; Model     = Model
  ; models    = ms
  ; translate = λ f → mapMaybe (λ _ → f) (eval (Bundle.conns b) (mk true true true one) f)
  ; trueIn    = λ m f → eqVal (bval b m f) one
  ; definedIn = λ m f → not (eqVal (bval b m f) und)
  ; ent       = Bundle.ent b ms (bval b)
  ; felic     = Bundle.felic b ms (bval b)
  ; cons      = λ ps → any (λ m → all (λ f → eqVal (bval b m f) one) ps) ms
  }
  where ms = filter (Bundle.constraint b) allModels
