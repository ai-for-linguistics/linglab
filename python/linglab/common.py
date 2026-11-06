"""Shared helpers: paths, JSON files, small constants."""
import json
import os
import datetime

TOOLKIT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_REGISTRY = {
    "ladder": ["lean", "python", "human", "paper-claim", "user-claim", "llm-judged"],
    "outcomes": ["pass", "fail", "pending", "out_of_scope"],
    "fact_types": ["entailment", "felicity", "truth", "preference", "consistency", "property", "other"],
    "coverage_metrics": [], "size_metrics": [], "views": [],
}
PRESENCE = ["in source", "mentioned not tested", "mentioned disregarded", "not mentioned"]
FINDING_STATUS = ["proved", "computed", "argued", "literature", "open"]
READING_REVIEW = ["unreviewed", "accepted", "corrected"]
THEORY_KINDS = ["original", "fix", "creative", "reference"]
CHECK_BY = ["llm", "human", "other"]
CHECK_WHAT = ["readback", "translation", "example", "other"]
CHECK_VERDICT = ["agrees", "disagrees", "partial", "unclear"]
REL = ["stronger", "weaker", "related", "incompatible"]
DATA_FILES = {"meta": {}, "statements": [], "theories": [], "results": [], "findings": [], "metrics": {}, "fragments": [], "readings": []}


def today():
    return datetime.date.today().isoformat()


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_project(root="."):
    """Return the project's data as a dict (missing files get empty defaults)."""
    d = {}
    for name, default in DATA_FILES.items():
        d[name] = read_json(os.path.join(root, "data", name + ".json"), default)
    d["registry"] = load_registry(root)
    return d


def load_registry(root="."):
    for p in (os.path.join(root, "custom", "registry.json"),
              os.path.join(TOOLKIT, "template", "custom", "registry.json")):
        r = read_json(p)
        if r is not None:
            return r
    return DEFAULT_REGISTRY


def save_results(root, results):
    write_json(os.path.join(root, "data", "results.json"), results)


def sort_results(results, statements, theories):
    """Deterministic order: fact order, theory order, then kind, who (stable)."""
    fo = {s["id"]: i for i, s in enumerate(statements)}
    to = {t["id"]: i for i, t in enumerate(theories)}
    return sorted(results, key=lambda e: (fo.get(e["fact"], 9999), to.get(e["theory"], 9999),
                                          e.get("kind", ""), e.get("who", "")))


def facts_of(statements):
    return [s for s in statements if s.get("role") == "fact"]


def drop_kind(root, kind):
    """Remove every entry of `kind` from data/results.json (stale proofs). Returns how many were removed."""
    d = load_project(root)
    keep = [e for e in d["results"] if e.get("kind") != kind]
    if len(keep) != len(d["results"]):
        write_json(os.path.join(root, "data", "results.json"), sort_results(keep, d["statements"], d["theories"]))
    return len(d["results"]) - len(keep)
