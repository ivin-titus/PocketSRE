# PLAN.md — Phase 1 Functional Build Plan

**Scope:** Make PocketSRE Phase 1 (Mode A: text + magic-link console + SSH runbooks) genuinely functional end-to-end — testable by the operator against the real Yuki VM.

**Current state:** ~50% of Phase 1. Detection + execution spine + proactive *and* reactive Discord loops (live `/status`, `/approve`, mention triage, Devin dispatch) exist; persistence, console UI, budget governor, and LLM wiring remain absent.

## 0. Where we are vs what's pending

| Capability | Status | Notes |
|---|---|---|
| Presence poller (all deterministic triggers, dedup, auto-resolve) | ✅ Done | `incidents/poller.py`, tested |
| Discord webhook alert ingestion | ✅ Done | Parses alerts, creates incident, emits `opened` on the alert bridge |
| Service→container name resolution | ✅ Done | `actions/runbooks.py` aliases→pinned containers |
| Typed runbook whitelist (logs/restart/stop/start/inspect) | ✅ Done | Enum-mapped, validated params (`tail_lines` 1–500, safe-charset grep) |
| RBAC core gate (LEAD + approval for mutations) | ✅ Done | Enforced in `execute()`; Discord roles mapped via `actor_role_for()` |
| Magic-link token signing (HMAC, 15-min) | ✅ Done | Shared `shared/magic_link.py`; alert cards embed the console link |
| Yuki key pool + LLM router | ✅ Done | `ai/key_pool.py`, `ai/router.py`, tested |
| Infra docs local load (`docs/infra`) | ⚠️ Partial | Loads into prompt string; never injected (no LLM call) |
| FastAPI skeleton + incident CRUD + execute | ✅ Done | `/health`, `/api/incidents`, `/api/actions/plan`, `/api/actions/execute` |
| Docker packaging (`pocketsre-core`) | ⚠️ Partial | `python:3.14-slim` now; compose still lacks SSH/doc mounts |
| Audit log | ⚠️ Partial | In-memory only; no NeonDB/`audit_log.jsonl` |
| **SSH execution (Paramiko)** | ✅ Done | `actions/ssh_executor.py` — timeouts, exit-code capture, `POST /api/actions/execute` |
| **Tool-call registry** | ✅ Done | `actions/tools.py` — name/description/mutating per tool; LLM-ready schemas |
| **Autonomy mode enforcement** | ⚠️ Partial | `FULL_AUTONOMY` auto-runs + announces; `READ_AUTO` free-run vs `STRICT_CONFIRMATION` ask-gate not yet differentiated |
| **Proactive flow** | ✅ Done | Card→buttons→execute→report→resolution loop live incl. Devin dispatch button + mode badge |
| **Reactive flow** (`/status` live, free-text triage) | ⚠️ Partial | `/status` shows live presence per route + open incidents; mention/`pocketsre` messages triage via keyword heuristics (Gemini free-text parsing still pending) |
| **Discord RBAC + DM guards** | ✅ Done | `ROLE_PERMISSIONS` config (`SRE-Lead`→lead, `DevOps`→responder, `Junior-Dev`→viewer), `guild_only` on all commands, DM early-return, highest-rank wins |
| **Approval surfaces** (buttons, `/approve`, magic-link) | ⚠️ Partial | Buttons + `/approve` slash + `@PocketSRE approve` text path done; console-side approve pending |
| **Devin dispatch** (code-regression path) | ⚠️ Partial | `swe/dispatch.py` posts to `/v1/sessions` with stub fallback; button on cards (lead-gated); Linear/GitHub linking pending |
| **NeonDB persistence** | ❌ Pending | `storage/` empty; no driver in deps |
| **Budget governor** ($5 cap, per-provider ledger) | ❌ Pending | Nothing |
| **Loop guard / escalation dossier** | ❌ Pending | Nothing |
| **Web console UI** (incident page, action pills, logs) | ❌ Pending | 8-line stub |
| **Mission-control page** (health cards, spend gauge, SSE) | ❌ Pending | Nothing |
| **Knowledge upload + injection into triage** | ❌ Pending | No `/api/knowledge/upload`, no `/pocketsre learn-infra` |
| **GeminiClient wiring** | ❌ Pending | Protocol exists; real client ports from Yuki |
| `scripts/inject_mock_incident.sh` | ❌ Pending | Referenced in README; doesn't exist |

**Phase readiness:** Phase 1 ≈ 50% · Phase 2 (voice notes/code-mixing) = 0% · Phase 3 (live voice) = 0%

**Verified environment facts:**
- SSH to target VM works: `ssh -i ~/.ssh/pocketsre_bot_ed25519 pocketsre@161.118.252.7 'sudo /usr/bin/docker logs --tail 10 yuki-telegram-bot'`
- `/etc/sudoers.d/pocketsre` on Yuki VM is configured and `visudo -cf` validated (sudo 1.9+ compatible: trailing wildcards only, absolute paths, no `requiretty`).
- `docker logs *` wildcard permits extra args (`--tail N`), and `grep` pipelines work because grep runs outside sudo: `ssh ... 'sudo docker logs <c> | grep -i error'` — filters are part of the SSH shell string, not the sudo'd argv.
- Gemini keys already provisioned; `GeminiClient` ports directly from `project-yuki/chat/api/app/services/ai/clients/gemini.py`.

---

## 1. Interaction model (locked decisions)

**Surfaces (all three):**
- Discord slash commands (`/status`, `/triage`, `/approve`, `/actions`)
- Discord free-text messages (natural language triage; code-mixed Manglish/Hinglish inputs tolerated — language mirroring deferred to Phase 2)
- Signed magic-link web console (incident console + mission-control page)

**Autonomy modes** (`AUTONOMY_MODE`, replacing current `autonomy_mode` semantics):
| Mode | Reads | Mutations |
|---|---|---|
| `READ_AUTO` (default) | run freely, announce post-facto | always ask |
| `STRICT_CONFIRMATION` | ask | ask |
| `FULL_AUTONOMY` | run, announce | run, announce |

**No free-form CLI.** All remote operations are modeled as typed, well-described tool calls — one tool per command category (`inspect_docker`, `fetch_logs`, `restart_container`, `docker_stats`, `docker_ps`, `nginx_restart`, `disk_prune`, `service_journal`). Each tool maps to sudoers-whitelisted binaries; parameters are validated enums/strings, never raw shell. Optional filters (e.g. log grep pattern) are validated `[a-zA-Z0-9_.:|-]+` and applied in the remote shell pipeline, outside sudo.

**Approval flow:** mutating tool calls render a Discord card `[Approve] [Deny]` plus the magic-link. Approving executes the whitelisted command, returns a concise Discord report, and the console shows the full dossier. Full-autonomy mode runs without asking but always announces.

**Loop guard (anti-infinite-loop):** `max_trials_per_incident` (default 3) + "no identical runbook twice on one incident" + `max_incident_age_minutes` cap. When exceeded or remediation is outside the whitelist (e.g. host postgres socket), PocketSRE halts, generates the escalation dossier, and hands off to the lead — never retries.

**Budget governor:** per-provider budgets — `BUDGET_DEVIN_USD` (daily $), `BUDGET_LLM_USD` (Gemini = $0 free tier), `BUDGET_PER_INCIDENT_USD` ($5 default cap), plus `BUDGET_SARVAM_USD` / `BUDGET_SMALLEST_USD` guarding the metered speech credits (Sarvam 500 credits + Smallest.ai $60 provisioned; `POCKETSRE_SARVAM_API_KEY` and `POCKETSRE_SMALLEST_AI_API_KEY` in `.env`). Lockout at cap until manual override. Ledger persisted to NeonDB `budget_ledger`. Credit-burn hygiene: speech keys stay dormant until Phase 2, TTS/STT calls are cached and rate-limited per incident, and a `MOCK_SPEECH=true` test path replays fixtures instead of calling paid APIs.

---

## 2. Functional flows to implement

### 2.1 Proactive flow (observability → Discord)
```
poller/webhook alert → incident created → Discord card: diagnosis + proposed allowed actions
  → "May I run: fetch_logs(yuki-core-api)?" [Approve via reply/slash/console]
  → READ_AUTO diagnostics run; mutations gate on approval
  → execute whitelisted command(s) over SSH → parse stdout
  → concise Discord report + magic-link to full dossier on console
  → if code regression → "Dispatch Devin fix?" permission card → Devin session → PR link
  → on resolution → Discord summary card (actions taken, cost, uptime restored)
```

### 2.2 Reactive flow (human-initiated)
```
"is everything fine?" / /status / user reports an issue
  → presence snapshot + docker stats investigation
  → same propose→approve→execute→report loop as proactive
```

### 2.3 Simple issue
```
detect → investigate → run fixing runbook (e.g. restart) → transparent report (what ran, exit code, recovery verification)
```

---

## 3. Implementation steps (ordered critical path)

### Track A — Execution spine (blocks everything)
- **A1. ✅ `src/app/actions/ssh_executor.py`** — Paramiko SSH client: `AutoAddPolicy`, key from `target_ssh_key_path`, connect timeout 10s, exec timeout 30s, captures exit code/stdout/stderr. Per-call client (no singleton yet).
- **A2. ✅ Tool-call registry (`src/app/actions/tools.py`)** — Typed tools `{name, description, mutating}` for logs/inspect/restart/stop/start; LLM-ready `tool_schemas()`. Params validated (`tail_lines`, safe-charset grep → `shlex.quote`). Remaining tools to add: `docker stats`, `docker ps`, `nginx_restart`, `service_journal`, `disk_prune`.
- **A3. ✅ `ActionService.execute()`** — runs the tool over SSH, records exit code + output into audit (`POST /api/actions/execute`). Duration/cost fields still to add.
- **A4. ✅ Pre-flight integrity check** — `_preflight()` re-queries `/presence/<route>` via `PresenceProbe`; blocks mutations on `maintenance_mode == true`. Post-run `_post_verify()` marks `verified`/`executed_unverified`.
- **A5. Autonomy enforcement** — implement `READ_AUTO` / `STRICT_CONFIRMATION` / `FULL_AUTONOMY` gating in `ActionService` keyed off `AUTONOMY_MODE`; destructive flag on each tool drives the ask.
- **A6. ✅ Config deltas** — `max_trials_per_incident`, budget vars, `DEVIN_API_KEY`, `NEON_DATABASE_URL`, `LINEAR_API_KEY`, speech keys, `ROLE_PERMISSIONS`, `PUBLIC_BASE_URL` added. Still missing: `EXECUTION_PRIVILEGE_MODE`.

### Track B — Discord conversation flows
- **B1. ✅ RBAC guards** — `guild_only()` on all commands, `getattr(interaction.user, "roles", [])`, configurable `ROLE_PERMISSIONS` (`SRE-Lead` → lead/all incl. Devin dispatch, `DevOps` → responder/mutations, `Junior-Dev` → viewer/read-only), DM rejection.
- **B2. ✅ Alert card** — embed with summary + buttons (Fetch logs / Inspect / Approve & Restart / Dispatch Devin / Deny) + console link + autonomy-mode badge.
- **B3. ✅ Approval handler** — button callbacks + `/approve <incident_id>` + `@PocketSRE approve` text path → `ActionService.execute()`.
- **B4. ⚠️ Reactive commands** — `/status` live presence + open incidents (spend gauge pending Track D); `/triage` done; free-text mention triage uses keyword heuristics until GeminiClient lands.
- **B5. ✅ Result report** — `report_embed` posts status + truncated output; `resolution_embed` posts recovery summary.
- **B6. ⚠️ Devin dispatch card** — lead-gated `Dispatch Devin fix` button → `POST /v1/sessions` → session URL posted; stub fallback when `DEVIN_API_KEY` unset. PR link-back + Linear pending.
- **B7. ✅ Line-1 deferral** — `defer()` first in every handler (FAIL-1.1).

### Track C — Persistence (NeonDB)
- **C1. `storage/db.py`** — asyncpg (or psycopg) pool, `SELECT 1` keepalive every 4 min.
- **C2. DDL migration** — `incidents`, `audit_logs`, `budget_ledger`, `learned_playbooks`, `infra_knowledge_docs` per PRD §9.2.
- **C3. Swap in-memory stores** — `IncidentService`, `AuditLog`, budget ledger backed by DB; local `audit_log.jsonl` append-only fallback when DB unreachable.

### Track D — Budget governor
- **D1. `ai/budget.py`** — thread-safe `SpendTracker`; `record(provider, usd)`; `check(incident_id)` → locked/unlocked; per-provider + per-incident caps; manual override flag.

### Track E — Web console (Vite + vanilla CSS, token-gated)
- **E1. Console API** — token-validated endpoints: `GET /api/console/{incident_id}`, `POST /api/console/{incident_id}/actions/{tool}` (execute), `GET /api/console/{incident_id}/logs`, `POST /api/knowledge/upload`.
- **E2. Incident console page** — incident detail, allowed action pills, approve/execute buttons, log tail pane, dossier section.
- **E3. Mission-control page** — live health cards per service, spend gauge, SSE audit feed (`/stream`), incident list. Single-page, mobile-first.
- **E4. SSE `/stream`** — Server-Sent Events broadcasting audit entries + poller status.

### Track F — Knowledge & docs
- **F1. Knowledge injection** — `load_infra_context()` output injected into the triage prompt; top-3 chunk selection stays simple (filename/section match by service name — no vector DB for Phase 1).
- **F2. `deploy/sudoers.pocketsre`** — version the verified sudoers file in-repo (keeps whitelist ↔ tool registry in sync).
- **F3. `docs/infra/yuki_architecture.md`** — append verified SSH + sudoers notes.

### Track G — Verification & demo plumbing
- **G1. `scripts/inject_mock_incident.sh`** — mock trigger for crash/bug/socket-lock scenarios (README references it; it doesn't exist).
- **G2. Tests** — executor (mocked transport), tool registry param validation, autonomy gating, budget lockout, magic-link expiry, console API auth.
- **G3. Dockerfile/compose fixes** — `python:3.14-slim`, mount SSH key + `docs/infra` volumes per PRD compose snippet.

---

## 4. Deferred (Phase 2+, confirmed out of scope for Phase 1)
- Voice notes / Sarvam STT-TTS / code-mixed TTS replies (natural-language *text* input parsing is in-scope; Indic voice is Phase 2).
- Live voice channel (Phase 3).
- Learned playbooks auto-execution (schema lands with C2; learning loop is Phase 2).
- Tailscale/Terraform plugins, Sentry webhook, Linear wiring (Linear issue creation optional stretch in B6).
- Kiwi/Vikram avatar personas (tone presets land free with Gemini prompts — stretch only).

## 5. Definition of done (operator-testable)
1. `./scripts/inject_mock_incident.sh --scenario crash` → Discord card appears → approve → real `docker restart` runs on `161.118.252.7` → recovery verified → summary posted.
2. `/status` in Discord returns live presence + spend.
3. Magic-link opens incident console on phone; approving there executes over SSH.
4. Mission-control page shows live health cards, audit feed, spend gauge.
5. Read actions auto-run under `READ_AUTO`; mutations ask; `FULL_AUTONOMY` announces post-facto.
6. Loop guard escalates a locked-socket incident to a dossier after 3 trials — no infinite retry.
7. `make test` equivalent (`pytest tests/`) passes; `visudo -cf` clean on any sudoers change.
