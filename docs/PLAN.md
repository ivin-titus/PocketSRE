# PLAN.md — Post-Hackathon Reality Audit & Sprint Conclusion

> **Status:** **DEVELOPMENT CONCLUDED / STOPPED**  
> **Final Architecture:** Discord Bot + Signed Mobile Web Console + Paramiko SSH Runbooks  
> **Target Track Outcome:** Track 02 (Voice & Language) reduced to Discord bot text/embeds + template multilingual presentation; voice notes, live voice channels, and conversational text exchange were **deferred due to hackathon time limits**.

---

## 1. Executive Summary: Solo Build Vision vs. What Landed

PocketSRE was designed for **HackaThoni 2026 Track 02: Voice & Language ("Beyond English")** as an overnight solo build with the goal of providing an autonomous, speech-first on-call SRE companion that engineers could converse with in English, Malayalam, Hindi, or code-mixed speech (Manglish/Hinglish) from a phone on a houseboat without opening a laptop.

**The Reality at the Sprint Stopping Point:**
As a solo build within a strict 12-hour overnight window, building both an out-of-band SRE control plane and an Indic speech AI stack was a heavy lift. The solo developer prioritized building a stable, crash-proof operational core (SSH execution, restricted sudoers, presence polling, budget caps, loop guards, signed mobile web console) over fragile experimental voice pipelines. 

As a consequence:
1. **Interactive Voice is 0% Complete:** Neither async voice notes (Sarvam Saaras STT + Bulbul TTS) nor live Discord voice channels were built. The speech API keys in config are dormant.
2. **Interactive Text Conversation is NOT Implemented:** PocketSRE is **not** a conversational chatbot. It does not engage in free-form text dialogue. Casual inquiries like `"@PocketSRE Yuki de services ellam okay aano ? I just need a simple reply"` fail to receive any reply.
3. **Discord Bot Operational Commands Work:** Slash commands (`/status`, `/approve`, `/triage`, `/pocketsre avatar`, `/pocketsre help`) and incident card buttons (`Fetch logs`, `Inspect`, `Approve & Restart`, `Deny`, `Dispatch Devin fix`) work as intended over Paramiko SSH against the live Project Yuki VM.
4. **Incidents Work Within Rigid Boundaries:** Presence polling, webhook alerting, loop guards, and signed console triage work, but remain limited by rigid heuristic classifiers and lack of cross-incident correlation.

Development is officially **concluded here** with no plans to continue.

---

## 2. Capability Scorecard (Vision vs. Implemented Reality)

| Capability | Planned Vision (PRD) | Implemented Reality | Operational Status |
|---|---|---|---|
| **Out-of-Band SSH Execution** | Non-root `pocketsre` SSH execution on target VM | Paramiko SSH client running typed runbooks against verified `/etc/sudoers.d/pocketsre` whitelist | ✅ **100% Working** |
| **Typed Runbook Whitelist** | Whitelisted Docker, Nginx, and host diagnostics | Full coverage of logs, inspect, top, restart, stop, start, stats, ps, prune, nginx status/test/restart, and journalctl | ✅ **100% Working** |
| **Discord Slash Commands** | Complete slash suite for triage and ops | `/status`, `/approve`, `/triage`, `/pocketsre avatar`, `/pocketsre help` implemented and synced | ✅ **95% Working** |
| **Signed Mobile Web Console** | Anti-timeout mobile console with live log tailing | Token-gated `/console/` with "What should I do next?", grouped tools, pre-flight checks, confirmation modal, and ANSI-sanitized logs | ✅ **95% Working** |
| **Mission Control Dashboard** | Central operational dashboard with live SSE stream | `/console/mission-control.html` with granular health states, open incident count, spend gauge, and live SSE feed | ✅ **95% Working** |
| **Presence Poller** | Dual-channel proactive monitoring of Yuki endpoints | Polls `/presence/{central,discord,horiz,telegram}` every 15s with 2-failure flap threshold; auto-resolves its own incidents | ✅ **90% Working** |
| **Webhook Alert Ingestion** | Ingest host watchdog alerts in real-time | Listens to Discord webhook messages; classifies via Gemini Decision 1 / keyword heuristics | ✅ **85% Working** |
| **Budget Governor** | Hard $5 incident cap & provider limits | Thread-safe spend tracker enforcing incident and provider flat/daily caps before calls; persisted in NeonDB | ✅ **90% Working** |
| **Loop Guard & Escalation** | Prevent runaway retry loops; 4-pillar dossier | Capped at 3 mutating trials; blocks duplicate mutations; generates 4-pillar dossier and halts safely | ✅ **90% Working** |
| **Autonomous SWE Dispatch** | Dispatch Devin sessions + Linear/GitHub issues | Devin API `POST /v1/sessions` dispatch works with key; stub fallback without key; PR watch loop polls merge state | ⚠️ **Functional / Partial** |
| **Text Multilingual Presentation** | Adaptive code-mixing in English, Malayalam, Hindi | Regex/keyword detector (`src/app/persona/presentation.py`) formats embed titles/intros in 5 template styles | ⚠️ **Template-Only (No Dynamic Gen)** |
| **Free-Text Conversational Chat** | Interactive conversational on-call triage | Mention handler only looks for specific operational intents; no conversational chat loop exists | ❌ **Broken / Missing** |
| **Sarvam Speech (Voice Notes)** | Mode B: `.ogg` voice notes, Saaras STT, Bulbul TTS | Unimplemented. `sarvam_api_key` in config is unused. | ❌ **0% (Deferred)** |
| **Live Discord Voice Channel** | Mode C: Live voice channel war room | Unimplemented. RTP Opus decoding and voice gateway deferred. | ❌ **0% (Deferred)** |
| **Adaptive Incident Memory** | Self-learning playbooks in `learned_playbooks` | Table not created in DDL; learning loop from human lead approvals not implemented. | ❌ **0% (Deferred)** |

---

## 3. Deep Dive: Why Free-Text Messages Fail (The "No Reply" Bug)

Responders testing PocketSRE in Discord noticed that messages such as:
> `"@PocketSRE Yuki de services ellam okay aano ? I just need a simple reply"`

receive **absolutely no reply** from the bot. 

### Technical Root Cause in `src/app/bot/discord_runtime.py`:
1. **The Bot Is Not a Conversational Agent:** PocketSRE has no chat completion loop, no conversational context buffer, and no general LLM reply handler. It is strictly an operational event dispatcher.
2. **Rigid Branching in `on_message`:** When the bot is mentioned (`bot.user in message.mentions`), execution enters lines 670–751 of `discord_runtime.py`. It evaluates only three hardcoded execution paths:
   - **Path A: Approval Check:** If `"approve"` is in the message, it runs `_approve_text_path()`.
   - **Path B: LLM / Keyword Classification:** It calls `classify_message()` or `is_status_query()`.
     - If classified as `intent == "status"`: It sends a structured Discord Embed (`status_embed`) listing container checkmarks. It **never** sends a plain-text conversational answer (such as *"Yes, Yuki services are fine"*).
     - If classified as `intent == "incident"`: It creates a formal Incident object and posts an `alert_embed` action card with buttons.
   - **Path C: Down/Crash Keyword Fallback:** If words like `"down"`, `"crash"`, `"error"`, `"broken"` appear, it opens a P2 incident.
3. **The Fall-Through Black Hole:**
   If the LLM classifier (`classify_message`) returns `intent: "other"` (or if LLM keys are absent, rate-limited, or timing out) AND the message does not match exact status markers (`_STATUS_MARKERS`) or incident keywords, **the handler executes nothing**. It simply hits `await bot.process_commands(message)` and exits silently.
4. **Mention Parsing Failures:**
   If a user types `@PocketSRE` as plain text without selecting Discord's autocomplete tag (`<@bot_user_id>`), `bot.user in message.mentions` evaluates to `False`, causing the bot to ignore the message completely.

---

## 4. Discord Bot Commands Reality (What Works vs. Edge Cases)

### Working Slash Commands
All slash commands are registered under `@app_commands.guild_only()` and enforce Discord role mapping:
- **`/status`:** Queries `actions.presence.health_reasons()` across all four Yuki presence routes and returns a color-coded Discord embed with open incident counts and active autonomy mode.
- **`/approve <incident_id>`:** Allows a lead to approve container restarts directly from Discord chat without clicking card buttons. Matches full or prefix incident IDs.
- **`/triage <service> <summary>`:** Manually opens a P2 incident for a monitored Yuki container.
- **`/pocketsre avatar <kiwi|vikram>`:** Sets the server's persona (Kiwi = empathetic companion; Vikram = formal corporate SRE).
- **`/pocketsre avatar`:** Displays the currently active server persona.
- **`/pocketsre help`:** Displays the persona and language mirroring explanation card.

### Working Interactive Card Buttons
Incident alert cards render five interactive UI buttons:
- **`[Fetch logs]`:** Executes `sudo docker logs --tail 50 <container>` over SSH and posts a green/orange report embed.
- **`[Inspect]`:** Executes `sudo docker inspect <container>` over SSH.
- **`[Approve & Restart]`:** Requires `SRE-Lead` role; executes `sudo docker restart <container>` over SSH, followed by a 3-second sleep and post-execution verification via `PresenceProbe`.
- **`[Dispatch Devin fix]`:** Requires `SRE-Lead` role; posts to `https://api.devin.ai/v1/sessions` and initiates the background PR watch task.
- **`[Deny]`:** Cancels the pending action and disables the button.

### Known Discord Quirks & Bugs
- **10-Minute View Expiry:** Discord interaction views expire after 600 seconds. After 10 minutes, buttons are disabled and the footer updates to instruct responders to use `/approve` or the signed console link.
- **Volatile Guild Personas:** Server persona choices are held in-memory (`guild_personas: dict[int, Persona]`) in the Python process. Restarting the Docker container resets all guilds back to `POCKETSRE_PERSONA_DEFAULT` (`kiwi`).
- **DM Guard Rejection:** All slash commands reject direct messages (DMs) by design because DMs lack server roles, preventing RBAC role evaluation.

---

## 5. Incident Lifecycle & Autonomy Edge Cases

### Ingestion & Flap Damping
- **Presence Poller Flap Threshold:** The poller requires **2 consecutive failed polls** (`flap_threshold = 2`) before opening an incident. Transient network blips or momentary drops will not page the channel.
- **Isolation of Resolution:** The poller will **only** resolve incidents whose source is `presence_poller:<route>`. It will never auto-resolve an incident opened manually via `/triage` or ingested via webhook, avoiding premature closure of unrelated outages.

### Autonomy Policy Modes
- **`read_auto` (Default):** Read-only diagnostics (`fetch_service_logs`, `inspect_service`) execute automatically upon incident creation and announce results in Discord; mutating restarts require human approval.
- **`strict_confirmation`:** All actions (including logs) require explicit human click approval.
- **`full_autonomy`:** Runs diagnostics and container restarts immediately without asking, announcing post-facto.

### Loop Guard & Break-Glass Escalation
- If a mutating action fails and is re-attempted on the same incident, or if an incident reaches **3 mutating trials** (`MAX_TRIALS_PER_INCIDENT`), the loop guard triggers `EscalationRequiredError`.
- It halts automated attempts and posts a **4-Pillar Analyst Dossier** embed to Discord detailing:
  1. What happened
  2. What was tried
  3. Why it halted
  4. Recommended next steps for the human lead

### Known Incident Bugs & Limitations
- **No Cross-Incident Correlation:** If `yuki-core-api` crashes, triggering downstream disconnections on `yuki-discord-bot` and `yuki-telegram-bot`, the system may open separate incidents for each service instead of correlating them to the root cause container.
- **Single Active Incident per Service:** `get_active_for_service()` dedups to a single open incident per service. Subsequent distinct errors on the same container while an incident remains open will not spawn new alerts.

---

## 6. Web Console & Mission Control Reality

The web application is served as static HTML, CSS, and Vanilla JavaScript from `src/web/dist/` (mounted by FastAPI at `/console/`). No Node.js runtime is required in production.

### Mobile Incident Console (`/console/?token=...`)
- **HMAC Token Gated:** Requires a 15-minute cryptographically signed token (`make_console_link`) containing `incident_id` and `actor_id`.
- **"What should I do next?":** Evaluates action history and recommends safe, non-destructive diagnostics (logs/inspect) first.
- **Tool Categorization & Pre-Flight:** Actions are grouped into *Recommended*, *Safe diagnostics*, *Recovery*, and *Advanced/Host*. Pre-flight checks disable incompatible tools with hover tooltips.
- **Mutating Action Confirmation:** Destructive actions trigger a modal detailing the exact command, target service, and side-effect warnings.
- **ANSI Stripping:** Raw terminal color escape sequences are sanitized via `stripAnsi` before rendering into scrollable code blocks.

### Operational Mission Control (`/console/mission-control.html?token=...`)
- **Summary Metrics:** Overall system state, healthy/degraded/unreachable/no-coverage counters, open incident count, and spend.
- **Granular Health Cards:** Real-time presence statuses with collapsible payload JSON.
- **Null-Safe Spend Display:** Shows `"Not configured"` or `"—"` rather than `$null`.
- **Live SSE Feed:** Subscribes to `/api/console/stream` for real-time poller alert events.

---

## 7. Track 02 Speech & Language: Final Verdict

| Track 02 Objective | Target Specification | Delivered Reality |
|---|---|---|
| **Malayalam Voice Interface** | Mode B/C Sarvam Saaras STT & Bulbul TTS | **0% implemented**; no audio pipelines exist. |
| **Multilingual Assistance** | Interactive bilingual SRE conversations | **Template presentation only** in Discord embed headers; no conversational text generation. |
| **Speech-Led Workflows** | Discord voice notes (`.ogg`) & voice channel triage | **0% implemented**; strictly restricted to Discord text buttons and slash commands. |
| **Code-Mixing Parsing** | Dynamic extraction of technical nouns in Manglish/Hinglish | **Regex wordlist matching** in `detect_language()` used exclusively for selecting static embed strings. |

---

## 8. Conclusion

PocketSRE succeeded in demonstrating that an out-of-band, budget-governed, non-root SRE control plane can remotely manage production container infrastructure safely over SSH with signed anti-timeout mobile webviews. 

However, because a 12-hour solo hackathon sprint was insufficient to deliver both rock-solid infrastructure safety and a complete Indian-language voice stack, the project stopped at the Discord-bot + Web-Console stage. All further development is concluded.
