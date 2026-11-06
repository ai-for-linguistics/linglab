import Linglab.Toy.Base
/-! The principles of the toy fragment, one tagged chunk each. A theory is a
choice of principles (see T_SK.lean etc.). Size is measured on the chunks. -/
namespace Linglab.Toy
open Linglab

-- BEGIN principle:P-NEG
def negV : Val → Val
  | .one => .zero | .zero => .one | .und => .und
-- END principle:P-NEG

-- BEGIN principle:P-AND-SK
def andSK : Val → Val → Val
  | .zero, _ => .zero | _, .zero => .zero
  | .one, .one => .one | _, _ => .und
-- END principle:P-AND-SK

-- BEGIN principle:P-AND-WK
def andWK : Val → Val → Val
  | .und, _ => .und | _, .und => .und
  | .one, .one => .one | _, _ => .zero
-- END principle:P-AND-WK

-- BEGIN principle:P-AND-MK
def andMK : Val → Val → Val
  | .zero, _ => .zero | .und, _ => .und | .one, y => y
-- END principle:P-AND-MK

-- BEGIN principle:P-OR-SK
def orSK : Val → Val → Val
  | .one, _ => .one | _, .one => .one
  | .zero, .zero => .zero | _, _ => .und
-- END principle:P-OR-SK

-- BEGIN principle:P-OR-WK
def orWK : Val → Val → Val
  | .und, _ => .und | _, .und => .und
  | .zero, .zero => .zero | _, _ => .one
-- END principle:P-OR-WK

-- BEGIN principle:P-OR-MK
def orMK : Val → Val → Val
  | .one, _ => .one | .und, _ => .und | .zero, y => y
-- END principle:P-OR-MK

-- BEGIN principle:P-ENT-T
def entT (ms : List Model) (v : Model → S → Val) (ps : List S) (c : S) : Bool :=
  ms.all fun m => !ps.all (fun p => v m p == .one) || v m c == .one
-- END principle:P-ENT-T

-- BEGIN principle:P-FELIC-DEF
def felicDef (ms : List Model) (v : Model → S → Val) (d : List S) : Bool :=
  ms.all fun m => d.all fun f => v m f != .und
-- END principle:P-FELIC-DEF

-- BEGIN principle:P-FELIC-SOME
def felicSome (ms : List Model) (v : Model → S → Val) (d : List S) : Bool :=
  ms.any fun m => d.all fun f => v m f != .und
-- END principle:P-FELIC-SOME

-- BEGIN principle:P-AUX-PRESUP
def auxPresup (m : Model) : Bool := (m.a == Val.und) == !m.s
-- END principle:P-AUX-PRESUP

/-- Atoms of the fragment. -/
def s : S := .atom "s"
def p : S := .atom "p"
def q : S := .atom "q"
def a : S := .atom "a"

end Linglab.Toy
