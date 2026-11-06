"""LaTeX helpers: `notation_auto` (LaTeX generated from a fact spec) and the KaTeX assets inlined in the report.

Conventions of `notation_auto` (the project may override it with an explicit `notation` on the fact):
  atoms and constants: one letter as is, longer names \\mathrm{name}; variables ?x -> x
  not/and/or/if/iff -> \\neg \\land \\lor \\to \\leftrightarrow; must/may -> \\Box \\Diamond
  some/every/no x R S -> \\mathrm{some}\\,x\\,(R)\\,(S) (any other binder-shaped head the same way)
  exists/forall -> \\exists x\\,A, \\forall x\\,A; predicates and unknown operators -> P(a), \\mathrm{exh}(A)
  entailment   premises \\vDash conclusion   (\\nvDash when expected is "fails"; empty premises: \\vDash C)
  felicity     \\mathrm{felic}(d1 ; d2)       (negated, \\neg\\,\\mathrm{felic}(d), when expected fails)
  consistency  \\mathrm{cons}(A, B)          (negated when expected fails)
  truth        \\llbracket s \\rrbracket = | \\subseteq | \\supseteq \\llbracket t \\rrbracket  (\\neq, \\nsubseteq, \\nsupseteq when fails)
  preference   B \\succ_{A} C  (\\nsucc when fails);  property  \\mathrm{prop}(name)
"""
import base64
import os
import re

from .common import TOOLKIT

CONN = {"and": r"\land", "or": r"\lor", "if": r"\to", "iff": r"\leftrightarrow"}
MODAL = {"must": r"\Box", "may": r"\Diamond"}
BINDER_Q = {"exists": r"\exists", "forall": r"\forall"}
_ESC = {"_": r"\_", "&": r"\&", "%": r"\%", "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}",
        "\\": r"\backslash ", "~": r"\sim ", "^": r"\hat{}"}


def _name(x):
    x = str(x)
    if len(x) == 1 and x.isalpha():
        return x
    return r"\mathrm{%s}" % "".join(_ESC.get(c, c) for c in x)


def _term(x):
    return _name(x[1:]) if isinstance(x, str) and x.startswith("?") else _name(x)


def _isvar(x):
    return isinstance(x, str) and x.startswith("?") and len(x) > 1


def _atomic(s):
    return isinstance(s, str) or (isinstance(s, list) and s and s[0] not in CONN and s[0] not in BINDER_Q
                                  and s[0] not in MODAL and s[0] != "not" and not _binder_shaped(s))


def _binder_shaped(s):
    return (len(s) >= 3 and _isvar(s[1]) and any(isinstance(a, list) for a in s[2:])) or \
        (s[0] in ("some", "every", "no") and len(s) == 4)


def sentence(s):
    """Shared-syntax s-expression -> LaTeX (never raises on odd input: falls back to \\mathrm of the JSON)."""
    if isinstance(s, str):
        return _term(s)
    if not isinstance(s, list) or not s or not isinstance(s[0], str):
        return r"\mathrm{?}"
    op, args = s[0], s[1:]

    def sub(a):                     # child of a connective: parenthesise unless atomic or a negation
        t = sentence(a)
        return t if (_atomic(a) or (isinstance(a, list) and a and a[0] == "not")) else "(" + t + ")"

    def whole(a):                   # child of a unary operator or quantifier body
        return sentence(a) if _atomic(a) or (isinstance(a, list) and a and a[0] in ("not",) + tuple(MODAL)) \
            else "(" + sentence(a) + ")"
    if op == "not" and len(args) == 1:
        return r"\neg " + whole(args[0])
    if op in CONN and len(args) == 2:
        return "%s %s %s" % (sub(args[0]), CONN[op], sub(args[1]))
    if op in MODAL and len(args) == 1:
        return MODAL[op] + " " + whole(args[0])
    if op in BINDER_Q and len(args) == 2 and _isvar(args[0]):
        return r"%s %s\," % (BINDER_Q[op], _term(args[0])) + whole(args[1])
    if len(args) >= 2 and _isvar(args[0]) and any(isinstance(a, list) for a in args[1:]):
        return r"%s\,%s\,%s" % (_name(op), _term(args[0]), r"\,".join("(" + sentence(a) + ")" for a in args[1:]))
    return "%s(%s)" % (_name(op), ", ".join(sentence(a) for a in args))


def _seq(l, sep=", "):
    return sep.join(sentence(x) for x in l) if isinstance(l, list) else ""


def notation_auto(f):
    """LaTeX for a fact from its spec and `expected`, or None (no spec / type other / unreadable)."""
    sp, t = f.get("spec"), f.get("type")
    if not isinstance(sp, dict) or t == "other":
        return None
    fails = f.get("expected", "holds") == "fails"
    try:
        if t == "entailment":
            return "%s %s %s" % (_seq(sp.get("premises")), r"\nvDash" if fails else r"\vDash",
                                 sentence(sp["conclusion"]))
        if t in ("felicity", "consistency"):
            body = (r"\mathrm{felic}(%s)" % _seq(sp.get("discourse"), r" \,;\, ")) if t == "felicity" \
                else r"\mathrm{cons}(%s)" % _seq(sp.get("premises"))
            return (r"\neg\," + body) if fails else body
        if t == "truth":
            rel = {"equals": (r"=", r"\neq"), "within": (r"\subseteq", r"\nsubseteq"),
                   "includes": (r"\supseteq", r"\nsupseteq")}[sp.get("relation", "equals")][1 if fails else 0]
            return r"\llbracket %s \rrbracket %s \llbracket %s \rrbracket" % (
                sentence(sp["sentence"]), rel, sentence(sp["target"]))
        if t == "preference":
            return r"%s %s_{%s} %s" % (sentence(sp["preferred"]), r"\nsucc" if fails else r"\succ",
                                       sentence(sp["sentence"]), sentence(sp["over"]))
        if t == "property":
            return r"\mathrm{prop}(%s)" % _name(sp.get("check", ""))
    except (KeyError, TypeError, ValueError):
        return None
    return None


# ---- KaTeX assets -------------------------------------------------------------------------------------------

KATEX_FONTS = ["Main-Regular", "Main-Bold", "Main-Italic", "Math-Italic", "AMS-Regular", "Size1-Regular",
               "Size2-Regular", "Caligraphic-Regular", "Script-Regular", "Typewriter-Regular",
               "SansSerif-Regular", "SansSerif-Bold", "SansSerif-Italic", "Fraktur-Regular"]
CSS_PLACEHOLDER = "/*__KATEX_CSS__*/"
JS_PLACEHOLDER = "/*__KATEX_JS__*/"


def katex_dir(root="."):
    for p in (os.path.join(root, "report", "vendor", "katex"),
              os.path.join(TOOLKIT, "template", "report", "vendor", "katex")):
        if os.path.exists(os.path.join(p, "katex.min.js")) and os.path.exists(os.path.join(p, "katex.min.css")):
            return p
    return None


def katex_assets(root="."):
    """-> (css, js) with only the needed fonts embedded as base64 woff2, or None if the vendor files are missing."""
    d = katex_dir(root)
    if d is None:
        return None
    css = open(os.path.join(d, "katex.min.css"), encoding="utf-8").read()
    js = open(os.path.join(d, "katex.min.js"), encoding="utf-8").read()
    keep = {"KaTeX_%s.woff2" % n for n in KATEX_FONTS}

    def face(m):
        block = m.group(0)
        w = re.search(r"url\(fonts/([^)]+\.woff2)\)", block)
        fp = os.path.join(d, "fonts", w.group(1)) if w else None
        if not w or w.group(1) not in keep or not os.path.exists(fp):
            return ""
        b64 = base64.b64encode(open(fp, "rb").read()).decode("ascii")
        return re.sub(r"src:[^}]*", 'src:url(data:font/woff2;base64,%s) format("woff2")' % b64, block, count=1)
    css = re.sub(r"@font-face\{[^}]*\}", face, css)
    return css, js
