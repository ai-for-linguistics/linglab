{-# OPTIONS --safe --without-K #-}
-- Shared syntax S: every fact is written over it, every theory translates it
-- (or cannot: then the fact is out of scope for that theory).
-- Add an operator = add a constructor; theories that do not know it return `nothing`
-- (end every translate/evaluator with a wildcard clause `_ = nothing`).
-- Version 2 (JSON forms in docs/INTERFACE.md section 1): predicates over terms, iff,
-- generalized quantifiers someₛ/everyₛ/noₛ x R S, first-order existsₛ/forallₛ,
-- modals mustₛ/mayₛ, and op1/op2 name args for theory-defined operators (for example "exh").
module Linglab.Syntax where

open import Linglab.Prelude

infixr 8 ¬ₛ_
infixr 7 _∧ₛ_
infixr 6 _∨ₛ_
infixr 5 _⇒ₛ_
infixr 4 _⇔ₛ_

-- Individual terms: constants and variables ("?x" in the data files is varₜ "x").
data Term : Set where
  constₜ : String → Term
  varₜ   : String → Term

eqTerm : Term → Term → Bool
eqTerm (constₜ a) (constₜ b) = eqString a b
eqTerm (varₜ a) (varₜ b) = eqString a b
eqTerm _ _ = false

data S : Set where
  atom  : String → S
  ¬ₛ_   : S → S
  _∧ₛ_  : S → S → S
  _∨ₛ_  : S → S → S
  _⇒ₛ_  : S → S → S
  _⇔ₛ_  : S → S → S
  pred    : String → List Term → S            -- ["Student","?x"]
  someₛ   : String → S → S → S                -- variable, restrictor, scope
  everyₛ  : String → S → S → S
  noₛ     : String → S → S → S
  existsₛ : String → S → S                    -- first-order
  forallₛ : String → S → S
  mustₛ   : S → S                             -- modals (flavour left to the theory)
  mayₛ    : S → S
  op1     : String → S → S                    -- theory-defined operators, arity 1 and 2
  op2     : String → S → S → S

-- A discourse is a list of sentences.
Discourse : Set
Discourse = List S

eqS : S → S → Bool
eqS (atom a) (atom b) = eqString a b
eqS (¬ₛ a) (¬ₛ b) = eqS a b
eqS (a ∧ₛ b) (c ∧ₛ d) = eqS a c ∧ eqS b d
eqS (a ∨ₛ b) (c ∨ₛ d) = eqS a c ∧ eqS b d
eqS (a ⇒ₛ b) (c ⇒ₛ d) = eqS a c ∧ eqS b d
eqS (a ⇔ₛ b) (c ⇔ₛ d) = eqS a c ∧ eqS b d
eqS (pred n as) (pred m bs) = eqString n m ∧ eqList eqTerm as bs
eqS (someₛ x r s) (someₛ y r' s') = eqString x y ∧ eqS r r' ∧ eqS s s'
eqS (everyₛ x r s) (everyₛ y r' s') = eqString x y ∧ eqS r r' ∧ eqS s s'
eqS (noₛ x r s) (noₛ y r' s') = eqString x y ∧ eqS r r' ∧ eqS s s'
eqS (existsₛ x a) (existsₛ y b) = eqString x y ∧ eqS a b
eqS (forallₛ x a) (forallₛ y b) = eqString x y ∧ eqS a b
eqS (mustₛ a) (mustₛ b) = eqS a b
eqS (mayₛ a) (mayₛ b) = eqS a b
eqS (op1 n a) (op1 m b) = eqString n m ∧ eqS a b
eqS (op2 n a b) (op2 m c d) = eqString n m ∧ eqS a c ∧ eqS b d
eqS _ _ = false
