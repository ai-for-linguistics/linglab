#!/usr/bin/env node
// Optional behaviour check in a real browser (headless Chrome through the DevTools protocol; no dependency).
// Usage: node browser_check.mjs path/to/report.html      (CHROME=/path/to/chrome to choose the browser; skipped when none is found)
// Checks what the DOM stub of smoke_test.js cannot: browser history and scroll restoration, the panel closing on navigation,
// the theory cards block of Theoretical Space, sticky band and tabs, the plot and its controls visible in the viewport.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const page = process.argv[2];
if (!page) { console.error("usage: node browser_check.mjs report.html"); process.exit(2); }
const CANDIDATES = [process.env.CHROME, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"].filter(Boolean);
const chrome = CANDIDATES.find(p => existsSync(p));
if (!chrome) { console.log("browser check skipped: no Chrome found (set CHROME=/path/to/chrome)"); process.exit(0); }
const port = 9400 + Math.floor(Math.random() * 400);
const ch = spawn(chrome, ["--headless=new", "--remote-debugging-port=" + port, "--window-size=1400,900", "--user-data-dir=" + mkdtempSync(join(tmpdir(), "linglab-")), "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets = [];
for (let i = 0; i < 50; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch (e) {} await sleep(200); }
const t = targets.find(x => x.type === "page");
if (!t) { console.log("browser check skipped: could not reach the browser"); ch.kill(); process.exit(0); }
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => (ws.onopen = r));
let id = 0; const pend = {};
ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend[d.id]) { pend[d.id](d); delete pend[d.id]; } };
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true }); if (r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails)); return r.result.result.value; };
const fails = [];
const ok = (name, cond, info) => { if (!cond) fails.push(name + (info !== undefined ? " " + JSON.stringify(info) : "")); };
const view = (w, h, mobile) => send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: !!mobile });
await send("Page.enable"); await send("Page.navigate", { url: "file://" + resolve(page) }); await sleep(1500); await view(1400, 900); await sleep(300);
const nav = tab => ev(`document.querySelector('nav a[data-tab="${tab}"]').click()`);
// history: every tab click is an entry; back restores the tab and the scroll position
await nav("empirical"); await sleep(250);
await ev(`document.body.style.minHeight='3000px'`); await ev(`window.scrollTo(0,420)`); await sleep(100);
await nav("matrix"); await sleep(250);
ok("tab click pushes a history entry", (await ev(`location.hash`)) === "#matrix");
await ev(`history.back()`); await sleep(500);
ok("back returns to the previous tab", (await ev(`location.hash`)) === "#empirical");
ok("back restores the scroll position", Math.abs((await ev(`Math.round(window.scrollY)`)) - 420) < 4);
// panel closes on any navigation
await nav("matrix"); await sleep(250);
if (await ev(`!!document.querySelector('td.cell')`)) {
  await ev(`document.querySelector('td.cell').click()`); await sleep(100);
  ok("a cell opens the panel", await ev(`document.getElementById('pop').style.display==='block'`));
  await nav("overview"); await sleep(250);
  ok("navigation closes the panel", await ev(`document.getElementById('pop').style.display!=='block'`));
}
// theory cards: the last block of Theoretical Space
const first = await ev(`(document.querySelector('#t-cards .sub button')||{dataset:{}}).dataset.card||''`);
if (first) {
  await ev(`location.hash='#cards:${first}'`); await sleep(500);
  ok("#cards:ID opens Theoretical Space", await ev(`document.getElementById('t-principles').classList.contains('on')`));
  ok("the theory is selected", (await ev(`document.querySelector('#t-cards .sub button.on, #t-cards select').dataset?.card||document.querySelector('#t-cards select').value`)) === first);
  const topC = await ev(`(Math.round(document.getElementById('t-cards').getBoundingClientRect().top)||0)`);
  ok("the cards block is scrolled into view", topC < 450, topC);
  await ev(`location.hash='#audits'`); await sleep(300);
  ok("old #audits links still work", await ev(`document.getElementById('t-principles').classList.contains('on')`));
}
// sticky band, then tabs
await ev(`location.hash='#matrix'`); await sleep(300); await ev(`window.scrollTo(0,600)`); await sleep(200);
const st = await ev(`(function(){var b=document.getElementById('band').getBoundingClientRect(),n=document.getElementById('top').getBoundingClientRect();return {band:Math.round(b.top)||0,nav:Math.round(n.top)||0,bandH:Math.round(b.height)}})()`);
ok("band sticks at the top, tabs just below", st.band === 0 && Math.abs(st.nav - st.bandH) < 2, st);
// the plot and its controls fit in the viewport
for (const h of [800, 1000]) {
  await view(1400, h); await ev(`location.hash='#pareto'`); await sleep(400); await ev(`window.scrollTo(0,0)`);
  await ev(`window.scrollTo(0, document.querySelector('.pareto-main').getBoundingClientRect().top + scrollY - document.getElementById('band').offsetHeight - document.getElementById('top').offsetHeight - 6)`); await sleep(200);
  const p = await ev(`(function(){var m=document.querySelector('.pp-x').getBoundingClientRect(),y=document.querySelector('.pp-yrot').getBoundingClientRect();return {bottom:Math.round(m.bottom),top:Math.round(y.top),vh:innerHeight}})()`);
  ok("plot and controls visible at height " + h, p.bottom <= p.vh && p.top >= 0, p);
}
ch.kill();
if (fails.length) { console.error(fails.map(f => "FAIL: " + f).join("\n")); console.error(fails.length + " failure(s)"); process.exit(1); }
console.log("browser check OK");
process.exit(0);
