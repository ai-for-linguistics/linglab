{-# OPTIONS --safe --without-K #-}
-- The Theory interface.
--
-- A theory says: which models exist (a finite list), how to translate the shared
-- syntax into its own formulas (`nothing` = cannot express it = out of scope), when a
-- formula is true / defined in a model, and its own notions of consequence
-- (`ent`), felicity (`felic`), consistency (`cons`) over those models.
--
-- A fact is a `Claim` over the shared syntax. For a theory T:
--   Holds T c  the claim is expressible in T and true
--   Fails T c  the claim is expressible in T and false (the negation)
-- Out of scope: neither Holds nor Fails is provable (no vacuous truth).
-- Proofs are `refl`: every check is a Bool computed over the finite model list.
module Linglab.Theory where

open import Linglab.Prelude
open import Linglab.Syntax public

record Theory : Set₁ where
  field
    name      : String
    Form      : Set                          -- the theory's own formulas
    Model     : Set                          -- the models
    models    : List Model                   -- complete finite list (constraints already applied)
    translate : S → Maybe Form               -- nothing = not expressible
    trueIn    : Model → Form → Bool          -- the formula is true in the model
    definedIn : Model → Form → Bool          -- the formula has a truth value in the model
    ent       : List Form → Form → Bool      -- consequence
    felic     : List Form → Bool             -- felicity (null context)
    cons      : List Form → Bool             -- consistency

-- How a truth set relates to another: equal, within, includes.
data Rel : Set where
  equals within includes : Rel

-- The shapes of fact (SPEC section 2). Equivalence = two `entails`.
data Claim : Set where
  entails    : List S → S → Claim
  felicitous : List S → Claim
  consistent : List S → Claim
  truth      : S → Rel → S → Claim

eqRel : Rel → Rel → Bool
eqRel equals equals = true
eqRel within within = true
eqRel includes includes = true
eqRel _ _ = false

eqClaim : Claim → Claim → Bool
eqClaim (entails ps c) (entails qs d) = eqList eqS ps qs ∧ eqS c d
eqClaim (felicitous a) (felicitous b) = eqList eqS a b
eqClaim (consistent a) (consistent b) = eqList eqS a b
eqClaim (truth s r t) (truth s' r' t') = eqS s s' ∧ eqRel r r' ∧ eqS t t'
eqClaim _ _ = false

-- translate a whole list; nothing if any sentence is not expressible
translateAll : (T : Theory) → List S → Maybe (List (Theory.Form T))
translateAll T [] = just []
translateAll T (x ∷ xs) = do
  f ← Theory.translate T x
  fs ← translateAll T xs
  just (f ∷ fs)

truthSubset : (T : Theory) → Theory.Form T → Theory.Form T → Bool
truthSubset T f g =
  all (λ m → not (Theory.trueIn T m f) ∨ Theory.trueIn T m g) (Theory.models T)

-- The verdict of the claim: nothing = out of scope, just b = the claim is b.
check : (T : Theory) → Claim → Maybe Bool
check T (entails ps c) = do
  fs ← translateAll T ps
  f ← Theory.translate T c
  just (Theory.ent T fs f)
check T (felicitous d) = do
  fs ← translateAll T d
  just (Theory.felic T fs)
check T (consistent ps) = do
  fs ← translateAll T ps
  just (Theory.cons T fs)
check T (truth s r t) = do
  f ← Theory.translate T s
  g ← Theory.translate T t
  just (verdict r f g)
  where
    verdict : Rel → Theory.Form T → Theory.Form T → Bool
    verdict equals f g = truthSubset T f g ∧ truthSubset T g f
    verdict within f g = truthSubset T f g
    verdict includes f g = truthSubset T g f

-- The claim holds in the theory.
Holds : Theory → Claim → Set
Holds T c = check T c ≡ just true

-- The claim is expressible and does not hold.
Fails : Theory → Claim → Set
Fails T c = check T c ≡ just false
