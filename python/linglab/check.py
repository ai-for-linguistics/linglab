"""`linglab check`: validate the data files. Errors exit 1; warnings do not."""
import glob
import json
import os
import re
import datetime

from .common import (load_project, PRESENCE, FINDING_STATUS, READING_REVIEW, THEORY_KINDS, REL,
                     CHECK_BY, CHECK_WHAT, CHECK_VERDICT)
from .metrics import PY_TAG, chunks

SCOPE_REASONS = ("fragment", "no_prediction", "primitive")
PARSE_POLICIES = ("first", "any", "all")
FACT_TYPES = ["entailment", "felicity", "truth", "preference", "consistency", "property", "other"]
KNOWN_OPS = {"not": 1, "and": 2, "or": 2, "if": 2, "iff": 2, "must": 1, "may": 1}   # arities (items after the head)
BINDERS = {"some": 3, "every": 3, "no": 3, "exists": 2, "forall": 2}                # items after the head, variable included
BASE_CONNECTIVES = {"not", "and", "or", "if"}       # never warned about: every fragment has them
SPEC_FIELDS = {"entailment": ["premises", "conclusion"], "felicity": ["discourse"], "consistency": ["premises"],
               "truth": ["sentence", "relation", "target"], "preference": ["sentence", "preferred", "over"],
               "property": ["check"], "other": []}


PRINCIPLE_DECO = re.compile(r'@(?:\w+\.)?principle\(\s*["\']([^"\']+)["\']')


DEFINES = re.compile(r'\.(?:connective|operator|predicate)\(\s*["\']([^"\']+)["\']')


def defined_names(root):
    """Heads defined by the project's Python code (`.connective/.operator/.predicate("name"`), or None if the
    project has no Python code (then nothing can be said)."""
    names, found = set(), False
    for p in glob.glob(os.path.join(root, "python", "**", "*.py"), recursive=True):
        if "tests" in p.split(os.sep):
            continue
        found = True
        with open(p, encoding="utf-8") as fh:
            names |= set(DEFINES.findall(fh.read()))
    return names if found else None


def _var(x):
    return isinstance(x, str) and x.startswith("?")


def check_syntax(s, where, err, warn, bound=frozenset(), used=None):
    """Validate a sentence of the shared syntax (v2): structure, arities, variables bound. `used` (a set)
    collects the non-base heads, to warn when no theory defines them."""
    if isinstance(s, str):
        if _var(s):
            err(where, "variable %r used as a sentence" % s) if len(s) > 1 else err(where, "empty variable name '?'")
        return
    if not isinstance(s, list) or not s or not isinstance(s[0], str):
        err(where, "malformed sentence %r" % (s,))
        return
    op, args = s[0], s[1:]
    if used is not None and op not in BASE_CONNECTIVES:
        used.add(op)
    if op in BINDERS:
        if len(args) != BINDERS[op]:
            err(where, "%r takes a variable and %d formula(s): [%r, \"?x\"%s]" % (
                op, BINDERS[op] - 1, op, ", A" if BINDERS[op] == 2 else ", Restrictor, Scope"))
            return
        if not _var(args[0]) or len(args[0]) < 2:
            err(where, "%r needs a variable like \"?x\" as first argument, got %r" % (op, args[0]))
            return
        for a in args[1:]:
            check_syntax(a, where, err, warn, bound | {args[0]}, used)
        return
    if op in KNOWN_OPS:
        if len(args) != KNOWN_OPS[op]:
            err(where, "operator %r takes %d argument(s)" % (op, KNOWN_OPS[op]))
        for a in args:
            check_syntax(a, where, err, warn, bound, used)
        return
    if not args:
        err(where, "%r needs at least one argument (a predicate takes terms, an operator takes sentences)" % op)
        return
    if _var(args[0]) and any(isinstance(a, list) for a in args[1:]):
        # binder-shaped, theory-defined (for example ["most","?x",R,S])
        for a in args[1:]:
            check_syntax(a, where, err, warn, bound | {args[0]}, used)
        return
    for a in args:      # predicate application (terms) or theory-defined operator (sentences)
        if _var(a) and a not in bound:
            err(where, "variable %r is not bound by any quantifier in %s" % (a, json.dumps(s)))
        elif not isinstance(a, str):
            check_syntax(a, where, err, warn, bound, used)
        elif _var(a) and len(a) < 2:
            err(where, "empty variable name '?'")


def check_log(entries, file, ident, E, W):
    """Validate a `checks` list (log entries of statements and fragments)."""
    if entries is None:
        return
    if not isinstance(entries, list):
        E(file, ident, "checks must be a list")
        return
    for n, c in enumerate(entries, 1):
        w = "check #%d" % n
        if not isinstance(c, dict):
            E(file, ident, "%s must be an object" % w)
            continue
        for fld, allowed in (("by", CHECK_BY), ("what", CHECK_WHAT), ("verdict", CHECK_VERDICT)):
            if c.get(fld) not in allowed:
                E(file, ident, "%s: %s %r must be one of %s" % (w, fld, c.get(fld), "|".join(allowed)))
        when = c.get("when")
        if when:
            try:
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(when)):
                    raise ValueError
                datetime.date.fromisoformat(when)
            except ValueError:
                E(file, ident, "%s: when %r must be YYYY-MM-DD" % (w, when))
        for fld in ("who", "readback", "note", "ref"):
            if fld in c and not isinstance(c[fld], str):
                E(file, ident, "%s: %s must be a string" % (w, fld))
        if c.get("what") == "readback" and c.get("by") == "llm" and not c.get("readback"):
            W(file, ident, "%s: an llm readback check should carry the readback text" % w)


def check_fragments(frs, E, W):
    f_ = "data/fragments.json"
    if not isinstance(frs, list):
        E(f_, "-", "must be a list")
        return set()
    seen = set()
    for fr in frs:
        i = fr.get("id") if isinstance(fr, dict) else None
        if not i:
            E(f_, "-", "fragment without id")
            continue
        if i in seen:
            E(f_, i, "duplicate id")
        seen.add(i)
        if not fr.get("name"):
            W(f_, i, "no name")
        for fld in ("name", "summary", "notation", "notes"):
            if fld in fr and not isinstance(fr[fld], str):
                E(f_, i, "%s must be a string" % fld)
        defs = fr.get("defs", [])
        if not isinstance(defs, list):
            E(f_, i, "defs must be a list")
        else:
            for n, dd in enumerate(defs, 1):
                if not isinstance(dd, dict) or not dd.get("label") or not (dd.get("text") or dd.get("notation")):
                    E(f_, i, "def #%d needs a label and a text or notation" % n)
                elif any(k in dd and not isinstance(dd[k], str) for k in ("label", "text", "notation")):
                    E(f_, i, "def #%d: label, text and notation must be strings" % n)
        files = fr.get("files", {})
        if not isinstance(files, dict) or any(not isinstance(v, list) for v in files.values()):
            E(f_, i, "files must be an object {language: [paths]}")
        check_log(fr.get("checks"), f_, i, E, W)
    return seen


def check_display_options(meta, reg, ladder, E):
    """Optional display settings of the report: meta.short_names / family_short / fact_kinds (objects of strings),
    meta.theory_kinds (object of strings), meta.page_title / subtitle / banner / banner_title (strings), meta.banner_points (list of strings),
    meta.paper ({title, authors, year, url}), registry.layers (list of ids or {id, name}), registry.proof_kinds (kinds of the ladder)."""
    if isinstance(meta, dict):
        for k in ("short_names", "family_short", "fact_kinds", "theory_kinds"):
            v = meta.get(k)
            if v is not None and (not isinstance(v, dict) or any(not isinstance(x, str) for x in v.values())):
                E("data/meta.json", k, "must be an object whose values are strings")
        for k in ("banner", "banner_title", "page_title", "subtitle"):
            if k in meta and not isinstance(meta[k], str):
                E("data/meta.json", k, "must be a string" + (" (empty = no band)" if k == "banner" else ""))
        bp = meta.get("banner_points")
        if bp is not None and (not isinstance(bp, list) or any(not isinstance(x, str) for x in bp)):
            E("data/meta.json", "banner_points", "must be a list of strings")
        pa = meta.get("paper")
        if pa is not None and (not isinstance(pa, dict) or not isinstance(pa.get("title"), str)
                               or any(k in pa and not isinstance(pa[k], (str, int)) for k in ("authors", "year", "url"))):
            E("data/meta.json", "paper", "must be an object {title, authors, year, url} with a title string")
    lay = reg.get("layers")
    if lay is not None:
        if not isinstance(lay, list) or any(not (isinstance(x, str) or (isinstance(x, dict) and isinstance(x.get("id"), str))) for x in lay):
            E("custom/registry.json", "layers", "must be a list of ids or of {id, name}")
    pk = reg.get("proof_kinds")
    if pk is not None:
        if not isinstance(pk, list) or any(x not in ladder for x in pk):
            E("custom/registry.json", "proof_kinds", "must be a list of kinds of the ladder")


def check_skills(root, W):
    """Warn when installed linglab skills no longer match utils/moves/ (the toolkit was replaced). Projects
    without installed linglab skills are not warned: they may use another assistant."""
    from .init import skills_status, MANAGED_SKILLS
    sk = os.path.join(root, ".claude", "skills")
    if not os.path.isfile(os.path.join(sk, MANAGED_SKILLS)):
        return
    stale, missing, removed = skills_status(root)
    parts = ["%s: %s" % (k, ", ".join(v)) for k, v in (("outdated", stale), ("missing", missing),
                                                      ("no longer in the toolkit", removed)) if v]
    if parts:
        W(".claude/skills", "-", "skills do not match utils/moves/ (%s): run `python3 utils/bin/linglab.py skills`"
          % "; ".join(parts))


def run_check(root=".", out=print):
    d = load_project(root)
    errors, warnings = [], []
    E = lambda f, i, m: errors.append("ERROR   %s %s: %s" % (f, i, m))
    W = lambda f, i, m: warnings.append("warning %s %s: %s" % (f, i, m))
    reg = d["registry"]
    ladder, outcomes = reg.get("ladder", []), reg.get("outcomes", [])
    types = reg.get("fact_types", FACT_TYPES)

    meta = d["meta"]
    if not isinstance(meta, dict) or not meta.get("title"):
        E("data/meta.json", "-", "title is required")
    for p in (meta.get("papers") or []) if isinstance(meta, dict) else []:
        if p.get("role") not in (None, "target", "data", "proposal", "background"):
            E("data/meta.json", p.get("id", "?"), "paper role %r unknown" % p.get("role"))

    check_display_options(meta, reg, ladder, E)

    st = d["statements"]
    ids, roles = {}, {}
    for s in st:
        i = s.get("id")
        if not i:
            E("data/statements.json", "-", "statement without id")
            continue
        if i in ids:
            E("data/statements.json", i, "duplicate id")
        ids[i] = s
        roles[i] = s.get("role")
    f_ = "data/statements.json"
    fact_used = {}      # fact id -> heads of its sentences that are not base connectives
    for s in st:
        i = s.get("id", "?")
        role = s.get("role")
        if role not in ("fact", "principle"):
            E(f_, i, "role must be fact or principle")
            continue
        if role == "fact" and not re.match(r"^F", i):
            E(f_, i, "fact ids start with F")
        if role == "principle" and not i.startswith("P-"):
            E(f_, i, "principle ids start with P-")
        if not s.get("name"):
            W(f_, i, "no name")
        if not s.get("text"):
            W(f_, i, "no text")
        c = s.get("confidence")
        if c is None:
            W(f_, i, "no confidence") if role == "fact" else None
        elif not isinstance(c, (int, float)) or not 0 <= c <= 1:
            E(f_, i, "confidence must be a number in [0,1]")
        if "notation" in s and not isinstance(s["notation"], str):
            E(f_, i, "notation must be a string (LaTeX)")
        if role == "fact":
            for k in ("kind", "layer"):      # display grouping of the Theories x Facts heatmap (SPEC section 7)
                if k in s and not isinstance(s[k], str):
                    E(f_, i, "%s must be a string (a kind of fact / a reliability set)" % k)
            rq = s.get("requires")
            if rq is not None and not (isinstance(rq, str) or (isinstance(rq, list) and all(isinstance(x, str) for x in rq))):
                E(f_, i, "requires must be a fragment id or a list of fragment ids")
        check_log(s.get("checks"), f_, i, E, W)
        for o in s.get("origins", []):
            if not isinstance(o, dict) or "source" not in o:
                E(f_, i, "origin needs a source")
        for r in s.get("relations", []):
            if r.get("rel") not in REL:
                E(f_, i, "relation %r unknown" % r.get("rel"))
            if r.get("to") not in ids:
                E(f_, i, "relation points to unknown id %r" % r.get("to"))
        if role == "fact":
            t = s.get("type")
            if t not in types:
                E(f_, i, "type %r unknown" % t)
                continue
            if s.get("expected", "holds") not in ("holds", "fails"):
                E(f_, i, "expected must be holds or fails")
            if s.get("about", "language") not in ("language", "system"):
                E(f_, i, "about must be language or system")
            used = fact_used.setdefault(i, set())
            if "uses" in s and not (isinstance(s["uses"], list) and all(isinstance(x, str) for x in s["uses"])):
                E(f_, i, "uses must be a list of primitive names")
            if "parses" in s:
                ps = s["parses"]
                if not isinstance(ps, list):
                    E(f_, i, "parses must be a list of {id, spec}")
                else:
                    seen = {"main"}
                    for pr in ps:
                        pid = pr.get("id") if isinstance(pr, dict) else None
                        if not isinstance(pid, str) or not pid:
                            E(f_, i, "a parse needs an id"); continue
                        if pid in seen:
                            E(f_, i, "parse id %r is duplicated (or reserved)" % pid)
                        seen.add(pid)
                        sp = pr.get("spec")
                        if not isinstance(sp, dict):
                            E(f_, i, "parse %r needs a spec" % pid); continue
                        for fld in SPEC_FIELDS.get(t, []):
                            if fld not in sp:
                                E(f_, i, "parse %r: spec of type %s lacks %r" % (pid, t, fld))
                        for fld in ("premises", "discourse"):
                            for x in (sp.get(fld) if isinstance(sp.get(fld), list) else []):
                                check_syntax(x, "%s %s" % (f_, i), lambda w, m: E(f_, i, m), lambda w, m: W(f_, i, m), used=used)
                        for fld in ("conclusion", "sentence", "target", "preferred", "over"):
                            if fld in sp:
                                check_syntax(sp[fld], "", lambda w, m: E(f_, i, m), lambda w, m: W(f_, i, m), used=used)
            spec = s.get("spec")
            if t == "other":
                continue
            if not isinstance(spec, dict):
                E(f_, i, "type %s needs a spec" % t)
                continue
            for fld in SPEC_FIELDS.get(t, []):
                if fld not in spec:
                    E(f_, i, "spec of type %s lacks %r" % (t, fld))
            if t == "truth" and spec.get("relation") not in ("equals", "within", "includes"):
                E(f_, i, "truth relation must be equals, within or includes")
            for fld in ("premises", "discourse"):
                if fld in spec:
                    if not isinstance(spec[fld], list):
                        E(f_, i, "%s must be a list" % fld)
                    else:
                        for x in spec[fld]:
                            check_syntax(x, "%s %s" % (f_, i), lambda w, m: E(f_, i, m), lambda w, m: W(f_, i, m), used=used)
            for fld in ("conclusion", "sentence", "target", "preferred", "over"):
                if fld in spec:
                    check_syntax(spec[fld], "", lambda w, m: E(f_, i, m), lambda w, m: W(f_, i, m), used=used)
        else:
            if "type" in s or "spec" in s:
                W(f_, i, "type/spec on a principle are ignored")

    defined = defined_names(root)
    if defined is not None:
        for i, heads in fact_used.items():
            for h in sorted(heads - defined):
                W(f_, i, "no principle of the project defines %r (connective, operator or predicate): "
                         "the fact is out of scope in every theory" % h)

    th = d["theories"]
    frids = check_fragments(d["fragments"], E, W)
    for i, s in ids.items():            # the fragment(s) a fact requires (optional, shown in the heatmap panel)
        rq = s.get("requires")
        for fr in ([rq] if isinstance(rq, str) else rq if isinstance(rq, list) else []):
            if isinstance(fr, str) and fr not in frids:     # a project without any fragment: only a warning
                (E if frids else W)("data/statements.json", i, "requires unknown fragment %r" % fr)
    tids = set()
    for t in th:
        i = t.get("id")
        if i in tids:
            E("data/theories.json", i, "duplicate id")
        tids.add(i)
    for t in th:
        i = t.get("id", "?")
        if t.get("kind") not in (None,) + tuple(THEORY_KINDS):
            E("data/theories.json", i, "kind %r unknown" % t.get("kind"))
        if t.get("parent") and t["parent"] not in tids:
            E("data/theories.json", i, "parent %r unknown" % t["parent"])
        if "notation" in t and not isinstance(t["notation"], str):
            E("data/theories.json", i, "notation must be a string (LaTeX)")
        for k in ("short", "family"):
            if k in t and not isinstance(t[k], str):
                E("data/theories.json", i, "%s must be a string" % k)
        if not isinstance(t.get("fragments", []), list):
            E("data/theories.json", i, "fragments must be a list of fragment ids")
        else:
            for fr in t.get("fragments", []):
                if fr not in frids:
                    E("data/theories.json", i, "unknown fragment %r" % fr)
        for k, vals in (("predicts", FACT_TYPES), ("primitives", None)):
            if k in t:
                if not (isinstance(t[k], list) and all(isinstance(x, str) for x in t[k])):
                    E("data/theories.json", i, "%s must be a list of strings" % k)
                elif vals and any(x not in types for x in t[k]):
                    E("data/theories.json", i, "predicts: unknown fact type(s) %s" % ", ".join(x for x in t[k] if x not in types))
        if t.get("parse_policy", "first") not in PARSE_POLICIES:
            E("data/theories.json", i, "parse_policy must be one of %s" % ", ".join(PARSE_POLICIES))
        if "picks" in t:
            pk = t["picks"]
            if not isinstance(pk, dict):
                E("data/theories.json", i, "picks must map a fact id to a list of parse ids")
            else:
                for fid, lst in pk.items():
                    have = {"main"} | {str(x.get("id")) for x in (ids.get(fid, {}).get("parses") or []) if isinstance(x, dict)}
                    if fid not in ids:
                        E("data/theories.json", i, "picks: unknown fact %r" % fid)
                    elif not (isinstance(lst, list) and all(x in have for x in lst)):
                        E("data/theories.json", i, "picks %s: unknown parse id(s) (candidates: %s)" % (fid, ", ".join(sorted(have))))
        for p in t.get("principles", []):
            if p not in ids:
                E("data/theories.json", i, "unknown principle %r" % p)
            elif roles[p] != "principle" and not t.get("generated"):
                E("data/theories.json", i, "%r is not a principle" % p)
    used = {p for t in th for p in t.get("principles", [])}
    for i, s in ids.items():
        if s.get("role") == "principle" and i not in used:
            W(f_, i, "principle used by no theory")
    # `uses` only has an effect on theories that declare `primitives`: facts with `uses` and no such
    # theory suggest that coverage was never declared, so fails may hide "not modelled" cells
    uses_facts = [i for i, s in ids.items() if s.get("role") == "fact" and s.get("uses")]
    if uses_facts and not any("primitives" in t for t in th
                              if t.get("kind") != "reference" and not t.get("generated")):
        W(f_, uses_facts[0], "%d fact(s) declare `uses` but no theory (other than a reference one) declares "
          "`primitives`: `uses` has no effect; declare what each theory covers (a fact a theory's source "
          "leaves to another mechanism is out of scope, not a fail)" % len(uses_facts))

    py_ids = set()
    for p in glob.glob(os.path.join(root, "python", "**", "*.py"), recursive=True):
        py_ids |= set(chunks(p, PY_TAG))
    for i, s in ids.items():
        pid = (s.get("code") or {}).get("python")
        if s.get("role") == "principle" and pid and pid not in py_ids:
            W(f_, i, "Python principle %r not found in python/ (no tagged chunk)" % pid)

    pydir = os.path.join(root, "python")
    if os.path.isdir(pydir):
        static = set()
        for p in glob.glob(os.path.join(pydir, "**", "*.py"), recursive=True):
            with open(p, encoding="utf-8") as fh:
                static |= set(PRINCIPLE_DECO.findall(fh.read()))
        for t in th:
            if t.get("generated"):
                continue
            for p in t.get("principles", []):
                if p in ids and p not in static:
                    W("data/theories.json", t.get("id", "?"),
                      "principle %r has no Python code in python/ (no @principle(%r))" % (p, p))

    for e in d["results"]:
        w = "%s/%s" % (e.get("fact"), e.get("theory"))
        if e.get("fact") not in ids or roles.get(e.get("fact")) != "fact":
            E("data/results.json", w, "unknown fact")
        if e.get("theory") not in tids:
            E("data/results.json", w, "unknown theory")
        if e.get("outcome") not in outcomes:
            E("data/results.json", w, "outcome %r unknown" % e.get("outcome"))
        if e.get("kind") not in ladder:
            E("data/results.json", w, "kind %r not in the ladder" % e.get("kind"))
        if e.get("scope") not in (None, "") + SCOPE_REASONS:
            E("data/results.json", w, "scope %r must be one of %s" % (e.get("scope"), ", ".join(SCOPE_REASONS)))
        elif e.get("scope") and e.get("outcome") != "out_of_scope":
            W("data/results.json", w, "scope is only meaningful on an out_of_scope entry")
        if e.get("kind") == "paper-claim" and e.get("presence") not in (None, "") + tuple(PRESENCE):
            E("data/results.json", w, "presence %r unknown" % e.get("presence"))
        b = e.get("bound", "")
        if b and not re.match(r"^(exhaustive|first \d+ models|size<=\d+)( within .+)?$", b):
            E("data/results.json", w, "bound %r must be exhaustive or first n models (optionally followed by 'within <scope>')" % b)
    for r in d["findings"]:
        i = r.get("id", "?")
        if r.get("status") not in FINDING_STATUS:
            E("data/findings.json", i, "status %r unknown" % r.get("status"))
        for p in r.get("principles", []) + r.get("facts", []):
            if p not in ids:
                E("data/findings.json", i, "unknown id %r" % p)
    # readings: an LLM's (or a person's) meta-reading of a cell; never evidence, never pooled
    fids = {i for i, s in ids.items() if s.get("role") == "fact" or (not s.get("role") and str(i).startswith("F"))}
    seen_rd = set()
    for n, r in enumerate(d["readings"]):
        w = "%s x %s" % (r.get("fact", "?"), r.get("theory", "?"))
        if r.get("fact") not in fids:
            E("data/readings.json", w, "unknown fact %r" % r.get("fact"))
        if r.get("theory") not in tids:
            E("data/readings.json", w, "unknown theory %r" % r.get("theory"))
        if not str(r.get("text", "")).strip():
            E("data/readings.json", w, "empty text")
        if r.get("review", "unreviewed") not in READING_REVIEW:
            E("data/readings.json", w, "review %r must be one of %s" % (r.get("review"), ", ".join(READING_REVIEW)))
        if (r.get("fact"), r.get("theory")) in seen_rd:
            E("data/readings.json", w, "two readings for the same cell")
        seen_rd.add((r.get("fact"), r.get("theory")))
    check_skills(root, W)
    # informational summaries (not warnings, one line each)
    infos = []
    pr = [s for s in st if s.get("role") == "principle"]
    no_not = [s["id"] for s in pr if not s.get("notation")]
    no_code = [s["id"] for s in pr if not any((s.get("code") or {}).values())]
    real = [t for t in th if not t.get("generated")]
    no_fr = [t.get("id", "?") for t in real if not t.get("fragments")]
    proof_kinds = d["registry"].get("proof_kinds") or ["lean"]
    formal = {e.get("fact") for e in d["results"] if e.get("kind") in proof_kinds}
    no_rb = [s["id"] for s in st if s.get("role") == "fact" and s.get("id") in formal
             and not any(isinstance(c, dict) and c.get("what") == "readback" for c in s.get("checks") or [])]
    for n, ids_, msg in ((len(no_not), no_not, "principle(s) without notation"),
                         (len(no_code), no_code, "principle(s) without code"),
                         (len(no_fr), no_fr, "theory(ies) without fragments"),
                         (len(no_rb), no_rb, "formally proved fact(s) without a readback check")):
        if n:
            infos.append("info: %d %s (e.g. %s)" % (n, msg, ", ".join(ids_[:3])))
    for m in warnings + errors + infos:
        out(m)
    out("%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0
