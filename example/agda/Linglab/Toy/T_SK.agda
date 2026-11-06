{-# OPTIONS --safe --without-K #-}
-- Theory T_SK = NEG AND-SK OR-SK ENT-T FELIC-DEF AUX-PRESUP. Facts below: F.. = claim proved; F.._fail = its negation proved.
module Linglab.Toy.T_SK where

open import Linglab.Prelude
open import Linglab.Theory
open import Linglab.Toy.Base
open import Linglab.Toy.Principles

-- T_SK as a set of principles: NEG AND-SK OR-SK ENT-T FELIC-DEF AUX-PRESUP
theory : Theory
theory = toTheory record
  { name       = "T_SK"
  ; conns      = record { neg = just negV ; and = just andSK ; or = just orSK }
  ; constraint = auxPresup
  ; ent        = entT
  ; felic      = felicDef
  }

F01 : Holds theory (felicitous ((s ∧ₛ a) ∷ []))
F01 = refl

F02 : Holds theory (felicitous ((a ∧ₛ s) ∷ []))
F02 = refl

F03_fail : Fails theory (felicitous (a ∷ []))
F03_fail = refl

F04 : Holds theory (felicitous ((¬ₛ s ∨ₛ a) ∷ []))
F04 = refl

F05a : Holds theory (entails ((p ∧ₛ q) ∷ []) (q ∧ₛ p))
F05a = refl

F05b : Holds theory (entails ((q ∧ₛ p) ∷ []) (p ∧ₛ q))
F05b = refl

F06_fail : Fails theory (entails (p ∷ []) (p ∧ₛ q))
F06_fail = refl

F07_fail : Fails theory (entails [] (a ∨ₛ ¬ₛ a))
F07_fail = refl

F08_fail : Fails theory (consistent (s ∷ ¬ₛ s ∷ []))
F08_fail = refl

F09 : Holds theory (truth (s ∧ₛ a) equals a)
F09 = refl
