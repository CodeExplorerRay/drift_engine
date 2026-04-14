# ruff: noqa: E501

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

router = APIRouter(tags=["ui"])

FAVICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0f172a"/>
  <path d="M16 39 L27 28 L36 35 L49 21" fill="none" stroke="#38bdf8"
        stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M16 46 H50" fill="none" stroke="#64748b" stroke-width="4"
        stroke-linecap="round"/>
  <circle cx="16" cy="39" r="4" fill="#22c55e"/>
  <circle cx="27" cy="28" r="4" fill="#f59e0b"/>
  <circle cx="36" cy="35" r="4" fill="#38bdf8"/>
  <circle cx="49" cy="21" r="4" fill="#ef4444"/>
</svg>
"""

UI_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>System Drift Engine</title>
  <link rel="icon" href="/favicon.ico" type="image/svg+xml" />
  <style>
    :root {
      --bg: #f5f7fb;
      --card: #ffffff;
      --ink: #0f172a;
      --muted: #64748b;
      --line: #dbe3ef;
      --nav: #08111f;
      --brand: #0369a1;
      --brand-2: #0ea5e9;
      --green: #16a34a;
      --amber: #d97706;
      --red: #dc2626;
      --shadow: 0 20px 55px rgba(15, 23, 42, 0.08);
      --radius: 18px;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 72% -12%, rgba(14, 165, 233, 0.16), transparent 30rem),
        linear-gradient(180deg, #fbfdff 0%, var(--bg) 44%, #edf3fa 100%);
      font-family: "Aptos", "Segoe UI Variable Text", "Segoe UI", sans-serif;
    }
    button, input, select { font: inherit; }
    a { color: inherit; }
    button:focus-visible, input:focus-visible, select:focus-visible, a:focus-visible {
      outline: 3px solid rgba(14, 165, 233, 0.35);
      outline-offset: 2px;
    }
    .shell { display: grid; grid-template-columns: 280px minmax(0, 1fr); min-height: 100vh; }
    .sidebar {
      position: sticky;
      top: 0;
      display: flex;
      flex-direction: column;
      gap: 24px;
      height: 100vh;
      padding: 24px;
      color: #dbeafe;
      background: linear-gradient(180deg, rgba(14, 165, 233, 0.14), transparent 22rem), var(--nav);
      border-right: 1px solid rgba(148, 163, 184, 0.18);
    }
    .brand { display: grid; grid-template-columns: 46px 1fr; gap: 12px; align-items: center; }
    .mark {
      display: grid;
      width: 46px;
      height: 46px;
      place-items: center;
      border-radius: 14px;
      background: linear-gradient(135deg, var(--brand-2), #2563eb);
      box-shadow: 0 18px 42px rgba(14, 165, 233, 0.3);
      color: #fff;
      font-weight: 900;
    }
    .brand h1 { margin: 0; font-size: 1rem; letter-spacing: -0.03em; }
    .brand p, .nav-label { margin: 2px 0 0; color: #94a3b8; font-size: 0.75rem; }
    .nav { display: grid; gap: 6px; }
    .nav-label { margin-top: 4px; font-weight: 850; letter-spacing: 0.1em; text-transform: uppercase; }
    .nav a {
      display: flex;
      gap: 10px;
      align-items: center;
      min-height: 38px;
      padding: 0 12px;
      border-radius: 12px;
      color: #cbd5e1;
      font-size: 0.9rem;
      font-weight: 760;
      text-decoration: none;
    }
    .nav a:hover { background: rgba(148, 163, 184, 0.13); color: #fff; }
    .dot { width: 8px; height: 8px; border-radius: 99px; background: var(--brand-2); }
    .side-card {
      display: grid;
      gap: 8px;
      margin-top: auto;
      padding: 16px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 18px;
      background: rgba(15, 23, 42, 0.62);
      color: #94a3b8;
      font-size: 0.83rem;
      line-height: 1.5;
    }
    .side-card strong { color: #fff; }
    .workspace { min-width: 0; padding: 24px; }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      gap: 18px;
      align-items: center;
      justify-content: space-between;
      min-height: 70px;
      margin: -24px -24px 22px;
      padding: 14px 24px;
      border-bottom: 1px solid rgba(203, 213, 225, 0.75);
      background: rgba(248, 251, 255, 0.88);
      backdrop-filter: blur(18px);
    }
    .crumb span, label {
      color: var(--muted);
      font-size: 0.73rem;
      font-weight: 850;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .crumb strong { display: block; margin-top: 2px; font-size: 1.14rem; letter-spacing: -0.03em; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end; }
    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 0 14px;
      border: 1px solid transparent;
      border-radius: 12px;
      background: var(--ink);
      color: #fff;
      cursor: pointer;
      font-size: 0.86rem;
      font-weight: 850;
      text-decoration: none;
      transition: transform 160ms ease, box-shadow 160ms ease;
    }
    .button:hover { transform: translateY(-1px); box-shadow: 0 12px 24px rgba(15, 23, 42, 0.14); }
    .button.secondary { border-color: var(--line); background: #fff; color: var(--ink); }
    .button.brand { background: var(--brand); }
    .button.warn { background: var(--amber); }
    .button:disabled { cursor: not-allowed; opacity: 0.52; transform: none; box-shadow: none; }
    .link-button {
      border: 0;
      background: transparent;
      color: var(--brand);
      cursor: pointer;
      font-weight: 850;
      padding: 0;
      text-align: left;
    }
    .hero, .panel, .metric {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.94);
      box-shadow: var(--shadow);
    }
    .overview { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr); gap: 18px; }
    .hero { position: relative; overflow: hidden; padding: 28px; }
    .hero:after {
      position: absolute;
      right: -80px;
      top: -110px;
      width: 270px;
      height: 270px;
      border-radius: 999px;
      background: rgba(14, 165, 233, 0.12);
      content: "";
    }
    .eyebrow {
      display: inline-flex;
      gap: 8px;
      align-items: center;
      padding: 7px 10px;
      border: 1px solid var(--line);
      border-radius: 99px;
      background: #f8fafc;
      color: var(--brand);
      font-size: 0.72rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .pulse {
      width: 8px;
      height: 8px;
      border-radius: 99px;
      background: var(--green);
      box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.45);
      animation: pulse 1.9s infinite;
    }
    .hero h2 {
      position: relative;
      max-width: 800px;
      margin: 18px 0 10px;
      font-size: clamp(2rem, 4vw, 4.1rem);
      line-height: 0.98;
      letter-spacing: -0.065em;
    }
    .hero p { position: relative; max-width: 760px; margin: 0; color: var(--muted); line-height: 1.7; }
    .hero .actions { position: relative; justify-content: flex-start; margin-top: 22px; }
    .metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .metric { display: grid; gap: 6px; min-height: 132px; padding: 18px; }
    .metric span { color: var(--muted); font-size: 0.74rem; font-weight: 850; text-transform: uppercase; }
    .metric strong { font-size: clamp(1.8rem, 3vw, 2.7rem); letter-spacing: -0.06em; }
    .metric em { color: var(--muted); font-size: 0.8rem; font-style: normal; line-height: 1.4; }
    .command-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin: 18px 0; }
    .content-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(340px, 0.42fr); gap: 18px; align-items: start; }
    .stack { display: grid; gap: 18px; }
    .section { scroll-margin-top: 92px; }
    .panel { overflow: hidden; }
    .panel-header {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      justify-content: space-between;
      padding: 18px;
      border-bottom: 1px solid var(--line);
    }
    .panel h2, .panel h3 { margin: 0; font-size: 1rem; letter-spacing: -0.02em; }
    .panel p { margin: 4px 0 0; color: var(--muted); font-size: 0.84rem; line-height: 1.45; }
    .panel-body { padding: 18px; }
    .form { display: grid; gap: 12px; }
    label { display: grid; gap: 6px; }
    input, select {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      color: var(--ink);
      padding: 0 12px;
      font-size: 0.9rem;
    }
    .check { display: flex; gap: 9px; align-items: center; color: var(--ink); text-transform: none; }
    .check input { width: auto; min-height: auto; }
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th {
      padding: 11px 12px;
      border-bottom: 1px solid #cbd5e1;
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-align: left;
      text-transform: uppercase;
      white-space: nowrap;
    }
    td { padding: 13px 12px; border-bottom: 1px solid var(--line); color: #243047; vertical-align: top; }
    tr:last-child td { border-bottom: 0; }
    tbody tr:hover { background: #f8fafc; }
    .cell { display: grid; gap: 4px; min-width: 170px; }
    .cell strong { color: var(--ink); }
    .cell span, .mono {
      color: var(--muted);
      font-family: "Cascadia Mono", "Consolas", monospace;
      font-size: 0.76rem;
      word-break: break-all;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 0 9px;
      border-radius: 99px;
      background: #eef2f7;
      color: #475569;
      font-size: 0.73rem;
      font-weight: 900;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .pill.good { background: rgba(22, 163, 74, 0.1); color: var(--green); }
    .pill.warn { background: rgba(217, 119, 6, 0.1); color: var(--amber); }
    .pill.bad { background: rgba(220, 38, 38, 0.1); color: var(--red); }
    .pill.info { background: rgba(14, 165, 233, 0.1); color: var(--brand); }
    .row-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .empty { display: grid; place-items: center; min-height: 110px; padding: 16px; color: var(--muted); text-align: center; }
    .cards, .log { display: grid; gap: 10px; max-height: 420px; overflow: auto; }
    .info {
      display: grid;
      gap: 8px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #f8fafc;
    }
    .info strong { font-size: 0.92rem; }
    .info p { margin: 0; color: var(--muted); font-size: 0.82rem; line-height: 1.5; }
    .split { display: flex; gap: 10px; align-items: center; justify-content: space-between; }
    .toast {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 50;
      display: none;
      max-width: min(480px, calc(100vw - 36px));
      padding: 13px 15px;
      border-radius: 14px;
      background: #0f172a;
      box-shadow: var(--shadow);
      color: #fff;
      font-size: 0.88rem;
      font-weight: 750;
    }
    .toast.show { display: block; }
    @keyframes pulse {
      70% { box-shadow: 0 0 0 12px rgba(22, 163, 74, 0); }
      100% { box-shadow: 0 0 0 0 rgba(22, 163, 74, 0); }
    }
    @media (max-width: 1180px) {
      .shell, .overview, .content-grid, .command-grid { grid-template-columns: 1fr; }
      .sidebar { position: static; height: auto; }
      .side-card { margin-top: 0; }
    }
    @media (max-width: 760px) {
      .workspace { padding: 16px; }
      .topbar { position: static; align-items: flex-start; margin: -16px -16px 16px; flex-direction: column; }
      .metrics { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar" aria-label="Primary navigation">
      <div class="brand">
        <div class="mark" aria-hidden="true">DE</div>
        <div><h1>System Drift Engine</h1><p>Operator Console</p></div>
      </div>
      <nav class="nav" aria-label="Dashboard sections">
        <p class="nav-label">Workspace</p>
        <a href="#overview"><span class="dot"></span>Overview</a>
        <a href="#reports"><span class="dot"></span>Drift reports</a>
        <a href="#remediation"><span class="dot"></span>Remediation</a>
        <a href="#baselines"><span class="dot"></span>Baselines</a>
        <a href="#collectors"><span class="dot"></span>Collectors</a>
        <a href="#integrations"><span class="dot"></span>Integrations</a>
        <a href="#jobs"><span class="dot"></span>Scheduled jobs</a>
        <a href="#audit"><span class="dot"></span>Audit trail</a>
      </nav>
      <div class="side-card">
        <strong id="nav-health">Checking service health</strong>
        <span id="nav-health-detail">Live API state, dry-run remediation, and audit telemetry.</span>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div class="crumb"><span>Production operations</span><strong>Drift posture control</strong></div>
        <div class="actions">
          <span class="pill info" id="api-state">Connecting</span>
          <a class="button secondary" href="/docs">API docs</a>
          <button class="button brand" id="refresh-button" type="button">Refresh dashboard</button>
        </div>
      </header>

      <section class="section overview" id="overview">
        <div class="hero">
          <span class="eyebrow"><span class="pulse"></span>Live posture</span>
          <h2>Control configuration drift before it becomes an incident.</h2>
          <p>
            Monitor collectors, baselines, drift reports, remediation approvals, and audit activity
            from one operator-focused console.
          </p>
          <div class="actions">
            <button class="button brand" data-scroll-target="reports" type="button">Review drift</button>
            <button class="button secondary" data-scroll-target="remediation" type="button">Open approvals</button>
            <button class="button secondary" data-scroll-target="integrations" type="button">Check integrations</button>
          </div>
        </div>
        <div class="metrics">
          <div class="metric"><span>Risk score</span><strong id="kpi-risk">-</strong><em id="kpi-risk-detail">Waiting for reports</em></div>
          <div class="metric"><span>Open findings</span><strong id="kpi-findings">-</strong><em id="kpi-findings-detail">High and critical drift</em></div>
          <div class="metric"><span>Collectors ready</span><strong id="kpi-collectors">-</strong><em id="kpi-collectors-detail">No collector data yet</em></div>
          <div class="metric"><span>Pending approvals</span><strong id="kpi-remediation">-</strong><em id="kpi-remediation-detail">No remediation queue yet</em></div>
        </div>
      </section>

      <section class="command-grid" aria-label="Operator actions">
        <article class="panel">
          <div class="panel-header"><div><h2>Run drift scan</h2><p>Compare current state against a baseline.</p></div></div>
          <div class="panel-body">
            <form class="form" id="scan-form">
              <label>Baseline<select id="scan-baseline" required></select></label>
              <label>Collectors<input id="scan-collectors" placeholder="file,package,kubernetes" /></label>
              <label class="check"><input id="scan-auto-remediate" type="checkbox" />Auto-remediate after scan</label>
              <button class="button brand" type="submit">Run scan</button>
            </form>
          </div>
        </article>
        <article class="panel">
          <div class="panel-header"><div><h2>Capture baseline</h2><p>Create a baseline from currently collected resources.</p></div></div>
          <div class="panel-body">
            <form class="form" id="baseline-form">
              <label>Name<input id="baseline-name" placeholder="prod-platform" required /></label>
              <label>Version<input id="baseline-version" value="1.0.0" required /></label>
              <label>Collectors<input id="baseline-collectors" placeholder="file,package,service" /></label>
              <button class="button" type="submit">Capture baseline</button>
            </form>
          </div>
        </article>
        <article class="panel">
          <div class="panel-header"><div><h2>Kubernetes readiness</h2><p>Validate cluster access before Kubernetes scans.</p></div></div>
          <div class="panel-body">
            <form class="form" id="kubernetes-form">
              <label>Namespaces<input id="kubernetes-namespaces" placeholder="default,platform" /></label>
              <button class="button secondary" type="submit">Check Kubernetes</button>
              <div class="info" id="kubernetes-result">
                <strong>No check run yet</strong>
                <p>Works with kind, minikube, or a remote cluster.</p>
              </div>
            </form>
          </div>
        </article>
        <article class="panel">
          <div class="panel-header"><div><h2>Create job</h2><p>Schedule recurring drift scans.</p></div></div>
          <div class="panel-body">
            <form class="form" id="job-form">
              <label>Job name<input id="job-name" placeholder="prod-hourly" required /></label>
              <label>Baseline<select id="job-baseline" required></select></label>
              <label>Interval seconds<input id="job-interval" min="60" type="number" value="3600" required /></label>
              <label>Collectors<input id="job-collectors" placeholder="file,package,kubernetes" /></label>
              <button class="button" type="submit">Create job</button>
            </form>
          </div>
        </article>
      </section>

      <div class="content-grid">
        <div class="stack">
          <section class="section panel" id="reports">
            <div class="panel-header"><div><h2>Report history</h2><p>Recent scans, risk scores, and remediation entry points.</p></div><span class="pill info" id="selected-report-pill">No report selected</span></div>
            <div class="table-wrap"><table><thead><tr><th>Report</th><th>Risk</th><th>Findings</th><th>Generated</th><th>Actions</th></tr></thead><tbody id="reports-body"></tbody></table></div>
          </section>
          <section class="section panel" id="findings">
            <div class="panel-header"><div><h2>Findings</h2><p>Resource-level drift from the selected or latest report.</p></div></div>
            <div class="table-wrap"><table><thead><tr><th>Resource</th><th>Type</th><th>Severity</th><th>Path</th><th>Status</th></tr></thead><tbody id="findings-body"></tbody></table></div>
          </section>
          <section class="section panel" id="baselines">
            <div class="panel-header"><div><h2>Baselines</h2><p>Declared state used as the drift source of truth.</p></div></div>
            <div class="table-wrap"><table><thead><tr><th>Baseline</th><th>Version</th><th>Resources</th><th>Checksum</th><th>Created</th></tr></thead><tbody id="baselines-body"></tbody></table></div>
          </section>
          <section class="section panel" id="collectors">
            <div class="panel-header"><div><h2>Collectors</h2><p>Enabled local, Kubernetes, and cloud inventory collectors.</p></div></div>
            <div class="table-wrap"><table><thead><tr><th>Collector</th><th>Resource type</th><th>Status</th><th>Integration</th><th>Description</th></tr></thead><tbody id="collectors-body"></tbody></table></div>
          </section>
          <section class="section panel" id="jobs">
            <div class="panel-header"><div><h2>Scheduled jobs</h2><p>Recurring scans and latest run state.</p></div></div>
            <div class="table-wrap"><table><thead><tr><th>Job</th><th>Interval</th><th>Next run</th><th>Last run</th><th>Actions</th></tr></thead><tbody id="jobs-body"></tbody></table></div>
          </section>
        </div>

        <div class="stack">
          <section class="section panel" id="integrations">
            <div class="panel-header"><div><h2>Integrations</h2><p>Readiness and missing configuration for external systems.</p></div></div>
            <div class="panel-body"><div class="cards" id="integrations-list"></div></div>
          </section>
          <section class="section panel" id="remediation">
            <div class="panel-header"><div><h2>Remediation queue</h2><p>Approval-gated actions generated from drift reports.</p></div></div>
            <div class="panel-body">
              <div class="row-actions" style="margin-bottom: 12px;">
                <button class="button secondary" id="plan-selected-report" type="button">Plan remediation</button>
                <button class="button warn" id="execute-selected-report" type="button">Execute approved</button>
              </div>
              <div class="cards" id="remediation-list"></div>
            </div>
          </section>
          <section class="section panel" id="audit">
            <div class="panel-header"><div><h2>Audit trail</h2><p>Recent actor, action, target, and correlation events.</p></div></div>
            <div class="panel-body"><div class="log" id="audit-log"></div></div>
          </section>
          <section class="panel">
            <div class="panel-header"><div><h2>Activity log</h2><p>Browser-side workflow updates from this console session.</p></div></div>
            <div class="panel-body"><div class="log" id="activity-log"></div></div>
          </section>
        </div>
      </div>
    </main>
  </div>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>

  <script>
    const state = {health:null, collectors:[], integrations:[], baselines:[],
      reports:[], jobs:[], runs:[], actions:[], audit:[], selectedReportId:null, errors:[]};
    const $ = (id) => document.getElementById(id);
    function esc(v) {
      const m = {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'};
      return String(v ?? '').replace(/[&<>"']/g, (c) => m[c]);
    }
    function csv(v) {
      const out = String(v || '').split(',').map((x) => x.trim()).filter(Boolean);
      return out.length ? out : null;
    }
    function short(v, n = 12) {
      const text = String(v || '');
      return text.length > n ? `${text.slice(0, n)}...` : text || '-';
    }
    function when(v) {
      if (!v) return 'Never';
      const date = new Date(v);
      return Number.isNaN(date.getTime()) ? String(v) : date.toLocaleString();
    }
    function cls(status) {
      const value = String(status || '').toLowerCase();
      if (['ok','ready','passed','enabled','succeeded','approved'].includes(value)) return 'good';
      if (['warning','degraded','missing_configuration','planned','waiting_approval'].includes(value)) return 'warn';
      if (['failed','error','not_ready','disabled','critical'].includes(value)) return 'bad';
      return 'info';
    }
    function sev(severity) {
      const value = String(severity || '').toLowerCase();
      if (['critical','high'].includes(value)) return 'bad';
      if (value === 'medium') return 'warn';
      return 'info';
    }
    function activity(message) {
      const entry = document.createElement('div');
      entry.className = 'info';
      entry.innerHTML = `<strong>${esc(message)}</strong><p>${esc(new Date().toLocaleString())}</p>`;
      $('activity-log').prepend(entry);
      $('toast').textContent = message;
      $('toast').className = 'toast show';
      window.setTimeout(() => {$('toast').className = 'toast';}, 3200);
    }
    async function json(path, options = {}) {
      const headers = {'Content-Type':'application/json', ...(options.headers || {})};
      const response = await fetch(path, {...options, headers});
      const text = await response.text();
      let body = null;
      if (text) { try { body = JSON.parse(text); } catch { body = text; } }
      if (!response.ok) {
        const detail = typeof body === 'object' && body !== null
          ? body.detail || body.error || JSON.stringify(body)
          : body || response.statusText;
        throw new Error(detail);
      }
      return body;
    }
    async function optional(path, fallback) {
      try { return await json(path); }
      catch (error) { state.errors.push(`${path}: ${error.message}`); return fallback; }
    }
    function selectedReport() {
      return state.reports.find((r) => r.id === state.selectedReportId) || state.reports[0] || null;
    }
    function actionReportId(action) {
      const report = state.reports.find((r) =>
        (r.findings || []).some((finding) => finding.id === action.finding_id));
      return report ? report.id : state.selectedReportId;
    }
    function empty(id, cols, message) {
      $(id).innerHTML = `<tr><td colspan="${cols}"><div class="empty">${esc(message)}</div></td></tr>`;
    }
    function renderHealth() {
      const status = state.health?.status || 'not_ready';
      const details = state.health?.details || {};
      $('api-state').textContent = status;
      $('api-state').className = `pill ${cls(status)}`;
      $('nav-health').textContent = status === 'ready' ? 'Service ready' : 'Service checking';
      $('nav-health-detail').textContent = [
        details.environment ? `Environment: ${details.environment}` : null,
        details.storage_backend ? `Storage: ${details.storage_backend}` : null,
        state.errors.length ? `${state.errors.length} optional endpoint issue(s)` : null
      ].filter(Boolean).join(' | ') || 'API, collectors, and dashboard shell are reachable.';
    }
    function renderMetrics() {
      const report = selectedReport();
      const findings = report?.findings || [];
      const severe = findings.filter((f) => ['critical','high'].includes(String(f.severity).toLowerCase()));
      const ready = state.collectors.filter((c) => c.enabled && ['ready','ok'].includes(String(c.status).toLowerCase()));
      const pending = state.actions.filter((a) => ['planned','waiting_approval'].includes(String(a.status).toLowerCase()));
      $('kpi-risk').textContent = report ? Math.round(Number(report.risk_score || 0)) : '0';
      $('kpi-risk-detail').textContent = report ? `Latest report ${short(report.id, 14)}` : 'No report yet';
      $('kpi-findings').textContent = severe.length;
      $('kpi-findings-detail').textContent = report ? `${findings.length} total finding(s)` : 'Run a scan';
      $('kpi-collectors').textContent = `${ready.length}/${state.collectors.length}`;
      $('kpi-collectors-detail').textContent = state.collectors.length ? 'Ready enabled collectors' : 'No collectors';
      $('kpi-remediation').textContent = pending.length;
      $('kpi-remediation-detail').textContent = state.actions.length ? `${state.actions.length} queued action(s)` : 'No plan yet';
    }
    function renderBaselineOptions() {
      const options = state.baselines.map((b) =>
        `<option value="${esc(b.id)}">${esc(b.name)} (${esc(b.version)})</option>`).join('');
      const blank = '<option value="">Create a baseline first</option>';
      $('scan-baseline').innerHTML = options || blank;
      $('job-baseline').innerHTML = options || blank;
      $('scan-baseline').disabled = !options;
      $('job-baseline').disabled = !options;
    }
    function renderBaselines() {
      if (!state.baselines.length) return empty('baselines-body', 5, 'No baselines yet.');
      $('baselines-body').innerHTML = state.baselines.map((b) => `
        <tr><td><div class="cell"><strong>${esc(b.name)}</strong><span>${esc(b.id)}</span></div></td>
        <td>${esc(b.version)}</td><td>${Object.keys(b.resources || {}).length}</td>
        <td><span class="mono">${esc(short(b.checksum, 18))}</span></td>
        <td>${esc(when(b.created_at))}</td></tr>`).join('');
    }
    function renderCollectors() {
      if (!state.collectors.length) return empty('collectors-body', 5, 'No collectors registered.');
      $('collectors-body').innerHTML = state.collectors.map((c) => `
        <tr><td><div class="cell"><strong>${esc(c.name)}</strong><span>${esc(c.enabled ? 'enabled' : 'disabled')}</span></div></td>
        <td>${esc(c.resource_type)}</td><td><span class="pill ${cls(c.status)}">${esc(c.status || 'local')}</span></td>
        <td>${esc(c.integration || 'local')}</td><td>${esc(c.description || 'Local source')}</td></tr>`).join('');
    }
    function renderIntegrations() {
      if (!state.integrations.length) {
        $('integrations-list').innerHTML = '<div class="empty">No integrations found.</div>';
        return;
      }
      $('integrations-list').innerHTML = state.integrations.map((i) => `
        <div class="info"><div class="split"><strong>${esc(i.display_name || i.name)}</strong>
        <span class="pill ${cls(i.status)}">${esc(i.status)}</span></div>
        <p>${esc(i.description)}</p><p><strong>Collector:</strong> ${esc(i.collector_name)}</p>
        <p><strong>Resources:</strong> ${esc((i.resource_types || []).join(', ') || 'None')}</p>
        <p><strong>Missing:</strong> ${esc((i.missing || []).join(', ') || 'None')}</p>
        <p>${esc(i.setup_hint || '')}</p></div>`).join('');
    }
    function renderReports() {
      const selected = selectedReport();
      $('selected-report-pill').textContent = selected ? `Selected ${short(selected.id, 16)}` : 'No report selected';
      if (!state.reports.length) return empty('reports-body', 5, 'No drift reports yet. Run a scan.');
      $('reports-body').innerHTML = state.reports.map((r) => {
        const s = r.summary || {};
        const total = s.total ?? (r.findings || []).length;
        return `<tr><td><div class="cell"><strong>${esc(short(r.id, 18))}</strong>
        <span>baseline ${esc(short(r.baseline_id, 18))}</span></div></td>
        <td><span class="pill ${Number(r.risk_score || 0) >= 70 ? 'bad' : 'warn'}">${Math.round(Number(r.risk_score || 0))}</span></td>
        <td>${esc(total)} <span class="mono">A:${esc(s.added || 0)} M:${esc(s.modified || 0)} R:${esc(s.removed || 0)}</span></td>
        <td>${esc(when(r.generated_at))}</td><td><div class="row-actions">
        <button class="link-button" data-action="select-report" data-report-id="${esc(r.id)}" type="button">${r.id === selected?.id ? 'Selected' : 'Select'}</button>
        <button class="link-button" data-action="plan-report" data-report-id="${esc(r.id)}" type="button">Plan</button>
        <button class="link-button" data-action="execute-report" data-report-id="${esc(r.id)}" type="button">Execute approved</button>
        </div></td></tr>`;
      }).join('');
    }
    function renderFindings() {
      const findings = selectedReport()?.findings || [];
      if (!findings.length) return empty('findings-body', 5, 'No findings for the selected report.');
      $('findings-body').innerHTML = findings.map((f) => `
        <tr><td><div class="cell"><strong>${esc(short(f.resource_key, 42))}</strong><span>${esc(short(f.fingerprint, 26))}</span></div></td>
        <td>${esc(f.drift_type)} / ${esc(f.resource_type)}</td>
        <td><span class="pill ${sev(f.severity)}">${esc(f.severity)}</span></td>
        <td><span class="mono">${esc(f.path || '/')}</span></td><td>${esc(f.status)}</td></tr>`).join('');
    }
    function renderJobs() {
      if (!state.jobs.length) return empty('jobs-body', 5, 'No scheduled jobs yet. Create job to schedule scans.');
      $('jobs-body').innerHTML = state.jobs.map((j) => `
        <tr><td><div class="cell"><strong>${esc(j.name)}</strong><span>${esc(j.id)}</span></div></td>
        <td>${esc(j.interval_seconds)}s</td><td>${esc(when(j.next_run_at))}</td>
        <td>${esc(when(j.last_run_at))}</td><td><button class="link-button" data-action="run-job" data-job-id="${esc(j.id)}" type="button">Run now</button></td></tr>`).join('');
    }
    function renderRemediation() {
      if (!state.actions.length) {
        $('remediation-list').innerHTML = '<div class="empty">No remediation actions yet. Select a report and create a plan.</div>';
        return;
      }
      $('remediation-list').innerHTML = state.actions.map((a) => {
        const reportId = actionReportId(a);
        const approved = ['approved','skipped','succeeded'].includes(a.status);
        return `<div class="info"><div class="split"><strong>${esc(a.strategy)}</strong>
        <span class="pill ${cls(a.status)}">${esc(a.status)}</span></div><p>${esc(a.description)}</p>
        <p><strong>Risk:</strong> ${esc(Math.round(Number(a.risk_score || 0)))}
        | <strong>Dry run:</strong> ${esc(a.dry_run ? 'yes' : 'no')}
        | <strong>Approval:</strong> ${esc(a.requires_approval ? 'required' : 'auto')}</p>
        <div class="row-actions"><button class="button secondary" data-action="approve-action"
        data-action-id="${esc(a.id)}" type="button" ${approved ? 'disabled' : ''}>Approve action</button>
        <button class="button warn" data-action="execute-report" data-report-id="${esc(reportId || '')}"
        type="button" ${reportId ? '' : 'disabled'}>Execute approved</button></div></div>`;
      }).join('');
    }
    function renderAudit() {
      if (!state.audit.length) {
        $('audit-log').innerHTML = '<div class="empty">No audit events yet.</div>';
        return;
      }
      $('audit-log').innerHTML = state.audit.map((e) => `
        <div class="info"><strong>${esc(e.action || 'audit.event')}</strong>
        <p>${esc(e.actor_id || 'unknown actor')} -> ${esc(e.target_type || 'target')} ${esc(short(e.target_id, 20))}</p>
        <p>${esc(when(e.created_at))}</p></div>`).join('');
    }
    function renderAll() {
      renderHealth(); renderMetrics(); renderBaselineOptions(); renderBaselines();
      renderCollectors(); renderIntegrations(); renderReports(); renderFindings();
      renderJobs(); renderRemediation(); renderAudit();
    }
    async function refreshData({quiet = false} = {}) {
      $('refresh-button').disabled = true;
      $('refresh-button').textContent = 'Refreshing';
      state.errors = [];
      try {
        const [health, collectors, integrations, baselines, reports, jobs, runs, actions, audit] =
          await Promise.all([
            optional('/health/ready', {status:'not_ready', details:{}}),
            optional('/collectors', []), optional('/integrations', []),
            optional('/baselines', []), optional('/drifts?limit=50', []),
            optional('/jobs', []), optional('/jobs/runs?limit=50', []),
            optional('/remediation/actions', []), optional('/audit?limit=50', [])
          ]);
        Object.assign(state, {health, collectors, integrations, baselines, reports, jobs, runs, actions, audit});
        if (!state.selectedReportId && reports.length) state.selectedReportId = reports[0].id;
        renderAll();
        if (!quiet) activity('Dashboard refreshed');
      } finally {
        $('refresh-button').disabled = false;
        $('refresh-button').textContent = 'Refresh dashboard';
      }
    }
    async function createBaseline(event) {
      event.preventDefault();
      const baseline = await json('/baselines/from-current', {method:'POST', body:JSON.stringify({
        name:$('baseline-name').value, version:$('baseline-version').value,
        collector_names:csv($('baseline-collectors').value),
        metadata:{created_from:'operator-console'}
      })});
      activity(`Baseline created: ${baseline.name}`);
      await refreshData({quiet:true});
    }
    async function runScan(event) {
      event.preventDefault();
      const baselineId = $('scan-baseline').value;
      if (!baselineId) return activity('Create a baseline before running a scan');
      const report = await json('/drifts/run', {method:'POST', body:JSON.stringify({
        baseline_id:baselineId, collector_names:csv($('scan-collectors').value),
        auto_remediate:$('scan-auto-remediate').checked
      })});
      state.selectedReportId = report.id;
      activity(`Drift scan completed: ${short(report.id, 18)}`);
      await refreshData({quiet:true});
    }
    async function createJob(event) {
      event.preventDefault();
      const baselineId = $('job-baseline').value;
      if (!baselineId) return activity('Create a baseline before scheduling a job');
      const job = await json('/jobs', {method:'POST', body:JSON.stringify({
        name:$('job-name').value, baseline_id:baselineId,
        interval_seconds:Number($('job-interval').value || 3600),
        collector_names:csv($('job-collectors').value), enabled:true
      })});
      activity(`Scheduled job created: ${job.name}`);
      await refreshData({quiet:true});
    }
    async function checkKubernetes(event) {
      event.preventDefault();
      const ns = $('kubernetes-namespaces').value.trim();
      const query = ns ? `?namespaces=${encodeURIComponent(ns)}` : '';
      const result = await json(`/integrations/kubernetes/check${query}`);
      const checks = (result.checks || []).map((c) => `${c.name}: ${c.status}${c.error ? ` (${c.error})` : ''}`);
      $('kubernetes-result').innerHTML = `<strong>${esc(result.ready ? 'Kubernetes ready' : 'Kubernetes not ready')}</strong><p>${esc(result.context || 'No active context')}</p><p>${esc(checks.join(' | ') || 'No checks returned')}</p>`;
      activity('Kubernetes readiness check completed');
    }
    async function plan(reportId) {
      if (!reportId) return activity('Select a report before planning remediation');
      await json(`/remediation/reports/${encodeURIComponent(reportId)}/plan`, {method:'POST'});
      activity(`Remediation plan created for ${short(reportId, 18)}`);
      await refreshData({quiet:true});
    }
    async function approve(actionId) {
      await json(`/remediation/actions/${encodeURIComponent(actionId)}/approve`, {method:'POST', body:JSON.stringify({})});
      activity(`Remediation action approved: ${short(actionId, 18)}`);
      await refreshData({quiet:true});
    }
    function key() {
      return window.crypto?.randomUUID ? window.crypto.randomUUID() : `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
    async function execute(reportId) {
      if (!reportId) return activity('Select a report before executing remediation');
      await json(`/remediation/reports/${encodeURIComponent(reportId)}/execute`,
        {method:'POST', headers:{'Idempotency-Key':key()}});
      activity(`Approved remediation executed for ${short(reportId, 18)}`);
      await refreshData({quiet:true});
    }
    async function runJob(jobId) {
      const run = await json(`/jobs/${encodeURIComponent(jobId)}/run`, {method:'POST'});
      if (run.report_id) state.selectedReportId = run.report_id;
      activity(`Scheduled job run completed: ${short(run.id, 18)}`);
      await refreshData({quiet:true});
    }
    document.addEventListener('click', async (event) => {
      const target = event.target.closest('[data-action], [data-scroll-target]');
      if (!target) return;
      if (target.dataset.scrollTarget) return document.getElementById(target.dataset.scrollTarget)?.scrollIntoView();
      try {
        const action = target.dataset.action;
        if (action === 'select-report') { state.selectedReportId = target.dataset.reportId; renderAll(); activity(`Selected report ${short(state.selectedReportId, 18)}`); }
        if (action === 'plan-report') await plan(target.dataset.reportId);
        if (action === 'execute-report') await execute(target.dataset.reportId);
        if (action === 'approve-action') await approve(target.dataset.actionId);
        if (action === 'run-job') await runJob(target.dataset.jobId);
      } catch (error) { activity(error.message || 'Action failed'); }
    });
    $('refresh-button').addEventListener('click', () => refreshData());
    $('baseline-form').addEventListener('submit', (e) => createBaseline(e).catch((x) => activity(x.message)));
    $('scan-form').addEventListener('submit', (e) => runScan(e).catch((x) => activity(x.message)));
    $('job-form').addEventListener('submit', (e) => createJob(e).catch((x) => activity(x.message)));
    $('kubernetes-form').addEventListener('submit', (e) => checkKubernetes(e).catch((x) => activity(x.message)));
    $('plan-selected-report').addEventListener('click', () => plan(selectedReport()?.id).catch((x) => activity(x.message)));
    $('execute-selected-report').addEventListener('click', () => execute(selectedReport()?.id).catch((x) => activity(x.message)));
    refreshData({quiet:true}).catch((error) => activity(error.message || 'Dashboard failed to load'));
  </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(UI_HTML)


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(FAVICON_SVG, media_type="image/svg+xml")
