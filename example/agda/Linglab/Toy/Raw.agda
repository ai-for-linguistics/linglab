{-# OPTIONS --safe --without-K #-}
-- Raw Facts: the theory made of the facts themselves. Each fact is listed with
-- its expected outcome; its "proof" is membership in the list. Lists the same
-- claims as `data/statements.json` (hand-written for now; `linglab listing` will
-- generate it). Checks the setup and that no claim is listed with both outcomes.
module Linglab.Toy.Raw where

open import Linglab.Prelude
open import Linglab.Theory
open import Linglab.Toy.Principles using (s; p; q; a)

record Listed : Set where
  constructor listed
  field
    id       : String
    claim    : Claim
    expected : Bool          -- true = holds, false = fails

eqListed : Listed → Listed → Bool
eqListed (listed i c e) (listed i' c' e') = eqString i i' ∧ eqClaim c c' ∧ eqBool e e'

facts : List Listed
facts =
    listed "F01" (felicitous ((s ∧ₛ a) ∷ [])) true
  ∷ listed "F02" (felicitous ((a ∧ₛ s) ∷ [])) false
  ∷ listed "F03" (felicitous (a ∷ [])) false
  ∷ listed "F04" (felicitous ((¬ₛ s ∨ₛ a) ∷ [])) true
  ∷ listed "F05a" (entails ((p ∧ₛ q) ∷ []) (q ∧ₛ p)) true
  ∷ listed "F05b" (entails ((q ∧ₛ p) ∷ []) (p ∧ₛ q)) true
  ∷ listed "F06" (entails (p ∷ []) (p ∧ₛ q)) false
  ∷ listed "F07" (entails [] (a ∨ₛ ¬ₛ a)) false
  ∷ listed "F08" (consistent (s ∷ ¬ₛ s ∷ [])) false
  ∷ listed "F09" (truth (s ∧ₛ a) equals a) true
  ∷ []

-- No claim is listed with both outcomes.
consistent-listing :
  all (λ x → all (λ y → not (eqClaim (Listed.claim x) (Listed.claim y) ∧ not (eqBool (Listed.expected x) (Listed.expected y)))) facts) facts ≡ true
consistent-listing = refl

F01 : elem eqListed (listed "F01" (felicitous ((s ∧ₛ a) ∷ [])) true) facts ≡ true
F01 = refl

F02 : elem eqListed (listed "F02" (felicitous ((a ∧ₛ s) ∷ [])) false) facts ≡ true
F02 = refl

F03 : elem eqListed (listed "F03" (felicitous (a ∷ [])) false) facts ≡ true
F03 = refl

F04 : elem eqListed (listed "F04" (felicitous ((¬ₛ s ∨ₛ a) ∷ [])) true) facts ≡ true
F04 = refl

F05a : elem eqListed (listed "F05a" (entails ((p ∧ₛ q) ∷ []) (q ∧ₛ p)) true) facts ≡ true
F05a = refl

F05b : elem eqListed (listed "F05b" (entails ((q ∧ₛ p) ∷ []) (p ∧ₛ q)) true) facts ≡ true
F05b = refl

F06 : elem eqListed (listed "F06" (entails (p ∷ []) (p ∧ₛ q)) false) facts ≡ true
F06 = refl

F07 : elem eqListed (listed "F07" (entails [] (a ∨ₛ ¬ₛ a)) false) facts ≡ true
F07 = refl

F08 : elem eqListed (listed "F08" (consistent (s ∷ ¬ₛ s ∷ [])) false) facts ≡ true
F08 = refl

F09 : elem eqListed (listed "F09" (truth (s ∧ₛ a) equals a) true) facts ≡ true
F09 = refl
