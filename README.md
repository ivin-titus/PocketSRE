# PocketSRE 🛡️🎙️
> **The Autonomous, Budget-Governed On-Call SRE Companion**  
> *Built for [HackaThoni 2026](https://hackathoni.in) (Alappuzha, Kerala) | **Track 02: Voice & Language ("Beyond English")***

[![HackaThoni 2026](https://img.shields.io/badge/HackaThoni-Track%2002%3A%20Voice%20%26%20Language-orange?style=for-the-badge)](https://hackathoni.in)
[![Python 3.14+](https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.165+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.14+-e92063?style=for-the-badge&logo=pydantic)](https://docs.pydantic.dev)
[![discord.py](https://img.shields.io/badge/discord.py-2.7+-5865F2?style=for-the-badge&logo=discord)](https://discordpy.readthedocs.io)
[![Sarvam AI](https://img.shields.io/badge/Sarvam%20AI-Saaras%20%26%20Bulbul-purple?style=for-the-badge)](https://sarvam.ai)
[![NeonDB](https://img.shields.io/badge/NeonDB-Serverless%20Postgres-00E599?style=for-the-badge&logo=postgresql)](https://neon.tech)
[![Vite](https://img.shields.io/badge/Vite-8.3+-646CFF?style=for-the-badge&logo=vite)](https://vitejs.dev)
[![React](https://img.shields.io/badge/React-19.3+-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![Cognition Devin](https://img.shields.io/badge/SWE%20Engine-Devin%20API-black?style=for-the-badge)](https://cognition.ai)

---

## 📌 The One-Sentence Pitch
> **"PocketSRE is a speech-led, budget-governed on-call SRE companion that lets engineers triage, diagnose, and resolve production outages entirely over Discord in pure English, native Malayalam or Hindi, or natural code-mixed speech without opening a laptop."**

---

## 🌊 HackaThoni 2026: Why Track 02 (Voice & Language)?

Engineering incidents strike at the worst moments—while commuting, traveling on a houseboat in Alappuzha, or in bed at 2 AM. Triage on mobile is usually miserable: tiny terminals, fragile VPNs, multi-tab context switching, and high cognitive panic.

**PocketSRE was created specifically for Track 02: Voice & Language ("Beyond English")**:
* **DevOps Beyond English:** Global infrastructure tooling has historically forced 100% English interaction. PocketSRE treats **native Indian languages (Malayalam, Hindi)** as first-class citizens alongside standard English.
* **Natural Conversational Code-Mixing:** SREs under stress don't speak in pure textbook grammar—they code-mix technical jargon with their mother tongue (*"Kiwi, Yuki chat container down aayi, onnu check cheyth restart cheyyuo?"* or *"Vikram, production-il entha issue? Logs pull cheythu nokk"*). Powered by **Sarvam AI** (`saaras:v4` STT + `bulbul:v3/v4-flash` TTS), PocketSRE accurately parses technical nouns inside regional speech and mirrors the dialect naturally.
* **Zero-Forced-Dialect Guarantee:** Engineers who prefer clean English receive professional, concise English briefings with zero unwanted code-mixing.
* **Speech-Led On-Call Workflows:** Turn passive phone notifications into an active conversational war room—speak into Discord voice notes or jump into a live voice channel to triage outages hands-free.

---

## ✨ Key Features & Differentiators

### 1. 🎙️ Track 02 Voice & Mirroring Engine
* **Multimodal Discord Audio:** Intercepts audio voice notes (`.ogg`) and live voice channels.
* **Sarvam AI Audio Stack:** Sub-second speech transcription via `saaras:v4` and lifelike Indic speech synthesis via `bulbul:v3` / `bulbul:v4-flash`.
* **Zero-Cost Edge Fallback:** Seamlessly shifts to Microsoft `edge-tts` (`en-IN-PrabhatNeural`, `ml-IN-SobhanaNeural`, `hi-IN-SwaraNeural`) if API quotas expire.

### 2. 🎭 Dual-Avatar Persona Architecture
Toggle personalities instantly via Discord (`/pocketsre avatar kiwi` or `/pocketsre avatar vikram`):
* **Kiwi (Kiwi-chan):** Empathetic, warm, playful companion (*"Daijoubu Senpai! Yuki crashed, but I grabbed the logs. Should I restart it?"*). Purpose-built to lower adrenaline and panic during 2 AM outages.
* **Vikram:** Crisp, objective, formal senior enterprise SRE lead (*"Incident 501: Container yuki-core-api terminated by kernel OOM. Recommending immediate restart."*).

### 3. 🔐 Signed Magic-Link Web Console (The Anti-Timeout Architecture)
* **The Discord Trap:** Standard Discord interaction buttons timeout in **3 seconds** and often fail with `"Interaction failed"` on mobile or network jitter.
* **The Fix:** PocketSRE delivers a cryptographic JWT **Signed Magic-Link URL button** (`[🚨 Open Incident Console]`).
* Opens an ephemeral, responsive mobile webview (Vite + Vanilla CSS) where responders can tail Docker logs in real time, trigger runbooks, or approve actions with zero timeout constraints.

### 4. 🛡️ Bounded Safe Autonomy (The Anti-Rogue Sandbox)
* The AI is strictly prohibited from running arbitrary, unvetted bash commands (`rm -rf`, raw systemctl, etc.).
* All infrastructure actions are strictly typed **Pydantic v2 Enums** mapped to whitelisted binaries in `/etc/sudoers.d/pocketsre`.
* **Least-Privilege by Default:** Operates as non-root user `pocketsre` over Paramiko SSH.

### 5. 🧠 Adaptive Incident Memory (Self-Learning Playbooks)
* **Learns from Human SRE Leads:** When a senior engineer manually resolves or approves a fix (e.g., restarting Yuki's Hori-Z connector on `platform_not_connected`), PocketSRE records the error fingerprint in NeonDB.
* **Confidence-Scored Auto-Remediation:** On future recurrences, PocketSRE either surfaces a 1-tap suggestion or autonomously auto-remediates in `<500ms` when confidence $\ge 3$ with zero regressions.

### 6. 🚨 Radical Transparency & Break-Glass Emergency Console
* **Anti-Blackbox Guarantee:** When an issue exceeds its autonomous runbook whitelist (e.g., a locked host PostgreSQL UNIX domain socket requiring root), PocketSRE halts honestly instead of hallucinating.
* Generates a **4-Pillar Analyst Dossier** (<800ms) summarizing what happened, what was tried, why it halted, and recommended next steps.
* Unlocks an **Ephemeral Break-Glass Web Console** on the Lead's phone with diagnostic action pills, an interactive ad-hoc bash runner, and live SSE streaming logs.

### 7. 🤖 Pluggable Autonomous SWE Engine
* Dispatches code regressions to **Cognition AI Devin** (`POST /v1/sessions`) to clone repos, reproduce tracebacks in cloud sandboxes, synthesize patches, and open GitHub PRs.
* Architecturally swappable with local/air-gapped runners (**OpenCode**, **SWE-agent**) via unified `AutonomousSweProvider` contract.
* Automatically cross-links incidents to **Linear** and **GitHub Issues**.

### 8. 🏢 Enterprise Privacy & Sovereign LLM Support
* **Dual-Key Gemini Flash Lite:** Primary fast multimodal inference for the hackathon showcase with automatic failover on HTTP 429.
* **OpenAI SDK Abstraction:** Can route 100% of telemetry to internal air-gapped models (**vLLM, Ollama, LocalAI**) over Tailscale, ensuring sensitive logs and code never leave the enterprise network.

### 9. 💰 Hard Budget Governor & Spend Circuit Breaker
* Enforces a hard spending cap of **$5.00** per incident or testing cycle, protecting developers from runaway agent billing loops.

---

## 🏛️ System Architecture

PocketSRE enforces an **Out-of-Band Two-VM Topology** across Oracle Cloud Infrastructure (OCI) to reflect real enterprise DevOps reliability:

```
                               ┌────────────────────────────────────────────────────────┐
                               │                   INCIDENT INGESTION                   │
                               │   • Discord Webhook Monitor (Infra Alerts in 2 min)    │
                               │   • Yuki Presence Poller (/presence/{central,etc})     │
                               │   • Infra Docs Knowledge Base (docs/infra/*.md)        │
                               │   • [Future: Sentry Webhooks & Generic JSON Ingest]    │
                               └───────────────────────────┬────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                    OCI VM 1: POCKETSRE CONTROL PLANE (Out-of-Band VM)                       │
│  Container: `container_name: pocketsre-core` (Completely isolated Docker environment)       │
│  Ingress: Cloudflare Tunnels (cloudflared) or static NGINX reverse proxy                    │
│                                                                                             │
│  • Web Framework: FastAPI (Async event router, webhook listener, SSE /stream)               │
│  • Data Contracts: Pydantic v2 (Strict action schemas & runtime parameter validation)       │
│  • Storage & Memory: NeonDB (Serverless PostgreSQL + keepalive ping)                        │
│  • AI Provider: Google Gemini (Dual-Key Pool) + OpenAI-compatible SDK (Local/vLLM)          │
│  • Speech & Track 02: Sarvam Saaras STT + Bulbul TTS + Code-Mixing Engine                   │
│  • Autonomous SWE: Devin API (Cognition AI) + Local OpenCode runner fallback                │
│  • Remote Runner: Paramiko SSH Client (Mounts /app/.ssh/id_ed25519)                         │
│  • Budget Governor: Thread-safe spend tracker enforcing hard $5.00 limit                   │
└───────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                │
                                                │ Remote SSH over OCI Private Network / Tailscale
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                 OCI VM 2: TARGET MONITORED INFRASTRUCTURE (Project Yuki VM)                 │
│  Zero PocketSRE agent processes installed locally (Standard OpenSSH Server only)            │
│                                                                                             │
│  • Unprivileged System User: `pocketsre` (/etc/sudoers.d/pocketsre whitelisted commands)    │
│  • Monitored Containers: `yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`, `yuki-telegram-bot`, `yuki-redis` │
│  • Host Services: PostgreSQL (UNIX Domain Socket), NGINX Reverse Proxy, Docker Engine       │
│  • Health Endpoints: https://yuki-net.ivin.site/presence/{central,discord,horiz,telegram}   │
│  • Infra Alert Webhook: Discord Webhook (emits alerts within 2m of infra events)             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
    ┌─────────────────────────────────┐                   ┌─────────────────────────────────┐
    │     PC: SRE MISSION CONTROL     │                   │     PHONE: ON-THE-GO DISCORD    │
    │   • Lightweight Vite/React UI   │                   │   • Discord Mobile App          │
    │   • Server-Sent Events (/stream)│                   │   • Kiwi & Vikram voice notes   │
    │   • Live audit log & spend gauge│                   │   • Signed Magic-Link Web Button│
    └─────────────────────────────────┘                   └─────────────────────────────────┘
```

---

## 📁 Project Structure

PocketSRE ships as one container: FastAPI serves the API and mounts the built Vite application for the signed mobile console and Mission Control. There is no separate backend deployment.

```text
PocketSRE/
├── src/
│   ├── app/
│   │   ├── main.py              # FastAPI startup and Vite static-file mounting
│   │   ├── config.py
│   │   ├── api/                 # Webhooks, signed-console API, health routes
│   │   ├── bot/                 # Discord commands, events, and voice notes
│   │   ├── incidents/           # Triage, lifecycle, and notifications
│   │   ├── actions/             # Typed runbooks, policy checks, and direct SSH
│   │   ├── ai/                  # LLM routing, key rotation, and budget governor
│   │   ├── storage/             # Neon database access and migrations
│   │   └── shared/              # Contracts, RBAC, audit, and observability helpers
│   └── web/                     # Vite + vanilla CSS source; FastAPI mounts web/dist
├── docs/
│   ├── PRD.md
│   └── infra/
├── tests/
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

The project creates folders only for features it implements. Discord and direct SSH are the initial delivery paths. Slack, Tailscale, Terraform, and further providers belong under `integrations/` when their implementation begins.

### Current foundation

The codebase now provides a FastAPI health endpoint, incident and action contracts, an allow-listed Yuki diagnostic/restart runbook executor over Paramiko SSH (pre-flight integrity check + post-run verification), configurable RBAC (`ROLE_PERMISSIONS`), NeonDB write-through persistence (incidents/audit/budget/knowledge), signed 15-minute console links, a dependency-free static console + mission-control page (SSE feed), a Discord bot with proactive alert cards and reactive free-text triage via Gemini/OpenAI, Devin dispatch for code regressions, and tests. Confidential infra topology never lives in this repo: upload it via `POST /api/knowledge/upload` (admin-secret gated) → `infra_knowledge_docs` in NeonDB; `docs/infra/` holds only sanitized, public-safe docs.

---

## 🚀 3-Stage Phased Implementation Roadmap

To guarantee 100% demo resilience during the 12-hour hackathon, PocketSRE follows a disciplined 3-stage rollout:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               PHASED ROLLOUT ROADMAP                                    │
├──────────────────────────┬──────────────────────────────┬───────────────────────────────┤
│ Mode A: Text & Magic-Link│ Mode B: Multimodal Voice Note│ Mode C: Live Voice Channel    │
│ (Phase 1: Hours 1–4)     │ (Phase 2: Hours 5–7)         │ (Phase 3: Hours 8–10)         │
├──────────────────────────┼──────────────────────────────┼───────────────────────────────┤
│ • Discord text & slashes │ • Async .ogg voice notes     │ • Live bot inside voice call  │
│ • Signed Magic-Link Web  │ • Sarvam Saaras (saaras:v4)  │ • discord-ext-voice-receive   │
│ • Pydantic runbooks      │ • Sarvam Bulbul TTS          │ • RTP / Opus decode + VAD     │
│ • OCI SSH & NeonDB core  │ • Conversational Code-Mix    │ • Live interactive triage    │
│ • 100% crash-proof base  │ • Reliable HTTP/TCP upload   │ • High-tech live demo stretch │
└──────────────────────────┴──────────────────────────────┴───────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Language & Runtime** | Python 3.14+ | PEP 649 deferred annotations, PEP 779 free-threading/no-GIL support, native Zstandard (`compression.zstd`). |
| **Backend Framework** | FastAPI 0.165+, Uvicorn 0.54+ | Latest high-throughput asynchronous request routing and Server-Sent Events (`/stream`). |
| **Data Validation** | Pydantic v2.14+ | Strict runtime typing, zero-overhead schema reflection, and robust parameter parsing. |
| **Speech-to-Text (STT)** | Sarvam AI (`saaras:v4`) | Native Indian language support; robust recognition of code-mixed Manglish/Hinglish. |
| **Text-to-Speech (TTS)** | Sarvam AI (`bulbul:v3`, `bulbul:v4-flash`), `edge-tts` | Warm, lifelike Indic voices (Priya/Shubh) with zero-cost Edge TTS fallback. |
| **Reasoning Engine** | Google Gemini Flash Lite (`google-genai` 3.6+) | Sub-second reflex triage, dual-key rotation on 429 quota exhaustion. |
| **Sovereign LLM Option**| `openai` Python SDK (vLLM / Ollama) | Enterprise air-gapped inference guarantee (Llama-3-70B, Qwen-2.5-Coder). |
| **Operator Interface** | Discord API (`discord.py` 2.7+, `discord-ext-voice-receive`) | Ubiquitous mobile presence, native roles/RBAC, and voice gateway support. |
| **Web Console** | Vanilla HTML/JS/CSS static assets (`web/dist`, no Node needed) | Ultra-lightweight mobile webview for HMAC magic-link execution; SSE-driven. |
| **Storage & Memory** | NeonDB (Serverless PostgreSQL) | Serverless relational store with keepalive pings for learned incident playbooks. |
| **Autonomous SWE** | Cognition AI Devin API + OpenCode | Autonomous repo cloning, bug reproduction, and PR dispatch. |
| **Cloud Execution** | Paramiko 5.1+ SSH Client | Out-of-band remote SSH execution with non-root sudoers whitelist. |
| **Enterprise Plugins** | Tailscale API & Terraform CLI | Zero-Trust mesh telemetry and IaC anti-drift with Zero-Destroy safety invariant. |

---

## ⚡ Quickstart & Setup Guide

### 1. Prerequisites
* Python 3.14+ (or Docker `python:3.14-slim`)
* Docker & Docker Compose
* FFmpeg & Libopus (for Discord voice decoding and synthesis)
* Discord Bot Token (with Message Content, Server Members, and Presence Intents enabled)
* NeonDB PostgreSQL connection string
* Google Gemini API Key(s) and/or Sarvam AI API Key

### 2. Clone & Environment Configuration
```bash
git clone https://github.com/your-username/PocketSRE.git
cd PocketSRE

# Copy and populate secrets
cp .env.example .env
```

Your `.env` should include (see `.env.example` for the full list — all settings use the `POCKETSRE_` prefix):
```env
# Discord
POCKETSRE_DISCORD_TOKEN="your_discord_bot_token"
POCKETSRE_DISCORD_GUILD_ID="your_server_id"
POCKETSRE_DISCORD_ALERT_CHANNEL_ID="your_alerts_channel_id"

# AI & Speech
POCKETSRE_AI_PROVIDER="gemini"          # or "openai"
POCKETSRE_GEMINI_API_KEYS="primary_key,fallback_key"
POCKETSRE_GEMINI_MODEL="gemini-2.0-flash-lite"
POCKETSRE_OPENAI_API_KEY=""             # OpenAI/OpenRouter fallback
POCKETSRE_OPENAI_BASE_URL=""
POCKETSRE_OPENAI_MODEL="gpt-4o-mini"
POCKETSRE_SARVAM_API_KEY=""        # Phase 2 — metered credits (500)
POCKETSRE_SMALLEST_AI_API_KEY=""   # Phase 2 — metered credits ($60)

# Infrastructure & Console
POCKETSRE_TARGET_SSH_HOST="<YUKI_VM_IP>"
POCKETSRE_TARGET_SSH_USER="pocketsre"
POCKETSRE_TARGET_SSH_KEY_PATH="/app/.ssh/pocketsre_bot_ed25519"
POCKETSRE_MAGIC_LINK_SECRET="your_cryptographic_signing_secret"
POCKETSRE_AUTONOMY_MODE="read_auto"
# NEON_DATABASE_URL, DEVIN_API_KEY, LINEAR_API_KEY — pending Phase 1 tracks C/B6
```

> **Note:** The PRD lists unprefixed env names (`DISCORD_BOT_TOKEN`, `JWT_SECRET`, ...). The implementation standardizes on the `POCKETSRE_` prefix via `pydantic-settings`; the PRD will be aligned when Phase 1 config lands (PLAN.md §A6).

### 3. Deploy Control-Plane via Docker Compose
```bash
docker compose up -d --build
```

### 4. Verify Remote Out-of-Band SSH Connectivity
```bash
# Test remote non-root execution into target VM
ssh -i ~/.ssh/pocketsre_bot_ed25519 pocketsre@<TARGET_VM_IP> 'sudo /usr/bin/docker logs --tail 5 yuki-core-api'
```

---

## 🧪 Incident Simulation & Demo Script

PocketSRE ships an air-gapped mock incident injector to rehearse demo scenarios (posts a crafted incident to `/api/incidents`; the real Discord→approve→SSH loop runs from there):

```bash
# 1. Trigger container crash (Resource Starvation)
./scripts/inject_mock_incident.sh --scenario crash --service yuki-core-api

# 2. Trigger application code regression (Devin Auto-PR)
./scripts/inject_mock_incident.sh --scenario bug --service yuki-core-api

# 3. Trigger autonomy ceiling (Database socket lock -> Break-Glass Hand-Off)
./scripts/inject_mock_incident.sh --scenario socket-lock --service yuki-core-api
```

---

## 👥 HackaThoni 2026 Team & Acknowledgments
* **Lead Architect & Developer:** Ivin Titus
* **Target Workload:** Project Yuki Infrastructure (`yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`, `yuki-telegram-bot`, `yuki-redis`)
* **Core Technology Partners:** [Sarvam AI](https://sarvam.ai) (Speech & Language Track Sponsor), [Cognition AI](https://cognition.ai) (Devin API), [Google AI Studio](https://aistudio.google.com) (Gemini Models), [NeonDB](https://neon.tech) (Serverless Postgres).

---
*PocketSRE is open-source under the [MIT License](LICENSE).*
