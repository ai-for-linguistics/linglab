"""Toy presupposition fragment: principles as tagged chunks.

Values are 1 (true), 0 (false) and "#" (undefined). Atoms: s ("there is a king"),
p, q (plain), a ("the king is bald", presupposes s).
"""
import itertools

from linglab.vocab import principle, base_models

U = "#"


@base_models
def toy_models():
    """All valuations of s, p, q and a in {1, 0, #}: 24 candidates. P-AUX-PRESUP keeps 12."""
    for s, p, q, a in itertools.product((0, 1), (0, 1), (0, 1), (1, 0, U)):
        yield {"s": s, "p": p, "q": q, "a": a}


# BEGIN principle:P-NEG
@principle("P-NEG")
def neg(b):
    b.connective("not", lambda x: x if x == U else 1 - x)
# END principle:P-NEG


# BEGIN principle:P-AND-SK
@principle("P-AND-SK")
def and_sk(b):
    b.connective("and", lambda x, y: 0 if 0 in (x, y) else (1 if x == y == 1 else U))
# END principle:P-AND-SK


# BEGIN principle:P-AND-WK
@principle("P-AND-WK")
def and_wk(b):
    b.connective("and", lambda x, y: U if U in (x, y) else x * y)
# END principle:P-AND-WK


# BEGIN principle:P-AND-MK
@principle("P-AND-MK")
def and_mk(b):
    # left to right: a false or undefined left conjunct settles the value
    b.connective("and", lambda x, y: x if x in (0, U) else y)
# END principle:P-AND-MK


# BEGIN principle:P-OR-SK
@principle("P-OR-SK")
def or_sk(b):
    b.connective("or", lambda x, y: 1 if 1 in (x, y) else (0 if x == y == 0 else U))
# END principle:P-OR-SK


# BEGIN principle:P-OR-WK
@principle("P-OR-WK")
def or_wk(b):
    b.connective("or", lambda x, y: U if U in (x, y) else max(x, y))
# END principle:P-OR-WK


# BEGIN principle:P-OR-MK
@principle("P-OR-MK")
def or_mk(b):
    b.connective("or", lambda x, y: x if x in (1, U) else y)
# END principle:P-OR-MK


# BEGIN principle:P-ENT-T
@principle("P-ENT-T")
def ent_t(b):
    # entailment: whenever all premises are true, the conclusion is true
    b.set("ent_ok", lambda T, m, prem, concl: not all(T.true_in(m, p) for p in prem) or T.true_in(m, concl))
# END principle:P-ENT-T


# BEGIN principle:P-FELIC-DEF
@principle("P-FELIC-DEF")
def felic_def(b):
    # felicitous iff defined in every model
    b.set("felic_kind", "forall")
    b.set("felic_ok", lambda T, m, disc: all(T.defined_in(m, f) for f in disc))
# END principle:P-FELIC-DEF


# BEGIN principle:P-FELIC-SOME
@principle("P-FELIC-SOME")
def felic_some(b):
    # felicitous iff defined in some model
    b.set("felic_kind", "exists")
    b.set("felic_ok", lambda T, m, disc: all(T.defined_in(m, f) for f in disc))
# END principle:P-FELIC-SOME


# BEGIN principle:P-AUX-PRESUP
@principle("P-AUX-PRESUP")
def aux_presup(b):
    # auxiliary: a is undefined exactly when there is no king
    b.constrain(lambda m: (m.vals["a"] == U) == (m.vals["s"] == 0))
# END principle:P-AUX-PRESUP
