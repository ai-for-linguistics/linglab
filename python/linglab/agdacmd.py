"""`linglab agda`: typecheck the optional Agda workspace and turn theorems into `agda` entries.

Same naming convention as `linglab lean` (SPEC section 5), with the module name in place of the
Lean namespace: in a file whose module is `Linglab.Toy.T_MK`, the signature `F01 : Holds ...`
proves the claim, `F01_fail : Fails ...` proves its negation. Module `...Raw` maps to theory RAW.
Lean stays the default and authoritative kind; `agda` ranks just below it in the ladder.
"""
import glob
import os
import re
import shutil
import subprocess

from .common import load_project, write_json, today, sort_results, facts_of, drop_kind
from . import forbidden

MOD = re.compile(r"^\s*module\s+(\S+)")
SIG = re.compile(r"^\s*(F\d+[A-Za-z]*?)(_fail)?\s*:")
HINT = ("Agda not found. To use the Agda checks install Agda 2.6.4 or newer "
        "(https://agda.readthedocs.io/en/latest/getting-started/installation.html), then re-run `linglab agda`. "
        "Lean and the Python checks still work.")
SKIP_DIRS = ("_build", ".git")


def scan_theorems(root):
    """-> [(module last name, fact id, negated, relative file)]"""
    found = []
    for p in sorted(glob.glob(os.path.join(root, "agda", "**", "*.agda"), recursive=True)):
        if set(SKIP_DIRS) & set(p.split(os.sep)):
            continue
        mod = None
        for line in open(p, encoding="utf-8"):
            if line.lstrip().startswith("--"):
                continue
            m = MOD.match(line)
            if m:
                mod = m.group(1).split(".")[-1]
                continue
            m = SIG.match(line)
            if m and mod:
                found.append((mod, m.group(1), bool(m.group(2)), os.path.relpath(p, root)))
    return found


def init_agda(root="."):
    """Copy the toolkit's Agda workspace to <project>/agda/ (once), without build artifacts."""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "extras", "agda")
    dst = os.path.join(root, "agda")
    if os.path.exists(dst):
        print("agda/ already exists: nothing copied")
        return 0
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("_build", "*.agdai"))
    print("copied the Agda workspace to agda/ (the interface; put your theories under agda/Linglab/Theories/, a worked example is in utils/example/agda/)")
    return 0


def run_agda(root="."  , build_only=False, out=print):
    agda_dir = os.path.join(root, "agda")
    if not os.path.isdir(agda_dir):
        out("no agda/ folder yet: run `python3 utils/bin/linglab.py agda --init` to create it")
        return 0
    if shutil.which("agda") is None:
        out(HINT)
        return 0
    r = subprocess.run(["agda", os.path.join("Linglab", "All.agda")], cwd=agda_dir, capture_output=True, text=True)
    if r.returncode != 0:
        n = drop_kind(root, "agda")
        msg = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if not l.lstrip().startswith("Checking"))
        out("agda failed:\n" + msg[-4000:])
        out("%d stale agda entries removed from data/results.json" % n)
        return 1
    bad = forbidden.scan_agda(root)
    if bad:
        n = drop_kind(root, "agda")
        out("agda ok, but the check is not a proof: postulates, holes or termination pragmas found:")
        for b in bad:
            out("  " + b)
        out("no agda entries recorded; %d stale agda entries removed from data/results.json" % n)
        return 1
    out("agda ok")
    if build_only:
        return 0
    d = load_project(root)
    norm = lambda s: s.replace("-", "_")
    theories = {norm(t["id"]): t["id"] for t in d["theories"]}
    theories["Raw"] = "RAW"
    facts = {f["id"]: f for f in facts_of(d["statements"])}
    new, seen = {}, {}
    for mod, fid, neg, rel in scan_theorems(root):
        tid, f = theories.get(mod), facts.get(fid)
        if tid is None or f is None:
            continue
        exp = f.get("expected", "holds") == "holds"
        outcome = "pass" if tid == "RAW" else ("pass" if (exp != neg) else "fail")
        key = (fid, tid)
        if key in seen and seen[key] != neg:
            out("ERROR both %s and its negation are proved in %s" % (fid, tid))
            return 1
        seen[key] = neg
        new[key] = {"fact": fid, "theory": tid, "outcome": outcome, "kind": "agda", "who": "agda",
                    "when": today(), "reasons": "theorem %s.%s%s typechecks" % (mod, fid, "_fail" if neg else ""),
                    "ref": rel, "bound": "", "outside_fragment": False, "depends_on": "", "note": ""}
    results = [e for e in d["results"] if not (e["kind"] == "agda" and e.get("who") == "agda")]
    results += new.values()
    write_json(os.path.join(root, "data", "results.json"),
               sort_results(results, d["statements"], d["theories"]))
    out("%d agda entries written" % len(new))
    return 0
