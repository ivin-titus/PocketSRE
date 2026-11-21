# PLAN.md — Phase 1 Functional Build Plan

**Scope:** Make PocketSRE Phase 1 (Mode A: text + magic-link console + SSH runbooks) genuinely functional end-to-end — testable by the operator against the real Yuki VM.

**Current state:** ~60% of Phase 1. Detection + execution spine + proactive *and* reactive Discord loops + NeonDB write-through + token-gated console/mission-control pages exist; budget governor, loop guard, and LLM wiring remain absent.

## 0. Where we are vs what's pending

| Capability | Status | Notes |
|---|---|---|
| Presence poller (all deterministic triggers, dedup, auto-resolve) | ✅ Done | `incidents/poller.py` — 2-consecutive-failure flap threshold; resolves only incidents it opened (no cross-source resolution) |
| Discord webhook alert ingestion | ✅ Done | Layered gate: container-name + alert-keyword pre-filter, dedup per service, `opened` on alert bridge |
| Alert-vs-noise decision classification | ✅ Done | `ai/decision.py` — Gemini Decision 1 (`gemini-decision-1`, Decisions API: noul + choice verdicts, zero output tokens) behind `DECISION_PROVIDER`; `local` provider for Laya/Ollama-class models via `DECISION_BASE_URL`; budget-gated; keyword fallback |
| Service→container name resolution | ✅ Done | `actions/runbooks.py` aliases→pinned containers |
| Typed runbook whitelist | ✅ Done | Enum-mapped, validated params; covers every sudoers entry — logs/inspect/top per container, restart/stop/start, `docker ps -a`, `docker stats --no-stream`, `docker system prune -f`, nginx restart/status/`nginx -t`, `journalctl -u nginx|docker`, `systemctl status docker` |
| RBAC core gate (LEAD + approval for mutations) | ✅ Done | Enforced in `execute()`; Discord roles mapped via `actor_role_for()` |
| Magic-link token signing (HMAC, 15-min) | ✅ Done | Shared `shared/magic_link.py`; alert cards embed the console link |
| Yuki key pool + LLM router | ✅ Done | `ai/key_pool.py`, `ai/router.py`, tested |
| Infra docs local load (`docs/infra`) | ✅ Done | `load_infra_context(db)` → injected into every `classify_message` triage prompt (24KB cap); file fallback when DB empty |
| FastAPI skeleton + incident CRUD + execute | ✅ Done | `/health`, `/api/incidents`, `/api/actions/plan`, `/api/actions/execute` |
| Docker packaging (`pocketsre-core`) | ✅ Done | `python:3.14-slim`, no Node stage; compose mounts SSH key + `docs/infra` read-only; smoke-verified |
| Audit log | ✅ Done | `audit_logs` Neon write-through + optional `audit_log.jsonl` mirror |
| **SSH execution (Paramiko)** | ✅ Done | `actions/ssh_executor.py` — timeouts, exit-code capture, `POST /api/actions/execute` |
| **Tool-call registry** | ✅ Done | `actions/tools.py` — name/description/mutating per tool; LLM-ready schemas |
| **Autonomy mode enforcement** | ✅ Done | `READ_AUTO`: diagnostics auto-run on alert + announce post-facto, mutations still ask · `STRICT_CONFIRMATION`: everything is click-gated · `FULL_AUTONOMY`: auto-runs restart + announces |
| **Proactive flow** | ✅ Done | Card→buttons→execute→report→resolution loop live incl. Devin dispatch button + mode badge |
| **Reactive flow** (`/status` live, free-text triage) | ✅ Done | LLM classification (`ai/triage.py`) parses intent/service/severity; keyword heuristics remain deterministic fallback when router absent or LLM fails |
| **Discord RBAC + DM guards** | ✅ Done | `ROLE_PERMISSIONS` config (`SRE-Lead`→lead, `DevOps`→responder, `Junior-Dev`→viewer), `guild_only` on all commands, DM early-return, highest-rank wins |
| **Approval surfaces** (buttons, `/approve`, magic-link) | ✅ Done | Buttons + `/approve` slash + `@PocketSRE approve` text + console-side approve pills (click = approval, runs as LEAD). Discord cards immediately acknowledge clicks, switch button to "Working…" and disable it, display progress notices (up to 30s), provide next-steps guidance on failure/denial, and disable with a clear console/`/approve` fallback message upon 10-minute timeout. |
| **Devin dispatch** (code-regression path) | ✅ Done | `swe/dispatch.py` posts to `/v1/sessions` (stub fallback); `swe/tracker.py` — code-level → GitHub Issue + Linear `issueCreate`, infra-only → Linear only; `link_pr()` comments PR URL on both; `pr_status()` polls merge state; `pr_watch_consumer` task posts follow-ups (PR opened → merged-by → health re-check → resolution, stale-PR re-ping at `PR_WATCH_TIMEOUT_MINUTES`); PocketSRE never merges — human SWE owns merge; all gated by budget governor + lead role |
| **NeonDB persistence** | ✅ Done | `storage/db.py` — psycopg write-through for `incidents`/`audit_logs`/`budget_ledger` (PRD DDL), `SELECT 1` keepalive, JSONL audit mirror, open incidents restored into `IncidentService` on startup (`restore_from_db`); graceful in-memory fallback when `NEON_DATABASE_URL` unset |
| **Budget governor** ($5 cap, per-provider ledger) | ✅ Done | `shared/budget.py` — pre-call `check()` enforces provider caps (`BUDGET_DEVIN_USD`/`LLM`/`SARVAM`/`SMALLEST`) + $5/incident cap + optional `BUDGET_*_DAILY_USD` per-day caps → `BudgetExhaustedError`; Neon `budget_ledger` write-through with in-memory fallback; Devin dispatch gated + recorded (`DEVIN_SESSION_COST_ESTIMATE_USD`), LLM calls gated (+ `LLM_CALL_COST_ESTIMATE_USD`); `/api/console/spend` returns incident + provider totals vs caps |
| **Loop guard / escalation dossier** | ✅ Done | `_loop_guard` caps mutating trials (`MAX_TRIALS_PER_INCIDENT`) + blocks repeat mutations → `EscalationRequiredError` with 4-pillar dossier; Discord renders a dossier embed, APIs return 409 + dossier JSON, escalation audited |
| **Web console UI** (incident page, actions, logs) | ✅ Done | `/console/` — calm, mobile-first design with high-contrast hierarchy; header with severity, status, service, summary, and copyable incident ID; prominent "What should I do next?" section with primary safe action; categorized actions (Recommended, Safe diagnostics, Recovery, and Advanced/Host behind progressive disclosure); pre-flight availability checks with tooltips; modal confirmation with exact action, target service, and side-effect warning; compact result cards with ANSI stripping (`stripAnsi`), scrollable terminal code blocks, and copy buttons; structured API error handling; empty states for action history and audit feed |
| **Mission-control page** (overview, health, spend, SSE) | ✅ Done | `/console/mission-control.html` — operational overview with top summary metrics (overall system state, monitored services status breakdown, open incidents count, spend); compact health cards distinguishing Healthy, Degraded, Unreachable, No Coverage, and Not Configured with collapsible payload details; spend governor display replacing nulls with "Not configured" / "—" (never `$null`); live SSE audit feed with empty state |
| **Knowledge upload + injection into triage** | ✅ Done | `POST /api/knowledge/upload` (admin-secret gated, .md/.txt ≤256KB) → `infra_knowledge_docs` in Neon; `load_infra_context(db)` is DB-first, `docs/infra/` is the sanitized public fallback; injected into every triage prompt. Repo docs scrubbed of IP/key names (repo is public) — real topology goes via upload only. `/pocketsre learn-infra` deferred (upload API covers it) |
| **Gemini + OpenAI client wiring** | ✅ Done | `ai/clients/gemini.py` + `ai/clients/openai.py` (Yuki ports adapted to LLMProvider), `ai/factory.py` picks provider via `AI_PROVIDER`; wired into reactive triage |
| `scripts/inject_mock_incident.sh` | ✅ Done | Air-gapped trigger POSTs crafted crash/bug/socket-lock incidents to `/api/incidents`; verified against the container |

**Phase readiness:** Phase 1 ≈ 85% · Phase 2 (voice notes/code-mixing) = 0% · Phase 3 (live voice) = 0%

**Verified environment facts:**
- SSH to target VM works: `ssh -i ~/.ssh/pocketsre_bot_ed25519 pocketsre@<YUKI_VM_IP> 'sudo /usr/bin/docker logs --tail 10 yuki-telegram-bot'`
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
- **A6. ✅ Config deltas** — `max_trials_per_incident`, budget vars, `DEVIN_API_KEY`, `NEON_DATABASE_URL`, `LINEAR_API_KEY`, speech keys, `ROLE_PERMISSIONS`, `PUBLIC_BASE_URL` added. `EXECUTION_PRIVILEGE_MODE` also added.

### Track B — Discord conversation flows
- **B1. ✅ RBAC guards** — `guild_only()` on all commands, `getattr(interaction.user, "roles", [])`, configurable `ROLE_PERMISSIONS` (`SRE-Lead` → lead/all incl. Devin dispatch, `DevOps` → responder/mutations, `Junior-Dev` → viewer/read-only), DM rejection.
- **B2. ✅ Alert card** — embed with summary + buttons (Fetch logs / Inspect / Approve & Restart / Dispatch Devin / Deny) + console link + autonomy-mode badge.
- **B3. ✅ Approval handler** — button callbacks + `/approve <incident_id>` + `@PocketSRE approve` text path → `ActionService.execute()`.
- **B4. ✅ Reactive commands** — `/status` live presence + open incidents; `/triage` done; free-text mention triage runs through the LLM router (Gemini default, OpenAI-compatible via `OPENAI_BASE_URL`) with keyword fallback.
- **B5. ✅ Result report** — `report_embed` posts status + truncated output; `resolution_embed` posts recovery summary.
- **B6. ⚠️ Devin dispatch card** — lead-gated `Dispatch Devin fix` button → `POST /v1/sessions` → session URL posted; stub fallback when `DEVIN_API_KEY` unset. PR link-back + Linear pending.
- **B7. ✅ Line-1 deferral** — `defer()` first in every handler (FAIL-1.1).

### Track C — Persistence (NeonDB)
- **C1. ✅ `storage/db.py`** — psycopg sync driver, `SELECT 1` keepalive every 4 min.
- **C2. ✅ DDL migration** — `incidents`, `audit_logs`, `budget_ledger` per PRD §9.2 (`learned_playbooks`/`infra_knowledge_docs` deferred to Phase 2).
- **C3. ✅ Swap in-memory stores** — `IncidentService`/`AuditLog` write-through to DB; `audit_log.jsonl` mirror supported; in-memory fallback when `NEON_DATABASE_URL` unset.

### Track D — Budget governor
- **D1. `ai/budget.py`** — thread-safe `SpendTracker`; `record(provider, usd)`; `check(incident_id)` → locked/unlocked; per-provider + per-incident caps; manual override flag.

### Track E — Web console (dependency-free static assets, token-gated; Vite scaffold dropped — no Node on target)
- **E1. ✅ Console API** — `GET /api/console/incident|health|spend|stream`, `POST /api/console/action` — all HMAC-token-validated (`api/console.py`). `POST /api/knowledge/upload` still pending.
- **E2. ✅ Incident console page** — incident detail, tool pills (mutating = confirm gate), result/log panes, spend gauge, SSE feed, mission-control link.
- **E3. ✅ Mission-control page** — live presence cards per endpoint (15s auto-refresh), spend gauge vs per-incident cap, SSE audit feed.
- **E4. ✅ SSE `/api/console/stream`** — bridges poller `AlertBridge` open/resolved events + heartbeat.

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
- Voice persona output and Sarvam/Smallest speech integration remain deferred until the text persona/language layer is stable.

## 5. Definition of done (operator-testable)
1. `./scripts/inject_mock_incident.sh --scenario crash` → Discord card appears → approve → real `docker restart` runs on `<YUKI_VM_IP>` → recovery verified → summary posted.
2. `/status` in Discord returns live presence + spend.
3. Magic-link opens incident console on phone; approving there executes over SSH.
4. Mission-control page shows live health cards, audit feed, spend gauge.
5. Read actions auto-run under `READ_AUTO`; mutations ask; `FULL_AUTONOMY` announces post-facto.
6. Loop guard escalates a locked-socket incident to a dossier after 3 trials — no infinite retry.
7. `make test` equivalent (`pytest tests/`) passes; `visudo -cf` clean on any sudoers change.

## 6. Planned — Persona-aware multilingual interaction (text first, voice later)

This is a presentation-layer capability. It must not duplicate or alter incident policy, tool selection, RBAC, approval, autonomy, budget, loop-guard, audit, or SSH execution logic.

### 6.1 Persona profiles

- **Kiwi** — memorable cute anime SRE companion: warm, encouraging, lightly playful, concise during incidents, and technically precise when proposing actions. Use `src/assets/kiwi_icon.png` in Discord/web presentation where appropriate.
- **Vikram** — formal corporate SRE lead: concise, evidence-led, severity/action/verification oriented, and suitable for executive or enterprise channels. Use `src/assets/vikram_icon.png` where appropriate.
- Both personas must produce the same structured action request and receive identical authorization and safety enforcement. Only wording, formatting, iconography, and eventual voice profile differ.

### 6.2 Automatic language and code-mixing mirroring

- Normal messages should automatically detect the operator's response language/style; users should not need to address the bot by persona name or language handle.
- Mirror pure English, pure Hindi, pure Malayalam, Hinglish, Manglish, and natural mixed input by default.
- Add an explicit override later (`/pocketsre language auto|english|hindi|malayalam`) without changing the underlying incident/action contract.
- Extend triage output with language metadata (for example `response_language` and `code_mixed`) while retaining the existing structured fields for intent, service, severity, and summary.
- Keep service names, incident IDs, command names, tool names, and approval wording semantically exact; translated text must never become a shell command or tool identifier.

### 6.3 Shared response-rendering layer

- Add persona definitions and a renderer that consumes structured incident/action results and emits channel-neutral response content.
- Discord embeds, ordinary text replies, web-console labels, and future voice output should consume that same rendered response model.
- Add `/pocketsre avatar kiwi|vikram`, `/pocketsre avatar`, and `/help`; ordinary messages use the active/default persona automatically.
- Store the initial selection in memory or configuration; add Neon persistence only if cross-restart/guild preferences are needed.
- Provide deterministic Kiwi and Vikram templates for provider failures so persona behavior remains stable when the LLM is unavailable.

### 6.4 Verification requirements

- Fixture tests for English, Hindi, Malayalam, Hinglish, Manglish, and mixed messages.
- Persona snapshot/contract tests proving presentation differs while generated tool calls, parameters, permissions, and approval requirements remain identical.
- Tests proving ordinary messages resolve the active persona without requiring a persona handle.
- Budget tests proving text mirroring does not call Sarvam or Smallest.
- Docker test run remains the source of truth before marking this capability complete.

### 6.5 Voice integration after text stability

- Reuse the same persona and language metadata for voice-note STT and optional TTS; do not move incident logic into speech providers.
- Add Sarvam/Smallest behind provider interfaces with mock fixtures, per-incident rate limits, caching, and separate budget caps.
- Keep text as the default response path; generate audio only for voice workflows or explicit requests.
- Treat live voice channels as a later milestone after voice notes are stable and verified.
