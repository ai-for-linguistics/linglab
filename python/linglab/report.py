"""`linglab report`: inline the data into the report template."""
import glob
import json
import os
import re
import textwrap

from .common import load_project, TOOLKIT, facts_of
from . import metrics, leancmd, latex

MAX_SNIPPET = 12

PLACEHOLDER = "/*__DATA__*/null"


def find_template(root):
    for p in (os.path.join(root, "report", "template.html"),
              os.path.join(TOOLKIT, "template", "report", "template.html")):
        if os.path.exists(p):
            return p
    return None


BINDER_HEADS = ("some", "every", "no", "exists", "forall")


def infix(s, top=True):
    """Shared-syntax s-expression (JSON) -> readable text (outer parentheses dropped). Examples:
    "not s or a", "some x (Student x) (Passed x)", "must (p or q)", "(Student x) and (Passed x)"."""
    if isinstance(s, str):
        return s.lstrip("?") if s.startswith("?") else s
    if not isinstance(s, list) or not s or not isinstance(s[0], str):
        return json.dumps(s)
    op, args = s[0], s[1:]

    def arg(a):                     # an argument of a prefix form: atoms bare, the rest in parentheses
        return a.lstrip("?") if isinstance(a, str) else "(" + infix(a, True) + ")"
    if op == "not" and len(args) == 1:
        a = infix(args[0], False)
        return "not " + (a if not isinstance(args[0], list) or args[0][0] == "not" or a.startswith("(") else "(" + a + ")")
    if op in ("and", "or", "if", "iff") and len(args) == 2:
        r = "%s %s %s" % (infix(args[0], False), op, infix(args[1], False))
        return r if top else "(" + r + ")"
    binder = (op in BINDER_HEADS or (len(args) >= 2 and isinstance(args[0], str) and args[0].startswith("?")
                                     and any(isinstance(a, list) for a in args[1:]))) \
        and args and isinstance(args[0], str) and args[0].startswith("?")
    if binder:
        r = "%s %s %s" % (op, args[0].lstrip("?"), " ".join(arg(a) for a in args[1:]))
        return r if top else "(" + r + ")"
    if op in ("must", "may") and len(args) == 1:
        r = "%s %s" % (op, arg(args[0]))
        return r if top else "(" + r + ")"
    if args and all(isinstance(a, str) for a in args):          # predicate application
        r = " ".join([op] + [a.lstrip("?") if a.startswith("?") else a for a in args])
        return r if top else "(" + r + ")"
    return "%s(%s)" % (op, ", ".join(infix(a) for a in args))


def md_to_html(text):
    """A small markdown subset (headings, bullet and numbered lists, fenced code, paragraphs; inline code, bold,
    italic) to HTML, everything escaped. Enough for METHOD.md and docs/SPEC.md."""
    import html as _h

    def inline(t):
        t = _h.escape(t, quote=False)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
        return re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])", r"<i>\1</i>", t)
    out, state = [], {"para": [], "items": [], "kind": None}

    def flush():
        if state["para"]:
            out.append("<p>%s</p>" % inline(" ".join(state["para"])))
        if state["items"]:
            k = state["kind"]
            out.append("<%s>%s</%s>" % (k, "".join("<li>%s</li>" % inline(i) for i in state["items"]), k))
        state.update(para=[], items=[], kind=None)
    code = None
    for line in text.split("\n"):
        if code is not None:
            if line.startswith("```"):
                out.append("<pre>%s</pre>" % _h.escape("\n".join(code), quote=False))
                code = None
            else:
                code.append(line)
            continue
        m = re.match(r"^(#{1,4}) (.*)", line)
        b = re.match(r"^\s*[-*] (.*)", line)
        n = re.match(r"^\s*\d+\. (.*)", line)
        if line.startswith("```"):
            flush()
            code = []
        elif m:
            flush()
            out.append("<h%d>%s</h%d>" % (len(m.group(1)), inline(m.group(2)), len(m.group(1))))
        elif b or n:
            k = "ul" if b else "ol"
            if state["kind"] != k:
                flush()
                state["kind"] = k
            state["items"].append((b or n).group(1))
        elif line.startswith("  ") and state["items"]:
            state["items"][-1] += " " + line.strip()
        elif not line.strip():
            flush()
        else:
            if state["items"]:
                flush()
            state["para"].append(line.strip())
    flush()
    # "__" would make the quoted placeholders (/*__DATA__*/, __KATEX_*__) of the template appear twice in the page
    return "\n".join(out).replace("__", "_&#95;")


def toolkit_docs():
    """METHOD.md and docs/SPEC.md of the toolkit, rendered for the Instructions tab (missing files are skipped)."""
    docs = []
    for title, rel in (("Method", "METHOD.md"), ("Technical contract", os.path.join("docs", "SPEC.md"))):
        p = os.path.join(TOOLKIT, rel)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                docs.append({"title": title, "html": md_to_html(f.read())})
    return docs


def _list(l):
    return " ; ".join(infix(x) for x in l) if isinstance(l, list) and l else "(none)"


def spec_text(f):
    sp = f.get("spec")
    if not isinstance(sp, dict):
        return ""
    t = f.get("type")
    try:
        if t == "entailment":
            return "premises: %s; conclusion: %s" % (_list(sp.get("premises")), infix(sp.get("conclusion")))
        if t == "felicity":
            return "discourse: " + _list(sp.get("discourse"))
        if t == "consistency":
            return "premises: " + _list(sp.get("premises"))
        if t == "truth":
            return "%s %s %s" % (infix(sp.get("sentence")), sp.get("relation", "equals"), infix(sp.get("target")))
        if t == "preference":
            return "%s: %s preferred over %s" % (infix(sp.get("sentence")), infix(sp.get("preferred")), infix(sp.get("over")))
        if t == "property":
            return "property check: %s" % sp.get("check", "")
    except Exception:
        pass
    return json.dumps(sp, ensure_ascii=False)


def _files(root, sub, ext, skip):
    out = []
    for p in sorted(glob.glob(os.path.join(root, sub, "**", "*" + ext), recursive=True)):
        if set(skip) & set(p.split(os.sep)) or ("tests" in p.split(os.sep) and sub == "python"):
            continue
        out.append(p)
    return out


def _chunk_text(lines):
    return textwrap.dedent("\n".join(lines)).strip("\n")


def principle_code(root):
    res = {}
    for lang, sub, ext, skip in (("python", "python", ".py", ("__pycache__",)),
                                 ("lean", "lean", ".lean", (".lake",))):
        tag = metrics.PY_TAG if lang == "python" else metrics.LEAN_TAG
        for p in _files(root, sub, ext, skip):
            try:
                for pid, ls in metrics.chunks(p, tag).items():
                    t = _chunk_text(ls)
                    if t.strip():
                        d = res.setdefault(pid, {})
                        d[lang] = (d[lang] + "\n\n" + t) if lang in d else t
            except (OSError, UnicodeDecodeError):
                pass
    return res


def _snippet(lines, i):
    first = lines[i]
    ind = len(first) - len(first.lstrip())
    out = [first.rstrip()]
    for l in lines[i + 1:]:
        if not l.strip() or len(out) >= MAX_SNIPPET:
            break
        cur = len(l) - len(l.lstrip())
        if cur <= ind:
            break
        out.append(l.rstrip())
    return textwrap.dedent("\n".join(out))


def fact_code(root, d):
    """-> {fact id: {spec_text, lean: [{theory, text}]}}"""
    res = {}
    theories = {t["id"].replace("-", "_"): t["id"] for t in d["theories"]}
    for f in facts_of(d["statements"]):
        res[f["id"]] = {"spec_text": spec_text(f), "lean": []}
        na = latex.notation_auto(f)
        if na:
            res[f["id"]]["notation_auto"] = na
    for p in _files(root, "lean", ".lean", (".lake",)):
        try:
            lines = open(p, encoding="utf-8").read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        ctx = []
        for i, line in enumerate(lines):
            if line.lstrip().startswith("--"):
                continue
            m = leancmd.NS.match(line)
            if m:
                ctx.append(m.group(1)); continue
            m = leancmd.END.match(line)
            if m and ctx and ctx[-1] == m.group(1):
                ctx.pop(); continue
            m = leancmd.THM.match(line)
            if not m or not ctx or m.group(1) not in res:
                continue
            tid = theories.get(ctx[-1].split(".")[-1])
            if tid is None:
                continue
            res[m.group(1)]["lean"].append({"theory": tid, "text": _snippet(lines, i)})
    return res


def build_code(root, d):
    code = {"principles": {}, "facts": {}}
    try:
        code["principles"] = principle_code(root)
    except Exception:
        pass
    try:
        code["facts"] = fact_code(root, d)
    except Exception:
        pass
    return code


def fragment_users(d):
    """{fragment id: [theory ids that use it]} (every fragment is a key; theories in file order)."""
    users = {fr["id"]: [] for fr in d["fragments"] if isinstance(fr, dict) and fr.get("id")}
    for t in d["theories"]:
        for f in t.get("fragments") or []:
            if f in users and t.get("id") not in users[f]:
                users[f].append(t.get("id"))
    return users


def has_notation(data):
    if any((x.get("notation") or "").strip() for k in ("statements", "theories", "fragments") for x in data[k]
           if isinstance(x, dict)):
        return True
    return any(v.get("notation_auto") for v in data["code"]["facts"].values())


def inject_katex(html, root, data, out=print):
    """Fill the optional KaTeX placeholders of the template (CSS with base64 fonts, JS); empty if no LaTeX is used."""
    if latex.CSS_PLACEHOLDER not in html and latex.JS_PLACEHOLDER not in html:
        return html
    css = js = ""
    if has_notation(data):
        assets = latex.katex_assets(root)
        if assets is None:
            out("warning: KaTeX files not found (template/report/vendor/katex/ in the toolkit); "
                "notation will be shown as LaTeX source")
        else:
            css, js = assets
            js = js.replace("</", "<\\/")
            css = css.replace("</", "<\\/")
    # callables: the replacement text must not be scanned for backslash escapes
    html = html.replace(latex.CSS_PLACEHOLDER, css, 1)
    return html.replace(latex.JS_PLACEHOLDER, js, 1)


def build_report(root=".", output=None, out=print):
    lines = []
    from .check import run_check
    if run_check(root, out=lines.append):
        n = next((l for l in reversed(lines) if l.endswith("warning(s)")), "errors")
        out("warning: linglab check reports errors (%s); the report is built anyway, run `linglab check`" % n)
    tpl = find_template(root)
    if tpl is None:
        out("error: no report template found (looked for report/template.html in the project "
            "and template/report/template.html in the toolkit)")
        return 2
    d = load_project(root)
    data = {k: d[k] for k in ("meta", "statements", "theories", "results", "findings", "metrics", "registry", "readings")}
    from .version import toolkit_info
    data["toolkit"] = toolkit_info()
    data["docs"] = toolkit_docs()
    data["code"] = build_code(root, d)
    data["fragments"] = d["fragments"]
    data["fragment_users"] = fragment_users(d)
    # same escaping as the old build_report: no "</script>" inside the inlined JSON
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/") \
        .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    html = open(tpl, encoding="utf-8").read()
    if PLACEHOLDER not in html:
        out("error: template %s lacks the placeholder %s" % (tpl, PLACEHOLDER))
        return 2
    html = html.replace(PLACEHOLDER, blob, 1)
    html = inject_katex(html, root, data, out)
    dest = output or os.path.join(root, "report", "index.html")
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    out("wrote %s (%d bytes)" % (dest, len(html)))
    return 0
