"""`linglab listing`: build Raw Facts (theory RAW) and its results; flag contradictory facts."""
import json
import os

from .common import load_project, write_json, today, sort_results, facts_of


def norm_key(f):
    """Normalized claim of a fact, ignoring id/name/expected: same key = same claim."""
    spec = f.get("spec")
    if spec and "premises" in spec:
        spec = dict(spec, premises=sorted(json.dumps(p, sort_keys=True) for p in spec["premises"]))
    return json.dumps([f.get("type"), spec, f.get("context", "null")], sort_keys=True) if spec else None


def contradictions(facts):
    seen, bad = {}, []
    for f in facts:
        k = norm_key(f)
        if k is None:
            continue
        for g in seen.get(k, []):
            if g.get("expected", "holds") != f.get("expected", "holds"):
                bad.append((g["id"], f["id"]))
        seen.setdefault(k, []).append(f)
    return bad


def build_listing(root=".", out=print):
    d = load_project(root)
    facts = facts_of(d["statements"])
    bad = contradictions(facts)
    for a, b in bad:
        out("ERROR facts %s and %s state the same claim with opposite expected outcomes" % (a, b))
    raw = {"id": "RAW", "name": "Raw Facts", "description": "The theory made of all the facts, one by one. "
           "Maximal coverage and maximal complexity; the baseline every theory should beat.",
           "principles": [f["id"] for f in facts], "parent": None, "kind": "reference",
           "origin": {"source": "", "page": ""}, "family": "", "generated": "listing", "notes": ""}
    th = [t for t in d["theories"] if t["id"] != "RAW"] + [raw]
    results = [e for e in d["results"] if not (e["theory"] == "RAW" and e["kind"] == "python"
                                               and e.get("who") == "listing")]
    for f in facts:
        results.append({"fact": f["id"], "theory": "RAW", "outcome": "pass", "kind": "python",
                        "who": "listing", "when": today(), "reasons": "listed", "ref": "linglab listing",
                        "bound": "exhaustive", "outside_fragment": False, "depends_on": "", "note": ""})
    write_json(os.path.join(root, "data", "theories.json"), th)
    write_json(os.path.join(root, "data", "results.json"), sort_results(results, d["statements"], th))
    out("Raw Facts: %d facts listed" % len(facts))
    return 1 if bad else 0
