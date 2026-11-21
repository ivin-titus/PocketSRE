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

function formatMoney(amount) {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return "Not configured";
  }
  return `$${Number(amount).toFixed(2)}`;
}

async function api(path) {
  const sep = path.includes("?") ? "&" : "?";
  const res = await fetch(`/api/console${path}${sep}token=${encodeURIComponent(token || "")}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

if (!token) {
  app.innerHTML = `
    <div class="panel">
      <h1 class="service-title" style="color: var(--color-danger);">Access Denied</h1>
      <p style="color: var(--text-secondary);">A valid signed HMAC link is required to view Mission Control.</p>
    </div>
  `;
} else {
  init();
}

async function init() {
  app.innerHTML = `
    <nav class="top-nav">
      <div class="brand-badge">
        <span class="brand-dot"></span>
        <span>PocketSRE Mission Control</span>
      </div>
      <div>
        <a href="index.html?token=${encodeURIComponent(token)}">← Back to Incident Console</a>
      </div>
    </nav>

    <!-- Top Operational Summary Row -->
    <section class="summary-grid" id="summaryGrid">
      <div class="stat-tile">
        <span class="stat-label">System State</span>
        <div class="stat-value" id="statOverallState">Loading…</div>
        <span class="stat-sub" id="statOverallSub">Checking live probes</span>
      </div>
      <div class="stat-tile">
        <span class="stat-label">Monitored Services</span>
        <div class="stat-value" id="statServicesCount">—</div>
        <span class="stat-sub" id="statServicesSub">Healthy / Degraded</span>
      </div>
      <div class="stat-tile">
        <span class="stat-label">Active Incidents</span>
        <div class="stat-value" id="statIncidentsCount">—</div>
        <span class="stat-sub">Requiring attention</span>
      </div>
      <div class="stat-tile">
        <span class="stat-label">Incident Spend</span>
        <div class="stat-value" id="statSpendVal">—</div>
        <span class="stat-sub" id="statSpendSub">Autonomous budget</span>
      </div>
    </section>

    <!-- Presence Health Cards Grid -->
    <section class="panel">
      <div class="section-title">
        <span>Production Services Health</span>
        <span style="font-size: 0.75rem; color: var(--text-muted);" id="lastPolledTime">Polled live</span>
      </div>
      <p class="section-desc">Real-time status of Project Yuki microservices and presence routes.</p>
      <div class="health-grid" id="healthGrid" style="margin-top: 1rem;"></div>
    </section>

    <!-- Spend & Budget Breakdown -->
    <section class="panel">
      <div class="section-title">
        <span>Autonomous Spending Governor</span>
      </div>
      <div id="spendDetailBox"></div>
    </section>

    <!-- Real-time Audit Feed -->
    <section class="panel">
      <div class="section-title">
        <span>Real-Time Audit Stream</span>
      </div>
      <ul id="feed" class="feed" style="margin-top: 0.75rem;"></ul>
      <div id="feedEmpty" class="empty-state">No events recorded yet. PocketSRE is listening for incident activity…</div>
    </section>
  `;

  await refreshHealth();
  await refreshSpend();
  setInterval(refreshHealth, 15000);
  setInterval(refreshSpend, 30000);
  startFeed();
}

async function refreshHealth() {
  const healthBox = document.querySelector("#healthGrid");
  const overallVal = document.querySelector("#statOverallState");
  const overallSub = document.querySelector("#statOverallSub");
  const servicesCount = document.querySelector("#statServicesCount");
  const servicesSub = document.querySelector("#statServicesSub");
  const incidentsCount = document.querySelector("#statIncidentsCount");
  const lastPolled = document.querySelector("#lastPolledTime");

  try {
    const data = await api("/health");
    const summary = data.summary || {};
    const cards = data.cards || {};

    // Update Top Summary Row
    const state = summary.overall_state || "unknown";
    const dotClass = state === "healthy" ? "healthy" : state === "degraded" ? "degraded" : "unreachable";
    overallVal.innerHTML = `<span class="status-dot ${dotClass}"></span> ${esc(state.charAt(0).toUpperCase() + state.slice(1))}`;
    overallSub.textContent = `Probes checked ${summary.checked_at ? new Date(summary.checked_at).toLocaleTimeString() : "just now"}`;

    const totalEndpoints = Object.keys(cards).length;
    servicesCount.textContent = `${summary.healthy_count || 0} / ${totalEndpoints}`;
    servicesSub.textContent = `${summary.degraded_count || 0} degraded · ${summary.unreachable_count || 0} unreachable`;

    incidentsCount.textContent = String(summary.open_incidents ?? 0);
    if (lastPolled) {
      lastPolled.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    }

    // Render Health Cards
    healthBox.innerHTML = "";
    for (const [key, card] of Object.entries(cards)) {
      const cardEl = document.createElement("div");
      const cardState = card.state || (!card.reachable ? "unreachable" : card.healthy ? "healthy" : "degraded");
      cardEl.className = `health-card ${esc(cardState)}`;

      const reasons = card.reasons && card.reasons.length > 0 ? card.reasons : [];
      const hasPayload = card.payload && typeof card.payload === "object";

      cardEl.innerHTML = `
        <div class="health-card-header">
          <div>
            <div class="health-card-title">${esc(card.display_name || key)}</div>
            <div class="health-card-sub">${esc(key)}</div>
          </div>
          <span class="badge ${esc(cardState)}">${esc(cardState.replace("_", " "))}</span>
        </div>

        ${
          reasons.length > 0
            ? `
          <div class="health-card-reasons">
            <ul>
              ${reasons.map((r) => `<li>${esc(r)}</li>`).join("")}
            </ul>
          </div>
        `
            : `
          <div style="font-size: 0.8125rem; color: var(--color-success); display: flex; align-items: center; gap: 0.4rem;">
            <span>✓</span> All health checks passing
          </div>
        `
        }

        ${
          hasPayload
            ? `
          <details style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">
            <summary style="cursor: pointer; user-select: none;">View probe payload</summary>
            <pre style="background: var(--bg-input); padding: 0.5rem; border-radius: 4px; overflow-x: auto; margin-top: 0.25rem; color: var(--text-secondary);">${esc(
              JSON.stringify(card.payload, null, 2)
            )}</pre>
          </details>
        `
            : ""
        }

        <div class="health-card-footer">
          <span>Checked: ${card.checked_at ? new Date(card.checked_at).toLocaleTimeString() : "Live"}</span>
          <span>${card.reachable ? "HTTP 200 OK" : "Unreachable"}</span>
        </div>
      `;

      healthBox.appendChild(cardEl);
    }
  } catch (e) {
    if (healthBox) {
      healthBox.innerHTML = `<div class="empty-state">Unable to load presence probes: ${esc(e.message)}</div>`;
    }
  }
}

async function refreshSpend() {
  const spendBox = document.querySelector("#spendDetailBox");
  const statSpendVal = document.querySelector("#statSpendVal");
  const statSpendSub = document.querySelector("#statSpendSub");

  try {
    const s = await api("/spend");
    const cap = s.budgets ? s.budgets.per_incident_usd : null;
    const spent = s.spent_usd || 0;
    const capVal = typeof cap === "number" && !isNaN(cap) ? cap : null;
    const pct = capVal && capVal > 0 ? Math.min(100, (spent / capVal) * 100) : 0;

    // Update Top Summary Stat
    if (statSpendVal) {
      statSpendVal.textContent = `$${spent.toFixed(2)}`;
    }
    if (statSpendSub) {
      statSpendSub.textContent = capVal !== null ? `of $${capVal.toFixed(2)} cap` : "No limit set";
    }

    // Detail Box
    const budgets = s.budgets || {};
    spendBox.innerHTML = `
      <div class="gauge-track">
        <div class="gauge-fill ${pct > 80 ? "hot" : ""}" style="width: ${pct}%"></div>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 1rem;">
        <span>Spent: <strong>$${spent.toFixed(4)}</strong> ${capVal !== null ? `of $${capVal.toFixed(2)} per-incident cap` : ""}</span>
        <span>Storage: <strong style="color: ${s.db_connected ? "var(--color-success)" : "var(--color-warning)"}">${s.db_connected ? "Connected" : "Offline"}</strong></span>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin-top: 1rem;">
        <div class="stat-tile" style="padding: 0.75rem;">
          <span class="stat-label">Devin SWE Cap</span>
          <span style="font-size: 1rem; font-weight: 600; color: var(--text-main);">${formatMoney(budgets.devin_usd)}</span>
        </div>
        <div class="stat-tile" style="padding: 0.75rem;">
          <span class="stat-label">LLM Triage Cap</span>
          <span style="font-size: 1rem; font-weight: 600; color: var(--text-main);">${formatMoney(budgets.llm_usd)}</span>
        </div>
        <div class="stat-tile" style="padding: 0.75rem;">
          <span class="stat-label">Sarvam Voice Cap</span>
          <span style="font-size: 1rem; font-weight: 600; color: var(--text-main);">${formatMoney(budgets.sarvam_usd)}</span>
        </div>
        <div class="stat-tile" style="padding: 0.75rem;">
          <span class="stat-label">Smallest AI Cap</span>
          <span style="font-size: 1rem; font-weight: 600; color: var(--text-main);">${formatMoney(budgets.smallest_usd)}</span>
        </div>
      </div>
    `;
  } catch (e) {
    if (spendBox) {
      spendBox.innerHTML = `<div class="empty-state">Unable to load budget metrics: ${esc(e.message)}</div>`;
    }
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
    // Reconnects automatically
  };
}
