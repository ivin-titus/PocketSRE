const app = document.querySelector("#app");
const token = new URLSearchParams(window.location.search).get("token");

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

if (!token) {
  app.innerHTML = "<h1>PocketSRE</h1><p>A signed incident link is required.</p>";
} else {
  load();
}

async function api(path, method = "GET") {
  const res = await fetch(`/api/console${path}${path.includes("?") ? "&" : "?"}token=${encodeURIComponent(token)}`, { method });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${res.status}`);
  }
  return res.json();
}

async function load() {
  let data;
  try {
    data = await api("/incident");
  } catch (e) {
    app.innerHTML = `<h1>PocketSRE</h1><p class="muted">${esc(e.message)}</p>`;
    return;
  }
  const inc = data.incident;
  app.innerHTML = `
    <h1>${esc(inc.service)}</h1>
    <p>
      <span class="badge ${esc(inc.severity)}">${esc(inc.severity.toUpperCase())}</span>
      <span class="badge ${esc(inc.status)}">${esc(inc.status)}</span>
      <span class="muted">${esc(inc.id)}</span>
    </p>
    <p>${esc(inc.summary)}</p>
    <p class="muted">Source: ${esc(inc.source)} · Opened: ${esc(inc.created_at)}</p>
    <h2>Runbooks</h2>
    <div class="pills" id="pills"></div>
    <h2>Spend</h2>
    <div id="spend"></div>
    <h2>Results</h2>
    <div id="results"></div>
    <h2>Audit feed</h2>
    <ul id="feed" class="feed"></ul>
    <p><a href="mission-control.html?token=${encodeURIComponent(token)}">Open Mission Control →</a></p>
  `;
  renderTools(data.tools);
  renderResults(data.action_results);
  refreshSpend();
  startFeed();
}

function renderTools(tools) {
  const box = document.querySelector("#pills");
  for (const t of tools) {
    const btn = document.createElement("button");
    btn.className = "pill" + (t.mutating ? " mutating" : "");
    btn.textContent = t.name;
    btn.title = t.description;
    btn.onclick = async () => {
      if (t.mutating && !window.confirm(`Approve mutating action ${t.name}?`)) return;
      btn.disabled = true;
      try {
        const qs = t.action === "fetch_service_logs" ? "&tail_lines=200" : "";
        const { result } = await api(`/action?action=${encodeURIComponent(t.action)}${qs}`, "POST");
        prependResult(result);
      } catch (e) {
        prependResult({ action: t.action, service: "", status: "failed", output: e.message });
      } finally {
        btn.disabled = false;
      }
    };
    box.appendChild(btn);
  }
}

function renderResults(results) {
  const box = document.querySelector("#results");
  box.innerHTML = "";
  for (const r of results.slice().reverse()) prependResult(r);
}

function prependResult(r) {
  const box = document.querySelector("#results");
  const div = document.createElement("div");
  div.className = "result";
  div.innerHTML = `
    <div><span class="status">${esc(r.action)} → ${esc(r.service)}</span> · <code>${esc(r.status)}</code> · <span class="muted">${esc(r.executed_at)}</span></div>
    ${r.output ? `<pre class="output">${esc(r.output)}</pre>` : ""}
  `;
  box.prepend(div);
}

async function refreshSpend() {
  try {
    const s = await api("/spend");
    const cap = s.budgets.per_incident_usd;
    const pct = cap > 0 ? Math.min(100, (s.spent_usd / cap) * 100) : 0;
    document.querySelector("#spend").innerHTML = `
      <div class="gauge"><div class="${pct > 80 ? "hot" : ""}" style="width:${pct}%"></div></div>
      <p class="muted">$${s.spent_usd.toFixed(4)} of $${cap} per-incident cap · DB ${s.db_connected ? "connected" : "offline"}</p>
    `;
  } catch (e) {
    document.querySelector("#spend").innerHTML = `<p class="muted">${esc(e.message)}</p>`;
  }
}

function startFeed() {
  const feed = document.querySelector("#feed");
  const es = new EventSource(`/api/console/stream?token=${encodeURIComponent(token)}`);
  es.onmessage = (m) => {
    const { kind, incident } = JSON.parse(m.data);
    const li = document.createElement("li");
    li.innerHTML = `<time>${new Date().toLocaleTimeString()}</time>${esc(kind)} — ${esc(incident.service)}`;
    feed.prepend(li);
  };
}
