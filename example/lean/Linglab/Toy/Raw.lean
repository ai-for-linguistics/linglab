import Linglab.Theory
import Linglab.Toy.Principles
/-! Raw Facts: the theory made of the facts themselves. Each fact is listed with
its expected outcome; its "proof" is membership in the list. Lists the same
claims as `data/statements.json` (hand-written for now; `linglab listing` will
generate it). Checks the setup and that no claim is listed with both outcomes. -/
namespace Raw
open Linglab Linglab.Toy

structure Listed where
  id : String
  claim : Claim
  expected : Bool   -- true = holds, false = fails
  deriving DecidableEq

def facts : List Listed := [
  ⟨"F01", .felicitous [.and s a], true⟩,
  ⟨"F02", .felicitous [.and a s], false⟩,
  ⟨"F03", .felicitous [a], false⟩,
  ⟨"F04", .felicitous [.or (.not s) a], true⟩,
  ⟨"F05a", .entails [.and p q] (.and q p), true⟩,
  ⟨"F05b", .entails [.and q p] (.and p q), true⟩,
  ⟨"F06", .entails [p] (.and p q), false⟩,
  ⟨"F07", .entails [] (.or a (.not a)), false⟩,
  ⟨"F08", .consistent [s, .not s], false⟩,
  ⟨"F09", .truth (.and s a) .equals a, true⟩ ]

/-- No claim is listed with both outcomes. -/
theorem consistent_listing :
    facts.all (fun x => facts.all fun y => !(x.claim == y.claim && x.expected != y.expected)) = true := by
  decide

theorem F01 : (⟨"F01", .felicitous [.and s a], true⟩ : Listed) ∈ facts := by decide
theorem F02 : (⟨"F02", .felicitous [.and a s], false⟩ : Listed) ∈ facts := by decide
theorem F03 : (⟨"F03", .felicitous [a], false⟩ : Listed) ∈ facts := by decide
theorem F04 : (⟨"F04", .felicitous [.or (.not s) a], true⟩ : Listed) ∈ facts := by decide
theorem F05a : (⟨"F05a", .entails [.and p q] (.and q p), true⟩ : Listed) ∈ facts := by decide
theorem F05b : (⟨"F05b", .entails [.and q p] (.and p q), true⟩ : Listed) ∈ facts := by decide
theorem F06 : (⟨"F06", .entails [p] (.and p q), false⟩ : Listed) ∈ facts := by decide
theorem F07 : (⟨"F07", .entails [] (.or a (.not a)), false⟩ : Listed) ∈ facts := by decide
theorem F08 : (⟨"F08", .consistent [s, .not s], false⟩ : Listed) ∈ facts := by decide
theorem F09 : (⟨"F09", .truth (.and s a) .equals a, true⟩ : Listed) ∈ facts := by decide

end Raw
