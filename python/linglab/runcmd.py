"""`linglab run`: run the Python checker over the project's cells and write entries."""
import glob
import hashlib
import importlib.util
import json
import os
import sys

from . import vocab, runner, metrics
from .common import load_project, save_results, sort_results, facts_of
from . import pooling
from . import check as checkmod


def principle_code(root):
    """-> {principle id: stripped Python chunk text} from the project's python/**/*.py (tagged chunks)."""
    code = {}
    for p in sorted(glob.glob(os.path.join(root, "python", "**", "*.py"), recursive=True)):
        if "tests" in p.split(os.sep):
            continue
        for pid, ls in metrics.chunks(p, metrics.PY_TAG).items():
            code.setdefault(pid, []).extend(metrics.strip_py(ls))
    return {k: "\n".join(v) for k, v in code.items()}


def cell_digest(fact, theory, code, bound):
    """sha1 of everything a runner entry depends on: the fact's claim, the theory's ordered principles,
    their Python code and the bound. A cell is recomputed when its digest differs (stored as `digest`)."""
    payload = {"type": fact.get("type"), "spec": fact.get("spec"), "expected": fact.get("expected", "holds"),
               "context": fact.get("context"), "parses": fact.get("parses"), "uses": fact.get("uses"),
               "theory_cfg": {k: theory.get(k) for k in ("predicts", "primitives", "parse_policy")},
               "picks": (theory.get("picks") or {}).get(fact.get("id")), "principles": list(theory.get("principles", [])),
               "code": [code.get(p, "") for p in theory.get("principles", [])],
               "bound": bound if bound is not None else ""}
    return hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def load_principles(root):
    path = os.path.join(root, "python", "principles.py")
    if not os.path.exists(path):
        return None
    vocab._PRINCIPLES.clear()
    spec = importlib.util.spec_from_file_location("project_principles", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return path


def run_project(root=".", theory=None, fact=None, bound=None, force=False, out=print):
    lines = []
    if checkmod.run_check(root, out=lines.append):
        for l in lines:
            if l.startswith("ERROR") or l.endswith("warning(s)"):
                out(l)
        out("linglab run aborted: fix the errors above (see `linglab check`)")
        return 1
    path = load_principles(root)
    if path is None:
        out("no python/principles.py in this project: nothing to run")
        return 1
    d = load_project(root)
    results = list(d["results"])
    facts = [f for f in facts_of(d["statements"]) if fact in (None, f["id"])]
    code = principle_code(root)
    have = {(e["fact"], e["theory"]): e.get("digest") for e in results
            if e["kind"] == "python" and e.get("who") == "runner" and e["outcome"] != "pending"}
    n_new = 0
    for t in d["theories"]:
        if t.get("generated") or theory not in (None, t["id"]):
            continue
        digests = {f["id"]: cell_digest(f, t, code, bound) for f in facts}
        # a cell is skipped only when its stored digest equals the current one (no digest = stale)
        pend = [f for f in facts if force or have.get((f["id"], t["id"])) != digests[f["id"]]]
        if not pend:
            continue
        try:
            T = vocab.Theory(t["id"], t.get("name", t["id"]), t.get("principles", []))
        except KeyError as e:
            out("%s: skipped (%s)" % (t["id"], e.args[0]))
            continue
        dec = runner.run_theory(T, pend, bound, t)
        new = runner.entries_for(T, dec, "python/principles.py", digests)
        mine = {(f["id"], t["id"]) for f in pend}
        # replace only this checker's own entries for the cells it decided; other kinds stay
        results = [e for e in results if not (e["kind"] == "python" and e.get("who") == "runner"
                                              and (e["fact"], e["theory"]) in mine)]
        results += new
        n_new += len(new)
        out("%s: %d entries (%d facts left pending)" % (t["id"], len(new), sum(v is None for v in dec.values())))
    from .common import write_json
    write_json(os.path.join(root, "data", "results.json"),
               sort_results(results, d["statements"], d["theories"]))
    metrics.write_metrics(root)
    s = pooling.summary(d["statements"], d["theories"], results, d["registry"]["ladder"])
    for tid, c in s.items():
        out("  %-10s passed %d / applicable %d (of %d facts)" % (tid, c["passed"], c["applicable"], c["total"]))
    return 0
