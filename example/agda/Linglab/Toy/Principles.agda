{-# OPTIONS --safe --without-K #-}
-- The principles of the toy fragment, one tagged chunk each. A theory is a
-- choice of principles (see T_SK.agda etc.). Size is measured on the chunks.
module Linglab.Toy.Principles where

open import Linglab.Prelude
open import Linglab.Theory
open import Linglab.Toy.Base

-- BEGIN principle:P-NEG
negV : Val → Val
negV one = zero
negV zero = one
negV und = und
-- END principle:P-NEG

-- BEGIN principle:P-AND-SK
andSK : Val → Val → Val
andSK zero _ = zero
andSK _ zero = zero
andSK one one = one
andSK _ _ = und
-- END principle:P-AND-SK

-- BEGIN principle:P-AND-WK
andWK : Val → Val → Val
andWK und _ = und
andWK _ und = und
andWK one one = one
andWK _ _ = zero
-- END principle:P-AND-WK

-- BEGIN principle:P-AND-MK
andMK : Val → Val → Val
andMK zero _ = zero
andMK und _ = und
andMK one y = y
-- END principle:P-AND-MK

-- BEGIN principle:P-OR-SK
orSK : Val → Val → Val
orSK one _ = one
orSK _ one = one
orSK zero zero = zero
orSK _ _ = und
-- END principle:P-OR-SK

-- BEGIN principle:P-OR-WK
orWK : Val → Val → Val
orWK und _ = und
orWK _ und = und
orWK zero zero = zero
orWK _ _ = one
-- END principle:P-OR-WK

-- BEGIN principle:P-OR-MK
orMK : Val → Val → Val
orMK one _ = one
orMK und _ = und
orMK zero y = y
-- END principle:P-OR-MK

-- BEGIN principle:P-ENT-T
entT : List Model → (Model → S → Val) → List S → S → Bool
entT ms v ps c = all (λ m → not (all (λ p → eqVal (v m p) one) ps) ∨ eqVal (v m c) one) ms
-- END principle:P-ENT-T

-- BEGIN principle:P-FELIC-DEF
felicDef : List Model → (Model → S → Val) → List S → Bool
felicDef ms v d = all (λ m → all (λ f → not (eqVal (v m f) und)) d) ms
-- END principle:P-FELIC-DEF

-- BEGIN principle:P-FELIC-SOME
felicSome : List Model → (Model → S → Val) → List S → Bool
felicSome ms v d = any (λ m → all (λ f → not (eqVal (v m f) und)) d) ms
-- END principle:P-FELIC-SOME

-- BEGIN principle:P-AUX-PRESUP
auxPresup : Model → Bool
auxPresup m = eqBool (eqVal (Model.va m) und) (not (Model.vs m))
-- END principle:P-AUX-PRESUP

-- Atoms of the fragment.
s p q a : S
s = atom "s"
p = atom "p"
q = atom "q"
a = atom "a"
