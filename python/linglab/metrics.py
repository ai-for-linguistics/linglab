"""`linglab metrics`: size of tagged principle chunks, comments and blank lines stripped."""
import glob
import gzip
import io
import json
import os
import re
import textwrap
import tokenize

from .common import load_project, write_json

PY_TAG = re.compile(r"^\s*#\s*(BEGIN|END)\s+principle:(\S+)\s*$")
LEAN_TAG = re.compile(r"^\s*--\s*(BEGIN|END)\s+principle:(\S+)\s*$")


def chunks(path, tag):
    """-> {principle id: [lines]} for the tagged chunks of one file."""
    out, cur = {}, None
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            m = tag.match(line)
            if m:
                if m.group(1) == "BEGIN":
                    cur = m.group(2)
                    out.setdefault(cur, [])
                elif m.group(2) == cur:
                    cur = None
            elif cur is not None:
                out[cur].append(line)
    return out


def strip_py(lines):
    src = textwrap.dedent("\n".join(lines)) + "\n"
    cuts = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                cuts[tok.start[0] - 1] = tok.start[1]
    except (tokenize.TokenError, IndentationError):
        pass
    ls = src.splitlines()
    return [ls[i][:cuts[i]].rstrip() if i in cuts else ls[i].rstrip() for i in range(len(ls))]


def strip_lean(lines):
    text = re.sub(r"/-.*?-/", "", "\n".join(lines), flags=re.S)
    return [re.sub(r"--.*$", "", l).rstrip() for l in text.splitlines()]


def strip_agda(lines):
    text = re.sub(r"\{-.*?-\}", "", "\n".join(lines), flags=re.S)
    return [re.sub(r"(^|\s)--(\s.*)?$", "", l).rstrip() for l in text.splitlines()]


def measure(lines):
    text = "\n".join(l for l in lines if l.strip())
    return {"chars": len(text), "words": len(text.split()), "lines": len([l for l in lines if l.strip()]),
            "gzip": len(gzip.compress(text.encode("utf-8"), 9, mtime=0))}


def collect(root):
    """-> (py {pid: lines}, lean {file stem: {pid: lines}})."""
    py = {}
    for p in sorted(glob.glob(os.path.join(root, "python", "**", "*.py"), recursive=True)):
        if "tests" in p.split(os.sep):
            continue
        for pid, ls in chunks(p, PY_TAG).items():
            py.setdefault(pid, []).extend(strip_py(ls))
    lean = {}
    for p in sorted(glob.glob(os.path.join(root, "lean", "**", "*.lean"), recursive=True)):
        if ".lake" in p.split(os.sep):
            continue
        stem = os.path.splitext(os.path.basename(p))[0]
        for pid, ls in chunks(p, LEAN_TAG).items():
            lean.setdefault(stem, {}).setdefault(pid, []).extend(strip_lean(ls))
    return py, lean


def collect_agda(root):
    """-> {file stem: {pid: lines}} for the tagged chunks of agda/**/*.agda (optional workspace)."""
    agda = {}
    for p in sorted(glob.glob(os.path.join(root, "agda", "**", "*.agda"), recursive=True)):
        if "_build" in p.split(os.sep):
            continue
        stem = os.path.splitext(os.path.basename(p))[0]
        for pid, ls in chunks(p, LEAN_TAG).items():  # same `-- BEGIN principle:` tag
            agda.setdefault(stem, {}).setdefault(pid, []).extend(strip_agda(ls))
    return agda


def theory_metrics(t, py, lean, no_aux_ids, agda=None):
    """Per-principle and total sizes for theory t. Lean chunks come from the file named
    after the theory (T-MK -> T_MK.lean); a principle with no chunk there falls back to
    a chunk of the same id in any other file."""
    stem = t["id"].replace("-", "_")
    res, tot = {}, {"python": [], "lean": [], "agda": []}
    for pid in t.get("principles", []):
        r = {}
        if pid in py:
            r["python"] = measure(py[pid])
            tot["python"] += py[pid]
        lc = lean.get(stem, {}).get(pid)
        if lc is None:
            lc = next((c[pid] for s, c in sorted(lean.items()) if pid in c), None)
        if lc is not None:
            r["lean"] = measure(lc)
            tot["lean"] += lc
        ac = (agda or {}).get(stem, {}).get(pid)
        if ac is None:
            ac = next((c[pid] for s, c in sorted((agda or {}).items()) if pid in c), None)
        if ac is not None:
            r["agda"] = measure(ac)
            tot["agda"] += ac
        res[pid] = r
    total = {k: measure(v) for k, v in tot.items() if v}
    ids = t.get("principles", [])
    return {"principles": res, "total": total, "n_principles": len(ids),
            "n_principles_no_aux": len([i for i in ids if i not in no_aux_ids])}


def raw_metrics(root, d, lean, agda=None):
    """Raw Facts: python = the facts' claims serialized (what a listing must state);
    lean = chunks tagged principle:RAW if the Lean workspace has them."""
    facts = [s for s in d["statements"] if s.get("role") == "fact"]
    lines = [json.dumps({k: f.get(k) for k in ("type", "spec", "expected")}, sort_keys=True) for f in facts]
    r = {"principles": {}, "total": {"python": measure(lines)}, "n_principles": len(facts),
         "n_principles_no_aux": len(facts)}
    rl = [l for c in lean.values() for l in c.get("RAW", [])]
    if rl:
        r["total"]["lean"] = measure(rl)
    ra = [l for c in (agda or {}).values() for l in c.get("RAW", [])]
    if ra:
        r["total"]["agda"] = measure(ra)
    return r


def write_metrics(root="."):
    d = load_project(root)
    py, lean = collect(root)
    aux = {s["id"] for s in d["statements"] if s.get("auxiliary")}
    agda = collect_agda(root)
    out = {"theories": {}, "raw": raw_metrics(root, d, lean, agda)}
    for t in d["theories"]:
        if not t.get("generated"):
            out["theories"][t["id"]] = theory_metrics(t, py, lean, aux, agda)
    write_json(os.path.join(root, "data", "metrics.json"), out)
    return out
