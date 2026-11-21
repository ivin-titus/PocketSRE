const app = document.querySelector("#app");
const token = new URLSearchParams(window.location.search).get("token");

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));

function stripAnsi(str) {
  if (!str) return "";
  return str.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, "");
}

function formatError(detail) {
  if (!detail) return "An unexpected error occurred.";
  if (typeof detail === "string") return detail;
  if (detail.reason) return detail.reason;
  if (detail.message) return detail.message;
  try {
    return JSON.stringify(detail, null, 2);
  } catch {
    return String(detail);
  }
}

async function copyText(text, btnElement, successMsg = "✓ Copied!") {
  try {
    await navigator.clipboard.writeText(text);
    const originalText = btnElement.textContent;
    btnElement.textContent = successMsg;
    setTimeout(() => {
      btnElement.textContent = originalText;
    }, 2000);
  } catch (e) {
    console.error("Clipboard error", e);
  }
}

if (!token) {
  app.innerHTML = `
    <div class="panel">
      <h1 class="service-title" style="color: var(--color-danger);">Access Denied</h1>
      <p style="color: var(--text-secondary);">A valid signed HMAC incident link is required to access the PocketSRE Console.</p>
    </div>
  `;
} else {
  load();
}

async function api(path, method = "GET") {
  const sep = path.includes("?") ? "&" : "?";
  const res = await fetch(`/api/console${path}${sep}token=${encodeURIComponent(token)}`, { method });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(formatError(body.detail) || `HTTP error ${res.status}`);
  }
  return res.json();
}

let currentIncident = null;

async function load() {
  let data;
  try {
    data = await api("/incident");
  } catch (e) {
    app.innerHTML = `
      <div class="panel">
        <h1 class="service-title" style="color: var(--color-danger);">Unable to Load Incident</h1>
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">${esc(e.message)}</p>
        <p><a href="mission-control.html?token=${encodeURIComponent(token)}">Go to Mission Control →</a></p>
      </div>
    `;
    return;
  }

  currentIncident = data.incident;
  const inc = data.incident;
  const rec = data.recommended_action || {};

  app.innerHTML = `
    <nav class="top-nav">
      <div class="brand-badge">
        <span class="brand-dot"></span>
        <span>PocketSRE Incident Console</span>
      </div>
      <div>
        <a href="mission-control.html?token=${encodeURIComponent(token)}">Mission Control Overview →</a>
      </div>
    </nav>

    <!-- Incident Header -->
    <header class="panel incident-header ${esc(inc.severity)}">
      <div class="header-meta">
        <span class="badge ${esc(inc.severity)}">${esc(inc.severity.toUpperCase())}</span>
        <span class="badge ${esc(inc.status)}">${esc(inc.status)}</span>
        <button type="button" class="id-badge" id="copyIdBtn" title="Click to copy full Incident ID">
          <span>📋 ${esc(inc.id.slice(0, 8))}…</span>
        </button>
      </div>

      <h1 class="service-title">${esc(inc.service)}</h1>
      <div class="incident-summary">${esc(inc.summary)}</div>

      <div class="incident-footer">
        <span>Source: <strong>${esc(inc.source)}</strong></span>
        <span>Opened: <time>${new Date(inc.created_at).toLocaleString()}</time></span>
        <span>Lead Actor: <code>${esc(data.actor_id)}</code></span>
      </div>
    </header>

    <!-- Prominent "What should I do next?" section -->
    <section class="recommendation-panel" id="recommendationSection">
      <div class="recommendation-title">
        <span>💡 What Should I Do Next?</span>
      </div>
      <div class="recommendation-card">
        <div class="recommendation-info">
          <div class="recommendation-name">${esc(rec.label || rec.name || "Fetch latest logs")}</div>
          <div class="recommendation-desc">
            ${esc(rec.description || "Safely inspect the most recent logs to understand container exit reasons or runtime faults.")}
          </div>
        </div>
        <div>
          <button type="button" id="runRecommendedBtn" class="btn-primary">
            <span>Run: ${esc(rec.label || rec.name || "Fetch latest logs")}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Categorized Runbooks -->
    <section class="panel">
      <div class="section-title">
        <span>Diagnostic & Recovery Runbooks</span>
      </div>
      <p class="section-desc">Whitelisted actions executed safely over secure remote connection.</p>

      <!-- Safe Diagnostics -->
      <h3 style="font-size: 0.875rem; font-weight: 700; color: var(--color-brand); text-transform: uppercase; letter-spacing: 0.05em; margin: 1.25rem 0 0.5rem; display: flex; align-items: center; gap: 0.4rem;">
        <span>🔍</span> Safe Diagnostics
      </h3>
      <div class="action-grid" id="diagnosticGrid"></div>

      <!-- Recovery Actions -->
      <h3 style="font-size: 0.875rem; font-weight: 700; color: var(--color-warning); text-transform: uppercase; letter-spacing: 0.05em; margin: 1.5rem 0 0.5rem; display: flex; align-items: center; gap: 0.4rem;">
        <span>⚡</span> Recovery Actions
      </h3>
      <div class="action-grid" id="recoveryGrid"></div>

      <!-- Progressive Disclosure: Advanced / Host Actions -->
      <button type="button" class="disclosure-toggle" id="advancedToggle">
        <span>⚙️ Advanced & Host-Level Actions</span>
        <span id="advancedToggleIcon">▼ Show</span>
      </button>
      <div class="disclosure-content" id="advancedSection">
        <p class="section-desc">Host-level systemd, docker daemon, and resource pruning actions. Use with caution.</p>
        <div class="action-grid" id="advancedGrid"></div>
      </div>
    </section>

    <!-- Execution Results -->
    <section class="panel">
      <div class="section-title">
        <span>Action History & Output</span>
      </div>
      <p class="section-desc">Chronological log of diagnostic runs and operational commands.</p>
      <div class="results-list" id="resultsList"></div>
    </section>

    <!-- Incident Spend Section -->
    <section class="panel">
      <div class="section-title">
        <span>Autonomous Budget & Spend</span>
      </div>
      <div id="spendBox"></div>
    </section>

    <!-- Real-time Audit Feed -->
    <section class="panel">
      <div class="section-title">
        <span>Live Audit Stream</span>
      </div>
      <ul id="feed" class="feed" style="margin-top: 0.75rem;"></ul>
      <div id="feedEmpty" class="empty-state">Listening for real-time incident events…</div>
    </section>
  `;

  // Bind copy Incident ID
  document.querySelector("#copyIdBtn").onclick = function () {
    copyText(inc.id, this, "✓ Copied ID");
  };

  // Bind Recommended Action button
  if (rec.action) {
    const recBtn = document.querySelector("#runRecommendedBtn");
    recBtn.onclick = () => executeTool(rec, recBtn);
  }

  // Bind Advanced Actions disclosure toggle
  const advToggle = document.querySelector("#advancedToggle");
  const advSection = document.querySelector("#advancedSection");
  const advIcon = document.querySelector("#advancedToggleIcon");
  advToggle.onclick = () => {
    const isExpanded = advSection.classList.toggle("expanded");
    advIcon.textContent = isExpanded ? "▲ Hide" : "▼ Show";
  };

  renderTools(data.tools);
  renderResults(data.action_results || []);
  refreshSpend();
  startFeed();
}

function renderTools(tools) {
  const diagBox = document.querySelector("#diagnosticGrid");
  const recovBox = document.querySelector("#recoveryGrid");
  const advBox = document.querySelector("#advancedGrid");

  diagBox.innerHTML = "";
  recovBox.innerHTML = "";
  advBox.innerHTML = "";

  for (const t of tools) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "action-card" + (t.mutating ? " mutating" : "");
    if (!t.available) {
      card.disabled = true;
      card.title = t.unavailable_reason || "Not available for this service";
    }

    const badgeClass = t.mutating ? "mutating" : "safe";
    const badgeText = t.mutating ? "Lead Approval" : "Safe";

    card.innerHTML = `
      <div class="action-card-header">
        <span class="action-card-label">${esc(t.label || t.name)}</span>
        <span class="action-card-badge ${badgeClass}">${badgeText}</span>
      </div>
      <div class="action-card-desc">${esc(t.description)}</div>
      ${!t.available ? `<div class="action-card-unavail">🔒 ${esc(t.unavailable_reason)}</div>` : ""}
    `;

    if (t.available) {
      card.onclick = () => executeTool(t, card);
    }

    if (t.category === "diagnostic") {
      diagBox.appendChild(card);
    } else if (t.category === "recovery") {
      recovBox.appendChild(card);
    } else {
      advBox.appendChild(card);
    }
  }
}

function confirmAction(tool, service) {
  return new Promise((resolve) => {
    const modal = document.querySelector("#confirmModal");
    const titleText = document.querySelector("#modalActionTitleText");
    const target = document.querySelector("#modalActionTarget");
    const warning = document.querySelector("#modalActionWarning");
    const cancelBtn = document.querySelector("#modalCancelBtn");
    const confirmBtn = document.querySelector("#modalConfirmBtn");
    const closeXBtn = document.querySelector("#modalCloseXBtn");

    if (!modal || !confirmBtn || !cancelBtn) {
      // Graceful fallback to browser dialog if modal DOM is missing
      const fallbackPrompt = `Confirm Action: ${tool.label || tool.name}\nTarget: ${service}\n\n${tool.side_effect_warning || "This action mutates system state."}`;
      return resolve(window.confirm(fallbackPrompt));
    }

    if (titleText) {
      titleText.textContent = `Confirm: ${tool.label || tool.name}`;
    }
    if (target) {
      target.innerHTML = `Target Service / Container: <strong><code>${esc(service || "target host")}</code></strong>`;
    }
    if (warning) {
      warning.textContent =
        tool.side_effect_warning ||
        "This action mutates system state. Ensure on-call lead approval before proceeding.";
    }

    let isDone = false;
    const cleanUp = (result) => {
      if (isDone) return;
      isDone = true;
      modal.classList.remove("active");
      cancelBtn.onclick = null;
      confirmBtn.onclick = null;
      if (closeXBtn) closeXBtn.onclick = null;
      modal.onclick = null;
      window.removeEventListener("keydown", onKeyDown);
      resolve(result);
    };

    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        cleanUp(false);
      }
    };

    cancelBtn.onclick = () => cleanUp(false);
    if (closeXBtn) closeXBtn.onclick = () => cleanUp(false);
    confirmBtn.onclick = () => cleanUp(true);

    // Click backdrop to dismiss
    modal.onclick = (e) => {
      if (e.target === modal) cleanUp(false);
    };

    window.addEventListener("keydown", onKeyDown);

    modal.classList.add("active");
    confirmBtn.focus();
  });
}

async function executeTool(tool, btnElement) {
  if (tool.mutating) {
    const confirmed = await confirmAction(tool, currentIncident ? currentIncident.service : "");
    if (!confirmed) return;
  }

  const prevText = btnElement.innerHTML;
  btnElement.disabled = true;
  btnElement.innerHTML = `<span>⏳ Working…</span>`;

  try {
    const qs = tool.action === "fetch_service_logs" ? "&tail_lines=150" : "";
    const { result } = await api(`/action?action=${encodeURIComponent(tool.action)}${qs}`, "POST");
    prependResult(result, true);
  } catch (err) {
    prependResult(
      {
        action: tool.action,
        service: currentIncident ? currentIncident.service : "host",
        status: "failed",
        executed_at: new Date().toISOString(),
        output: err.message,
      },
      true
    );
  } finally {
    btnElement.disabled = false;
    btnElement.innerHTML = prevText;
    refreshSpend();
  }
}

function renderResults(results) {
  const box = document.querySelector("#resultsList");
  box.innerHTML = "";

  if (!results || results.length === 0) {
    box.innerHTML = `
      <div class="empty-state">
        No actions executed yet for this incident. Start with the recommended action above.
      </div>
    `;
    return;
  }

  // Render newest first; newest expanded by default
  const sorted = results.slice();
  for (let i = sorted.length - 1; i >= 0; i--) {
    const isNewest = i === sorted.length - 1;
    prependResult(sorted[i], false, isNewest);
  }
}

function prependResult(r, isNewRun = false, startExpanded = true) {
  const box = document.querySelector("#resultsList");
  const emptyState = box.querySelector(".empty-state");
  if (emptyState) emptyState.remove();

  const card = document.createElement("div");
  card.className = "result-card" + (startExpanded ? " expanded" : "");

  const cleanOutput = stripAnsi(r.output || "");
  const shortSnippet = cleanOutput
    ? cleanOutput.slice(0, 140).trim() + (cleanOutput.length > 140 ? "…" : "")
    : "No terminal output recorded.";

  const statusClass = esc(r.status || "unknown");

  card.innerHTML = `
    <div class="result-card-header">
      <div class="result-card-meta">
        <span class="result-status-pill ${statusClass}">${esc(r.status)}</span>
        <span>${esc(r.action)} → <code>${esc(r.service || "host")}</code></span>
      </div>
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <span class="result-timestamp">${r.executed_at ? new Date(r.executed_at).toLocaleTimeString() : ""}</span>
        <span class="toggle-icon" style="font-size: 0.75rem; color: var(--text-muted);">${startExpanded ? "▲" : "▼"}</span>
      </div>
    </div>
    <div class="result-card-content">
      <div style="font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
        ${esc(shortSnippet)}
      </div>
      ${
        cleanOutput
          ? `
        <div class="terminal-box">
          <div class="terminal-header">
            <span>Terminal Output</span>
            <button type="button" class="copy-btn copy-output-btn">📋 Copy</button>
          </div>
          <pre class="terminal-code">${esc(cleanOutput)}</pre>
        </div>
      `
          : ""
      }
    </div>
  `;

  const header = card.querySelector(".result-card-header");
  const toggleIcon = card.querySelector(".toggle-icon");
  header.onclick = () => {
    const expanded = card.classList.toggle("expanded");
    toggleIcon.textContent = expanded ? "▲" : "▼";
  };

  const copyBtn = card.querySelector(".copy-output-btn");
  if (copyBtn) {
    copyBtn.onclick = (e) => {
      e.stopPropagation();
      copyText(cleanOutput, copyBtn, "✓ Copied!");
    };
  }

  if (isNewRun) {
    box.prepend(card);
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } else {
    box.appendChild(card);
  }
}

async function refreshSpend() {
  const box = document.querySelector("#spendBox");
  if (!box) return;
  try {
    const s = await api("/spend");
    const cap = s.budgets ? s.budgets.per_incident_usd : null;
    const spent = s.spent_usd || 0;
    const capVal = typeof cap === "number" && !isNaN(cap) ? cap : null;
    const pct = capVal && capVal > 0 ? Math.min(100, (spent / capVal) * 100) : 0;

    box.innerHTML = `
      <div class="gauge-track">
        <div class="gauge-fill ${pct > 80 ? "hot" : ""}" style="width: ${pct}%"></div>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.35rem;">
        <span>Spent: <strong>$${spent.toFixed(4)}</strong> ${capVal !== null ? `of $${capVal.toFixed(2)} cap` : "(No cap configured)"}</span>
        <span>Database: <strong style="color: ${s.db_connected ? "var(--color-success)" : "var(--color-warning)"}">${s.db_connected ? "Connected" : "Offline"}</strong></span>
      </div>
    `;
  } catch (e) {
    box.innerHTML = `<p style="font-size: 0.8125rem; color: var(--text-muted);">${esc(e.message)}</p>`;
  }
}

function startFeed() {
  const feed = document.querySelector("#feed");
  const feedEmpty = document.querySelector("#feedEmpty");
  const es = new EventSource(`/api/console/stream?token=${encodeURIComponent(token)}`);

  es.onmessage = (m) => {
    try {
      const { kind, incident } = JSON.parse(m.data);
      if (feedEmpty) feedEmpty.style.display = "none";

      const li = document.createElement("li");
      li.className = "feed-item";
      li.innerHTML = `
        <time>${new Date().toLocaleTimeString()}</time>
        <div>
          <strong>${esc(kind)}</strong> — ${esc(incident.service)}
          <span style="color: var(--text-muted); font-size: 0.75rem;">(${esc(incident.summary)})</span>
        </div>
      `;
      feed.prepend(li);
    } catch (e) {
      console.error("Stream parse error", e);
    }
  };

  es.onerror = () => {
    // SSE reconnects automatically
  };
}
