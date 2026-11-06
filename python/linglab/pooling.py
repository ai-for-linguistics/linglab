"""Pooling of a cell's entries (SPEC section 3), same rule as the report."""
from collections import Counter


def pool(entries, ladder):
    """-> {"outcome": pass|fail|out_of_scope|pending, "rank": kind or None,
           "conflict": bool, "warnings": [kinds that disagree from a weaker rank]}
    On a conflict at the strongest rank the outcome is the majority, ties go to fail."""
    real = [e for e in entries if e.get("outcome") != "pending"]
    if not real:
        return {"outcome": "pending", "rank": None, "conflict": False, "warnings": []}
    rank = lambda e: ladder.index(e["kind"]) if e.get("kind") in ladder else len(ladder)
    best = min(rank(e) for e in real)
    top = [e for e in real if rank(e) == best]
    dec = [e for e in top if e["outcome"] in ("pass", "fail")]
    if not dec:
        return {"outcome": "out_of_scope", "rank": top[0].get("kind"), "conflict": False, "warnings": []}
    npass = sum(e["outcome"] == "pass" for e in dec)
    nfail = len(dec) - npass
    conflict = npass > 0 and nfail > 0
    outcome = "pass" if npass > nfail else "fail"      # majority; a tie goes to fail (D30)
    warn = [] if conflict else sorted({e["kind"] for e in real if rank(e) > best and
                                       e["outcome"] in ("pass", "fail") and e["outcome"] != outcome})
    return {"outcome": outcome, "rank": top[0].get("kind"), "conflict": conflict, "warnings": warn}


def pool_all(results, ladder):
    cells = {}
    for e in results:
        cells.setdefault((e["fact"], e["theory"]), []).append(e)
    return {k: pool(v, ladder) for k, v in cells.items()}


def summary(statements, theories, results, ladder, include_llm=True, include_system=True):
    """Per theory counts: passed, applicable (not out_of_scope), total facts."""
    facts = [s for s in statements if s.get("role") == "fact"
             and (include_system or s.get("about", "language") != "system")]
    pooled = pool_all([e for e in results if include_llm or e["kind"] != "llm-judged"], ladder)
    out = {}
    for t in theories:
        cells = [pooled.get((f["id"], t["id"]), {"outcome": "pending", "conflict": False}) for f in facts]
        c = Counter(x["outcome"] for x in cells)
        c["conflict"] = sum(1 for x in cells if x["conflict"])
        out[t["id"]] = {"passed": c["pass"], "failed": c["fail"], "out_of_scope": c["out_of_scope"],
                        "pending": c["pending"], "conflict": c["conflict"], "total": len(facts),
                        "applicable": len(facts) - c["out_of_scope"]}
    return out
