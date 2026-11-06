"""Model-major Python runner.

Design choice (loop order). Compute is the scarce resource, and models are the expensive
objects (building one, and evaluating its subformulas, is where the time goes). So the
loops are: for each theory -> build claims for all pending facts -> loop over models ONCE,
and on each model evaluate every claim still undecided. The alternative (for each fact,
loop over all models) rebuilds every model once per fact. A violation (forall) or a
witness (exists) decides a claim at once; the model becomes its `reasons`. Subformula
values are cached on the model, so shared subformulas are computed once per model.
When the models run out (or the bound is reached) the remaining claims take their default.
"""
from collections import namedtuple

from . import vocab
from .common import today

Claim = namedtuple("Claim", "kind pred")  # kind: "forall" | "exists"; pred(model) -> bool
# scope: why an out_of_scope cell is out of scope: "fragment" (the sentence cannot be stated in the theory),
# "no_prediction" (the theory has no linking for this kind of fact), "primitive" (a notion the fact uses is not implemented)
# parses: {parse id: outcome} when several parses of the sentence were evaluated
Decision = namedtuple("Decision", "outcome reasons bound scope parses", defaults=("", None))

# the notion a type of fact needs from the theory (checked only when the theory declares its `primitives`)
TYPE_PRIMITIVE = {"entailment": "entailment", "felicity": "felicity", "consistency": "consistency",
                  "truth": "truth", "preference": "preference"}


def build_claim(T, fact, spec=None):
    """-> Claim, or "out_of_scope" (translate failed), or "pending" (unsupported type).
    `spec` overrides the fact's own spec (one of its parses)."""
    typ = fact.get("type")
    spec = (fact.get("spec") if spec is None else spec) or {}
    tr = lambda s: T.translate(s)
    try:
        if typ == "entailment":
            prem = [tr(s) for s in spec["premises"]]
            concl = tr(spec["conclusion"])
            if concl is None or None in prem:
                return "out_of_scope"
            return Claim("forall", lambda m: T.ent_ok(m, prem, concl))
        if typ == "felicity":
            disc = [tr(s) for s in spec["discourse"]]
            if None in disc:
                return "out_of_scope"
            return Claim(T.felic_kind, lambda m: T.felic_ok(m, disc))
        if typ == "consistency":
            prem = [tr(s) for s in spec["premises"]]
            if None in prem:
                return "out_of_scope"
            return Claim("exists", lambda m: T.cons_ok(m, prem))
        if typ == "truth":
            a, b = tr(spec["sentence"]), tr(spec["target"])
            if a is None or b is None:
                return "out_of_scope"
            rel = spec["relation"]
            def pred(m):
                x, y = T.true_in(m, a), T.true_in(m, b)
                return {"equals": x == y, "within": (not x) or y, "includes": x or (not y)}[rel]
            return Claim("forall", pred)
    except (KeyError, TypeError):
        return "pending"   # malformed spec: `linglab check` reports it
    return "pending"        # preference, other, property (handled by the caller), unknown


def scope_reason(T, fact, spec=None):
    """Why the fact cannot be stated in T: the first untranslatable part of its spec."""
    spec = (fact.get("spec") if spec is None else spec) or {}
    parts = []
    for k in ("premises", "discourse"):
        if isinstance(spec.get(k), list):
            parts += spec[k]
    parts += [spec[k] for k in ("conclusion", "sentence", "target") if k in spec]
    for p in parts:
        r = T.explain(p)
        if r:
            return r
    return ""


def candidates(fact):
    """the parses of a fact: [(id, spec)]; its own spec is the parse "main", then `parses` in order."""
    c = [("main", fact["spec"])] if fact.get("spec") else []
    for p in fact.get("parses") or []:
        c.append((str(p.get("id")), p.get("spec") or {}))
    return c or [("main", {})]


def select_parses(cfg, fact):
    """which parses the theory evaluates and how it combines them: ("first"|"any"|"all").
    The theory decides: `picks` {fact id: [parse ids]} and `parse_policy` (default: the fact's own spec only)."""
    cands = candidates(fact)
    pol = (cfg or {}).get("parse_policy", "first")
    picks = ((cfg or {}).get("picks") or {}).get(fact["id"])
    if picks:
        sel = [c for c in cands if c[0] in picks] or cands[:1]
        return sel, (pol if pol in ("any", "all") else ("any" if len(sel) > 1 else "first"))
    if pol == "first" or len(cands) == 1:
        return cands[:1], "first"
    return cands, pol


def _combine(fact, per, policy, bound_txt):
    """per: [(parse id, ("oos", why) | ("done", raw, reasons, by_model))] -> Decision for the cell"""
    expected = fact.get("expected", "holds") == "holds"
    if len(per) == 1:
        pid, r = per[0]
        if r[0] == "oos":
            return Decision("out_of_scope", "not expressible in this theory" + (": " + r[1] if r[1] else ""), "", "fragment")
        _, raw, why, by_model = r
        return Decision("pass" if raw == expected else "fail", why, "" if by_model else bound_txt)
    outs, parts, parses = [], [], {}
    for pid, r in per:
        if r[0] == "oos":
            outs.append("oos"); parts.append("%s: not expressible" % pid); parses[pid] = "out_of_scope"
        else:
            o = "pass" if r[1] == expected else "fail"
            outs.append(o); parts.append("%s: %s (%s)" % (pid, o, r[2])); parses[pid] = o
    undecided = any(r[0] == "done" and not r[3] for _, r in per)
    btxt = bound_txt if undecided else ""
    note = "; ".join(parts) + "; the theory combines its parses with policy '%s'" % policy
    if policy == "all":
        if "oos" in outs:
            return Decision("out_of_scope", note, "", "fragment", parses)
        return Decision("pass" if all(o == "pass" for o in outs) else "fail", note, btxt, "", parses)
    if all(o == "oos" for o in outs):
        return Decision("out_of_scope", note, "", "fragment", parses)
    return Decision("pass" if "pass" in outs else "fail", note, btxt, "", parses)


def run_theory(T, facts, bound=None, cfg=None):
    """Decide the given facts for theory T. Returns {fact_id: Decision or None (pending)}.
    `cfg` is the theory's record (optional fields: predicts, primitives, parse_policy, picks)."""
    cfg = cfg or {}
    out, live, per = {}, {}, {}    # per: fact id -> [(parse id, state)]; live: (fact id, parse id) -> (fact, claim)
    policy_of = {}
    prims, predicts = cfg.get("primitives"), cfg.get("predicts")
    for f in facts:
        if f.get("type") == "property":
            fn = vocab.registered_properties().get((f.get("spec") or {}).get("check"))
            if fn is None:
                out[f["id"]] = None
            else:
                ok = bool(fn(T))
                out[f["id"]] = Decision("pass" if ok == (f.get("expected", "holds") == "holds") else "fail",
                                        "property check", "")
            continue
        if prims is not None:           # the theory declares which notions it implements
            need = list(f.get("uses") or [])
            if TYPE_PRIMITIVE.get(f.get("type")):
                need.append(TYPE_PRIMITIVE[f["type"]])
            miss = [n for n in dict.fromkeys(need) if n not in prims]
            if miss:
                out[f["id"]] = Decision("out_of_scope", "uses a notion this theory does not implement: " + ", ".join(miss), "", "primitive")
                continue
        if predicts is not None and f.get("type") not in predicts and f.get("type") != "other":
            out[f["id"]] = Decision("out_of_scope", "this theory makes no prediction for facts of type %s" % f.get("type"), "", "no_prediction")
            continue
        sel, pol = select_parses(cfg, f)
        policy_of[f["id"]] = pol
        per[f["id"]] = []
        pending = False
        for pid, spec in sel:
            c = build_claim(T, f, spec)
            if c == "out_of_scope":
                why = scope_reason(T, f, spec)
                per[f["id"]].append((pid, ("oos", why)))
            elif c == "pending":
                pending = True
            else:
                live[(f["id"], pid)] = (f, c)
        if pending:
            out[f["id"]] = None
            per.pop(f["id"])
            for k in [k for k in live if k[0] == f["id"]]:
                del live[k]
    decided = {}   # (fact id, parse id) -> (raw, reasons, decided_by_model)
    exhausted, n = True, 0
    if live:
        for m in T.models():
            if bound is not None and n >= bound:
                exhausted = False       # more models exist than the bound allows
                break
            n += 1
            for key, (f, c) in list(live.items()):
                ok = c.pred(m)
                if c.kind == "forall" and not ok:
                    decided[key] = (False, "countermodel %s" % T.describe(m), True)
                elif c.kind == "exists" and ok:
                    decided[key] = (True, "witness %s" % T.describe(m), True)
                else:
                    continue
                del live[key]
            if not live:
                break
    btxt = "exhaustive" if exhausted else "first %d models" % bound
    for key, (f, c) in live.items():            # undecided claims take their default
        why = ("no countermodel in %d models" if c.kind == "forall" else "no witness in %d models") % n
        decided[key] = (c.kind == "forall", why, False)
    byid = {f["id"]: f for f in facts}
    for fid, items in per.items():
        # restore the order of the parses; a decided parse becomes ("done", raw, reasons, by_model)
        sel, _ = select_parses(cfg, byid[fid])
        oos = {pid: st for pid, st in items}
        rows = []
        for pid, _spec in sel:
            if pid in oos:
                rows.append((pid, oos[pid]))
            elif (fid, pid) in decided:
                raw, why, by_model = decided[(fid, pid)]
                rows.append((pid, ("done", raw, why, by_model)))
        out[fid] = _combine(byid[fid], rows, policy_of[fid], btxt)
    return out


def entries_for(T, decisions, ref, digests=None):
    es = []
    for fid, d in decisions.items():
        if d is None:
            continue
        e = {"fact": fid, "theory": T.id, "outcome": d.outcome, "kind": "python", "who": "runner",
             "when": today(), "reasons": d.reasons, "ref": ref, "bound": d.bound,
             "outside_fragment": False, "depends_on": "", "note": "",
             "digest": (digests or {}).get(fid, "")}
        if d.outcome == "out_of_scope" and d.scope:
            e["scope"] = d.scope
        if d.parses:
            e["parses"] = d.parses
        es.append(e)
    return es
