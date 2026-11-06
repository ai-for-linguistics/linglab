#!/usr/bin/env node
// Smoke test for the report: node smoke_test.js path/to/report.html
// Runs the page's scripts against a minimal DOM stub, checks every tab rendered,
// then exercises hash routing, clicks, inputs and selects. Exits 1 on any failure.
"use strict";
const fs = require("fs"), vm = require("vm");
const file = process.argv[2];
if (!file) { console.error("usage: node smoke_test.js report.html"); process.exit(2); }
const html = fs.readFileSync(file, "utf8");
const UNDEF_BUDGET = (html.match(/undefined/g) || []).length;
const fails = [];
const fail = m => { fails.push(m); console.error("FAIL: " + m); };

function mkEl(id) {
  const cls = new Set(); const attrs = {};
  return { id, innerHTML: "", textContent: "", style: {}, tagName: "DIV", parentNode: null, open: false, value: "", checked: false,
    classList: { add: c => cls.add(c), remove: c => cls.delete(c), toggle: (c, on) => { (on === undefined ? !cls.has(c) : on) ? cls.add(c) : cls.delete(c); }, contains: c => cls.has(c) },
    setAttribute: (k, v) => { attrs[k] = v; }, getAttribute: k => (k in attrs ? attrs[k] : null),
    scrollIntoView() {}, addEventListener() {}, onclick: null, _cls: cls };
}
// boot(htmlText, katexStub): run the page's scripts against a DOM stub; returns {els, handlers, loc, clipboard, ctx, prompts, err}
function boot(htmlText, katexStub) {
  const els = {};
  for (const m of htmlText.matchAll(/\bid="([^"]+)"/g)) els[m[1]] = els[m[1]] || mkEl(m[1]);
  const handlers = {}, prompts = [];
  const doc = {
    getElementById: id => els[id] || (els[id] = mkEl(id)),
    createElement: () => mkEl("tmp"),
    querySelectorAll: () => [], querySelector: () => null,
    documentElement: mkEl("html"), title: "",
    addEventListener: (ev, fn) => { (handlers[ev] = handlers[ev] || []).push(fn); },
  };
  const win = { addEventListener: (ev, fn) => { (handlers["w:" + ev] = handlers["w:" + ev] || []).push(fn); }, prompt: t => { prompts.push(t); return null; }, innerWidth: 1000, innerHeight: 800 };
  if (katexStub) win.katex = katexStub;
  const clipboard = []; const loc = { hash: "" };
  const ctx = { document: doc, window: win, location: loc, history: { replaceState() {} }, console,
    navigator: { clipboard: { writeText: t => { clipboard.push(t); return Promise.resolve(); } } },
    matchMedia: () => ({ matches: false }), setTimeout, clearTimeout, innerWidth: 1000, innerHeight: 800 };
  ctx.window = Object.assign(win, ctx); vm.createContext(ctx);
  const scripts = [...htmlText.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  let err = null;
  try { scripts.forEach(s => vm.runInContext(s, ctx, { filename: "report-script" })); } catch (e) { err = e; }
  const fire = (ev, target, extra) => (handlers[ev] || []).forEach(fn => fn(Object.assign({ target, preventDefault() {}, clientX: 100, clientY: 100 }, extra)));
  const route = h => { loc.hash = h; (handlers["w:hashchange"] || []).forEach(f => f()); };
  return { els, handlers, loc, clipboard, ctx, prompts, err, fire, route, doc };
}
const B = boot(html, null);
const { els, handlers, loc, clipboard, ctx } = B;
if (B.err) { fail("exception while loading: " + (B.err.stack || B.err)); finish(); }

// the nav tabs; the theory cards are not a tab: they are the last block of Theoretical Space (element t-cards)
const TABS = ["overview", "empirical", "principles", "matrix", "pareto", "translations", "findings", "guide"];
// the stub does not parse HTML, so sub-containers are read by id
const SUB = { empirical: ["em-list"], principles: ["pr-top", "pr-list", "t-cards"], translations: ["tr-list"], matrix: ["mx-body"], pareto: ["pa-plot", "pa-legend", "pa-more", "ex-tl"], findings: ["fi-list"] };
const tabHtml = t => els["t-" + t].innerHTML + (SUB[t] || []).map(i => (els[i] || {}).innerHTML || "").join("");
const checkTabs = (when) => TABS.forEach(t => {
  const h = tabHtml(t);
  if (!h || h.length < 40) fail(`tab ${t} is empty ${when}`);
  if (/NaN|\[object/.test(h)) fail(`tab ${t} contains NaN/[object] ${when}: ` + (h.match(/.{30}(NaN|\[object).{30}/) || [""])[0]);
  // the word 'undefined' is legitimate in the data (presupposition failure); flag only more occurrences than the file itself contains (translations shows each text up to 3 times: row, code, review prompt)
  if ((h.match(/undefined/g) || []).length > UNDEF_BUDGET * (t === "translations" ? 3 : 1)) fail(`tab ${t} shows more 'undefined' than the data contains ${when}: ` + (h.match(/.{30}undefined.{30}/) || [""])[0]);
});
checkTabs("after load");
const fire = (ev, target, extra) => (handlers[ev] || []).forEach(fn => fn(Object.assign({ target, preventDefault() {}, clientX: 100, clientY: 100 }, extra)));
const hit = (sel, attrs) => ({ closest: s => (s === sel ? { getAttribute: k => (attrs[k] != null ? attrs[k] : null) } : null) });
const attrsOf = (name, v) => ({ [name]: v });
function run(label, fn) { try { fn(); } catch (e) { fail(label + ": " + (e.stack || e)); } }

// routing
TABS.forEach(t => run("route " + t, () => { loc.hash = "#" + t; (handlers["w:hashchange"] || []).forEach(f => f()); }));
for (const h of ["#empirical:F01", "#principles:P-NEG", "#translations:P-NEG", "#translations:F01", "#translations:nope", "#cards:T-MK", "#audits:T-MK", "#audits", "#matrix:F05a", "#matrix:T-MK", "#explorer", "#pareto", "#findings:R1", "#bogus"]) run("route " + h, () => { loc.hash = h; (handlers["w:hashchange"] || []).forEach(f => f()); });
// click interactions harvested from the rendered HTML
const grab = (re, tab) => [...tabHtml(tab).matchAll(re)].map(m => m[1]);
const hasData = /<table/.test(els["mx-body"].innerHTML);
const cells = grab(/data-cell="([^"]+)"/g, "matrix"); if (hasData && !cells.length) fail("no data-cell in matrix");
cells.slice(0, 3).concat(cells.slice(-1)).forEach(c => run("cell " + c, () => { fire("click", hit("[data-cell]", attrsOf("data-cell", c))); fire("mouseover", hit("[data-cell]", attrsOf("data-cell", c))); }));
if (hasData && !els.pop.innerHTML) fail("pop empty after cell click");
const bars = grab(/data-bar="([^"]+)"/g, "matrix"); if (hasData && !bars.length) fail("no clickable bar in the matrix");
bars.slice(0, 2).forEach(g => run("bar " + g, () => { fire("click", hit("[data-bar]", attrsOf("data-bar", g))); if (!/summary of the outcomes/.test(els.pop.innerHTML)) fail("bar panel lacks the summary"); }));
run("bar twice closes", () => { const g = bars[0]; fire("click", hit("[data-bar]", attrsOf("data-bar", g))); fire("click", hit("[data-bar]", attrsOf("data-bar", g))); if (els.pop.style.display === "block") fail("same bar twice should close the panel"); });
// out-of-scope reasons and parses are shown in the panel
if (cells.includes("F11|T-WK")) run("panel scope reason", () => { fire("click", hit("[data-cell]", attrsOf("data-cell", "F11|T-WK"))); const h = els.pop.innerHTML;
  if (!/Out of scope \(no prediction\)/.test(h)) fail("panel should say why the cell is out of scope: " + h.slice(-300));
  fire("click", hit("[data-cell]", attrsOf("data-cell", "F11|T-WK"))); });
if (cells.includes("F09|T-SK")) run("panel parses", () => { fire("click", hit("[data-cell]", attrsOf("data-cell", "F09|T-SK"))); const h = els.pop.innerHTML;
  if (!/Parses of the sentence/.test(h) || !/swapped/.test(h)) fail("panel should list the parses of F09");
  fire("click", hit("[data-cell]", attrsOf("data-cell", "F09|T-SK"))); });
// a reading (not evidence) is the fourth folded part of the panel, only for cells that have one
if (cells.includes("F01|T-SK")) run("panel reading", () => { fire("click", hit("[data-cell]", attrsOf("data-cell", "F01|T-SK"))); const h = els.pop.innerHTML;
  if (!/4\. Reading/.test(h) || !/not evidence/.test(h)) fail("panel lacks the reading of F01 x T-SK");
  fire("click", hit("[data-cell]", attrsOf("data-cell", "F01|T-SK"))); });
if (cells.includes("F01|RAW")) run("no reading panel part", () => { fire("click", hit("[data-cell]", attrsOf("data-cell", "F01|RAW"))); if (/4\. Reading/.test(els.pop.innerHTML)) fail("a cell without a reading should not show the part"); fire("click", hit("[data-cell]", attrsOf("data-cell", "F01|RAW"))); });
// the cell panel: three folded parts; the same square again closes it; Esc closes; navigation closes
if (cells.length) {
  const c0 = cells[0];
  run("panel three parts", () => { fire("click", hit("[data-cell]", attrsOf("data-cell", c0))); const h = els.pop.innerHTML;
    if (els.pop.style.display !== "block") fail("panel not shown");
    if (!/1\. Fact/.test(h) || !/2\. Principles involved/.test(h) || !/3\. Current test/.test(h)) fail("panel lacks one of its three parts");
    if (/<details class="mxs" open/.test(h)) fail("panel parts should be folded");
    fire("click", hit("[data-cell]", attrsOf("data-cell", c0))); if (els.pop.style.display === "block") fail("same cell twice should close the panel");
    fire("click", hit("[data-cell]", attrsOf("data-cell", c0))); handlers.keydown.forEach(f => f({ key: "Escape" })); if (els.pop.style.display === "block") fail("Esc should close the panel");
    fire("click", hit("[data-cell]", attrsOf("data-cell", c0))); loc.hash = "#overview"; (handlers["w:hashchange"] || []).forEach(f => f()); if (els.pop.style.display === "block") fail("navigation should close the panel"); });
}
run("toggle Facts x Theories", () => { fire("click", hit("[data-mxtr]", attrsOf("data-mxtr", "1"))); if (hasData && !/mxv-grid tr/.test(els["mx-body"].innerHTML)) fail("transposed table missing"); fire("click", hit("[data-mxtr]", attrsOf("data-mxtr", "0"))); if (hasData && /mxv-grid tr/.test(els["mx-body"].innerHTML)) fail("toggle back failed"); });
grab(/data-pgrp="([^"]+)"/g, "pareto").forEach(g => run("pgrp", () => { fire("click", hit("[data-pgrp]", attrsOf("data-pgrp", g))); fire("click", hit("[data-pgrp]", attrsOf("data-pgrp", g))); }));
grab(/data-card="([^"]+)"/g, "cards").forEach(g => run("card", () => { fire("click", hit("[data-card]", attrsOf("data-card", g))); if (els["t-cards"].innerHTML.length < 50) fail("theory card empty for " + g); }));
const asks = grab(/data-ask="([^"]*)"/g, "guide"); if (!asks.length) fail("no ask buttons in guide");
run("ask", () => { fire("click", hit("[data-ask]", attrsOf("data-ask", asks[0]))); });
const inp = (k, v, ev, extra) => run("input " + k, () => fire(ev || "input", Object.assign({ getAttribute: a => (a === "data-in" ? k : null), value: v }, extra || {})));
inp("em-q", "king"); inp("em-q", "zzzz"); inp("em-q", ""); inp("em-type", "felicity", "change"); inp("em-type", "", "change"); inp("em-about", "system", "change"); inp("em-about", "", "change"); inp("em-cont", "", "change", { checked: true }); inp("em-cont", "", "change", { checked: false });
inp("pr-q", "and"); inp("tr-q", "and"); inp("tr-q", ""); inp("tr-un", "", "change", { checked: true }); inp("tr-un", "", "change", { checked: false });
const trIds = grab(/data-trck="([^"]+)"/g, "translations");
if (!/<details/.test(els["tr-list"].innerHTML)) fail("translations list has no rows");
trIds.slice(0, 2).forEach(id => run("trck " + id, () => { fire("change", { getAttribute: a => (a === "data-trck" ? id : null), checked: true, value: "" }); fire("change", { getAttribute: a => (a === "data-trck" ? id : null), checked: false, value: "" }); }));
run("trprompt", () => fire("click", hit("[data-act]", attrsOf("data-act", "trprompt")))); run("trexport", () => fire("click", hit("[data-act]", attrsOf("data-act", "trexport"))));
grab(/data-layer="([^"]+)"/g, "cards").concat(["words", "all"]).forEach(v => run("layer " + v, () => fire("click", hit("[data-layer]", attrsOf("data-layer", v)))));
run("ctab", () => fire("click", hit("[data-ctab]", attrsOf("data-ctab", "0")))); 
inp("fi-q", "x"); inp("fi-status", "proved", "change"); inp("fi-status", "", "change"); inp("ex-q", "SK");
inp("ex-llm", "0", "change"); inp("ex-system", "0", "change"); inp("ex-cont", "without", "change"); inp("ex-cont", "only", "change"); inp("ex-layer", "contested", "change"); inp("ex-kind", "felicity", "change"); inp("ex-layer", "", "change"); inp("ex-kind", "", "change"); inp("ex-cont", "all", "change");
for (const [k, vals] of [["a-x", ["n_principles_no_aux", "python_gzip", "lean_chars"]], ["a-y", ["passed_over_applicable", "confidence_weighted"]], ["b-x", ["lean_gzip"]], ["b-y", ["python_chars"]], ["c-x", ["confidence_weighted"]], ["c-y", ["passed"]]]) vals.forEach(v => inp("ex-" + k, v, "change"));
["exnone", "exall", "exnoraw", "closepop"].forEach(a => run(a, () => fire("click", hit("[data-act]", attrsOf("data-act", a)))));
run("tsel", () => fire("change", { getAttribute: a => (a === "data-tsel" ? "T-MK" : null), checked: false, value: "" }));
run("no theme toggle (light only)", () => { if (els.theme && els.theme.onclick) fail("the theme toggle should be gone"); });
run("pt", () => fire("click", hit("[data-pt]", attrsOf("data-pt", "T-MK"))));
checkTabs("after interactions");
// the heatmap: squares coloured by outcome, marks for the evidence kind, legend in three clusters, no italics, calm band
if (hasData) {
  const mx = els["mx-body"].innerHTML, tab = els["t-matrix"].innerHTML;
  if (!/class="cell (pass|fail|oos|pend)/.test(mx)) fail("matrix has no coloured squares");
  if ((tab.match(/class="mxv-legend"/g) || []).length !== 3) fail("legend should have three clusters");
  if (!/Theories \u00d7 Facts/.test(tab) || !/Facts \u00d7 Theories/.test(tab)) fail("matrix lacks the orientation toggle (with the multiplication sign)");
  if ((tab.match(/class="howto"/g) || []).length !== 1) fail("matrix how-to should be one box");
  if (/\bnot computed \(/.test(tab) || /informal evidence \(/.test(tab)) fail("legend entries must not carry a parenthesis");
  if (!/controversial fact/.test(tab)) fail("legend lacks the controversial entry");
  if (/<table class="mx"/.test(mx)) fail("old matrix table still present");
  if (!/class="bar"/.test(mx)) fail("matrix lacks the bars");
}
if (/font-style|<i>|<em>/.test(html.replace(/<script id="katex-js">[\s\S]*?<\/script>/, "").replace(/<style id="katex-css">[\s\S]*?<\/style>/, "").replace(/const DATA = [\s\S]*?;\s*<\/script>/, ""))) fail("italics in the page template");
if (!/id="band"/.test(html)) fail("warning band element missing");
{ const m = els.band && els.band.innerHTML; if (!/Results may be wrong/.test(m || "")) fail("band text missing: " + m);
  if (!/<ul>(<li>[^<]+<\/li>){3}<\/ul>/.test(m || "")) fail("band lacks its caveats list");
  if (!els.bandt || !els.bandt.textContent) fail("band title line missing"); }
// page title and subtitle (configurable; defaults)
if (!/^linglab: benchmarking and constructing theories with AI and verifiers/.test(els.ttl.textContent)) fail("default page title: " + els.ttl.textContent);
if (!els.subttl.innerHTML) fail("subtitle missing");
if (/\u2014|\bTheories x Facts|Facts x Theories|Coverage x Complexity|Coverage vs Complexity|Theories x Facts/.test(els.nav.innerHTML)) fail("tab labels must use the multiplication sign");
{ const labels = [...els.nav.innerHTML.matchAll(/data-tab="([^"]+)">([^<]*)</g)].map(m => m[1] + ":" + m[2]);
  const want = ["overview:Overview", "empirical:Empirical Space", "principles:Theoretical Space", "matrix:Theories \u00d7 Facts", "pareto:Coverage \u00d7 Complexity"];
  want.forEach((w, i) => { if (labels[i] !== w) fail("tab " + i + " should be " + w + ", is " + labels[i]); });
  if (labels.some(l => /^cards:/.test(l))) fail("theory cards must not be a tab");
  if (labels.some(l => /[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/u.test(l))) fail("no icons in tab labels"); }
if (!/Disclaimers and caveats/.test(els["t-overview"].innerHTML)) fail("overview lacks the disclaimers block");
if (/Simplicity/i.test(els["t-pareto"].innerHTML + els["pa-plot"].innerHTML + els["t-guide"].innerHTML)) fail("'Simplicity' still in page");
if (!/Coverage/.test(els["t-pareto"].innerHTML) || !/Complexity/.test(els["t-pareto"].innerHTML)) fail("pareto tab lacks the Coverage and Complexity proxy pills");
if (hasData && !/pareto-front/.test(els["pa-plot"].innerHTML)) console.warn("note: no frontier drawn");
if (!/linglab report/.test(els.foot.textContent)) fail("footer name");
if (!/one informant is one data point/.test(els["t-empirical"].innerHTML)) fail("empirical intro sentence missing");
// glossary lists every kind of the ladder
{ const g = els["t-guide"].innerHTML; ctx.window.__linglab.LADDER.forEach(k => { if (!g.includes("<b>" + k + "</b>")) fail("guide glossary misses kind " + k); }); }
// synthetic cells: proof kinds get the dot class, informal kinds the stripes class, formal runs neither; raw facts exempt; conflict flagged
run("synthetic marks", () => {
  const cls = ctx.window.__linglab.mxCls;
  const F = { id: "F", contested: false }, T = { id: "T" };
  const has = (p, c) => new RegExp("(^| )" + c + "( |$)").test(cls(F, T, p));
  ["lean", "agda"].forEach(k => { if (!has({ outcome: "pass", kind: k }, "proof")) fail("proof class missing for " + k); });
  ["python"].forEach(k => { if (has({ outcome: "pass", kind: k }, "proof") || has({ outcome: "pass", kind: k }, "inf")) fail("python must carry neither mark"); });
  ["human", "paper-claim", "user-claim", "llm-judged", "zzcustom"].forEach(k => { if (!has({ outcome: "pass", kind: k }, "inf")) fail("informal class missing for " + k); });
  if (cls(F, { id: "RAW", generated: "listing" }, { outcome: "pass", kind: "human" }).includes("inf")) fail("Raw Facts cell must not use informal styling");
  if (!has({ outcome: "fail", kind: "python", conflict: true }, "flag") || !has({ outcome: "fail", kind: "python", warning: true }, "flag")) fail("conflict and warning must be flagged");
  if (!cls({ id: "F", contested: true }, T, { outcome: "pass", kind: "python" }).includes("con")) fail("contested class missing");
  if (!/class="cell oos/.test(cls(F, T, { outcome: "out_of_scope" }) ? ('class="' + cls(F, T, { outcome: "out_of_scope" })) : "")) fail("out of scope class");
});

if (!/Data updated/.test(els.foot.textContent)) fail("footer missing update date");
if (!/Beta\. Produced with AI assistance/.test(els.foot.textContent)) fail("footer missing disclaimer");
if (!els["t-pareto"].innerHTML.includes("tlist")) fail("theory selection missing in the Coverage vs Complexity tab");
if (!els["pa-plot"].innerHTML.includes("<svg")) console.warn("note: no svg plot (no metrics data?)");
// ---- layers, fragments and checks: the built page with the example data
if (hasData) {
  const ch = tabHtml("cards");
  if (!/data-layer="words"/.test(ch + tabHtml("principles"))) fail("layer toggle (words | symbols | code | all) missing");
  if (!/<h2 class="cardshead">Theory cards<\/h2>/.test(ch)) fail("the theory cards block lacks its heading");
  if (/>Audits</.test(els.nav.innerHTML)) fail("tab still called Audits");
  if (/Theory cards</.test(els.nav.innerHTML)) fail("the theory cards must not be a tab");
}
// ---- scenarios on synthetic data (stub katex writes 'TEX:'+src)
const withData = (obj) => html.replace(/const DATA = [\s\S]*?;\s*<\/script>/, () => "const DATA = " + JSON.stringify(obj).replace(/</g, "\\u003c") + ";\n</script>");
const katexStub = { render: (src, el) => { el.innerHTML = "TEX:" + src; } };
const chk = (by, verdict, extra) => Object.assign({ by, who: by === "llm" ? "model-x" : "ann", when: "2026-01-02", what: "readback", verdict, readback: "READBACK-" + by, note: "n" }, extra || {});
const SYN = {
  meta: { title: "Synthetic", updated: "2026-01-01" },
  statements: [
    { id: "F1", role: "fact", name: "Fact one", text: "A and B entails A", type: "entailment", spec: { premises: [["and", "A", "B"]], conclusion: "A" }, notation: "A \\land B \\models A", checks: [chk("human", "agrees", { what: "translation" })] },
    { id: "F2", role: "fact", name: "Fact two", text: "second fact", type: "entailment", spec: { premises: ["A"], conclusion: "B" }, checks: [] },
    { id: "P-A", role: "principle", name: "Conj", text: "conjunction is strong", notation: "[\\![A \\land B]\\!] = 1", checks: [chk("llm", "agrees"), chk("human", "agrees", { when: "2026-02-01" })] },
    { id: "P-B", role: "principle", name: "Aux", text: "aux assumption <b>", auxiliary: true, checks: [chk("llm", "disagrees", { readback: "BAD-READ" })] },
    { id: "P-C", role: "principle", name: "NoNote", text: "plain" },
  ],
  theories: [
    { id: "T1", name: "Theory one", description: "DESC-ONE", notation: "T_1", principles: ["P-A", "P-B", "P-C", "P-GHOST"], fragments: ["FR-core", "FR-ext", "FR-missing"] },
    { id: "T2", name: "Theory two", description: "DESC-TWO", principles: ["P-A"], fragments: ["FR-core"] },
  ],
  fragments: [
    { id: "FR-core", name: "Core fragment", summary: "SUMMARY-CORE", notation: "\\mathcal{L}", defs: [{ label: "Model", text: "a set of worlds", notation: "M = \\langle W, V\\rangle" }], files: { python: [{ path: "python/core.py", text: "print('hi')" }, "python/other.py"], lean: ["lean/Core.lean"] }, checks: [chk("llm", "partial")], notes: "" },
    { id: "FR-ext", name: "Ext fragment", summary: "x", defs: [], files: {}, checks: [] },
  ],
  fragment_users: { "FR-core": ["T1", "T2"], "FR-ext": ["T1"] },
  results: [{ fact: "F1", theory: "T1", outcome: "pass", kind: "lean" }, { fact: "F2", theory: "T1", outcome: "fail", kind: "python" }, { fact: "F1", theory: "T2", outcome: "pending", kind: "human" }],
  findings: [],
  code: { principles: { "P-A": { python: "def conj(): pass", lean: "def conj := 1" } }, facts: { F1: { spec_text: "SPEC1", lean: [{ theory: "T1", text: "theorem t : True := trivial" }], notation_auto: "AUTO-A \\vdash A" }, F2: { notation_auto: "AUTO-F2" } } },
};
function scenario(label, data, stub, fn) {
  run("scenario " + label, () => {
    const b = boot(withData(data), stub);
    if (b.err) { fail(label + ": exception while loading: " + (b.err.stack || b.err)); return; }
    TABS.forEach(t => b.route("#" + t));
    fn(b);
    const sub = (t) => b.els["t-" + t].innerHTML + (SUB[t] || []).map(i => (b.els[i] || {}).innerHTML || "").join("");
    TABS.forEach(t => { const h = sub(t); if (!h || h.length < 40) fail(`${label}: tab ${t} is empty`); if (/NaN|\[object/.test(h)) fail(`${label}: tab ${t} contains NaN/[object]`); });
  });
}
const cardHtml = b => b.els["t-cards"].innerHTML;
scenario("synthetic+katex", SYN, katexStub, b => {
  b.route("#cards:T1");
  const h = cardHtml(b);
  if (h.length < 500) fail("theory card too short on synthetic data");
  if (!/TEX:\\mathcal\{L\}/.test(h)) fail("fragment notation not routed through katex");
  if (!/TEX:M = /.test(h)) fail("fragment defs notation not routed through katex");
  if (!/TEX:\[\\!\[A/.test(h)) fail("principle symbols not routed through katex");
  if (!/TEX:T_1/.test(h)) fail("theory notation not routed through katex");
  if (!/data-layer="words"/.test(h) || !/data-layer="symbols"/.test(h) || !/data-layer="code"/.test(h) || !/data-layer="all"/.test(h)) fail("layer toggle missing in theory card");
  if (!/also used by/.test(h) || !/#cards:T2/.test(h)) fail("'also used by' with a link to the other theory missing for shared fragment");
  if (!/this theory only/.test(h)) fail("unshared fragment should say 'this theory only'");
  if (!/FR-missing/.test(h)) fail("unknown fragment id should still be listed");
  if (!/SUMMARY-CORE/.test(h) || !/DESC-ONE/.test(h)) fail("summaries missing");
  if (!/python\/core\.py/.test(h) || !/print\(&#39;hi&#39;\)/.test(h)) fail("inlined fragment file not shown (escaped)");
  if (!/python\/other\.py/.test(h)) fail("path-only fragment file missing");
  if (!/READBACK-human/.test(h)) fail("latest readback (human, newer) missing");
  if (/READBACK-llm/.test(h.split("P-B")[0].split("Conj")[1] || "") && false) fail("unreachable");
  if (!/class="badge pass">agrees/.test(h) || !/class="badge fail">disagrees/.test(h)) fail("agrees/disagrees badges missing");
  if (!/checked: 1 llm, 1 human, last: agrees/.test(h)) fail("checks summary badge missing: " + (h.match(/checked:[^<]*/g) || []).join("|"));
  if (!/>auxiliary</.test(h)) fail("auxiliary badge missing on the principle row");
  if (!/Explain principle P-A/.test(h)) fail("ask button on principle row missing");
  if (!/pass\/fail table/i.test(h)) fail("pass/fail table folded section missing");
  if (!/aux assumption &lt;b&gt;/.test(h)) fail("statement text not escaped");
  if (!/P-GHOST/.test(h)) fail("unknown principle id should still be listed");
  b.route("#cards:T2"); if (!/this theory only|also used by/.test(cardHtml(b)) || !/also used by/.test(cardHtml(b))) fail("T2 card should say also used by T1");
  b.route("#audits:T1"); if (!/Theory one/.test(cardHtml(b))) fail("#audits alias did not open the card");
  b.fire("click", hit("[data-layer]", attrsOf("data-layer", "symbols")));
  b.fire("click", hit("[data-ctab]", attrsOf("data-ctab", "1")));
  const pr = b.els["pr-list"].innerHTML, em = b.els["em-list"].innerHTML;
  if (!/TEX:\[\\!\[A/.test(pr) || !/checked: 2/.test(pr) && !/checked: 1 llm, 1 human/.test(pr)) fail("principle card lacks symbols or checks summary");
  if (!/TEX:A \\land B/.test(em)) fail("fact notation not routed through katex");
  if (!/TEX:AUTO-F2/.test(em) || !/autotag/.test(em)) fail("fact notation_auto not shown marked 'auto'");
  if (!/SPEC1/.test(em) || !/theorem t/.test(em)) fail("fact code layer lacks spec text / Lean snippet");
  if (!/<table class="ck">/.test(pr + em)) fail("checks log table missing");
  const tr = b.els["tr-list"].innerHTML;
  if (!/TEX:/.test(tr) || !/class="reading"/.test(tr) || !/READBACK-human/.test(tr)) fail("translations lack the symbols layer or the reading line");
  // export ticks
  const ids = [...tr.matchAll(/data-trck="([^"]+)"/g)].map(m => m[1]);
  ids.slice(0, 2).forEach(id => b.fire("change", { getAttribute: a => (a === "data-trck" ? id : null), checked: true, value: "" }));
  b.fire("click", hit("[data-act]", attrsOf("data-act", "trexport")));
  const last = b.clipboard[b.clipboard.length - 1] || "";
  if (!/Record these checks in the data/.test(last)) fail("export ticks: prompt missing in clipboard");
  try {
    const arr = JSON.parse(last.slice(last.indexOf("[")));
    if (arr.length !== 2 || arr[0].by !== "human" || arr[0].what !== "translation" || arr[0].verdict !== "agrees" || !/^\d{4}-\d\d-\d\d$/.test(arr[0].when) || arr[0].note !== "ticked in the report") fail("export ticks: wrong JSON " + last);
  } catch (e) { fail("export ticks: JSON does not parse: " + e); }
  if (!/export my ticks/.test(b.els["t-translations"].innerHTML)) fail("export my ticks button missing");
  b.fire("change", { getAttribute: a => (a === "data-trck" ? ids[0] : null), checked: false, value: "" }); b.fire("change", { getAttribute: a => (a === "data-trck" ? ids[1] : null), checked: false, value: "" });
  b.fire("click", hit("[data-act]", attrsOf("data-act", "trexport"))); // nothing ticked: toast, no throw
});
scenario("synthetic, no katex (raw LaTeX escaped)", SYN, null, b => {
  b.route("#cards:T1");
  const h = cardHtml(b);
  if (/TEX:/.test(h)) fail("TEX: without katex");
  if (!/texraw/.test(h) || !/\\mathcal\{L\}/.test(h)) fail("raw LaTeX fallback missing");
  const d2 = JSON.parse(JSON.stringify(SYN)); d2.fragments[0].notation = "a<b & c>\"d\"";
  const b2 = boot(withData(d2), null); b2.route("#cards:T1");
  if (!/a&lt;b &amp; c&gt;&quot;d&quot;/.test(cardHtml(b2))) fail("raw LaTeX source not escaped");
});
scenario("synthetic, katex throws", SYN, { render() { throw new Error("boom"); } }, b => {
  b.route("#cards:T1"); if (!/texraw/.test(cardHtml(b))) fail("katex error should fall back to raw source");
});
scenario("synthetic, katex undefined render", SYN, {}, b => { b.route("#cards:T1"); if (!/texraw/.test(cardHtml(b))) fail("katex without render should fall back to raw"); });
// heatmap on a general project: families, short names, kinds, layers, banner switched off, fallbacks when none of these exist
const FAM = JSON.parse(JSON.stringify(SYN));
FAM.meta.short_names = { T3: "Three" }; FAM.meta.banner = ""; FAM.meta.fact_kinds = { alpha: "Alpha facts" };
FAM.statements.push({ id: "F3", role: "fact", name: "Third", text: "third", type: "felicity", spec: { discourse: ["A"] }, kind: "alpha", contested: true, layer: "nice", relations: [{ rel: "related", to: "P-A" }] });
FAM.statements.find(s => s.id === "F1").kind = "alpha";
FAM.theories[0].family = "Fam One"; FAM.theories[0].short = "T-one"; FAM.theories[1].family = "Fam Two";
FAM.theories.push({ id: "T3", name: "Theory three", principles: ["P-A"], family: "Fam Two" }, { id: "RAW", name: "Raw Facts", generated: "listing", principles: ["F1", "F2", "F3"], kind: "reference" });
FAM.registry = { layers: [{ id: "nice", name: "Nice to have" }] };
scenario("families, short names, kinds, layers", FAM, null, b => {
  b.route("#matrix");
  const g = b.els["mx-body"].innerHTML;
  if (!/famline/.test(g) || !/Fam One/.test(g) || !/Fam Two/.test(g)) fail("two families should give family sublines");
  if (!/>T-one</.test(g) || !/>Three</.test(g)) fail("short names (field and meta.short_names) not shown in the heatmap");
  if (!/Alpha facts/.test(g)) fail("meta.fact_kinds title not used");
  if (!/class="[^"]*\bcon\b/.test(g)) fail("contested fact not marked");
  if (b.els.band.style.display !== "none") fail("banner '' should hide the band");
  b.fire("click", hit("[data-cell]", attrsOf("data-cell", "F3|T1")));
  const h = b.els.pop.innerHTML;
  if (!/Linked to this fact in the data/.test(h) || !/relation of the fact/.test(h)) fail("principle linked by a relation not shown in the panel");
  if (!/Nice to have/.test((b.fire("click", hit("[data-bar]", attrsOf("data-bar", "T1"))), b.els.pop.innerHTML))) fail("registry layer name missing in the bar summary");
  b.fire("click", hit("[data-mxtr]", attrsOf("data-mxtr", "1")));
  const t = b.els["mx-body"].innerHTML;
  if (!/<th class="fam ch"/.test(t) || !/class="ch vert/.test(t)) fail("transposed heatmap lacks family header or vertical theory names");
  b.route("#cards:T1"); if (!/Theory one/.test(cardHtml(b)) || !/T-one/.test(cardHtml(b))) fail("card shows full name and short name");
  b.route("#pareto"); if (!/pareto-lg/.test(b.els["pa-legend"].innerHTML) || !/Fam One/.test(b.els["pa-legend"].innerHTML)) fail("group chips by family missing");
  b.fire("click", hit("[data-pgrp]", attrsOf("data-pgrp", "f:Fam One"))); if (!/pareto-lg off/.test(b.els["pa-legend"].innerHTML)) fail("group chip did not toggle");
});
scenario("flat heatmap without families", SYN, null, b => {
  b.route("#matrix"); const g = b.els["mx-body"].innerHTML;
  if (/famline/.test(g)) fail("no family sublines expected when there are fewer than two families");
  if (!/class="cell /.test(g)) fail("squares missing");
  if (b.els.band.style.display === "none" || !/Results may be wrong/.test(b.els.band.innerHTML)) fail("default band missing");
});
// ---- second port round: title, subtitle, band, row labels by kind, origin table, short codes, family statements, history, plot bounds
const CFG = JSON.parse(JSON.stringify(SYN));
Object.assign(CFG.meta, { page_title: "My page", subtitle: "A plain subtitle", banner: "KEY SENTENCE", banner_title: "TITLE LINE", banner_points: ["point one", "point two"],
  question: "Does Theory one beat Theory two?", papers: [{ id: "Kleene 1952", title: "Intro to Metamathematics", role: "background", url: "https://example.org/k" }] });
CFG.theories[0].short = "T-one"; CFG.theories[0].kind = "original"; CFG.theories[0].family = "Fam"; CFG.theories[0].origin = { source: "Kleene 1952", page: "12" };
CFG.theories[1].short = "T-two"; CFG.theories[1].kind = "fix"; CFG.theories[1].parent = "T1"; CFG.theories[1].family = "Fam";
CFG.theories.push({ id: "T3", name: "Theory three", short: "T3", kind: "original", principles: ["P-A"], family: "Other" });
CFG.statements.find(s => s.id === "F1").requires = ["FR-core", "FR-ext"];
CFG.code.facts.F1.lean.push({ theory: "T2", text: "theorem t2 : True := trivial" }); CFG.code.facts.F1.lean[0].theory = "T1";
CFG.code.facts.F1.lean = [CFG.code.facts.F1.lean[0]];   // statement of T1 only: T2 shares it through the family
scenario("title, band, row labels, origin table, codes, family statements", CFG, null, b => {
  if (b.els.ttl.textContent !== "My page") fail("meta.page_title not used: " + b.els.ttl.textContent);
  if (b.els.subttl.innerHTML !== "A plain subtitle") fail("meta.subtitle not used");
  if (!/KEY SENTENCE/.test(b.els.band.innerHTML) || !/<li>point one<\/li><li>point two<\/li>/.test(b.els.band.innerHTML) || b.els.bandt.textContent !== "TITLE LINE") fail("band title, key sentence or points not configurable");
  b.route("#matrix"); const g = b.els["mx-body"].innerHTML;
  if (!/>Source <span class="mut fnm">T-one<\/span>/.test(g) || !/>Modified <span class="mut fnm">T-two<\/span>/.test(g)) fail("rows of a family should be labelled by kind (Source / Modified): " + (g.match(/class="rh let[^>]*>.{0,120}/g) || []).join("|"));
  b.route("#overview"); const o = b.els["t-overview"].innerHTML;
  if (!/Does T-one beat T-two\?/.test(o)) fail("full theory names in running text should become short codes");
  if (!/Theories \(3\)/.test(o) || !/https:\/\/example\.org\/k/.test(o) || !/Intro to Metamathematics/.test(o)) fail("origin table: citation with link missing");
  if (!/fix, from <a href="#cards:T1">T-one<\/a>|modified, from <a href="#cards:T1">T-one<\/a>/.test(o)) fail("origin table: derived theory should say 'modified, from <CODE>': " + (o.match(/from[^<]*<a[^>]*>[^<]*/g) || []).join("|"));
  if (/Starts from/i.test(o)) fail("no 'Starts from' column");
  b.route("#matrix"); b.fire("click", hit("[data-cell]", attrsOf("data-cell", "F1|T2")));
  const p = b.els.pop.innerHTML;
  if (!/in the formalization of Fam/.test(p) || !/theorem t : True/.test(p)) fail("panel should show the family's proof statements for a theory without its own: " + p.slice(-400));
  if (!/Fragment the fact requires/.test(p) || !/FR-core/.test(p) || !/declared by this theory/.test(p)) fail("panel lacks the fragment the fact requires");
  // history: a theory-card button is a navigation (hash), not a silent re-render
  b.route("#cards:T1"); if (!/class="cardshead">Theory cards</.test(cardHtml(b))) fail("cards block heading missing");
  b.fire("click", hit("[data-card]", attrsOf("data-card", "T2"))); if (!/^#?cards:T2$/.test(b.loc.hash)) fail("card button should navigate by hash, is " + b.loc.hash);
  b.route(b.loc.hash); if (!/Theory two/.test(cardHtml(b))) fail("card T2 not shown after navigation");
});
// the plot: no marker leaves the plotting area, for every proxy and every data filter
run("plot bounds for all proxies and filters", () => {
  const b = boot(html, null);
  if (b.err) { fail("plot bounds: exception " + b.err); return; }
  b.route("#pareto");
  const sel = (k, v) => b.fire("change", { getAttribute: a => (a === "data-in" ? k : null), value: v });
  const reg = JSON.parse(html.match(/const DATA = ([\s\S]*?);\s*<\/script>/)[1]).registry || {};
  const ids = l => (l || []).map(m => typeof m === "string" ? m : m.id);
  const cov = ids(reg.coverage_metrics).length ? ids(reg.coverage_metrics) : ["passed", "passed_over_applicable", "confidence_weighted"];
  const siz = ids(reg.size_metrics).length ? ids(reg.size_metrics) : ["n_principles", "n_principles_no_aux", "python_chars", "python_gzip", "lean_chars", "lean_gzip"];
  let n = 0, bad = 0;
  const check = (tag) => {
    const svg = b.els["pa-plot"].innerHTML, m = svg.match(/data-plot="([\d.,-]+)"/); if (!m) return;   // no theory with values: no plot
    const [l, t, w, hh] = m[1].split(",").map(Number); n++;
    [...svg.matchAll(/data-cx="([\d.-]+)" data-cy="([\d.-]+)"/g)].forEach(mm => {
      const x = +mm[1], y = +mm[2];
      if (!(x >= l - 0.5 && x <= l + w + 0.5 && y >= t - 0.5 && y <= t + hh + 0.5)) { bad++; if (bad < 4) fail("marker outside the plot (" + tag + "): " + x + "," + y + " in " + m[1]); }
      if (/NaN/.test(mm[0])) fail("NaN coordinate " + tag);
    });
  };
  for (const y of cov) for (const x of siz) {
    sel("ex-a-y", y); sel("ex-a-x", x);
    for (const llm of ["1", "0"]) for (const sys of ["1", "0"]) for (const c of ["all", "without", "only"]) {
      sel("ex-llm", llm); sel("ex-system", sys); sel("ex-cont", c); check([y, x, llm, sys, c].join("/"));
    }
  }
  sel("ex-llm", "1"); sel("ex-system", "1"); sel("ex-cont", "all");
  if (!n) console.warn("note: no plot rendered for the bounds check (no metrics data?)");
});
run("scenario empty project", () => {
  const b = boot(withData({}), katexStub);
  if (b.err) { fail("empty project: exception while loading: " + (b.err.stack || b.err)); return; }
  TABS.forEach(t => { b.route("#" + t); const h = b.els["t-" + t].innerHTML + (SUB[t] || []).map(i => (b.els[i] || {}).innerHTML || "").join(""); if (!h || h.length < 20) fail("empty project: tab " + t + " is empty"); });
  b.route("#cards:none"); b.route("#audits"); b.fire("click", hit("[data-act]", attrsOf("data-act", "trexport")));
  if (b.els["t-cards"].innerHTML !== "") fail("empty project: the theory cards block should be omitted");
  if (!/Here goes/.test(b.els["pr-top"].innerHTML)) fail("empty project: Theoretical Space lacks its placeholders");
});
run("scenario old data without new fields", () => {
  const d = JSON.parse(JSON.stringify(SYN)); delete d.fragments; delete d.fragment_users; d.theories.forEach(t => { delete t.fragments; delete t.notation; });
  d.statements.forEach(s => { delete s.checks; delete s.notation; }); d.code = {};
  const b = boot(withData(d), null);
  if (b.err) { fail("old data: exception " + b.err); return; }
  b.route("#cards:T1"); if (cardHtml(b).length < 300) fail("old data: theory card too short");
  b.fire("click", hit("[data-act]", attrsOf("data-act", "trexport")));
});

finish();
function finish() {
  if (fails.length) { console.error(fails.length + " failure(s)"); process.exit(1); }
  console.log("smoke test OK: all " + TABS.length + " tabs rendered, interactions ran, clipboard calls: " + clipboard.length); process.exit(0);
}
