"""Theorems are checked against the facts' claims (`linglab lean`).

A theorem named after a fact (`F12`, or `F12_fail` for the negation) in the unit of a theory is only a
candidate. It is credited when a generated check file accepts it as a proof of the statement written by
the tool from `data/statements.json`: `Holds <unit>.theory <claim>` (`Fails` for `_fail`). So a theorem
that states something else, a file that is never compiled, or a fact whose spec changed after the theorem
was written gives no entry, and the run says why.

Claims are rendered from the shared syntax (docs/INTERFACE.md section 1) into Lean terms."""
import os

from . import runner, vocab
from .common import today

CLAIM_TYPES = {"entailment", "felicity", "consistency", "truth"}
RELS = ("equals", "within", "includes")
UNARY = ("not", "must", "may")
BINARY = ("and", "or", "if", "iff")
GQ = ("some", "every", "no")
FO = ("exists", "forall")


class Unstatable(Exception):
    """The fact has no claim the proof interface can state."""


def _var(x):
    return isinstance(x, str) and x.startswith("?") and len(x) > 1


def sentence(s):
    """Shared-syntax JSON -> AST: ("atom", n) | (head, A) | (head, A, B) | ("pred", n, [("var"|"const", n)])
    | (gq, x, R, S) | (fo, x, A) | ("op", name, [A] or [A, B])."""
    if isinstance(s, str):
        if _var(s):
            raise Unstatable("variable %r used as a sentence" % s)
        return ("atom", s)
    if not isinstance(s, list) or not s or not isinstance(s[0], str):
        raise Unstatable("malformed sentence %r" % (s,))
    h, args = s[0], s[1:]
    if h in UNARY or h in BINARY:
        if len(args) != (1 if h in UNARY else 2):
            raise Unstatable("%r takes %d argument(s)" % (h, 1 if h in UNARY else 2))
        return (h,) + tuple(sentence(a) for a in args)
    if h in GQ or h in FO:
        n = 2 if h in GQ else 1
        if len(args) != 1 + n or not _var(args[0]):
            raise Unstatable("%r takes a variable and %d formula(s)" % (h, n))
        return (h, args[0][1:]) + tuple(sentence(a) for a in args[1:])
    if args and all(isinstance(a, str) for a in args):          # predicate application (INTERFACE section 1)
        return ("pred", h, [("var", a[1:]) if _var(a) else ("const", a) for a in args])
    if len(args) in (1, 2):
        return ("op", h, [sentence(a) for a in args])
    raise Unstatable("operator %r with %d arguments has no constructor in the proof syntax (op1, op2)" % (h, len(args)))


def claim(fact):
    """The fact's claim as an AST: ("entails", [P], C) | ("felicitous", [D]) | ("consistent", [P]) | ("truth", A, rel, B).
    Raises Unstatable."""
    typ, spec = fact.get("type"), fact.get("spec")
    if typ not in CLAIM_TYPES:
        raise Unstatable("facts of type %r have no claim shape in the proof interface" % typ)
    if not isinstance(spec, dict):
        raise Unstatable("the fact has no spec")
    try:
        if typ == "entailment":
            return ("entails", [sentence(p) for p in spec["premises"]], sentence(spec["conclusion"]))
        if typ == "felicity":
            return ("felicitous", [sentence(p) for p in spec["discourse"]])
        if typ == "consistency":
            return ("consistent", [sentence(p) for p in spec["premises"]])
        if spec["relation"] not in RELS:
            raise Unstatable("unknown relation %r" % spec["relation"])
        return ("truth", sentence(spec["sentence"]), spec["relation"], sentence(spec["target"]))
    except (KeyError, TypeError):
        raise Unstatable("malformed spec")


# -- Lean ------------------------------------------------------------------
def lean_str(s):
    out = []
    for c in s:
        if c in '\\"':
            out.append("\\" + c)
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif ord(c) < 32:
            out.append("\\u%04x" % ord(c))
        else:
            out.append(c)
    return '"' + "".join(out) + '"'


_LEAN_HEAD = {"not": "not", "must": "must", "may": "may", "and": "and", "or": "or", "if": "imp", "iff": "iff",
              "some": "some", "every": "every", "no": "no", "exists": "exist", "forall": "forall'"}


def lean_s(a):
    h = a[0]
    if h == "atom":
        return "(Linglab.S.atom %s)" % lean_str(a[1])
    if h == "pred":
        terms = ", ".join("Linglab.Term.%s %s" % (k, lean_str(n)) for k, n in a[2])
        return "(Linglab.S.pred %s [%s])" % (lean_str(a[1]), terms)
    if h == "op":
        return "(Linglab.S.op%d %s %s)" % (len(a[2]), lean_str(a[1]), " ".join(lean_s(x) for x in a[2]))
    if h in GQ or h in FO:
        return "(Linglab.S.%s %s %s)" % (_LEAN_HEAD[h], lean_str(a[1]), " ".join(lean_s(x) for x in a[2:]))
    return "(Linglab.S.%s %s)" % (_LEAN_HEAD[h], " ".join(lean_s(x) for x in a[1:]))


def lean_claim(c):
    lst = lambda xs: "[" + ", ".join(lean_s(x) for x in xs) + "]"
    if c[0] == "entails":
        return "(Linglab.Claim.entails %s %s)" % (lst(c[1]), lean_s(c[2]))
    if c[0] in ("felicitous", "consistent"):
        return "(Linglab.Claim.%s %s)" % (c[0], lst(c[1]))
    return "(Linglab.Claim.truth %s Linglab.Rel.%s %s)" % (lean_s(c[1]), c[2], lean_s(c[3]))


# -- candidates --------------------------------------------------------------
def candidates(d, found, render):
    """found: [(unit, fact id, negated, relative file)], unit = the full namespace.
    -> (candidates, skipped): each candidate a dict with fact, theory, neg, unit, file, statement;
    skipped: ["unit.F12: why"] for theorems that name a fact but cannot be checked."""
    tids = {t["id"].replace("-", "_"): t for t in d["theories"]}
    facts = {f["id"]: f for f in d["statements"] if f.get("role") == "fact"}
    cands, skipped = [], []
    for unit, fid, neg, rel in found:
        last = unit.split(".")[-1]
        t, f = tids.get(last), facts.get(fid)
        if last == "Raw" or t is None or f is None:
            continue        # Raw Facts are credited by `linglab listing`; other units are not theories
        name = "%s.%s%s" % (unit, fid, "_fail" if neg else "")
        sel, _ = runner.select_parses(t, f)
        if len(sel) != 1 or sel[0][0] != "main":
            skipped.append("%s: not checked: theory %s evaluates other parses of %s than its main spec" % (name, t["id"], fid))
            continue
        try:
            c = claim(f)
        except Unstatable as e:
            skipped.append("%s: not checked: %s" % (name, e))
            continue
        cands.append({"fact": fid, "theory": t["id"], "neg": neg, "unit": unit, "file": rel, "name": name,
                      "quantified": vocab.uses_quantifiers(f.get("spec")),
                      "statement": "%s %s.theory %s" % ("Fails" if neg else "Holds", unit, render(c))})
    return cands, skipped


def entry(c, d, kind, who, verb, note=""):
    """The entry of a checked theorem. Its `bound` says what the theory's model list covers (`scope`):
    "exhaustive" for a complete list (a proof about the theory), "exhaustive within <scope>" otherwise
    (a kernel-checked computation within that bound, not a general proof)."""
    f = next(x for x in d["statements"] if x.get("id") == c["fact"])
    exp = f.get("expected", "holds") == "holds"
    scope = c.get("scope", "complete")
    why = "theorem %s %s; its statement was checked against data/statements.json" % (c["name"], verb)
    if scope != "complete":
        why += "; computed over a bounded model list (%s), not a general proof" % scope
    return {"fact": c["fact"], "theory": c["theory"], "outcome": "pass" if exp != c["neg"] else "fail",
            "kind": kind, "who": who, "when": today(), "reasons": why,
            "ref": c["file"], "bound": vocab.bound_text(scope), "outside_fragment": False, "depends_on": "", "note": note}


def warn_complete_with_quantifiers(cands, out):
    """A theory that declares a complete model list but is checked on facts with quantifiers or predicates:
    a finite list of models usually bounds the domain, so the declaration is probably wrong."""
    seen = {}
    for c in cands:
        if c.get("scope") == "complete" and c.get("quantified"):
            seen.setdefault(c["unit"], []).append(c["fact"])
    for unit, fids in sorted(seen.items()):
        out("warning: %s.theory declares scope \"complete\", but facts %s use quantifiers or predicates. If its models "
            "bound the domain, set `scope` (for example \"domain size <= 3\") so the results say so."
            % (unit, ", ".join(sorted(set(fids)))))


def module_of(rel, top):
    """lean/Linglab/Toy/T_MK.lean -> Linglab.Toy.T_MK (path relative to the workspace folder `top`)."""
    p = os.path.splitext(os.path.relpath(rel, top))[0]
    return ".".join(p.split(os.sep))
