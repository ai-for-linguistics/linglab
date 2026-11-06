{-# OPTIONS --safe --without-K #-}
-- Minimal prelude (no standard library): Bool, List, Maybe, String, equality, and a few helpers.
module Linglab.Prelude where

open import Agda.Builtin.Bool public
open import Agda.Builtin.List public
open import Agda.Builtin.Maybe public
open import Agda.Builtin.String public
open import Agda.Builtin.Equality public

infixr 6 _∧_
infixr 5 _∨_

not : Bool → Bool
not true = false
not false = true

_∧_ : Bool → Bool → Bool
true ∧ b = b
false ∧ _ = false

_∨_ : Bool → Bool → Bool
true ∨ _ = true
false ∨ b = b

if_then_else_ : {A : Set} → Bool → A → A → A
if true then x else _ = x
if false then _ else y = y

eqBool : Bool → Bool → Bool
eqBool true b = b
eqBool false b = not b

eqString : String → String → Bool
eqString = primStringEquality

map : {A B : Set} → (A → B) → List A → List B
map f [] = []
map f (x ∷ xs) = f x ∷ map f xs

filter : {A : Set} → (A → Bool) → List A → List A
filter p [] = []
filter p (x ∷ xs) = if p x then x ∷ filter p xs else filter p xs

_++_ : {A : Set} → List A → List A → List A
[] ++ ys = ys
(x ∷ xs) ++ ys = x ∷ (xs ++ ys)

concatMap : {A B : Set} → (A → List B) → List A → List B
concatMap f [] = []
concatMap f (x ∷ xs) = f x ++ concatMap f xs

all : {A : Set} → (A → Bool) → List A → Bool
all p [] = true
all p (x ∷ xs) = p x ∧ all p xs

any : {A : Set} → (A → Bool) → List A → Bool
any p [] = false
any p (x ∷ xs) = p x ∨ any p xs

eqList : {A : Set} → (A → A → Bool) → List A → List A → Bool
eqList e [] [] = true
eqList e (x ∷ xs) (y ∷ ys) = e x y ∧ eqList e xs ys
eqList e _ _ = false

elem : {A : Set} → (A → A → Bool) → A → List A → Bool
elem e x ys = any (e x) ys

infixl 1 _>>=_ _>>_
_>>=_ : {A B : Set} → Maybe A → (A → Maybe B) → Maybe B
nothing >>= _ = nothing
just x >>= f = f x

_>>_ : {A B : Set} → Maybe A → Maybe B → Maybe B
m >> k = m >>= λ _ → k

mapMaybe : {A B : Set} → (A → B) → Maybe A → Maybe B
mapMaybe f nothing = nothing
mapMaybe f (just x) = just (f x)
