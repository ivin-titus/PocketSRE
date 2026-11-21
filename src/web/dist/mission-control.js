const token = new URLSearchParams(window.location.search).get("token");
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(path) {
  const res = await fetch(`/api/console${path}${path.includes("?") ? "&" : "?"}token=${encodeURIComponent(token || "")}`);
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `${res.status}`);
  return res.json();
}

if (!token) {
  document.querySelector("#app").innerHTML = "<h1>Mission Control</h1><p>A signed link is required.</p>";
} else {
  refreshHealth();
  refreshSpend();
  setInterval(refreshHealth, 15000);
  startFeed();
}

async function refreshHealth() {
  const box = document.querySelector("#health");
  try {
    const { cards } = await api("/health");
    box.innerHTML = "";
    for (const [name, c] of Object.entries(cards)) {
      const cls = !c.reachable ? "unreachable" : c.healthy ? "healthy" : "unhealthy";
      const state = !c.reachable ? "unreachable" : c.healthy ? "healthy" : "degraded";
      const reasons = c.reasons.length ? `<ul>${c.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : "";
      box.insertAdjacentHTML("beforeend", `<div class="card ${cls}"><h3>${esc(name)}</h3><p>${state}</p>${reasons}</div>`);
    }
  } catch (e) {
    box.innerHTML = `<p class="muted">${esc(e.message)}</p>`;
  }
}

async function refreshSpend() {
  const box = document.querySelector("#spend");
  try {
    const s = await api("/spend");
    const cap = s.budgets.per_incident_usd;
    const pct = cap > 0 ? Math.min(100, (s.spent_usd / cap) * 100) : 0;
    box.innerHTML = `
      <h2>Spend</h2>
      <div class="gauge"><div class="${pct > 80 ? "hot" : ""}" style="width:${pct}%"></div></div>
      <p class="muted">$${s.spent_usd.toFixed(4)} of $${cap} · Devin cap $${s.budgets.devin_usd} · LLM cap $${s.budgets.llm_usd} · DB ${s.db_connected ? "connected" : "offline"}</p>
    `;
  } catch (e) {
    box.innerHTML = `<p class="muted">${esc(e.message)}</p>`;
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
