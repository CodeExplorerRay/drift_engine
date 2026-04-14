from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

UI_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>System Drift Engine</title>
  <style>
    :root {
      --ink: #17211b;
      --muted: #66736c;
      --paper: #fffaf0;
      --panel: rgba(255, 255, 255, 0.72);
      --line: rgba(23, 33, 27, 0.14);
      --accent: #e4572e;
      --accent-dark: #9c2f19;
      --gold: #f2b84b;
      --green: #1f8a70;
      --blue: #315c74;
      --danger: #b42318;
      --shadow: 0 24px 70px rgba(23, 33, 27, 0.14);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 15%, rgba(242, 184, 75, 0.45), transparent 28rem),
        radial-gradient(circle at 82% 8%, rgba(31, 138, 112, 0.25), transparent 26rem),
        linear-gradient(135deg, #fff6df 0%, #f4efe4 42%, #e4edf0 100%);
      font-family: "Bahnschrift", "Segoe UI Variable Display", "Trebuchet MS", sans-serif;
    }

    body::before {
      position: fixed;
      inset: 0;
      z-index: -1;
      pointer-events: none;
      content: "";
      background-image:
        linear-gradient(rgba(23, 33, 27, 0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(23, 33, 27, 0.045) 1px, transparent 1px);
      background-size: 38px 38px;
      mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.55), transparent 82%);
    }

    a {
      color: inherit;
    }

    .shell {
      width: min(1440px, calc(100% - 36px));
      margin: 0 auto;
      padding: 30px 0 42px;
    }

    .hero {
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
      gap: 22px;
      align-items: stretch;
      margin-bottom: 22px;
    }

    .hero-card,
    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .hero-card {
      position: relative;
      overflow: hidden;
      min-height: 330px;
      padding: 38px;
      border-radius: 34px;
    }

    .hero-card::after {
      position: absolute;
      right: -90px;
      bottom: -120px;
      width: 340px;
      height: 340px;
      border: 42px solid rgba(228, 87, 46, 0.22);
      border-radius: 999px;
      content: "";
    }

    .eyebrow {
      display: inline-flex;
      gap: 10px;
      align-items: center;
      width: fit-content;
      padding: 8px 12px;
      border: 1px solid rgba(23, 33, 27, 0.16);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.58);
      color: var(--blue);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .pulse {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--green);
      box-shadow: 0 0 0 0 rgba(31, 138, 112, 0.55);
      animation: pulse 1.8s infinite;
    }

    h1 {
      max-width: 820px;
      margin: 24px 0 18px;
      font-size: clamp(2.8rem, 7vw, 6.8rem);
      line-height: 0.88;
      letter-spacing: -0.08em;
    }

    .hero p {
      max-width: 720px;
      margin: 0;
      color: var(--muted);
      font-size: clamp(1rem, 1.5vw, 1.24rem);
      line-height: 1.65;
    }

    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 28px;
    }

    .button {
      display: inline-flex;
      gap: 10px;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 0 18px;
      border: 0;
      border-radius: 999px;
      background: var(--ink);
      color: #fffaf0;
      cursor: pointer;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 800;
      text-decoration: none;
      transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    .button:hover {
      transform: translateY(-2px);
      box-shadow: 0 14px 28px rgba(23, 33, 27, 0.18);
    }

    .button.secondary {
      border: 1px solid rgba(23, 33, 27, 0.16);
      background: rgba(255, 255, 255, 0.68);
      color: var(--ink);
    }

    .button.warn {
      background: var(--accent);
    }

    .button:disabled {
      cursor: not-allowed;
      opacity: 0.55;
      transform: none;
      box-shadow: none;
    }

    .command-card {
      display: grid;
      gap: 14px;
      padding: 24px;
      border-radius: 34px;
    }

    .status-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--line);
    }

    .status-title {
      font-size: 0.85rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 11px;
      border-radius: 999px;
      background: rgba(31, 138, 112, 0.12);
      color: var(--green);
      font-size: 0.78rem;
      font-weight: 900;
    }

    label {
      display: grid;
      gap: 7px;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    input,
    select {
      width: 100%;
      min-height: 45px;
      border: 1px solid rgba(23, 33, 27, 0.16);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.72);
      color: var(--ink);
      font: inherit;
      outline: none;
      padding: 0 14px;
    }

    input:focus,
    select:focus {
      border-color: rgba(228, 87, 46, 0.72);
      box-shadow: 0 0 0 4px rgba(228, 87, 46, 0.12);
    }

    .grid {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 22px;
      align-items: start;
    }

    .stack {
      display: grid;
      gap: 22px;
    }

    .panel {
      overflow: hidden;
      border-radius: 28px;
    }

    .panel-header {
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 18px;
      padding: 22px 22px 16px;
      border-bottom: 1px solid var(--line);
    }

    .panel-header h2 {
      margin: 0;
      font-size: 1rem;
      font-weight: 900;
      letter-spacing: -0.03em;
    }

    .panel-header p {
      margin: 7px 0 0;
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.5;
    }

    .panel-body {
      padding: 20px 22px 22px;
    }

    .collector-list,
    .integration-list,
    .baseline-list,
    .report-list,
    .job-list,
    .finding-list,
    .remediation-list,
    .audit-list {
      display: grid;
      gap: 10px;
    }

    .collector-item,
    .integration-item,
    .baseline-item,
    .report-item,
    .job-item,
    .finding-item,
    .remediation-item,
    .audit-item {
      display: grid;
      gap: 7px;
      padding: 13px 14px;
      border: 1px solid rgba(23, 33, 27, 0.1);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.55);
    }

    .collector-item {
      grid-template-columns: auto 1fr;
      align-items: center;
    }

    .integration-item {
      grid-template-columns: 1fr auto;
      align-items: start;
    }

    .inline-form {
      display: grid;
      grid-template-columns: minmax(180px, 1fr) minmax(120px, 0.35fr) auto;
      gap: 10px;
      align-items: end;
      padding-bottom: 16px;
      margin-bottom: 14px;
      border-bottom: 1px solid var(--line);
    }

    .item-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 4px;
    }

    .mini-button {
      width: fit-content;
      min-height: 32px;
      padding: 0 11px;
      border: 1px solid rgba(23, 33, 27, 0.14);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.68);
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      font-size: 0.72rem;
      font-weight: 900;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .mini-button:hover {
      border-color: rgba(228, 87, 46, 0.55);
      color: var(--accent-dark);
    }

    .collector-item input {
      width: 18px;
      min-height: 18px;
      accent-color: var(--accent);
    }

    .item-title {
      font-weight: 900;
      letter-spacing: -0.02em;
      word-break: break-word;
    }

    .item-meta {
      color: var(--muted);
      font-family: "Cascadia Mono", "Consolas", monospace;
      font-size: 0.76rem;
      word-break: break-word;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }

    .metric {
      position: relative;
      overflow: hidden;
      min-height: 132px;
      padding: 18px;
      border: 1px solid rgba(23, 33, 27, 0.1);
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.58);
    }

    .metric::after {
      position: absolute;
      right: -32px;
      bottom: -44px;
      width: 120px;
      height: 120px;
      border-radius: 999px;
      background: rgba(242, 184, 75, 0.26);
      content: "";
    }

    .metric strong {
      position: relative;
      z-index: 1;
      display: block;
      margin-top: 18px;
      font-size: clamp(2rem, 4vw, 3.4rem);
      line-height: 0.9;
      letter-spacing: -0.08em;
    }

    .metric span {
      position: relative;
      z-index: 1;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .risk-band {
      height: 14px;
      overflow: hidden;
      border-radius: 999px;
      background: rgba(23, 33, 27, 0.1);
    }

    .risk-fill {
      width: 0%;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--green), var(--gold), var(--accent));
      transition: width 360ms ease;
    }

    .log {
      min-height: 112px;
      max-height: 280px;
      overflow: auto;
      padding: 16px;
      border: 1px solid rgba(23, 33, 27, 0.1);
      border-radius: 20px;
      background: rgba(23, 33, 27, 0.88);
      color: #fffaf0;
      font-family: "Cascadia Mono", "Consolas", monospace;
      font-size: 0.78rem;
      line-height: 1.55;
      white-space: pre-wrap;
    }

    .empty {
      padding: 18px;
      border: 1px dashed rgba(23, 33, 27, 0.2);
      border-radius: 18px;
      color: var(--muted);
      text-align: center;
    }

    .severity {
      width: fit-content;
      padding: 5px 9px;
      border-radius: 999px;
      background: rgba(228, 87, 46, 0.14);
      color: var(--accent-dark);
      font-size: 0.72rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .integration-status {
      width: fit-content;
      padding: 5px 9px;
      border-radius: 999px;
      background: rgba(49, 92, 116, 0.13);
      color: var(--blue);
      font-size: 0.72rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .toast {
      position: fixed;
      right: 22px;
      bottom: 22px;
      z-index: 20;
      display: none;
      max-width: min(440px, calc(100% - 44px));
      padding: 16px 18px;
      border: 1px solid rgba(23, 33, 27, 0.14);
      border-radius: 18px;
      background: rgba(255, 250, 240, 0.94);
      box-shadow: var(--shadow);
      color: var(--ink);
      font-weight: 800;
    }

    .toast.show {
      display: block;
      animation: rise 260ms ease;
    }

    @keyframes pulse {
      70% {
        box-shadow: 0 0 0 12px rgba(31, 138, 112, 0);
      }
      100% {
        box-shadow: 0 0 0 0 rgba(31, 138, 112, 0);
      }
    }

    @keyframes rise {
      from {
        opacity: 0;
        transform: translateY(12px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @media (max-width: 1040px) {
      .hero,
      .grid,
      .inline-form {
        grid-template-columns: 1fr;
      }

      .metrics {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 640px) {
      .shell {
        width: min(100% - 22px, 1440px);
        padding-top: 14px;
      }

      .hero-card,
      .command-card,
      .panel {
        border-radius: 22px;
      }

      .hero-card {
        min-height: auto;
        padding: 24px;
      }

      .panel-header {
        display: grid;
      }

      .metrics {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <article class="hero-card">
        <div class="eyebrow"><span class="pulse"></span> Live control plane</div>
        <h1>System Drift Engine</h1>
        <p>
          Capture signed baselines, collect live infrastructure state, detect deviations,
          score risk, and prepare remediation from one operational cockpit.
        </p>
        <div class="hero-actions">
          <button class="button warn" id="run-scan-button">Run drift scan</button>
          <button class="button secondary" id="collect-button">Collect state</button>
          <a class="button secondary" href="/docs">Open API docs</a>
        </div>
      </article>

      <aside class="panel command-card">
        <div class="status-row">
          <div>
            <div class="status-title">Engine status</div>
            <div class="item-meta" id="health-detail">Checking service health...</div>
          </div>
          <span class="status-pill" id="health-pill">BOOTING</span>
        </div>

        <label>
          API key header
          <input id="api-key" type="password" placeholder="Optional for protected environments" />
        </label>

        <label>
          Baseline name
          <input id="baseline-name" value="local-browser-baseline" />
        </label>

        <label>
          Baseline to compare
          <select id="baseline-select"></select>
        </label>

        <label>
          Kubernetes namespaces
          <input id="kubernetes-namespaces" placeholder="Optional, e.g. prod,platform" />
        </label>

        <button class="button" id="baseline-button">Capture baseline from current state</button>
        <button class="button secondary" id="kubernetes-check-button">
          Check Kubernetes integration
        </button>
        <button class="button secondary" id="refresh-button">Refresh dashboard</button>
      </aside>
    </section>

    <section class="grid">
      <aside class="stack">
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Collectors</h2>
              <p>Choose the signal sources used for collection and drift scans.</p>
            </div>
          </div>
          <div class="panel-body collector-list" id="collector-list"></div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Integrations</h2>
              <p>External systems that can feed real infrastructure state into scans.</p>
            </div>
          </div>
          <div class="panel-body integration-list" id="integration-list"></div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Baselines</h2>
              <p>Known desired states currently loaded by the engine.</p>
            </div>
          </div>
          <div class="panel-body baseline-list" id="baseline-list"></div>
        </section>
      </aside>

      <section class="stack">
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Operational picture</h2>
              <p>Latest risk posture and drift summary from the most recent report.</p>
            </div>
          </div>
          <div class="panel-body">
            <div class="metrics">
              <div class="metric"><span>Risk score</span><strong id="risk-score">0</strong></div>
              <div class="metric"><span>Total drift</span><strong id="total-drift">0</strong></div>
              <div class="metric"><span>Baselines</span><strong id="baseline-count">0</strong></div>
              <div class="metric">
                <span>Collectors</span><strong id="collector-count">0</strong>
              </div>
            </div>
            <div style="height: 18px"></div>
            <div class="risk-band"><div class="risk-fill" id="risk-fill"></div></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Scheduled jobs</h2>
              <p>Persisted scan cadence and recent execution state.</p>
            </div>
          </div>
          <div class="panel-body">
            <div class="inline-form">
              <label>
                Job name
                <input id="job-name" value="continuous-drift-watch" />
              </label>
              <label>
                Interval seconds
                <input id="job-interval" type="number" min="60" value="3600" />
              </label>
              <button class="button secondary" id="job-button">Create job</button>
            </div>
            <div class="job-list" id="job-list"></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Report history</h2>
              <p>Recent drift reports available for inspection and remediation planning.</p>
            </div>
          </div>
          <div class="panel-body report-list" id="report-list"></div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Findings</h2>
              <p>Open configuration differences detected against the selected baseline.</p>
            </div>
          </div>
          <div class="panel-body finding-list" id="finding-list"></div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Remediation queue</h2>
              <p>Generated remediation actions remain gated until approval and execution.</p>
            </div>
          </div>
          <div class="panel-body remediation-list" id="remediation-list"></div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Audit trail</h2>
              <p>Durable write and security events visible to authorized operators.</p>
            </div>
          </div>
          <div class="panel-body audit-list" id="audit-list"></div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Activity log</h2>
              <p>Client-side command trail for this browser session.</p>
            </div>
          </div>
          <div class="panel-body">
            <div class="log" id="activity-log"></div>
          </div>
        </section>
      </section>
    </section>
  </main>

  <div class="toast" id="toast"></div>

  <script>
    const state = {
      collectors: [],
      integrations: [],
      baselines: [],
      reports: [],
      jobs: [],
      jobRuns: [],
      remediationActions: [],
      auditEvents: [],
      latestReport: null,
    };

    const $ = (id) => document.getElementById(id);

    function headers() {
      const apiKey = $("api-key").value.trim();
      const result = { "Content-Type": "application/json" };
      if (apiKey) {
        result["X-API-Key"] = apiKey;
      }
      return result;
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function log(message) {
      const time = new Date().toLocaleTimeString();
      $("activity-log").textContent = `[${time}] ${message}\\n` + $("activity-log").textContent;
    }

    function toast(message) {
      const node = $("toast");
      node.textContent = message;
      node.classList.add("show");
      window.setTimeout(() => node.classList.remove("show"), 3600);
    }

    async function fetchJson(path, options = {}) {
      const response = await fetch(path, {
        ...options,
        headers: { ...headers(), ...(options.headers || {}) },
      });
      const body = await response.text();
      const data = body ? JSON.parse(body) : null;
      if (!response.ok) {
        const detail = data?.detail || data?.error || response.statusText;
        throw new Error(`${response.status} ${detail}`);
      }
      return data;
    }

    async function safeFetchJson(path, fallback) {
      try {
        return await fetchJson(path);
      } catch (error) {
        log(`Skipped ${path}: ${error.message}`);
        return fallback;
      }
    }

    function selectedCollectors() {
      return Array.from(document.querySelectorAll("[data-collector]:checked")).map(
        (node) => node.value,
      );
    }

    function requestScope() {
      const namespaceValue = $("kubernetes-namespaces").value.trim();
      if (!namespaceValue) {
        return {};
      }
      return {
        kubernetes_namespaces: namespaceValue
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      };
    }

    function renderCollectors() {
      $("collector-count").textContent = state.collectors.length;
      if (!state.collectors.length) {
        $("collector-list").innerHTML = '<div class="empty">No collectors registered.</div>';
        return;
      }

      $("collector-list").innerHTML = state.collectors.map((collector) => `
        <label class="collector-item">
          <input
            data-collector
            value="${escapeHtml(collector.name)}"
            type="checkbox"
            ${collector.enabled ? "checked" : ""}
            ${collector.enabled ? "" : "disabled"}
          />
          <span>
            <span class="item-title">${escapeHtml(collector.name)}</span>
            <span class="item-meta">
              ${escapeHtml(collector.resource_type)} source / ${escapeHtml(collector.status)}
            </span>
          </span>
        </label>
      `).join("");
    }

    function renderIntegrations() {
      if (!state.integrations.length) {
        $("integration-list").innerHTML = '<div class="empty">No integrations registered.</div>';
        return;
      }

      $("integration-list").innerHTML = state.integrations.map((integration) => {
        const missing = integration.missing?.length
          ? `Missing: ${integration.missing.map(escapeHtml).join(", ")}`
          : "Ready to collect when enabled and selected.";
        return `
          <article class="integration-item">
            <span>
              <span class="item-title">${escapeHtml(integration.display_name)}</span>
              <span class="item-meta">${escapeHtml(integration.description)}</span>
              <span class="item-meta">${missing}</span>
            </span>
            <span class="integration-status">${escapeHtml(integration.status)}</span>
          </article>
        `;
      }).join("");
    }

    function renderBaselines() {
      $("baseline-count").textContent = state.baselines.length;
      $("baseline-select").innerHTML = state.baselines.length
        ? state.baselines.map((baseline) => `
            <option value="${escapeHtml(baseline.id)}">
              ${escapeHtml(baseline.name)} / ${escapeHtml(baseline.version)}
            </option>
          `).join("")
        : '<option value="">Capture a baseline first</option>';

      if (!state.baselines.length) {
        $("baseline-list").innerHTML = [
          '<div class="empty">No baselines yet. Capture one above.</div>',
        ].join("");
        return;
      }

      $("baseline-list").innerHTML = state.baselines.map((baseline) => `
        <article class="baseline-item">
          <div class="item-title">${escapeHtml(baseline.name)}</div>
          <div class="item-meta">${escapeHtml(baseline.id)}</div>
          <div class="item-meta">${Object.keys(baseline.resources || {}).length} resources</div>
        </article>
      `).join("");
    }

    function renderReport() {
      const report = state.latestReport;
      const risk = Math.round(Number(report?.risk_score || 0));
      const summary = report?.summary || {};
      const findings = report?.findings || [];

      $("risk-score").textContent = risk;
      $("risk-fill").style.width = `${Math.min(100, Math.max(0, risk))}%`;
      $("total-drift").textContent = summary.total || findings.length || 0;

      if (!findings.length) {
        $("finding-list").innerHTML = [
          '<div class="empty">',
          "No drift findings yet. Run a scan after capturing a baseline.",
          "</div>",
        ].join("");
        return;
      }

      $("finding-list").innerHTML = findings.slice(0, 20).map((finding) => `
        <article class="finding-item">
          <span class="severity">
            ${escapeHtml(finding.severity)} / ${escapeHtml(finding.drift_type)}
          </span>
          <div class="item-title">${escapeHtml(finding.resource_key)}</div>
          <div class="item-meta">Path: ${escapeHtml(finding.path || "/")}</div>
          <div class="item-meta">
            Risk: ${escapeHtml(finding.risk_score)} | Status: ${escapeHtml(finding.status)}
          </div>
        </article>
      `).join("");
    }

    function renderReports() {
      if (!state.reports.length) {
        $("report-list").innerHTML = [
          '<div class="empty">No drift reports yet. Run a scan to create one.</div>',
        ].join("");
        return;
      }

      $("report-list").innerHTML = state.reports.slice(0, 10).map((report) => {
        const total = report.summary?.total ?? report.findings?.length ?? 0;
        return `
          <article class="report-item">
            <div class="item-title">${escapeHtml(report.id)}</div>
            <div class="item-meta">
              Baseline: ${escapeHtml(report.baseline_id)} | Risk: ${escapeHtml(report.risk_score)}
            </div>
            <div class="item-meta">
              Findings: ${escapeHtml(total)} | Generated: ${escapeHtml(report.generated_at)}
            </div>
            <div class="item-actions">
              <button class="mini-button" data-select-report="${escapeHtml(report.id)}">
                Inspect
              </button>
              <button class="mini-button" data-plan-report="${escapeHtml(report.id)}">
                Plan remediation
              </button>
              <button class="mini-button" data-execute-report="${escapeHtml(report.id)}">
                Execute approved
              </button>
            </div>
          </article>
        `;
      }).join("");
    }

    function renderRemediationActions() {
      if (!state.remediationActions.length) {
        $("remediation-list").innerHTML = [
          '<div class="empty">No remediation actions generated yet.</div>',
        ].join("");
        return;
      }

      $("remediation-list").innerHTML = state.remediationActions.slice(0, 12).map((action) => `
        <article class="remediation-item">
          <span class="severity">${escapeHtml(action.status)}</span>
          <div class="item-title">${escapeHtml(action.strategy)}</div>
          <div class="item-meta">${escapeHtml(action.description)}</div>
          <div class="item-meta">
            Risk: ${escapeHtml(action.risk_score)}
            | Approval: ${escapeHtml(action.requires_approval ? "required" : "auto")}
            | Dry run: ${escapeHtml(action.dry_run)}
          </div>
          <div class="item-actions">
            <button class="mini-button" data-approve-action="${escapeHtml(action.id)}">
              Approve action
            </button>
          </div>
        </article>
      `).join("");
    }

    function renderAuditEvents() {
      if (!state.auditEvents.length) {
        $("audit-list").innerHTML = [
          '<div class="empty">',
          "No audit events visible. Add an API key with audit:read if needed.",
          "</div>",
        ].join("");
        return;
      }

      $("audit-list").innerHTML = state.auditEvents.slice(0, 12).map((event) => `
        <article class="audit-item">
          <div class="item-title">${escapeHtml(event.action)}</div>
          <div class="item-meta">
            Actor: ${escapeHtml(event.actor_id)} | Target: ${escapeHtml(event.target_type)}
            / ${escapeHtml(event.target_id)}
          </div>
          <div class="item-meta">${escapeHtml(event.created_at)}</div>
        </article>
      `).join("");
    }

    function renderJobs() {
      if (!state.jobs.length) {
        $("job-list").innerHTML = [
          '<div class="empty">No scheduled scan jobs yet. Create one above.</div>',
        ].join("");
        return;
      }

      const latestByJob = new Map(state.jobRuns.map((run) => [run.job_id, run]));
      $("job-list").innerHTML = state.jobs.slice(0, 8).map((job) => {
        const latest = latestByJob.get(job.id);
        const report = latest?.report_id ? ` / ${latest.report_id}` : "";
        const status = latest ? `${latest.status}${report}` : "never run";
        return `
          <article class="job-item">
            <div class="item-title">${escapeHtml(job.name)}</div>
            <div class="item-meta">Baseline: ${escapeHtml(job.baseline_id)}</div>
            <div class="item-meta">
              Every ${escapeHtml(job.interval_seconds)}s | Next: ${escapeHtml(job.next_run_at)}
            </div>
            <div class="item-meta">Latest: ${escapeHtml(status)}</div>
            <div class="item-actions">
              <button class="mini-button" data-run-job="${escapeHtml(job.id)}">Run now</button>
            </div>
          </article>
        `;
      }).join("");
    }

    async function refreshHealth() {
      try {
        await fetchJson("/health/live", { headers: {} });
        $("health-pill").textContent = "LIVE";
        $("health-detail").textContent = "API, collectors, and dashboard shell are reachable.";
      } catch (error) {
        $("health-pill").textContent = "DOWN";
        $("health-detail").textContent = error.message;
      }
    }

    async function refreshData() {
      const [
        collectors,
        integrations,
        baselines,
        reports,
        jobs,
        jobRuns,
        remediationActions,
        auditEvents,
      ] = await Promise.all([
        fetchJson("/collectors"),
        fetchJson("/integrations"),
        fetchJson("/baselines"),
        fetchJson("/drifts"),
        safeFetchJson("/jobs", []),
        safeFetchJson("/jobs/runs", []),
        safeFetchJson("/remediation/actions", []),
        safeFetchJson("/audit", []),
      ]);
      state.collectors = collectors;
      state.integrations = integrations;
      state.baselines = baselines;
      state.reports = reports;
      state.jobs = jobs;
      state.jobRuns = jobRuns;
      state.remediationActions = remediationActions;
      state.auditEvents = auditEvents;
      state.latestReport = reports[0] || null;
      renderCollectors();
      renderIntegrations();
      renderBaselines();
      renderReport();
      renderReports();
      renderJobs();
      renderRemediationActions();
      renderAuditEvents();
    }

    async function captureBaseline() {
      const names = selectedCollectors();
      const name = $("baseline-name").value.trim() || `baseline-${Date.now()}`;
      const baseline = await fetchJson("/baselines/from-current", {
        method: "POST",
        body: JSON.stringify({
          name,
          version: "1.0.0",
          collector_names: names.length ? names : null,
          scope: requestScope(),
          metadata: { created_from: "browser-ui" },
        }),
      });
      const resourceCount = Object.keys(baseline.resources || {}).length;
      log(`Captured baseline ${baseline.name} with ${resourceCount} resources.`);
      toast("Baseline captured.");
      await refreshData();
      $("baseline-select").value = baseline.id;
    }

    async function collectState() {
      const names = selectedCollectors();
      const result = await fetchJson("/drifts/collect", {
        method: "POST",
        body: JSON.stringify({
          collector_names: names.length ? names : null,
          scope: requestScope(),
        }),
      });
      const count = Object.keys(result.snapshot?.resources || {}).length;
      log(`Collected ${count} resources from ${result.collectors?.length || 0} collectors.`);
      toast("State collection completed.");
    }

    async function checkKubernetes() {
      const namespaces = requestScope().kubernetes_namespaces || [];
      const query = namespaces.length
        ? `?namespaces=${encodeURIComponent(namespaces.join(","))}`
        : "";
      const result = await fetchJson(`/integrations/kubernetes/check${query}`);
      const failed = result.checks.filter((check) => check.status !== "passed");
      const context = result.context ? ` on ${result.context}` : "";
      if (result.ready) {
        log(`Kubernetes integration is ready${context}.`);
        toast("Kubernetes integration is ready.");
        return;
      }
      const reasons = failed.map((check) => `${check.name}: ${check.error}`).join("; ");
      log(`Kubernetes integration is not ready${context}. ${reasons}`);
      toast("Kubernetes integration needs attention.");
    }

    async function runDriftScan() {
      const baselineId = $("baseline-select").value;
      if (!baselineId) {
        toast("Capture or select a baseline before running a scan.");
        return;
      }
      const names = selectedCollectors();
      const report = await fetchJson("/drifts/run", {
        method: "POST",
        body: JSON.stringify({
          baseline_id: baselineId,
          collector_names: names.length ? names : null,
          auto_remediate: false,
          scope: requestScope(),
        }),
      });
      state.latestReport = report;
      log(`Drift scan ${report.id} finished with risk score ${report.risk_score}.`);
      toast("Drift scan completed.");
      renderReport();
      await refreshData();
    }

    async function createScheduledJob() {
      const baselineId = $("baseline-select").value;
      if (!baselineId) {
        toast("Select a baseline before creating a job.");
        return;
      }
      const interval = Number($("job-interval").value || 0);
      if (!Number.isFinite(interval) || interval < 60) {
        toast("Use an interval of at least 60 seconds.");
        return;
      }
      const names = selectedCollectors();
      const job = await fetchJson("/jobs", {
        method: "POST",
        body: JSON.stringify({
          name: $("job-name").value.trim() || `drift-watch-${Date.now()}`,
          baseline_id: baselineId,
          interval_seconds: interval,
          collector_names: names.length ? names : null,
          enabled: true,
        }),
      });
      log(`Created scheduled job ${job.name}.`);
      toast("Scheduled scan job created.");
      await refreshData();
    }

    async function runJobNow(jobId) {
      const run = await fetchJson(`/jobs/${encodeURIComponent(jobId)}/run`, {
        method: "POST",
      });
      log(`Manual job run ${run.id} finished with status ${run.status}.`);
      toast("Scheduled job executed.");
      await refreshData();
    }

    function selectReport(reportId) {
      const report = state.reports.find((item) => item.id === reportId);
      if (!report) {
        toast("Report is no longer loaded.");
        return;
      }
      state.latestReport = report;
      renderReport();
      log(`Inspecting report ${report.id}.`);
    }

    async function planRemediation(reportId) {
      const plan = await fetchJson(`/remediation/reports/${encodeURIComponent(reportId)}/plan`, {
        method: "POST",
      });
      const actions = plan.actions || [];
      log(`Prepared remediation plan for ${reportId} with ${actions.length} actions.`);
      toast("Remediation plan prepared.");
      await refreshData();
    }

    async function approveRemediationAction(actionId) {
      const action = await fetchJson(
        `/remediation/actions/${encodeURIComponent(actionId)}/approve`,
        {
          method: "POST",
          body: JSON.stringify({ expires_in_seconds: 3600 }),
        },
      );
      log(`Approved remediation action ${action.id}.`);
      toast("Remediation action approved.");
      await refreshData();
    }

    async function executeRemediation(reportId) {
      const path = `/remediation/reports/${encodeURIComponent(reportId)}/execute`;
      const actions = await fetchJson(path, {
        method: "POST",
        headers: { "Idempotency-Key": `browser-${reportId}` },
      });
      log(`Executed remediation for ${reportId}; ${actions.length} actions returned.`);
      toast("Remediation execution requested.");
      await refreshData();
    }

    async function guard(button, task) {
      button.disabled = true;
      try {
        await task();
      } catch (error) {
        log(`Error: ${error.message}`);
        toast(error.message);
      } finally {
        button.disabled = false;
      }
    }

    $("baseline-button").addEventListener(
      "click",
      () => guard($("baseline-button"), captureBaseline),
    );
    $("kubernetes-check-button").addEventListener(
      "click",
      () => guard($("kubernetes-check-button"), checkKubernetes),
    );
    $("collect-button").addEventListener(
      "click",
      () => guard($("collect-button"), collectState),
    );
    $("run-scan-button").addEventListener(
      "click",
      () => guard($("run-scan-button"), runDriftScan),
    );
    $("job-button").addEventListener(
      "click",
      () => guard($("job-button"), createScheduledJob),
    );
    $("refresh-button").addEventListener(
      "click",
      () => guard($("refresh-button"), refreshData),
    );
    document.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const reportId = target.dataset.selectReport;
      if (reportId) {
        selectReport(reportId);
        return;
      }
      const planReportId = target.dataset.planReport;
      if (planReportId) {
        guard(target, () => planRemediation(planReportId));
        return;
      }
      const executeReportId = target.dataset.executeReport;
      if (executeReportId) {
        guard(target, () => executeRemediation(executeReportId));
        return;
      }
      const actionId = target.dataset.approveAction;
      if (actionId) {
        guard(target, () => approveRemediationAction(actionId));
        return;
      }
      const jobId = target.dataset.runJob;
      if (jobId) {
        guard(target, () => runJobNow(jobId));
      }
    });

    (async function boot() {
      await refreshHealth();
      try {
        await refreshData();
        log("Dashboard initialized.");
      } catch (error) {
        log(`Startup error: ${error.message}`);
        toast(error.message);
      }
    })();
  </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(UI_HTML)
