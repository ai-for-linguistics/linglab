"""Pooling of a cell's entries (SPEC section 3), same rule as the report."""
from collections import Counter

# Kinds that compute the verdict from an implementation of the theory (a proof checker or the Python runner).
# They are cross-checks of each other: when two of them disagree, one implementation (or one translation of the
# fact) is wrong, so the cell is a conflict whatever their ranks. A project may change the list
# (custom/registry.json `computed_kinds`).
COMPUTED_KINDS = ["lean", "python"]


def is_bounded(e):
    """The entry's verdict holds only within a bound (a model list that is not complete, or the first n models)."""
    b = e.get("bound") or ""
    return " within " in b or b.startswith("first ")


def pool(entries, ladder, computed=None):
    """-> {"outcome": pass|fail|out_of_scope|pending, "rank": kind or None,
           "conflict": bool, "warnings": [kinds that disagree from a weaker rank],
           "agree": [computed kinds that agree, when two or more do], "bounded": bool}
    Conflict: entries at the strongest rank disagree, or two computed kinds disagree (pass, fail or out of
    scope) at any ranks. On a conflict at the strongest rank the outcome is the majority, ties go to fail.
    `bounded`: a decided entry of the strongest rank holds only within a bound."""
    computed = COMPUTED_KINDS if computed is None else computed
    real = [e for e in entries if e.get("outcome") != "pending"]
    if not real:
        return {"outcome": "pending", "rank": None, "conflict": False, "warnings": [], "agree": [], "bounded": False}
    comp = [e for e in real if e.get("kind") in computed and e.get("who") != "listing"]
    cross = len({e["outcome"] for e in comp}) > 1
    agree = sorted({e["kind"] for e in comp}) if not cross and comp and comp[0]["outcome"] in ("pass", "fail") else []
    agree = agree if len(agree) > 1 else []
    rank = lambda e: ladder.index(e["kind"]) if e.get("kind") in ladder else len(ladder)
    best = min(rank(e) for e in real)
    top = [e for e in real if rank(e) == best]
    dec = [e for e in top if e["outcome"] in ("pass", "fail")]
    if not dec:
        return {"outcome": "out_of_scope", "rank": top[0].get("kind"), "conflict": cross, "warnings": [],
                "agree": [], "bounded": False}
    npass = sum(e["outcome"] == "pass" for e in dec)
    nfail = len(dec) - npass
    conflict = (npass > 0 and nfail > 0) or cross
    outcome = "pass" if npass > nfail else "fail"      # majority; a tie goes to fail (D30)
    warn = [] if conflict else sorted({e["kind"] for e in real if rank(e) > best and
                                       e["outcome"] in ("pass", "fail") and e["outcome"] != outcome})
    return {"outcome": outcome, "rank": top[0].get("kind"), "conflict": conflict, "warnings": warn,
            "agree": agree, "bounded": any(is_bounded(e) for e in dec)}


def pool_all(results, ladder, computed=None):
    cells = {}
    for e in results:
        cells.setdefault((e["fact"], e["theory"]), []).append(e)
    return {k: pool(v, ladder, computed) for k, v in cells.items()}


def summary(statements, theories, results, ladder, include_llm=True, include_system=True, computed=None):
    """Per theory counts: passed, applicable (not out_of_scope), total facts."""
    facts = [s for s in statements if s.get("role") == "fact"
             and (include_system or s.get("about", "language") != "system")]
    pooled = pool_all([e for e in results if include_llm or e["kind"] != "llm-judged"], ladder, computed)
    out = {}
    for t in theories:
        cells = [pooled.get((f["id"], t["id"]), {"outcome": "pending", "conflict": False}) for f in facts]
        c = Counter(x["outcome"] for x in cells)
        c["conflict"] = sum(1 for x in cells if x["conflict"])
        out[t["id"]] = {"passed": c["pass"], "failed": c["fail"], "out_of_scope": c["out_of_scope"],
                        "pending": c["pending"], "conflict": c["conflict"], "total": len(facts),
                        "applicable": len(facts) - c["out_of_scope"]}
    return out
