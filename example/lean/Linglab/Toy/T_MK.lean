import Linglab.Toy.Principles
/-! Theory T_MK = NEG AND-MK OR-MK ENT-T FELIC-DEF AUX-PRESUP. Facts below: F.. = claim proved; F.._fail = its negation proved. -/
namespace T_MK
open Linglab Linglab.Toy

/-- T_MK as a set of principles: NEG AND-MK OR-MK ENT-T FELIC-DEF AUX-PRESUP -/
def theory : Theory := Bundle.toTheory
  { name := "T_MK"
    conns := { neg := some negV, and := some andMK, or := some orMK }
    constraint := auxPresup
    ent := entT
    felic := felicDef }

theorem F01 : Holds theory (.felicitous [.and s a]) := by decide
theorem F02_fail : Fails theory (.felicitous [.and a s]) := by decide
theorem F03_fail : Fails theory (.felicitous [a]) := by decide
theorem F04 : Holds theory (.felicitous [.or (.not s) a]) := by decide
theorem F05a : Holds theory (.entails [.and p q] (.and q p)) := by decide
theorem F05b : Holds theory (.entails [.and q p] (.and p q)) := by decide
theorem F06_fail : Fails theory (.entails [p] (.and p q)) := by decide
theorem F07_fail : Fails theory (.entails [] (.or a (.not a))) := by decide
theorem F08_fail : Fails theory (.consistent [s, .not s]) := by decide
theorem F09 : Holds theory (.truth (.and s a) .equals a) := by decide

end T_MK
