# PocketSRE 🛡️🎙️
> **The Autonomous, Budget-Governed On-Call SRE Companion**  
> *Built as an overnight solo hackathon project for [HackaThoni 2026](https://hackathoni.in) (Alappuzha, Kerala) | Primary Track: **Track 02: Voice & Language ("Beyond English")***

[![HackaThoni 2026](https://img.shields.io/badge/HackaThoni-Track%2002%3A%20Voice%20%26%20Language-orange?style=for-the-badge)](https://hackathoni.in)
[![Status: Development Concluded](https://img.shields.io/badge/Status-Development%20Concluded-red?style=for-the-badge)](docs/PLAN.md)
[![Python 3.14+](https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.165+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.14+-e92063?style=for-the-badge&logo=pydantic)](https://docs.pydantic.dev)
[![discord.py](https://img.shields.io/badge/discord.py-2.7+-5865F2?style=for-the-badge&logo=discord)](https://discordpy.readthedocs.io)
[![NeonDB](https://img.shields.io/badge/NeonDB-Serverless%20Postgres-00E599?style=for-the-badge&logo=postgresql)](https://neon.tech)

---

> [!WARNING]
> ### 🛑 Solo Hackathon Reality & Scope Notice
> **Development on PocketSRE has concluded.** As an overnight solo build within a strict 12-hour window, development stopped at the foundational **Discord Bot + Signed Mobile Web Console** stage.
> 
> * **Track 02 (Voice & Language) Truncation:** PocketSRE originally targeted Track 02 with multimodal voice notes (`.ogg`), Sarvam AI (`saaras:v4` STT + `bulbul:v3/v4-flash` TTS), and live Discord voice channel triage. In this solo build with limited time, **interactive voice was deferred and is 0% implemented**; the Sarvam API keys in config are dormant.
> * **No Conversational Free-Text Chat:** PocketSRE is **not** a conversational AI chat agent. Mentioning `@PocketSRE` with casual messages like *"@PocketSRE Yuki de services ellam okay aano ? I just need a simple reply"* will **NOT** return any conversational reply. The mention handler only triggers on three rigid paths: `"approve"` text commands, status queries (returning a formatted Discord embed), or incident keywords (opening a formal incident card).
> * **PRD vs. Implementation:** `docs/PRD.md` remains the original overarching hackathon vision document. This README, along with [docs/PLAN.md](file:///media/ivintitus/Data/My%20Projects/Side/PocketSRE/docs/PLAN.md) and [docs/tracks.md](file:///media/ivintitus/Data/My%20Projects/Side/PocketSRE/docs/tracks.md), reflects the **actual working reality, limitations, and solo stopping point**.

---

## 📌 The Original Pitch vs. Delivered Reality

* **The Vision:**  
  > *"PocketSRE is a speech-led, budget-governed on-call SRE companion that lets engineers triage, diagnose, and resolve production outages entirely over Discord in pure English, native Malayalam or Hindi, or natural code-mixed speech without opening a laptop."*
* **The Delivered Reality:**  
  > **A Discord-first and signed web-console SRE companion that runs bounded, least-privilege runbooks over SSH against live OCI infrastructure, enforces hard budget caps and loop guards, ingests presence alerts, and renders static multilingual embed titles across English, Hindi, Malayalam, Hinglish, and Manglish.**

---

## 🚦 Reality Matrix: What Works vs. Limitations

### ✅ What Actually Works (Verified)
1. **Out-of-Band SSH Execution:**
   - Connects to the target Project Yuki VM over Paramiko SSH using an Ed25519 key as unprivileged user `pocketsre`.
   - Strict command whitelist validated against `/etc/sudoers.d/pocketsre` covering Docker (`restart`, `stop`, `start`, `logs`, `inspect`, `top`, `ps`, `stats`, `prune`), Nginx (`restart`, `status`, `nginx -t`), and systemd journals.
2. **Discord Slash Commands:**
   - `/status`: Live presence health checks across all Yuki routes + open incident count.
   - `/approve <incident_id>`: Approves container restart runbook for an incident directly from chat.
   - `/triage <service> <summary>`: Manually creates an incident.
   - `/pocketsre avatar [kiwi|vikram]`: Switches active persona for the server.
   - `/pocketsre help`: Displays persona and language presentation details.
3. **Interactive Discord Incident Cards:**
   - Action buttons: `[Fetch logs]`, `[Inspect]`, `[Approve & Restart]` (lead-only), `[Deny]`, and `[Dispatch Devin fix]`.
   - Cards switch to a `"Working…"` state during SSH execution, acknowledge interactions within 3 seconds, and disable cleanly upon the 10-minute Discord view timeout.
4. **Signed Mobile Web Console & Mission Control:**
   - Ephemeral 15-minute cryptographically signed HMAC token (`make_console_link`).
   - Incident Console (`/console/`): Recommends safe next actions, groups tools by category (diagnostics, recovery, advanced), verifies pre-flight availability, prompts with confirmation modals for mutating actions, and renders ANSI-sanitized logs.
   - Mission Control (`/console/mission-control.html`): Displays overall health metrics, open incidents, null-safe budget gauges, and a live SSE feed (`/api/console/stream`).
5. **Observability & Autonomy Governance:**
   - **Presence Poller:** Background poller checks Yuki endpoints (`central`, `discord`, `horiz`, `telegram`) every 15s with a 2-consecutive-failure flap dampener.
   - **Discord Webhook Ingest:** Listens for host watchdog alerts and filters noise using Gemini Decision 1 (`gemini-decision-1`) or keyword fallback.
   - **Hard Budget Governor:** Enforces a $5.00/incident cap and provider limits via NeonDB ledger.
   - **Loop Guard:** Capped at 3 mutating trials; duplicate mutations trigger an immediate halt and post a 4-Pillar Analyst Dossier.

---

### ⚠️ Known Limitations, Quirks & Bugs
1. **No Interactive Voice (0% Audio):**
   - No audio decoding, no voice note parsing, no Sarvam Saaras STT, no Sarvam Bulbul TTS, and no Discord voice channel gateway.
2. **No Conversational Free-Text Exchange:**
   - If a message mentions `@PocketSRE` with general conversational questions (e.g. asking for a simple reply or chatting about services), the bot is **completely silent**.
   - It only evaluates specific keywords: `"approve"`, status check markers (which return a formal embed card), or incident keywords (which open an incident).
3. **Template-Only Multilingual Mirroring:**
   - Language detection uses simple regex and keyword matching in `src/app/persona/presentation.py`.
   - It selects pre-written template titles and intros in English, Hindi, Malayalam, Hinglish, or Manglish for Discord embeds. It does **not** generate dynamic multilingual conversational text.
4. **In-Memory Server Persona Volatility:**
   - Selected avatars (`kiwi` vs `vikram`) are stored in an in-memory dictionary (`guild_personas`) and reset back to default on container restart.
5. **Incident Correlation Boundaries:**
   - The presence poller only auto-resolves incidents that it opened. Incidents opened via webhook or manual triage must be resolved manually.
   - Downstream microservice cascades (e.g. Redis dying and causing API and Bot failures) open separate incidents without cross-service root-cause grouping.
6. **SWE Auto-Fixing Scope:**
   - Devin dispatch creates a session URL via Cognition AI API; however, PR tracking requires GitHub PAT and Linear keys, and PocketSRE never auto-merges code.

---

## 🏛️ System Architecture (Out-of-Band Two-VM Topology)

```
                               ┌────────────────────────────────────────────────────────┐
                               │                   INCIDENT INGESTION                   │
                               │   • Discord Webhook Monitor (Host Watchdog)            │
                               │   • Yuki Presence Poller (/presence/{central,etc})     │
                               │   • Gemini Decision 1 Noise Filter (Decisions API)     │
                               └───────────────────────────┬────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                    OCI VM 1: POCKETSRE CONTROL PLANE (Out-of-Band VM)                       │
│  Container: `container_name: pocketsre-core` (Docker container on Python 3.14-slim)         │
│                                                                                             │
│  • Web Framework: FastAPI (Async event router, webhook listener, SSE /stream)               │
│  • Data Contracts: Pydantic v2 (Strict action schemas & runtime parameter validation)       │
│  • Storage: NeonDB (Serverless PostgreSQL for incidents, audit logs, and budget ledger)     │
│  • Governance: Loop Guard (3-trial limit) & Spend Governor ($5.00 incident cap)            │
│  • Remote Runner: Paramiko SSH Client (Mounts /app/.ssh/pocketsre_bot_ed25519)              │
│  • Static Webview: Mounted at /console (Vanilla HTML/CSS/JS, token-gated)                   │
└───────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                │
                                                │ Remote SSH over Private Network / OCI VCN
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                 OCI VM 2: TARGET MONITORED INFRASTRUCTURE (Project Yuki VM)                 │
│  Host: Ubuntu Linux (`yukihira` — 1 GB RAM Micro Instance + 4 GB Swap)                      │
│                                                                                             │
│  • Unprivileged System User: `pocketsre` (/etc/sudoers.d/pocketsre whitelisted commands)    │
│  • Monitored Containers: `yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`,          │
│                          `yuki-telegram-bot`, `yuki-redis`                                  │
│  • Host Services: NGINX Reverse Proxy, Docker Engine, PostgreSQL Socket                     │
│  • Telemetry Endpoints: https://yuki-net.ivin.site/presence/{central,discord,horiz,telegram}│
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
    ┌─────────────────────────────────┐                   ┌─────────────────────────────────┐
    │     PC: SRE MISSION CONTROL     │                   │     PHONE: ON-THE-GO DISCORD    │
    │   • Mobile-First Web Console    │                   │   • Discord Slash Commands      │
    │   • SSE Stream & Audit Log      │                   │   • Action Buttons (10m TTL)    │
    │   • 15-min HMAC Token Link      │                   │   • Signed Magic-Link Button    │
    └─────────────────────────────────┘                   └─────────────────────────────────┘
```

---

## 📁 Project Structure

```text
PocketSRE/
├── src/
│   ├── app/
│   │   ├── main.py              # FastAPI startup, lifespan, and static mounting
│   │   ├── config.py            # Pydantic BaseSettings (POCKETSRE_ prefix)
│   │   ├── api/                 # REST routes, signed console API, health endpoints
│   │   ├── bot/                 # Discord runtime, slash commands, views, and cards
│   │   ├── incidents/           # Presence poller, alert bridge, and incident service
│   │   ├── actions/             # Typed runbooks, sudoers mapping, and SSH executor
│   │   ├── ai/                  # LLM router, key rotation pool, and decision classifiers
│   │   ├── storage/             # NeonDB write-through persistence and migrations
│   │   ├── persona/             # Kiwi & Vikram presentation models and language regex
│   │   ├── swe/                 # Devin API dispatch and GitHub/Linear issue tracking
│   │   └── shared/              # Budget governor, RBAC, HMAC magic link, and contracts
│   └── web/dist/                # Static web console and mission control assets
├── docs/
│   ├── PRD.md                   # Full Hackathon Product Requirement Document (Vision)
│   ├── PLAN.md                  # Reality audit, post-mortem, and implementation status
│   ├── tracks.md                # HackaThoni Track 02 target alignment vs. reality
│   └── infra/
│       └── yuki_architecture.md # Target Yuki VM architecture & verified sudoers reference
├── tests/                       # Pytest test suite covering all core modules
├── scripts/
│   └── inject_mock_incident.sh  # Mock incident generator for rehearsal testing
├── Dockerfile                   # python:3.14-slim production container definition
├── docker-compose.yml           # Compose specification mounting SSH keys and docs
└── pyproject.toml               # Python package configuration and dependencies
```

---

## 🛠️ Technology Stack & Operational Status

| Component | Technology | Implemented Status |
|---|---|---|
| **Runtime & Language** | Python 3.14+ | Active (`python:3.14-slim`) |
| **API Framework** | FastAPI 0.165+, Uvicorn 0.54+ | Active (`/health`, `/api/*`) |
| **Validation** | Pydantic v2.14+ | Active (Strict contract enforcement) |
| **Discord Bot** | `discord.py` 2.7+ | Active (Slash commands & action views) |
| **Cloud Execution** | Paramiko 5.1+ SSH Client | Active (Non-root `pocketsre` remote runner) |
| **Persistent Storage** | NeonDB (Serverless PostgreSQL) | Active (Incidents, audit logs, budget ledger) |
| **Web Console** | Vanilla HTML / CSS / JS (`web/dist`) | Active (Token-gated `/console/`) |
| **Decision Engine** | Gemini Decision 1 (`gemini-decision-1`) | Active (Decisions API + keyword fallback) |
| **Autonomous SWE** | Cognition AI Devin API | Partial (Session creation active with key) |
| **Speech (Track 02)**| Sarvam AI (`saaras:v4`, `bulbul:v3/v4`) | **Unimplemented / Deferred (0%)** |
| **Discord Voice** | `discord-ext-voice-receive` / Opus RTP | **Unimplemented / Deferred (0%)** |

---

## ⚡ Setup & Configuration Guide

### 1. Prerequisites
* Docker & Docker Compose
* Target VM with OpenSSH Server and unprivileged `pocketsre` user with `/etc/sudoers.d/pocketsre`
* Discord Bot Token (Message Content and Guild Member intents enabled)
* NeonDB PostgreSQL database URL (optional: falls back to in-memory store)
* Google Gemini API key(s) (optional: falls back to keyword heuristics)

### 2. Environment Configuration
Copy `.env.example` to `.env` and populate necessary variables:
```env
# Discord Settings
POCKETSRE_DISCORD_TOKEN="your_discord_bot_token"
POCKETSRE_DISCORD_GUILD_ID="your_discord_server_id"
POCKETSRE_DISCORD_ALERT_CHANNEL_ID="your_alerts_channel_id"

# AI & Decision Models
POCKETSRE_AI_PROVIDER="gemini"
POCKETSRE_GEMINI_API_KEYS="primary_key,fallback_key"
POCKETSRE_GEMINI_MODEL="gemini-2.0-flash-lite"
POCKETSRE_DECISION_PROVIDER="gemini_decision"

# Target Infrastructure Remote SSH
POCKETSRE_TARGET_SSH_HOST="<TARGET_YUKI_VM_IP>"
POCKETSRE_TARGET_SSH_USER="pocketsre"
POCKETSRE_TARGET_SSH_KEY_PATH="/app/.ssh/pocketsre_bot_ed25519"

# Security & Console
POCKETSRE_MAGIC_LINK_SECRET="your_cryptographic_secret_key"
POCKETSRE_PUBLIC_BASE_URL="http://localhost:8000"
POCKETSRE_AUTONOMY_MODE="read_auto"

# Persistence & Budget
POCKETSRE_NEON_DATABASE_URL="postgres://..."
POCKETSRE_BUDGET_PER_INCIDENT_USD="5.00"
```

### 3. Running via Docker Compose
```bash
docker compose up -d --build
```

### 4. Running the Test Suite
Tests execute within the Python 3.14 container environment:
```bash
docker compose exec pocketsre-core pytest
```

---

## 👤 Solo Developer & HackaThoni 2026 Acknowledgments

* **Solo Architect & Developer:** Ivin Titus
* **Target Workload:** Project Yuki Infrastructure (`yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`, `yuki-telegram-bot`, `yuki-redis`)
* **Solo Sprint Verdict:** Building an out-of-band autonomous SRE agent solo in a 12-hour overnight hackathon required strict scope triage. PocketSRE proved that safe, out-of-band, budget-governed infrastructure remediation can be operated reliably without opening a laptop. While voice and conversational chat were cut due to solo build time constraints, the core operational foundation achieved complete safety, auditability, and zero-timeout mobile console access.

---
*PocketSRE is open-source under the [MIT License](LICENSE).*
