import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLI = os.path.join(ROOT, "bin", "linglab.py")
EXAMPLE = os.path.join(ROOT, "example")
sys.path.insert(0, os.path.join(ROOT, "python"))

from linglab import pooling  # noqa: E402

LADDER = ["lean", "python", "human", "paper-claim", "user-claim", "llm-judged"]


def linglab(cwd, *args):
    return subprocess.run([sys.executable, CLI] + list(args), cwd=cwd, capture_output=True, text=True)


def copy_example():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "ex")
    shutil.copytree(EXAMPLE, p, ignore=shutil.ignore_patterns("__pycache__", "report"))
    return d, p


def results(p):
    return json.load(open(os.path.join(p, "data", "results.json")))


def edit_fact(p, fid, change):
    path = os.path.join(p, "data", "statements.json")
    with open(path, encoding="utf-8") as f:
        st = json.load(f)
    for s in st:
        if s["id"] == fid:
            change(s)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)


class ExtensionApiTests(unittest.TestCase):
    """Operators that see formulas and other models (modals, exhaustification), overridable primitives."""
    def test_world_quantifying_operator_and_overrides(self):
        from linglab import vocab
        vocab._BASE_MODELS[:] = [lambda: [{"p": 1, "q": 1}, {"p": 1, "q": 0}, {"p": 0, "q": 0}]]
        reg = {}
        def conj(b): b.connective("and", lambda x, y: 1 if x == 1 and y == 1 else 0)
        def neg(b): b.connective("not", lambda x: 1 - x)
        def box(b):
            b.operator("box", lambda T, m, a: 1 if all(T.value(w, a) == 1 for w in T.worlds()) else 0, arity=1)
            b.set("describe_model", lambda T, m: "w(p=%s,q=%s)" % (m.vals["p"], m.vals["q"]))
        for pid, fn in (("A", conj), ("N", neg), ("B", box)):
            reg[pid] = vocab.Principle(pid, fn)
        T = vocab.Theory("T", "t", ["A", "N", "B"], registry=reg)
        f = T.translate(["box", "p"])
        self.assertIsNotNone(f)
        self.assertEqual(T.value(T.worlds()[0], f), 0)             # p is not true in every world
        self.assertIsNone(T.translate(["diamond", "p"]))           # unknown operator: not expressible
        self.assertEqual(T.describe(T.worlds()[0]), "w(p=0,q=0)")
        reg["O"] = vocab.Principle("O", lambda b: b.set("true_in", lambda T, m, g: m.vals["p"] == 1))
        T2 = vocab.Theory("T2", "t2", ["A", "N", "B", "O"], registry=reg)
        self.assertTrue(T2.true_in(T2.worlds()[-1], "p"))          # worlds sorted by size: last has p=1


class VersionTests(unittest.TestCase):
    def test_version_in_zip_project_report_and_site(self):
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(linglab(d, "version").returncode, 0)
            self.assertTrue(open(os.path.join(ROOT, "VERSION")).read().strip())
            self.assertEqual(linglab(ROOT, "zip").returncode, 0)
            with zipfile.ZipFile(os.path.join(ROOT, "dist", "linglab-beta.zip")) as z:
                names = z.namelist()
                self.assertIn("linglab/VERSION", names)
                info = json.loads(z.read("linglab/BUILD.json").decode("utf-8"))
                self.assertEqual(info["version"], open(os.path.join(ROOT, "VERSION")).read().strip())
                self.assertTrue(info["built"])
            self.assertEqual(linglab(d, "init", "V").returncode, 0)
            meta = json.load(open(os.path.join(d, "data", "meta.json")))
            self.assertEqual(meta["toolkit"]["version"], info["version"])
            self.assertEqual(linglab(d, "report").returncode, 0)
            self.assertIn('"toolkit"', open(os.path.join(d, "report", "index.html"), encoding="utf-8").read())
            self.assertEqual(linglab(ROOT, "site").returncode, 0)
            site = open(os.path.join(ROOT, "dist", "site", "index.html"), encoding="utf-8").read()
            self.assertIn("v" + info["version"], site)
            self.assertNotIn("{{VERSION}}", site)
        finally:
            shutil.rmtree(d)


class LinglibModeTests(unittest.TestCase):
    def test_init_linglib_and_refuse_to_build_before_fetch(self):
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(linglab(d, "init", "L").returncode, 0)
            r = linglab(d, "lean", "--init", "--linglib")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("LINGLIB MODE", r.stdout)
            lk = open(os.path.join(d, "lean", "lakefile.toml")).read()
            self.assertIn("linglib", lk)
            self.assertEqual(open(os.path.join(d, "lean", "lean-toolchain")).read().strip(), "leanprover/lean4:v4.34.0")
            self.assertTrue(os.path.exists(os.path.join(d, "lean", "Linglab", "Theories", "FoxIE.lean")))
            self.assertFalse(os.path.exists(os.path.join(d, "lean", "lake-manifest.json")))
            if shutil.which("lake"):
                r = linglab(d, "lean")
                self.assertIn("not fetched yet", r.stdout)
        finally:
            shutil.rmtree(d)


class ExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.p = copy_example()
        for c in ("listing", "run", "metrics"):
            r = linglab(cls.p, c)
            assert r.returncode == 0, r.stdout + r.stderr

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def py(self, f, t):
        es = [e for e in results(self.p) if e["fact"] == f and e["theory"] == t and e["kind"] == "python"]
        self.assertEqual(len(es), 1, (f, t))
        return es[0]["outcome"]

    def test_check(self):
        r = linglab(self.p, "check")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_expected_outcomes(self):
        exp = {
            "F01": dict(SK="pass", MK="pass", WK="fail", MKs="pass"),
            "F02": dict(SK="fail", MK="pass", WK="pass", MKs="fail"),
            "F03": dict(SK="pass", MK="pass", WK="pass", MKs="fail"),
            "F04": dict(SK="pass", MK="pass", WK="out_of_scope", MKs="pass"),
            "F07": dict(SK="pass", MK="pass", WK="out_of_scope", MKs="pass"),
        }
        for f in ("F05a", "F05b", "F06", "F08", "F09"):
            exp[f] = dict(SK="pass", MK="pass", WK="pass", MKs="pass")
        names = {"SK": "T-SK", "MK": "T-MK", "WK": "T-WK", "MKs": "T-MK-some"}
        for f, row in exp.items():
            for k, want in row.items():
                self.assertEqual(self.py(f, names[k]), want, (f, k))

    def test_pending_and_raw(self):
        rs = results(self.p)
        # F10/F11 are pending everywhere (not run), except F11 in T-WK, which declares that it makes no prediction for preferences
        extra = [e for e in rs if e["fact"] in ("F10", "F11") and e["kind"] == "python" and e["theory"] != "RAW"]
        self.assertEqual([(e["fact"], e["theory"], e["outcome"], e.get("scope")) for e in extra],
                         [("F11", "T-WK", "out_of_scope", "no_prediction")])
        raw = [e for e in rs if e["theory"] == "RAW" and e["kind"] == "python"]
        self.assertEqual(len(raw), 12)
        self.assertTrue(all(e["outcome"] == "pass" for e in raw))

    def test_pooling_markers(self):
        rs = results(self.p)
        cell = lambda f, t: pooling.pool([e for e in rs if e["fact"] == f and e["theory"] == t], LADDER)
        self.assertTrue(cell("F10", "T-WK")["conflict"])
        self.assertEqual(cell("F02", "T-SK")["warnings"], ["llm-judged"])
        self.assertEqual(cell("F02", "T-SK")["outcome"], "fail")
        self.assertEqual(cell("F10", "T-MK")["rank"], "human")

    def test_idempotent_and_keeps_other_kinds(self):
        before = results(self.p)
        linglab(self.p, "run", "--force")
        linglab(self.p, "listing")
        self.assertEqual(before, results(self.p))
        self.assertTrue(any(e["kind"] == "human" for e in before))

    def test_metrics(self):
        m = json.load(open(os.path.join(self.p, "data", "metrics.json")))
        t = m["theories"]["T-MK"]
        self.assertEqual(t["n_principles"], 6)
        self.assertEqual(t["n_principles_no_aux"], 5)
        self.assertGreater(t["principles"]["P-AND-MK"]["python"]["chars"], 10)
        self.assertNotIn("#", json.dumps(t["principles"]["P-AND-MK"]).replace("#", "") + "")
        self.assertIn("raw", m)

    def test_bound_text(self):
        r = linglab(self.p, "run", "--force", "--bound", "3", "--theory", "T-SK", "--fact", "F05a")
        e = [e for e in results(self.p) if e["fact"] == "F05a" and e["theory"] == "T-SK" and e["kind"] == "python"][0]
        self.assertEqual(e["bound"], "first 3 models")
        linglab(self.p, "run", "--force")
        e = [e for e in results(self.p) if e["fact"] == "F05a" and e["theory"] == "T-SK" and e["kind"] == "python"][0]
        self.assertEqual(e["bound"], "exhaustive")

    def test_report_with_stub(self):
        os.makedirs(os.path.join(self.p, "report"), exist_ok=True)
        open(os.path.join(self.p, "report", "template.html"), "w").write("<script>var D=/*__DATA__*/null;</script>")
        r = linglab(self.p, "report")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = open(os.path.join(self.p, "report", "index.html")).read()
        data = json.loads(html[len("<script>var D="):-len(";</script>")].replace("<\\/", "</"))
        self.assertEqual(set(data), {"meta", "statements", "theories", "results", "findings", "metrics", "registry", "code",
                                     "fragments", "fragment_users", "toolkit", "readings", "docs"})
        self.assertNotIn("</", html[len("<script>"):-len("</script>")])

    def test_code_data(self):
        from linglab import report, common
        d = common.load_project(self.p)
        code = report.build_code(self.p, d)
        self.assertIn("python", code["principles"]["P-AND-MK"])
        self.assertIn("lean", code["principles"]["P-AND-MK"])
        self.assertIn("and", code["facts"]["F05a"]["spec_text"])
        self.assertTrue(any(x["theory"] == "T-MK" and "F05a" in x["text"] for x in code["facts"]["F05a"]["lean"]))
        self.assertTrue(any("F02_fail" in x["text"] for x in code["facts"]["F02"]["lean"]))
        self.assertEqual(report.infix(["or", ["not", "s"], "a"]), "not s or a")


class LayersTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.p = copy_example()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit(self, name, fn):
        path = os.path.join(self.p, "data", name + ".json")
        d = json.load(open(path))
        fn(d)
        json.dump(d, open(path, "w"))

    def test_example_valid_and_users(self):
        r = linglab(self.p, "check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("without a readback check", r.stdout)       # one summary line
        from linglab import report, common
        d = common.load_project(self.p)
        users = report.fragment_users(d)
        self.assertEqual(users["FR-TOY"], ["T-SK", "T-WK", "T-MK", "T-MK-some"])
        self.assertEqual(set(users), {"FR-TOY", "FR-CONSEQ"})

    def test_fragments_optional(self):
        os.remove(os.path.join(self.p, "data", "fragments.json"))
        self.assertEqual(linglab(self.p, "check").returncode, 1)     # theories point to missing fragments
        self.edit("theories", lambda ts: [t.pop("fragments", None) for t in ts])
        r = linglab(self.p, "check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("without fragments", r.stdout)

    def test_check_errors(self):
        def bad(st):
            st[0]["checks"] = [{"by": "robot", "what": "readback", "verdict": "agrees"},
                               {"by": "llm", "what": "example", "verdict": "ok", "when": "10/10/2026"}]
            st[1]["notation"] = 3
        self.edit("statements", bad)
        def badfr(frs):
            frs.append({"id": "FR-TOY", "defs": [{"text": "no label"}]})
        self.edit("fragments", badfr)
        self.edit("theories", lambda ts: ts[0].update(fragments=["FR-NOPE"]))
        r = linglab(self.p, "check")
        self.assertEqual(r.returncode, 1)
        for m in ("by 'robot'", "verdict 'ok'", "YYYY-MM-DD", "notation must be a string", "duplicate id",
                  "def #1 needs a label", "unknown fragment 'FR-NOPE'"):
            self.assertIn(m, r.stdout)

    def test_notation_auto(self):
        from linglab.latex import notation_auto as na, sentence
        self.assertEqual(sentence(["or", ["not", "s"], "a"]), r"\neg s \lor a")
        self.assertEqual(sentence(["some", "?x", ["Student", "?x"], ["Passed", "?x"]]),
                         r"\mathrm{some}\,x\,(\mathrm{Student}(x))\,(\mathrm{Passed}(x))")
        self.assertEqual(sentence(["forall", "?x", ["if", ["P", "?x"], ["Q", "?x", "b"]]]), r"\forall x\,(P(x) \to Q(x, b))")
        self.assertEqual(sentence(["must", ["and", "p", "q"]]), r"\Box (p \land q)")
        self.assertEqual(sentence(["may", "p"]), r"\Diamond p")
        self.assertEqual(sentence(["exh", ["and", "p", "q"]]), r"\mathrm{exh}(p \land q)")
        self.assertEqual(sentence(["iff", "p", "q"]), r"p \leftrightarrow q")
        ent = {"type": "entailment", "spec": {"premises": [["and", "p", "q"]], "conclusion": "p"}}
        self.assertEqual(na(ent), r"p \land q \vDash p")
        self.assertEqual(na(dict(ent, expected="fails")), r"p \land q \nvDash p")
        self.assertEqual(na({"type": "entailment", "spec": {"premises": [], "conclusion": "p"}}), r" \vDash p")
        self.assertEqual(na({"type": "felicity", "spec": {"discourse": [["and", "s", "a"]]}}), r"\mathrm{felic}(s \land a)")
        self.assertEqual(na({"type": "felicity", "expected": "fails", "spec": {"discourse": ["a"]}}), r"\neg\,\mathrm{felic}(a)")
        self.assertEqual(na({"type": "consistency", "spec": {"premises": ["s", ["not", "s"]]}}), r"\mathrm{cons}(s, \neg s)")
        tr = {"type": "truth", "spec": {"sentence": ["and", "s", "a"], "relation": "equals", "target": "a"}}
        self.assertEqual(na(tr), r"\llbracket s \land a \rrbracket = \llbracket a \rrbracket")
        tr["spec"]["relation"] = "within"
        self.assertEqual(na(tr), r"\llbracket s \land a \rrbracket \subseteq \llbracket a \rrbracket")
        tr["spec"]["relation"] = "includes"
        self.assertEqual(na(dict(tr, expected="fails")), r"\llbracket s \land a \rrbracket \nsupseteq \llbracket a \rrbracket")
        self.assertEqual(na({"type": "preference", "spec": {"sentence": "a", "preferred": "p", "over": "q"}}), r"p \succ_{a} q")
        self.assertEqual(na({"type": "property", "spec": {"check": "my_prop"}}), r"\mathrm{prop}(\mathrm{my\_prop})")
        self.assertIsNone(na({"type": "other"}))

    def test_report_notation_auto_and_override(self):
        from linglab import report, common
        code = report.build_code(self.p, common.load_project(self.p))
        self.assertEqual(code["facts"]["F05a"]["notation_auto"], r"p \land q \vDash q \land p")
        self.assertNotIn("notation_auto", code["facts"]["F10"])
        self.assertIn("spec_text", code["facts"]["F05a"])

    def _build(self, tpl="<style id=\"katex-css\">/*__KATEX_CSS__*/</style><script id=\"katex-js\">/*__KATEX_JS__*/</script>"
               "<script>var D=/*__DATA__*/null;</script>"):
        os.makedirs(os.path.join(self.p, "report"), exist_ok=True)
        open(os.path.join(self.p, "report", "template.html"), "w").write(tpl)
        r = linglab(self.p, "report")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r, open(os.path.join(self.p, "report", "index.html")).read()

    def test_katex_injected_when_notation(self):
        r, html = self._build()
        self.assertNotIn("__KATEX", html)
        self.assertIn("data:font/woff2;base64,", html)
        self.assertNotIn(".woff)", html)
        self.assertNotIn("url(fonts/", html)
        self.assertIn("katex", html[html.index('id="katex-js"'):])
        self.assertGreater(len(html), 250000)

    def test_katex_absent_without_notation(self):
        def strip(st):
            for s in st:
                s.pop("notation", None)
                if s["role"] == "fact":
                    s["type"], s["spec"] = "other", None
        self.edit("statements", strip)
        self.edit("theories", lambda ts: [t.pop("notation", None) for t in ts])
        self.edit("fragments", lambda frs: [(f.pop("notation", None), [d.pop("notation", None) for d in f["defs"]]) for f in frs])
        r, html = self._build()
        from linglab import report
        docs = sum(len(x["html"]) for x in report.toolkit_docs())      # METHOD.md and SPEC.md of the Instructions tab
        self.assertLess(len(html) - docs, 100000)
        self.assertIn('<style id="katex-css"></style><script id="katex-js"></script>', html)

    def test_no_placeholders_and_missing_vendor(self):
        r, html = self._build("<script>var D=/*__DATA__*/null;</script>")
        self.assertIn("var D=", html)
        from linglab import report, latex
        old = latex.TOOLKIT
        latex.TOOLKIT = os.path.join(self.tmp, "nowhere")
        try:
            msgs = []
            html = report.inject_katex("<style>/*__KATEX_CSS__*/</style><script>/*__KATEX_JS__*/</script>", self.p,
                                       {"statements": [{"notation": "x"}], "theories": [], "fragments": [],
                                        "code": {"facts": {}}}, msgs.append)
            self.assertIn("KaTeX files not found", msgs[0])
            self.assertEqual(html, "<style></style><script></script>")
        finally:
            latex.TOOLKIT = old


class CodeDataNoWorkspaceTests(unittest.TestCase):
    def test_project_without_lean(self):
        d, p = copy_example()
        shutil.rmtree(os.path.join(p, "lean"))
        from linglab import report, common
        code = report.build_code(p, common.load_project(p))
        self.assertEqual(set(code["principles"]["P-NEG"]), {"python"})
        self.assertEqual(code["facts"]["F01"]["lean"], [])
        self.assertTrue(code["facts"]["F01"]["spec_text"])
        r = linglab(p, "report")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        shutil.rmtree(d)


class QuantifierModalTests(unittest.TestCase):
    """Shared syntax v2 on a tiny finite fragment: domain {0,1,2}, predicates Student and Passed,
    atoms p and q, and worlds; quantifiers and modals defined through the builder API."""

    def setUp(self):
        import itertools
        from linglab import vocab
        D = (0, 1, 2)

        def models():
            pairs = list(itertools.product((0, 1), repeat=2))
            perms = [frozenset(c) for k in range(1, 5) for c in itertools.combinations(pairs, k)]   # non-empty
            for passed in itertools.chain.from_iterable(itertools.combinations(D, k) for k in range(4)):
                for p, q in pairs:
                    for perm in perms:      # perm: the (p, q) valuations the modals can reach from this model
                        yield {"domain": D, "Student": frozenset({0, 1}), "Passed": frozenset(passed),
                               "p": p, "q": q, "perm": perm}
        vocab._BASE_MODELS[:] = [models]
        holds = lambda T, m, f, x, d: T.value(m, f, T.bind(x, d)) == 1
        reg = {}
        def prop(b):
            b.connective("not", lambda x: 1 - x)
            b.connective("and", lambda x, y: x * y)
            b.connective("or", lambda x, y: max(x, y))
            b.connective("if", lambda x, y: max(1 - x, y))
        def preds(b):
            b.predicate("Student", lambda T, m, d: int(d in m.vals["Student"]), arity=1)
            b.predicate("Passed", lambda T, m, d: int(d in m.vals["Passed"]), arity=1)
        def quant(b):
            dom = lambda m: m.vals["domain"]
            b.operator("some", lambda T, m, x, R, S: int(any(holds(T, m, R, x, d) and holds(T, m, S, x, d) for d in dom(m))))
            b.operator("every", lambda T, m, x, R, S: int(all(holds(T, m, S, x, d) for d in dom(m) if holds(T, m, R, x, d))))
            b.operator("no", lambda T, m, x, R, S: int(not any(holds(T, m, R, x, d) and holds(T, m, S, x, d) for d in dom(m))))
            b.operator("exists", lambda T, m, x, A: int(any(holds(T, m, A, x, d) for d in dom(m))))
            b.operator("forall", lambda T, m, x, A: int(all(holds(T, m, A, x, d) for d in dom(m))))
        acc = lambda T, m: [w for w in T.worlds() if (w.vals["p"], w.vals["q"]) in m.vals["perm"]]
        def modal(b):
            b.operator("may", lambda T, m, a: int(any(T.value(w, a) == 1 for w in acc(T, m))))
            b.operator("must", lambda T, m, a: int(all(T.value(w, a) == 1 for w in acc(T, m))))
        def free_choice(b):       # may (A or B) = may A and may B; plain `may` otherwise
            def may(T, m, a):
                if a[0] == "or":
                    return int(may(T, m, a[1]) == 1 and may(T, m, a[2]) == 1)
                return int(any(T.value(w, a) == 1 for w in acc(T, m)))
            b.operator("may", may)
        for pid, fn in (("PROP", prop), ("PRED", preds), ("Q", quant), ("M", modal), ("FC", free_choice)):
            reg[pid] = vocab.Principle(pid, fn)
        self.T = vocab.Theory("T", "t", ["PROP", "PRED", "Q", "M"], registry=reg)
        self.TFC = vocab.Theory("TFC", "tfc", ["PROP", "PRED", "Q", "M", "FC"], registry=reg)
        self.bare = vocab.Theory("B", "b", ["PROP"], registry=reg)
        self.some = ["some", "?x", ["Student", "?x"], ["Passed", "?x"]]

    def ent(self, T, prem, concl):
        from linglab import runner
        f = {"id": "F", "type": "entailment", "spec": {"premises": prem, "conclusion": concl}}
        return runner.run_theory(T, [f])["F"].outcome

    def test_translate_expressible(self):
        T = self.T
        self.assertEqual(T.translate(["Passed", "a"]), ("@", "Passed", "a"))
        self.assertEqual(T.translate(self.some),
                         ("some", "?x", ("@", "Student", "?x"), ("@", "Passed", "?x")))
        self.assertIsNotNone(T.translate(["forall", "?x", ["if", ["Student", "?x"], ["Passed", "?x"]]]))
        self.assertIsNotNone(T.translate(["must", ["or", "p", "q"]]))
        self.assertIsNotNone(T.translate(["may", ["some", "?y", ["Student", "?y"], ["Passed", "?y"]]]))

    def test_translate_not_expressible(self):
        T = self.T
        for bad in (["Failed", "?x"],                          # unknown predicate
                    ["Passed", "?x"],                           # unbound variable
                    "?x",                                       # a variable is not a sentence
                    ["Passed"],                                 # no term
                    ["some", "?x", ["Student", "?x"]],          # binder arity
                    ["some", "x", ["Student", "x"], ["Passed", "x"]],   # binder needs a variable
                    ["must", "p", "q"],                         # modal arity
                    ["exh", "p"],                               # unknown operator
                    ["iff", "p", "q"]):                         # iff not defined by this theory
            self.assertIsNone(T.translate(bad), bad)
        self.assertIsNone(self.bare.translate(["may", "p"]))
        self.assertIsNone(self.bare.translate(self.some))
        self.assertIn("predicate or operator 'Failed' not defined by any principle", T.explain(["Failed", "a"]))
        self.assertIn("variable '?x' is not bound", T.explain(["Passed", "?x"]))
        from linglab import runner
        d = runner.run_theory(T, [{"id": "F", "type": "felicity", "spec": {"discourse": [["Failed", "a"]]}}])["F"]
        self.assertEqual(d.outcome, "out_of_scope")
        self.assertIn("'Failed'", d.reasons)

    def test_values(self):
        T = self.T
        ms = {tuple(sorted(m.vals["Passed"])): m for m in T.worlds()
              if m.vals["p"] == 0 and m.vals["q"] == 0 and len(m.vals["perm"]) == 4}
        val = lambda m, s: T.value(m, T.translate(s))
        self.assertEqual(val(ms[(0,)], self.some), 1)
        self.assertEqual(val(ms[(2,)], self.some), 0)
        self.assertEqual(val(ms[(0, 1)], ["every", "?x", ["Student", "?x"], ["Passed", "?x"]]), 1)
        self.assertEqual(val(ms[(0,)], ["every", "?x", ["Student", "?x"], ["Passed", "?x"]]), 0)
        self.assertEqual(val(ms[(2,)], ["no", "?x", ["Student", "?x"], ["Passed", "?x"]]), 1)
        self.assertEqual(val(ms[(2,)], ["exists", "?x", ["Passed", "?x"]]), 1)
        self.assertEqual(val(ms[()], ["exists", "?x", ["Passed", "?x"]]), 0)
        self.assertEqual(val(ms[(0, 1, 2)], ["forall", "?x", ["Passed", "?x"]]), 1)
        self.assertEqual(val(ms[()], ["may", ["exists", "?x", ["Passed", "?x"]]]), 1)     # some world has a passer
        self.assertEqual(val(ms[()], ["must", ["exists", "?x", ["Passed", "?x"]]]), 0)
        # the memo is keyed by the environment: one formula, different values under different assignments
        f = ("@", "Passed", "?x")      # open formula, built by hand
        self.assertEqual([T.value(ms[(0,)], f, {"?x": d}) for d in (0, 1, 2)], [1, 0, 0])

    def test_entailments_through_runner(self):
        T = self.T
        self.assertEqual(self.ent(T, [self.some], ["exists", "?x", ["Passed", "?x"]]), "pass")
        self.assertEqual(self.ent(T, [["every", "?x", ["Student", "?x"], ["Passed", "?x"]]], self.some), "pass")
        self.assertEqual(self.ent(T, [self.some], ["every", "?x", ["Student", "?x"], ["Passed", "?x"]]), "fail")
        self.assertEqual(self.ent(T, [["no", "?x", ["Student", "?x"], ["Passed", "?x"]]], ["not", self.some]), "pass")
        self.assertEqual(self.ent(T, [["must", "p"]], ["may", "p"]), "pass")
        self.assertEqual(self.ent(self.bare, [self.some], self.some), "out_of_scope")

    def test_free_choice(self):
        mayor = ["may", ["or", "p", "q"]]
        self.assertEqual(self.ent(self.T, [mayor], ["may", "p"]), "fail")       # classical may
        self.assertEqual(self.ent(self.TFC, [mayor], ["may", "p"]), "pass")     # free choice

    def test_infix(self):
        from linglab import report
        self.assertEqual(report.infix(self.some), "some x (Student x) (Passed x)")
        self.assertEqual(report.infix(["must", ["or", "p", "q"]]), "must (p or q)")
        self.assertEqual(report.infix(["may", "p"]), "may p")
        self.assertEqual(report.infix(["forall", "?x", ["if", ["Student", "?x"], ["Passed", "?x"]]]),
                         "forall x ((Student x) if (Passed x))")
        self.assertEqual(report.infix(["Passed", "a"]), "Passed a")
        self.assertEqual(report.infix(["and", ["Student", "a"], ["iff", "p", "q"]]), "(Student a) and (p iff q)")
        self.assertEqual(report.infix(["not", ["Passed", "a"]]), "not (Passed a)")
        self.assertEqual(report.infix(["or", ["not", "s"], "a"]), "not s or a")

    def test_check_syntax_messages(self):
        from linglab import check
        def run(s):
            errs, warns = [], []
            used = set()
            check.check_syntax(s, "w", lambda w, m: errs.append(m), lambda w, m: warns.append(m), used=used)
            return errs, warns, used
        self.assertEqual(run(self.some)[:2], ([], []))
        self.assertEqual(run(self.some)[2], {"some", "Student", "Passed"})
        self.assertEqual(run(["most", "?x", ["Student", "?x"], ["Passed", "?x"]])[0], [])
        self.assertEqual(run(["may", ["or", "p", "q"]])[0], [])
        msg = lambda s: " | ".join(run(s)[0])
        self.assertIn("'some' takes a variable and 2 formula(s)", msg(["some", "?x", ["Student", "?x"]]))
        self.assertIn("'exists' takes a variable and 1 formula(s)", msg(["exists", "?x", "p", "q"]))
        self.assertIn("needs a variable", msg(["forall", "x", ["Student", "x"]]))
        self.assertIn("'may' takes 1 argument", msg(["may", "p", "q"]))
        self.assertIn("'iff' takes 2 argument", msg(["iff", "p"]))
        self.assertIn("variable '?y' is not bound", msg(["some", "?x", ["Student", "?x"], ["Passed", "?y"]]))
        self.assertIn("variable '?x' is not bound", msg(["Passed", "?x"]))
        self.assertIn("needs at least one argument", msg(["Passed"]))
        self.assertIn("used as a sentence", msg(["and", "?x", "p"]))
        self.assertIn("malformed", msg([]))

    def test_check_command_on_malformed_and_undefined(self):
        tmp, p = copy_example()
        try:
            path = os.path.join(p, "data", "statements.json")
            st = json.load(open(path))
            st[0]["spec"] = {"discourse": [["some", "?x", ["Student", "?x"]]]}
            st[1]["spec"] = {"discourse": [["may", ["exh", "p"]]]}
            json.dump(st, open(path, "w"))
            r = linglab(p, "check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("takes a variable and 2 formula(s)", r.stdout)
            self.assertIn("no principle of the project defines 'exh'", r.stdout)
            self.assertIn("no principle of the project defines 'may'", r.stdout)
        finally:
            shutil.rmtree(tmp)


class CheckTests(unittest.TestCase):
    def test_errors(self):
        tmp, p = copy_example()
        try:
            st = json.load(open(os.path.join(p, "data", "statements.json")))
            st[1]["id"] = "F01"          # duplicate
            st[0]["spec"] = {"discourse": [["and", "s"]]}   # arity
            json.dump(st, open(os.path.join(p, "data", "statements.json"), "w"))
            r = linglab(p, "check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("duplicate id", r.stdout)
            self.assertIn("takes 2", r.stdout)
        finally:
            shutil.rmtree(tmp)


class DisplayOptionsTests(unittest.TestCase):
    """Optional display settings of the report (heatmap grouping, short names, layers) and the page itself."""
    def test_check_rejects_bad_display_fields(self):
        tmp, p = copy_example()
        try:
            th = json.load(open(os.path.join(p, "data", "theories.json")))
            th[0]["short"] = 5
            json.dump(th, open(os.path.join(p, "data", "theories.json"), "w"))
            st = json.load(open(os.path.join(p, "data", "statements.json")))
            st[0]["kind"] = ["x"]
            json.dump(st, open(os.path.join(p, "data", "statements.json"), "w"))
            meta = json.load(open(os.path.join(p, "data", "meta.json")))
            meta["short_names"] = {"T-SK": 1}
            meta["banner"] = 3
            json.dump(meta, open(os.path.join(p, "data", "meta.json"), "w"))
            reg = json.load(open(os.path.join(p, "custom", "registry.json")))
            reg["layers"] = [5]
            reg["proof_kinds"] = ["nope"]
            json.dump(reg, open(os.path.join(p, "custom", "registry.json"), "w"))
            r = linglab(p, "check")
            self.assertEqual(r.returncode, 1)
            for m in ("short must be a string", "kind must be a string", "short_names", "banner", "layers", "proof_kinds"):
                self.assertIn(m, r.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_pages_are_light_only(self):
        """no dark or auto mode and no theme toggle in the generated page, the slides or the gate page"""
        import re as _re
        paths = ["template/report/template.html", "slides/index.html", "slides/examples.html"]
        for rel in paths:
            t = open(os.path.join(ROOT, rel), encoding="utf-8").read()
            self.assertNotIn("prefers-color-scheme: dark", t.replace("prefers-color-scheme:dark", "prefers-color-scheme: dark"), rel)
            self.assertNotIn("data-theme", t, rel)
            self.assertIn("color-scheme:light", t, rel)

    def _edit(self, p, name, fn):
        path = os.path.join(p, "data", name)
        d = json.load(open(path)); fn(d); json.dump(d, open(path, "w"))

    def test_out_of_scope_reasons(self):
        """the runner says why a cell is out of scope: fragment, primitive, no_prediction"""
        tmp, p = copy_example()
        try:
            def th(d):
                for t in d:
                    if t["id"] == "T-SK":
                        t["primitives"] = ["entailment", "consistency", "felicity"]   # no `truth`
                    if t["id"] == "T-MK":
                        t["predicts"] = ["entailment"]
            self._edit(p, "theories.json", th)
            def st(d):
                for x in d:
                    if x["id"] == "F05a":
                        x["uses"] = ["alternatives"]
                d.append({"id": "F20", "role": "fact", "type": "entailment", "name": "outside", "text": "uses an operator nobody defines",
                          "expected": "holds", "confidence": 0.5, "spec": {"premises": [["zork", "p"]], "conclusion": "p"}})
            self._edit(p, "statements.json", st)
            self.assertEqual(linglab(p, "run", "--force").returncode, 0)
            by = {(e["fact"], e["theory"]): e for e in results(p) if e["kind"] == "python"}
            self.assertEqual(by[("F09", "T-SK")]["scope"], "primitive")        # truth not implemented by T-SK
            self.assertEqual(by[("F01", "T-MK")]["scope"], "no_prediction")    # T-MK predicts only entailment
            self.assertEqual(by[("F20", "T-WK")]["scope"], "fragment")         # the operator is not in the theory
            self.assertEqual(by[("F05a", "T-SK")]["scope"], "primitive")       # `uses` names a notion T-SK does not list
            self.assertIn("alternatives", by[("F05a", "T-SK")]["reasons"])
            self.assertEqual(by[("F05b", "T-SK")]["outcome"], "pass")          # entailment itself is implemented
            self.assertNotIn("scope", by[("F01", "T-SK")])                     # decided cells carry no reason
            self.assertEqual(linglab(p, "check").returncode, 0)
        finally:
            shutil.rmtree(tmp)

    def test_parse_policies(self):
        """a fact may have several parses; the theory picks which it uses and how it combines them"""
        tmp, p = copy_example()
        try:
            def st(d):
                for x in d:
                    if x["id"] == "F09":      # first parse: and(s,a) equals a (holds in T-SK); second: a deliberately false parse
                        x["parses"] = [{"id": "bad", "spec": {"sentence": ["not", "a"], "relation": "equals", "target": "a"}}]
            self._edit(p, "statements.json", st)
            def th(d, pol=None, picks=None):
                for t in d:
                    if t["id"] == "T-SK":
                        if pol: t["parse_policy"] = pol
                        if picks: t["picks"] = picks
            def run(**kw):
                self._edit(p, "theories.json", lambda d: th(d, **kw))
                self.assertEqual(linglab(p, "run", "--force").returncode, 0)
                return {(e["fact"], e["theory"]): e for e in results(p) if e["kind"] == "python"}[("F09", "T-SK")]
            first = run()                                  # default: the fact's own spec only
            self.assertEqual(first["outcome"], "pass"); self.assertNotIn("parses", first)
            anyp = run(pol="any")
            self.assertEqual(anyp["outcome"], "pass"); self.assertEqual(anyp["parses"]["bad"], "fail"); self.assertIn("any", anyp["reasons"])
            allp = run(pol="all")
            self.assertEqual(allp["outcome"], "fail"); self.assertEqual(allp["parses"], {"main": "pass", "bad": "fail"})
            picked = run(pol="first", picks={"F09": ["bad"]})
            self.assertEqual(picked["outcome"], "fail")    # the theory picked the bad parse only
            self.assertEqual(linglab(p, "check").returncode, 0)
            self._edit(p, "theories.json", lambda d: [t.update({"picks": {"F09": ["nope"]}, "parse_policy": "some"}) for t in d if t["id"] == "T-SK"])
            r = linglab(p, "check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("unknown parse", r.stdout); self.assertIn("parse_policy", r.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_check_validates_readings(self):
        tmp, p = copy_example()
        try:
            rd = json.load(open(os.path.join(p, "data", "readings.json")))
            self.assertTrue(rd)                      # the example ships readings
            self.assertEqual(linglab(p, "check").returncode, 0)
            rd.append({"fact": "F01", "theory": "T-SK", "text": "again", "review": "perhaps"})   # duplicate cell, bad review
            rd.append({"fact": "NOPE", "theory": "T-ZZ", "text": ""})                           # unknown ids, empty text
            json.dump(rd, open(os.path.join(p, "data", "readings.json"), "w"))
            r = linglab(p, "check")
            self.assertEqual(r.returncode, 1)
            for m in ("unknown fact", "unknown theory", "empty text", "review", "two readings for the same cell"):
                self.assertIn(m, r.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_readings_are_not_evidence(self):
        """a reading never changes pooling: results and metrics are the same with and without readings"""
        tmp, p = copy_example()
        try:
            a = linglab(p, "metrics"); self.assertEqual(a.returncode, 0)
            m1 = open(os.path.join(p, "data", "metrics.json")).read()
            json.dump([], open(os.path.join(p, "data", "readings.json"), "w"))
            linglab(p, "metrics")
            m2 = open(os.path.join(p, "data", "metrics.json")).read()
            self.assertEqual(m1, m2)
        finally:
            shutil.rmtree(tmp)

    def test_check_rejects_bad_page_fields(self):
        tmp, p = copy_example()
        try:
            meta = json.load(open(os.path.join(p, "data", "meta.json")))
            meta.update({"page_title": 1, "subtitle": [], "banner_title": 2, "banner_points": "x", "paper": {"authors": "A"}, "theory_kinds": {"fix": 3}})
            json.dump(meta, open(os.path.join(p, "data", "meta.json"), "w"))
            st = json.load(open(os.path.join(p, "data", "statements.json")))
            st[0]["requires"] = "FR-NOPE"
            json.dump(st, open(os.path.join(p, "data", "statements.json"), "w"))
            r = linglab(p, "check")
            self.assertEqual(r.returncode, 1)
            for m in ("page_title", "subtitle", "banner_title", "banner_points", "paper", "theory_kinds", "requires unknown fragment"):
                self.assertIn(m, r.stdout)
        finally:
            shutil.rmtree(tmp)

    def test_example_page_has_the_second_round_features(self):
        meta = json.load(open(os.path.join(EXAMPLE, "data", "meta.json")))
        self.assertIn("paper", meta)
        self.assertIn("fact_kinds", meta)
        st = json.load(open(os.path.join(EXAMPLE, "data", "statements.json")))
        self.assertTrue(any(s.get("requires") for s in st))
        self.assertTrue({s.get("layer") for s in st if s.get("role") == "fact"} >= {"core", "disputed"})
        html = open(os.path.join(EXAMPLE, "report", "index.html"), encoding="utf-8").read()
        self.assertIn("Theories \u00d7 Facts", html)
        self.assertIn('id="t-cards"', html)
        self.assertNotIn('data-tab="cards"', html)

    def test_example_has_families_and_short_names_and_page_passes_smoke_test(self):
        th = json.load(open(os.path.join(EXAMPLE, "data", "theories.json")))
        fams = {t["family"] for t in th if t["family"]}
        self.assertGreaterEqual(len(fams), 2)
        self.assertTrue(all(t.get("short") for t in th if t["id"] != "RAW"))
        tmp, p = copy_example()
        try:
            out = os.path.join(tmp, "page.html")
            r = linglab(p, "report", "-o", out)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            html = open(out, encoding="utf-8").read()
            self.assertIn('"short": "SK"', html)
            self.assertIn("mxv-grid", html)
            if shutil.which("node"):
                t = subprocess.run(["node", os.path.join(ROOT, "template", "report", "smoke_test.js"), out], capture_output=True, text=True)
                self.assertEqual(t.returncode, 0, t.stdout + t.stderr)
                # real-browser behaviour (history, scroll, panel, cards block, sticky band); reports "skipped" without Chrome
                t = subprocess.run(["node", os.path.join(ROOT, "template", "report", "browser_check.mjs"), out], capture_output=True, text=True, timeout=120)
                self.assertEqual(t.returncode, 0, t.stdout + t.stderr)
        finally:
            shutil.rmtree(tmp)


class ListingTests(unittest.TestCase):
    def test_contradiction(self):
        tmp, p = copy_example()
        try:
            st = json.load(open(os.path.join(p, "data", "statements.json")))
            dup = dict(st[0], id="F99", expected="fails")
            st.append(dup)
            json.dump(st, open(os.path.join(p, "data", "statements.json"), "w"))
            r = linglab(p, "listing")
            self.assertEqual(r.returncode, 1)
            self.assertIn("F01 and F99", r.stdout)
        finally:
            shutil.rmtree(tmp)


class InitTests(unittest.TestCase):
    def test_init(self):
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(linglab(d, "init", "My Topic").returncode, 0)
            for f in ("brief.md", "AGENTS.md", "CLAUDE.md", "data/meta.json", "custom/registry.json", "literature/README.md"):
                self.assertTrue(os.path.exists(os.path.join(d, f)), f)
            self.assertEqual(json.load(open(os.path.join(d, "data", "meta.json")))["title"], "My Topic")
            self.assertEqual(linglab(d, "check").returncode, 0)
            self.assertNotEqual(linglab(d, "init", "Again").returncode, 0)
        finally:
            shutil.rmtree(d)

    def test_init_installs_playbooks_as_skills(self):
        from linglab import init
        moves = os.path.join(ROOT, "moves")
        names = {}
        for fn in os.listdir(moves):
            text = open(os.path.join(moves, fn), encoding="utf-8").read()
            names[fn] = init.skill_name(text)
            if names[fn]:
                self.assertEqual(names[fn], "linglab-" + fn[:-3], fn)
                desc = re.search(r'^description: "(.+)"$', text, re.M)
                self.assertTrue(desc and len(desc.group(1)) <= 1024, fn)
        self.assertEqual({fn for fn, n in names.items() if not n}, {"README.md", "possibilities.md"})
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(linglab(d, "init", "My Topic", "--claude-skills").returncode, 0)
            skills = os.path.join(d, ".claude", "skills")
            self.assertEqual(sorted(n for n in os.listdir(skills) if not n.startswith(".")), sorted(n for n in names.values() if n))
            for fn, n in names.items():
                if n:
                    self.assertEqual(open(os.path.join(skills, n, "SKILL.md"), encoding="utf-8").read(),
                                     open(os.path.join(moves, fn), encoding="utf-8").read())
        finally:
            shutil.rmtree(d)

    def test_skills_refresh_after_toolkit_change(self):
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(linglab(d, "init", "My Topic", "--claude-skills").returncode, 0)
            skills = os.path.join(d, ".claude", "skills")
            self.assertNotIn("skills do not match", linglab(d, "check").stdout)
            # as if utils/ were replaced: one playbook changed, one added, one retired; plus a user's own skill
            with open(os.path.join(skills, "linglab-prove", "SKILL.md"), "a", encoding="utf-8") as f:
                f.write("old text\n")
            shutil.rmtree(os.path.join(skills, "linglab-check"))
            for n in ("linglab-retired", "my-own", "linglab-my-own"):
                os.makedirs(os.path.join(skills, n))
                open(os.path.join(skills, n, "SKILL.md"), "w").write("---\nname: %s\n---\n" % n)
            manifest = os.path.join(skills, ".linglab-managed.json")
            with open(manifest, encoding="utf-8") as f:
                managed = json.load(f)
            with open(manifest, "w", encoding="utf-8") as f:
                json.dump(managed + ["linglab-retired"], f)
            r = linglab(d, "check")
            self.assertEqual(r.returncode, 0)   # a warning, not an error
            for s in ("outdated: linglab-prove", "missing: linglab-check", "no longer in the toolkit: linglab-retired",
                      "linglab.py skills"):
                self.assertIn(s, r.stdout)
            r = linglab(d, "skills")
            self.assertEqual(r.returncode, 0)
            self.assertIn("updated: linglab-prove", r.stdout)
            self.assertNotIn("skills do not match", linglab(d, "check").stdout)
            self.assertFalse(os.path.exists(os.path.join(skills, "linglab-retired")))
            self.assertTrue(os.path.exists(os.path.join(skills, "my-own", "SKILL.md")))
            self.assertTrue(os.path.exists(os.path.join(skills, "linglab-my-own", "SKILL.md")))
            self.assertIn("already match", linglab(d, "skills").stdout)
        finally:
            shutil.rmtree(d)


    def test_default_project_needs_no_claude_skills(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(linglab(root, "init", "Other Assistant").returncode, 0)
            self.assertFalse(os.path.exists(os.path.join(root, ".claude")))
            for fn in ("AGENTS.md", "CLAUDE.md"):
                with open(os.path.join(root, fn)) as f:
                    self.assertIn("BOOTSTRAP.md", f.read())
            self.assertEqual(linglab(root, "check").returncode, 0)
            self.assertEqual(linglab(root, "report").returncode, 0)
            self.assertTrue(os.path.isfile(os.path.join(root, "report", "index.html")))
            self.assertEqual(linglab(root, "skills").returncode, 0)
            self.assertTrue(os.path.isfile(os.path.join(root, ".claude", "skills", "linglab-check", "SKILL.md")))


class ZipTests(unittest.TestCase):
    def test_zip(self):
        self.assertEqual(linglab(ROOT, "zip").returncode, 0)
        names = zipfile.ZipFile(os.path.join(ROOT, "dist", "linglab-beta.zip")).namelist()
        self.assertTrue(all(n.startswith("linglab/") for n in names))
        self.assertIn("linglab/bin/linglab.py", names)
        self.assertFalse([n for n in names if "__pycache__" in n or "/.git/" in n or "/dist/" in n])




class ModelScopeTests(unittest.TestCase):
    """What a finite model list covers: declared with @base_models(scope=...), reported in the entries' bound."""

    def setUp(self):
        from linglab import vocab
        saved = (list(vocab._BASE_MODELS), vocab._SCOPE[0])
        def restore():
            vocab._BASE_MODELS[:] = saved[0]
            vocab._SCOPE[0] = saved[1]
        self.addCleanup(restore)

    def test_declare_and_report(self):
        from linglab import vocab, runner
        @vocab.base_models
        def plain():
            return [{"p": 0}, {"p": 1}]
        self.assertEqual(vocab.base_scope(), "complete")
        @vocab.base_models(scope="domain size <= 1")
        def small():
            return [{"p": 0}, {"p": 1}]
        self.assertEqual(vocab.base_scope(), "domain size <= 1")
        self.assertIs(vocab._BASE_MODELS[0], small)
        self.assertEqual(vocab.bound_text("complete"), "exhaustive")
        self.assertEqual(vocab.bound_text("domain size <= 1", "first 3 models"), "first 3 models within domain size <= 1")
        reg = {"N": vocab.Principle("N", lambda b: b.connective("not", lambda x: 1 - x))}
        T = vocab.Theory("T", "t", ["N"], registry=reg)
        facts = [{"id": "F1", "type": "entailment", "spec": {"premises": ["p"], "conclusion": "p"}},
                 {"id": "F2", "type": "entailment", "spec": {"premises": [], "conclusion": "p"}}]
        dec = runner.run_theory(T, facts)
        self.assertEqual(dec["F1"].bound, "exhaustive within domain size <= 1")   # no countermodel among bounded models
        self.assertEqual(dec["F2"].bound, "")                                      # a countermodel is a countermodel

    def test_uses_quantifiers(self):
        from linglab import vocab
        self.assertTrue(vocab.uses_quantifiers({"premises": [["some", "?x", ["Student", "?x"], ["Passed", "?x"]]]}))
        self.assertTrue(vocab.uses_quantifiers(["not", ["Passed", "a"]]))
        self.assertFalse(vocab.uses_quantifiers({"discourse": [["and", "s", ["not", "a"]]], "x": ["may", "p"]}))


class PoolingRuleTests(unittest.TestCase):
    def E(self, kind, outcome):
        return {"fact": "F", "theory": "T", "kind": kind, "outcome": outcome}

    def test_conflict_majority_tie_fails(self):
        P = lambda *es: pooling.pool(list(es), LADDER)
        r = P(self.E("python", "pass"), self.E("python", "fail"))
        self.assertEqual((r["outcome"], r["conflict"]), ("fail", True))          # tie goes to fail
        r = P(self.E("human", "pass"), self.E("human", "pass"), self.E("human", "fail"))
        self.assertEqual((r["outcome"], r["conflict"]), ("pass", True))          # majority
        r = P(self.E("human", "out_of_scope"), self.E("human", "pass"))
        self.assertEqual((r["outcome"], r["conflict"]), ("pass", False))
        r = P(self.E("python", "out_of_scope"))
        self.assertEqual(r["outcome"], "out_of_scope")
        r = P(self.E("python", "pass"), self.E("llm-judged", "fail"))
        self.assertEqual((r["outcome"], r["warnings"]), ("pass", ["llm-judged"]))

    def test_implementations_cross_check(self):
        P = lambda *es: pooling.pool(list(es), LADDER)
        r = P(self.E("lean", "pass"), self.E("python", "fail"))
        self.assertEqual((r["outcome"], r["conflict"], r["warnings"]), ("pass", True, []))    # was only a warning
        r = P(self.E("lean", "pass"), self.E("python", "out_of_scope"))
        self.assertTrue(r["conflict"])                 # one implementation cannot state what the other proves
        r = P(self.E("lean", "pass"), self.E("python", "pass"), self.E("human", "fail"))
        self.assertEqual((r["conflict"], r["agree"], r["warnings"]), (False, ["lean", "python"], ["human"]))
        r = P(self.E("python", "pass"), self.E("human", "pass"))
        self.assertEqual(r["agree"], [])               # one implementation is not a cross-check
        r = P(dict(self.E("python", "pass"), who="listing"), self.E("lean", "fail"))
        self.assertFalse(r["conflict"])                # Raw Facts listing entries are not an implementation
        r = pooling.pool([self.E("lean", "pass"), self.E("python", "fail")], LADDER, computed=["lean"])
        self.assertFalse(r["conflict"])                # the registry can narrow the list
        r = pooling.pool([self.E("lean", "pass"), self.E("python", "fail")], LADDER, computed=[])
        self.assertFalse(r["conflict"])                # an empty override disables cross-kind comparisons

    def test_bounded(self):
        P = lambda *es: pooling.pool(list(es), LADDER)
        self.assertFalse(P(dict(self.E("lean", "pass"), bound="exhaustive"))["bounded"])
        self.assertTrue(P(dict(self.E("lean", "pass"), bound="exhaustive within domain size <= 3"))["bounded"])
        self.assertTrue(P(dict(self.E("python", "pass"), bound="first 100 models"))["bounded"])
        self.assertFalse(P(dict(self.E("python", "fail"), bound=""))["bounded"])     # decided by a countermodel

    def test_summary_counts_conflict_cells(self):
        st = [{"id": "F1", "role": "fact"}]
        s = pooling.summary(st, [{"id": "T"}], [dict(self.E("python", "pass"), fact="F1"),
                                                  dict(self.E("python", "fail"), fact="F1")], LADDER)
        self.assertEqual((s["T"]["passed"], s["T"]["failed"], s["T"]["conflict"]), (0, 1, 1))


class RunnerFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.p = copy_example()
        self.addCleanup(shutil.rmtree, self.tmp)
        linglab(self.p, "listing")
        self.assertEqual(linglab(self.p, "run", "--force").returncode, 0)

    def runner_entries(self):
        return {(e["fact"], e["theory"]): e for e in results(self.p) if e["kind"] == "python" and e.get("who") == "runner"}

    def edit_json(self, name, fn):
        path = os.path.join(self.p, "data", name)
        d = json.load(open(path))
        fn(d)
        json.dump(d, open(path, "w"), indent=2)

    def test_digest_stored_and_cells_skipped(self):
        es = self.runner_entries()
        self.assertTrue(all(len(e["digest"]) == 40 for e in es.values()))
        out = linglab(self.p, "run")
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertTrue(all(" 0 entries (" in l for l in out.stdout.splitlines() if "entries (" in l))  # nothing recomputed
        self.assertEqual(self.runner_entries(), es)

    def test_declared_scope_recomputes_and_is_reported(self):
        path = os.path.join(self.p, "python", "principles.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(src.replace("@base_models\n", '@base_models(scope="toy bound")\n'))
        out = linglab(self.p, "run")
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertFalse([l for l in out.stdout.splitlines() if " 0 entries (" in l])    # every theory recomputed
        bounds = {e["bound"] for e in self.runner_entries().values()}
        self.assertIn("exhaustive within toy bound", bounds)
        self.assertNotIn("exhaustive", bounds)

    def test_warning_when_quantified_facts_meet_a_complete_list(self):
        def add(d):
            q = dict(next(s for s in d if s["id"] == "F05a"), id="F98", name="quantified")
            q["spec"] = {"premises": [["exists", "?x", ["Passed", "?x"]]], "conclusion": "p"}
            d.append(q)
        self.edit_json("statements.json", add)
        out = linglab(self.p, "run")
        self.assertIn("facts F98 use quantifiers or predicates, but @base_models declares no scope", out.stdout)

    def test_changed_fact_is_recomputed(self):
        def flip(d):
            for s in d:
                if s["id"] == "F05a":
                    s["expected"] = "fails" if s.get("expected", "holds") == "holds" else "holds"
        before = self.runner_entries()[("F05a", "T-SK")]
        self.edit_json("statements.json", flip)
        out = linglab(self.p, "run")
        after = self.runner_entries()[("F05a", "T-SK")]
        self.assertNotEqual(before["digest"], after["digest"])
        self.assertNotEqual(before["outcome"], after["outcome"])
        self.assertIn("entries (", out.stdout)

    def test_changed_theory_and_code_are_recomputed(self):
        before = self.runner_entries()[("F05a", "T-SK")]["digest"]
        self.edit_json("theories.json", lambda d: [t.update(principles=t["principles"][::-1]) for t in d if t["id"] == "T-SK"])
        linglab(self.p, "run")
        mid = self.runner_entries()[("F05a", "T-SK")]["digest"]
        self.assertNotEqual(before, mid)
        path = os.path.join(self.p, "python", "principles.py")
        txt = open(path).read().replace("# BEGIN principle:P-NEG\n", "# BEGIN principle:P-NEG\nx_changed = 1\n", 1)
        open(path, "w").write(txt)
        linglab(self.p, "run")
        self.assertNotEqual(mid, self.runner_entries()[("F05a", "T-SK")]["digest"])

    def test_entries_without_digest_are_stale(self):
        def strip(d):
            for e in d:
                e.pop("digest", None)
        self.edit_json("results.json", strip)
        linglab(self.p, "run")
        self.assertTrue(all(e["digest"] for e in self.runner_entries().values()))

    def test_run_aborts_on_check_errors_report_does_not(self):
        self.edit_json("results.json", lambda d: d[0].update(outcome="bogus"))
        out = linglab(self.p, "run")
        self.assertEqual(out.returncode, 1)
        self.assertIn("ERROR", out.stdout)
        os.makedirs(os.path.join(self.p, "report"), exist_ok=True)
        open(os.path.join(self.p, "report", "template.html"), "w").write("<script>var D=/*__DATA__*/null;</script>")
        out = linglab(self.p, "report")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("warning: linglab check reports errors", out.stdout)

    def test_bound_labels_accepted_by_check(self):
        for b in ("exhaustive", "first 5 models", "size<=5"):
            self.edit_json("results.json", lambda d, b=b: d[0].update(bound=b))
            self.assertEqual(linglab(self.p, "check").returncode, 0, b)

    def test_check_warns_on_principle_without_python_code(self):
        path = os.path.join(self.p, "python", "principles.py")
        open(path, "w").write(open(path).read().replace('@principle("P-NEG")', '@principle("P-NEG-OTHER")'))
        out = linglab(self.p, "check")
        self.assertIn("has no Python code", out.stdout)

    def test_check_warns_on_uses_without_primitives(self):
        self.assertNotIn("declare `uses`", linglab(self.p, "check").stdout)
        self.edit_json("statements.json", lambda d: next(s for s in d if s.get("role") == "fact").update(uses=["alternatives"]))
        self.assertIn("declare `uses` but no theory", linglab(self.p, "check").stdout)
        self.edit_json("theories.json", lambda d: next(t for t in d if t.get("kind") == "original").update(
            primitives=["entailment", "felicity", "consistency", "truth"]))
        self.assertNotIn("declare `uses`", linglab(self.p, "check").stdout)

    def test_out_of_scope_reason(self):
        from linglab import vocab
        vocab._BASE_MODELS[:] = [lambda: [{"p": 1}, {"p": 0}]]
        reg = {"N": vocab.Principle("N", lambda b: b.connective("not", lambda x: 1 - x))}
        T = vocab.Theory("T", "t", ["N"], registry=reg)
        self.assertEqual(T.explain(["not", "p"]), "")
        self.assertEqual(T.explain("zz"), "unknown atom 'zz'")
        self.assertIn("operator 'foo' not defined by any principle", T.explain(["not", ["foo", "p"]]))
        self.assertIn("takes 1", T.explain(["not", "p", "p"]))
        from linglab import runner
        d = runner.run_theory(T, [{"id": "F", "type": "felicity", "spec": {"discourse": [["foo", "p"]]}}])["F"]
        self.assertEqual(d.outcome, "out_of_scope")
        self.assertIn("operator 'foo'", d.reasons)


class StaleProofTests(unittest.TestCase):
    def test_scanner_ignores_comments_and_strings(self):
        from linglab import forbidden
        t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, t)
        os.makedirs(os.path.join(t, "lean", ".lake"))
        open(os.path.join(t, "lean", "A.lean"), "w").write(
            '-- sorry\n/- axiom x\n /- nested sorry -/ -/\ndef s := "sorry axiom"\ntheorem a : True := by sorry\naxiom bad : False\nopaque ok : Nat\n')
        open(os.path.join(t, "lean", ".lake", "B.lean"), "w").write("sorry")
        self.assertEqual(forbidden.scan_lean(t), ["lean/A.lean:5: sorry", "lean/A.lean:6: axiom"])

    def test_missing_folder_message(self):
        t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, t)
        linglab(t, "init", "x")
        proj = os.path.join(t, "x") if os.path.isdir(os.path.join(t, "x")) else t
        shutil.rmtree(os.path.join(proj, "lean"), ignore_errors=True)
        out = linglab(proj, "lean").stdout
        self.assertIn("no lean/ folder yet: run `python3 utils/bin/linglab.py lean --init` to create it", out)

    @unittest.skipUnless(shutil.which("lake"), "lake not installed")
    def test_sorry_blocks_entries_and_removes_stale(self):
        tmp, p = copy_example()
        self.addCleanup(shutil.rmtree, tmp)
        self.assertTrue([e for e in results(p) if e["kind"] == "lean"])
        d = os.path.join(p, "lean", "Linglab", "Toy")
        open(os.path.join(d, "Bad.lean"), "w").write("theorem bad_sorry : 1 = 2 := by sorry\n")
        open(os.path.join(p, "lean", "Linglab.lean"), "a").write("import Linglab.Toy.Bad\n")
        out = linglab(p, "lean")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn("Bad.lean:1: sorry", out.stdout)
        self.assertFalse([e for e in results(p) if e["kind"] == "lean"])
        self.assertIn("stale lean entries removed", out.stdout)

    @unittest.skipUnless(shutil.which("lake"), "lake not installed")
    def test_scope_of_the_theory_is_recorded(self):
        tmp, p = copy_example()
        self.addCleanup(shutil.rmtree, tmp)
        base = os.path.join(p, "lean", "Linglab", "Toy", "Base.lean")
        with open(base, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("    models := ms\n", src)
        with open(base, "w", encoding="utf-8") as f:
            f.write(src.replace("    models := ms\n", '    models := ms\n    scope := "toy bound"\n'))
        out = linglab(p, "lean")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        lean = [e for e in results(p) if e["kind"] == "lean"]
        self.assertEqual({e["bound"] for e in lean}, {"exhaustive within toy bound"})
        self.assertTrue(all("not a general proof" in e["reasons"] for e in lean))

    @unittest.skipUnless(shutil.which("lake"), "lake not installed")
    def test_only_theorems_of_the_stated_claim_are_credited(self):
        tmp, p = copy_example()
        self.addCleanup(shutil.rmtree, tmp)
        lean = os.path.join(p, "lean")
        with open(os.path.join(lean, "Linglab.lean"), encoding="utf-8") as f:
            root = f.read()
        with open(os.path.join(lean, "Linglab.lean"), "w", encoding="utf-8") as f:   # T_WK is no longer imported
            f.write(root.replace("import Linglab.Toy.T_WK\n", ""))
        with open(os.path.join(lean, "Linglab", "Toy", "Bogus.lean"), "w", encoding="utf-8") as f:   # nor is this
            f.write("namespace T_WK\ntheorem F04 : True := trivial\nend T_WK\n")
        edit_fact(p, "F06", lambda f: f["spec"].update(conclusion=["or", "p", "q"]))
        out = linglab(p, "lean")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn("NOT credited", out.stdout)
        self.assertIn("T_WK.F04 (lean/Linglab/Toy/Bogus.lean): its statement is not the claim", out.stdout)
        lean_cells = {(e["fact"], e["theory"]) for e in results(p) if e["kind"] == "lean"}
        self.assertNotIn(("F04", "T-WK"), lean_cells)                    # vacuous theorem: not credited
        self.assertFalse([k for k in lean_cells if k[0] == "F06"])       # written for the old spec: not credited
        self.assertIn(("F05a", "T-WK"), lean_cells)                      # unimported but correct: built and credited
        self.assertEqual(len(lean_cells), 34)
        self.assertFalse([k for k in lean_cells if k[1] == "RAW"])


class ProofCheckTests(unittest.TestCase):
    """Claims written from the shared syntax for the proof check, and which theorems are candidates."""

    def test_render_claims(self):
        from linglab import proofcheck as pc
        f = {"type": "entailment", "spec": {"premises": [["every", "?x", ["Student", "?x"], ["exh", ["may", "p"]]]],
                                            "conclusion": ["if", ["Passed", "a"], ["not", "q"]]}}
        c = pc.claim(f)
        self.assertEqual(pc.lean_claim(c),
                         '(Linglab.Claim.entails [(Linglab.S.every "x" (Linglab.S.pred "Student" [Linglab.Term.var "x"]) '
                         '(Linglab.S.op1 "exh" (Linglab.S.may (Linglab.S.atom "p"))))] (Linglab.S.imp (Linglab.S.pred "Passed" '
                         '[Linglab.Term.const "a"]) (Linglab.S.not (Linglab.S.atom "q"))))')
        t = pc.claim({"type": "truth", "spec": {"sentence": ["and", "s", "a"], "relation": "within", "target": 'a"b'}})
        self.assertEqual(pc.lean_claim(t), '(Linglab.Claim.truth (Linglab.S.and (Linglab.S.atom "s") (Linglab.S.atom "a")) '
                                           'Linglab.Rel.within (Linglab.S.atom "a\\"b"))')

    def test_unstatable_and_candidates(self):
        from linglab import proofcheck as pc
        for f in ({"type": "preference", "spec": {}}, {"type": "felicity", "spec": {"discourse": [["most", "?x", ["P", "?x"], ["Q", "?x"]]]}},
                  {"type": "felicity", "spec": {"discourse": ["?x"]}}):
            with self.assertRaises(pc.Unstatable):
                pc.claim(f)
        d = {"statements": [{"id": "F1", "role": "fact", "type": "felicity", "spec": {"discourse": ["p"]},
                             "parses": [{"id": "b", "spec": {"discourse": ["q"]}}]},
                            {"id": "F2", "role": "fact", "type": "other"}],
             "theories": [{"id": "T-A"}, {"id": "T-B", "parse_policy": "any"}]}
        found = [("T_A", "F1", False, "lean/A.lean"), ("T_B", "F1", True, "lean/B.lean"), ("Raw", "F1", False, "lean/Raw.lean"),
                 ("T_A", "F2", False, "lean/A.lean"), ("T_X", "F1", False, "lean/X.lean")]
        cands, skipped = pc.candidates(d, found, pc.lean_claim)
        self.assertEqual([(c["theory"], c["fact"]) for c in cands], [("T-A", "F1")])
        self.assertEqual(cands[0]["statement"], 'Holds T_A.theory (Linglab.Claim.felicitous [(Linglab.S.atom "p")])')
        self.assertEqual(len(skipped), 2)          # T_B combines parses; F2 has no claim shape; Raw and T_X are ignored


class OldAgdaEntriesTests(unittest.TestCase):
    """Agda support was removed; a project whose registry still lists `agda` keeps its entries valid."""

    def test_old_project_still_checks_and_reports(self):
        tmp, p = copy_example()
        self.addCleanup(shutil.rmtree, tmp)
        reg_p = os.path.join(p, "custom", "registry.json")
        reg = json.load(open(reg_p, encoding="utf-8"))
        reg["ladder"].insert(1, "agda")
        json.dump(reg, open(reg_p, "w", encoding="utf-8"))
        rs = results(p)
        rs.append(dict(next(e for e in rs if e["kind"] == "python"), kind="agda", who="agda", outcome="fail"))
        json.dump(rs, open(os.path.join(p, "data", "results.json"), "w", encoding="utf-8"))
        r = linglab(p, "check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(linglab(p, "report").returncode, 0)
        r = pooling.pool([self.E("agda", "fail"), self.E("python", "pass")], reg["ladder"])
        self.assertEqual((r["outcome"], r["conflict"], r["warnings"]), ("fail", False, ["python"]))   # no longer an implementation

    E = staticmethod(lambda kind, outcome: {"fact": "F01", "theory": "T-MK", "kind": kind, "outcome": outcome, "who": kind})


if __name__ == "__main__":
    unittest.main()
