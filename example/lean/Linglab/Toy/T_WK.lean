import Linglab.Toy.Principles
/-! Theory T_WK = NEG AND-WK ENT-T FELIC-DEF AUX-PRESUP. Facts below: F.. = claim proved; F.._fail = its negation proved. -/
namespace T_WK
open Linglab Linglab.Toy

/-- T_WK as a set of principles: NEG AND-WK ENT-T FELIC-DEF AUX-PRESUP -/
def theory : Theory := Bundle.toTheory
  { name := "T_WK"
    conns := { neg := some negV, and := some andWK, or := none }
    constraint := auxPresup
    ent := entT
    felic := felicDef }

theorem F01_fail : Fails theory (.felicitous [.and s a]) := by decide
theorem F02_fail : Fails theory (.felicitous [.and a s]) := by decide
theorem F03_fail : Fails theory (.felicitous [a]) := by decide
-- F04: not expressible in T_WK (no disjunction): out of scope, no theorem.
theorem F05a : Holds theory (.entails [.and p q] (.and q p)) := by decide
theorem F05b : Holds theory (.entails [.and q p] (.and p q)) := by decide
theorem F06_fail : Fails theory (.entails [p] (.and p q)) := by decide
-- F07: not expressible in T_WK (no disjunction): out of scope, no theorem.
theorem F08_fail : Fails theory (.consistent [s, .not s]) := by decide
theorem F09 : Holds theory (.truth (.and s a) .equals a) := by decide

end T_WK
