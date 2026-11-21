# Product Requirement Document (PRD)

# PocketSRE
**The Autonomous, Budget-Governed On-Call SRE Companion**  
*HackaThoni 2026 (Alappuzha, Kerala) | Primary Track: Track 02 — VOICE & LANGUAGE ("Beyond English")*

---

## 1. Executive Summary & Core Product Idea

### 1.1 Product Definition
**PocketSRE** is an open-source, speech-led autonomous AI site reliability engineering companion designed to eliminate the nightmare of production outages for engineers traveling or away from their laptops. Packaged and deployed as an isolated Docker container (**`container_name: pocketsre-core`**) on a **dedicated OCI Control-Plane VM** (separate from the monitored workload to ensure authentic, out-of-band SRE resilience), PocketSRE remotely manages target production infrastructure (Project Yuki's VM hosting production containers: `yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`, `yuki-telegram-bot`, and `yuki-redis`) via SSH over the OCI private network or Tailscale mesh. PocketSRE operates primarily through **Discord** (text chat, multimodal audio notes, and live voice channel calls) backed by a **Signed Magic-Link Mobile Web Console** and a lightweight **Vite Mission Control Dashboard**.

Built natively for **HackaThoni Track 02 (Voice & Language: Beyond English)**, PocketSRE delivers full, first-class support for **pure English** (the global standard for DevOps) alongside **pure Indian languages (Malayalam, Hindi)**, while introducing an optional, adaptive **Conversational Code-Mixing Feature** (Manglish and Hinglish). Rather than imposing a forced dependency, PocketSRE provides complete linguistic freedom: engineers who speak standard English receive crisp, professional English with zero unwanted code-mixing; responders who prefer native Indic languages receive fluent Malayalam or Hindi; and engineers who naturally mix languages on-call (*"Kiwi, Yuki chat container down aayi, onnu check cheyth restart cheyyuo?"*) are understood seamlessly via Sarvam AI (`saaras:v4` STT + `bulbul:v3`/`bulbul:v4-flash`). Responders can switch between distinct conversational avatars: **Kiwi (Kiwi-chan)**—an empathetic companion who relieves high-stakes on-call panic—and **Vikram**—a formal, boardroom-ready senior enterprise SRE lead. PocketSRE intercepts production crashes, conducts rapid reflex triage, executes bounded safe infrastructure runbooks over restricted SSH, and dispatches autonomous code patches via a **Pluggable Autonomous SWE Engine** (featuring the **Devin API** as primary for the hackathon showcase, with swappable support for local/air-gapped agent runners like **OpenCode**)—all governed by strict **Role-Based Access Control (RBAC)**, **custom production integrity rules**, and a **hard budget circuit breaker**.

### 1.2 The One-Sentence Pitch
> **"PocketSRE is a speech-led, budget-governed on-call SRE companion that lets engineers triage, diagnose, and resolve production outages entirely over Discord in pure English, native Malayalam or Hindi, or natural code-mixed speech without opening a laptop."**

### 1.3 Core Value Propositions
1. **Zero-Laptop Emergency Resolution:** Resolves production incidents on-the-go from a mobile device without requiring SSH terminal sessions or multi-tab browser triage.
2. **Bounded Safe Autonomy (The Anti-Rogue Sandbox):** The AI agent is prohibited from executing arbitrary bash commands. Cloud infrastructure operations are restricted to strictly typed, whitelisted Pydantic runbooks.
3. **Signed Magic-Link Web Architecture:** Completely eliminates Discord UI component timeout and caching bugs by offloading long-running, multi-step actions to a lightweight tokenized web console.
4. **Production Integrity Guardrails:** Replaces naive container restarts with declarative pre-flight checks (evaluating service flags like `restart_recommended` and `maintenance_mode` before issuing commands).
5. **Hard Budget Circuit Breaker:** Protects teams from runaway agent bills by enforcing strict per-incident and sprint-level circuit breaker caps (default: \$5.00 limit).
6. **Multi-Avatar Persona Architecture (Kiwi & Vikram):** Toggles between an empathetic, stress-relieving companion avatar (**Kiwi / Kiwi-chan**) and a formal, crisp enterprise responder avatar (**Vikram**).
7. **Adaptive Incident Memory (Self-Learning Playbooks):** Moves beyond static configs by observing the remediation actions of SRE Leads. When a senior engineer manually resolves or approves a recurring issue (e.g. Yuki's Hori-Z connector `platform_not_connected` error resolved via container restart), PocketSRE records the error signature and remediation in NeonDB. On future occurrences, PocketSRE dynamically surfaces the learned fix as an instant 1-tap suggestion, or autonomously executes it under full autonomy mode.
8. **Radical Transparency & Honest Escalation (The Anti-Blackbox Guarantee):** When incidents exceed PocketSRE's autonomous runbooks or require root privileges, PocketSRE deliberately halts instead of hallucinating. It sends a short, noise-free summary to Discord while unlocking an in-depth Analyst Hand-off Dossier and an Ephemeral Break-Glass Web Console on the Lead's phone.
9. **Enterprise Extended Access Plugins (Tailscale Zero-Trust & Terraform Anti-Drift):** Extensible plugin architecture supporting Tailscale mesh telemetry/keyless SSH and Terraform state inspection, with safe infra mutations governed by GitOps PR dispatch and an uncompromising "Zero-Destroy Invariant" (`destroy == 0`).
10. **Infra Knowledge Transfer & Architecture Ingestion:** Ingests markdown architecture documentation, service dependency graphs, and internal playbooks (via web console upload, Discord `/pocketsre learn-infra`, or git sync). PocketSRE understands the exact private topology (e.g. UNIX socket paths, internal ports, upstream APIs) rather than relying on generic guesses.
11. **Pluggable Multi-Provider LLM Engine & Enterprise Privacy Sovereignty:** Pairs seamlessly with internal self-hosted or air-gapped LLMs (vLLM, Ollama, LocalAI) via the standardized OpenAI Python SDK alongside Google Gemini API (`google-genai`). Guarantees that sensitive infra documentation, internal logs, and stack traces never leave the enterprise's private perimeter.
12. **Project Yuki Code Foundation (High-Leverage Scaffolding):** Bootstraps directly from Project Yuki's battle-tested core modules—specifically its multi-provider AI routing layer, multi-key rotation pool with rate-limit backoff, and asynchronous presence poller—saving 3+ hours of repetitive boilerplate during the 12-hour sprint.
13. **Out-of-Band Control Plane & Isolated Containerization (`pocketsre-core` on Separate VM):** Emulates authentic production DevOps architecture by deploying PocketSRE inside an isolated Docker container on an independent OCI Control-Plane VM (on the same OCI network/VPC). PocketSRE executes SRE runbooks remotely over SSH (with Tailscale Zero-Trust mesh support) into the target production VM (Project Yuki). This physical separation ensures that target host crashes, kernel lockups, or OOM storms never kill the SRE agent, while completely eliminating Python package conflicts on both machines.
14. **Universal Linguistic Flexibility (Pure English, Pure Indic & Adaptive Code-Mixing):** SREs are never locked into a single language or forced into a synthetic dialect. **Pure English** remains the fully supported, first-class baseline for global DevOps workflows, accompanied by **pure Malayalam** and **pure Hindi**. Crucially, code-mixing (Manglish and Hinglish) is an **adaptive conversational feature, NOT a forced dependency**: engineers speaking standard English are never subjected to forced code-mixing, while engineers who naturally blend technical nouns into colloquial phrasing (*"Kiwi, Yuki chat container down aayi, onnu check cheyth restart cheyyuo?"* or *"Vikram, production-il entha issue? Logs pull cheythu nokk"*) are understood instantly through Sarvam AI's speech stack.
15. **12-Hour Hackathon Feasibility:** Built entirely on high-leverage free tiers and standard APIs (FastAPI + Pydantic + NeonDB + Discord.py + Dual-Key Gemini Flash Lite + Devin API + edge-tts/Sarvam), ensuring a fully functional, crash-proof demo within a 12-hour build window.

---

## 2. Interaction Modes & Personas

### 2.1 The 3 Core Interaction Modes & Phased Rollout

PocketSRE provides 3 distinct operational modes to match the responder's connectivity, device constraints, and environment, developed in a **strict 3-stage phased rollout**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        POCKETSRE INTERACTION MODES                              │
├──────────────────────┬─────────────────────────────┬────────────────────────────┤
│ Mode A: Text-Only    │ Mode B: Multimodal Voice Msg│ Mode C: Live Discord Call  │
│ (Phase 1: Hours 1-4) │ (Phase 2: Hours 5-7)        │ (Phase 3: Hours 8-10)      │
├──────────────────────┼─────────────────────────────┼────────────────────────────┤
│ • Inbound: Text msg  │ • Inbound: Audio voice note │ • Inbound: Continuous bi-  │
│ • Outbound: Markdown │ • Outbound: Synthesized MP3 │   directional voice in VC  │
│ • Fast, low-bandwidth│ • Conversational Code-Mix   │ • Outbound: Live audio PCM │
│ • Rock-solid triage  │ • Manglish, Hinglish, Indic │ • Bot joins #incident-vc   │
│ • Zero voice failure │ • Uses reliable HTTP/TCP    │ • Opus UDP media stream    │
└──────────────────────┴─────────────────────────────┴────────────────────────────┘
```

#### The Strict 3-Stage Implementation Roadmap
1. **Phase 1: Mode A: Text-Based Chat & Signed Magic-Link Web Console (Core Foundation — Hours 1–4):**
   * *Mechanism:* Standard Discord text messaging, slash commands (`/approve`), and un-timeoutable Signed Magic-Link buttons (`ButtonStyle.link`).
   * *Flow:* User sends text or slash command $\rightarrow$ PocketSRE responds with structured Markdown, logs, and a signed magic-link card (bypassing Discord interaction gateway timeouts).
   * *Engineering Rule:* All core systems (incident webhook ingestion, health poller, RBAC, Pydantic runbooks, OCI SSH execution) are first verified and proven 100% stable via text before touching voice.
2. **Phase 2: Mode B: Multimodal Discord Voice Notes & Conversational Code-Mixing (The Star Feature — Hours 5–7):**
   * *Mechanism:* Responder holds the microphone button in Discord mobile and sends a voice note (`.ogg` audio attachment).
   * *Flow:* PocketSRE downloads the audio attachment, transcribes via **Sarvam Saaras STT** (`saaras:v4`), detects intent and language dialect, executes triage, and **always responds with a synthesized audio clip** alongside the Discord card.
   * *Reliability Invariant:* Operates over standard Discord HTTP/TCP attachment delivery, completely immune to UDP streaming packet drops over spotty houseboat cellular connections.
3. **Phase 3: Mode C: Live Discord Voice Channel Call (High-Tech Showcase — Hours 8–10 Stretch):**
   * *Mechanism:* Real-time bidirectional voice channel session directly inside Discord's `#incident-war-room`.
   * *Flow:* PocketSRE connects via Discord Voice Gateway. Outbound audio is streamed via `voice_client.play(FFmpegPCMAudio(...))`. Inbound audio is intercepted via `discord-ext-voice-receive` (SSRC demuxing $\rightarrow$ Opus decryption $\rightarrow$ PCM $\rightarrow$ VAD silence detection $\rightarrow$ Sarvam STT).
   * *Safety Fallback:* If mobile UDP cellular latency causes packet jitter, PocketSRE gracefully defers to Mode B voice notes.

#### Universal Linguistic Flexibility (Pure English, Pure Indic & Adaptive Code-Mixing)
PocketSRE provides complete linguistic freedom across all interaction modes. Pure languages—**especially English** as the primary industry-standard medium for DevOps—are fully supported as first-class citizens. The Phase 1 text surface mirrors English, Hindi, Malayalam, Hinglish, and Manglish through its presentation layer; Sarvam speech input/output remains the later voice phase. Code-mixing is an adaptive conversational feature, not a forced dependency:
* **Pure English In $\rightarrow$ Pure English Out (Core DevOps Standard):** Professional, concise SRE briefings synthesized via `bulbul:v4-flash` (`en-IN` / `shubh_enhi_ads`) or `en-IN-PrabhatNeural`. For responders speaking standard English, PocketSRE operates 100% in pure English with zero unwanted code-mixing.
* **Pure Malayalam In $\rightarrow$ Pure Malayalam Out:** Fluent native Malayalam incident alerts and diagnostics synthesized via `bulbul:v3` (`target_language_code="ml-IN"`, speaker: `priya` or `shubh`).
* **Pure Hindi In $\rightarrow$ Pure Hindi Out:** Formal, boardroom-ready Hindi incident reports synthesized via `bulbul:v4-flash` or `bulbul:v3` (`hi-IN`).
* **Adaptive Code-Mixing Feature (Manglish & Hinglish):** When engineers naturally mix technical terms with regional speech, PocketSRE mirrors their style seamlessly:
  * *Manglish:* *"Kiwi, Yuki chat container down aayi, onnu check cheyth restart cheyyuo?"* $\rightarrow$ *"Pinne entha senpai! Njan ippothanne yuki-core-api logs check cheythu restart cheyyaam. Emergency console-il link ayachittund!"*
  * *Hinglish:* *"Vikram, Yuki ka container crash ho gaya hai, ek baar check karke restart maar de"* $\rightarrow$ *"Ji sir, yuki-core-api ke logs inspect karke restart trigger kar raha hoon. Console link bhej diya hai!"*
* **Zero-Cost Fallback:** If Sarvam credits deplete, routes seamlessly to Microsoft `edge-tts` (`en-IN-NeerjaNeural` for English, `ml-IN-SobhanaNeural` for Malayalam, `hi-IN-SwaraNeural` for Hindi).

---

### 2.2 Dual-Avatar Persona Architecture: Kiwi vs Vikram

PocketSRE decouples the core platform intelligence from the visual and conversational persona. Responders can switch avatars at any time via Discord command (`/pocketsre avatar kiwi` or `/pocketsre avatar vikram`, aliased to `/kiwi mode friendly` or `/kiwi mode corporate`):

| Persona Attribute | **Avatar A: Kiwi (Kiwi-chan)** | **Avatar B: Vikram (Corporate SRE Lead)** |
|---|---|---|
| **Persona Role** | Empathetic on-call companion. | Formal enterprise SRE lead. |
| **Tone & Style** | Warm, encouraging, empathetic, slightly playful (*"Daijoubu Senpai! Kiwi is on it!"*). Relieves high-stakes 2 AM on-call panic. | Objective, concise, boardroom-ready, formal technical Markdown. Zero fluff. |
| **Voice Synthesis** | Cute, natural companion prosody (`ja-JP-NanamiNeural` or friendly Sarvam `priya`). | Deep, professional executive narration (Sarvam `shubh` or `en-IN-PrabhatNeural`). |
| **Voice / Alert Framing Examples** | *Pure English:* *"Senpai! Yuki container crashed, but I grabbed the logs. Should I restart it?"*<br>*Manglish:* *"Senpai! Yuki container down aayi, pakshe njan logs eduthittund. Onnu restart cheyyatte?"* | *Pure English:* *"Incident 501: Container `yuki-core-api` terminated by kernel OOM. Uptime degraded. Recommending immediate restart."*<br>*Manglish:* *"Incident 501: `yuki-core-api` container crash aayi. Uptime degrade aayi. Immediate restart recommend cheyyunnu."* |
| **Target Audience** | Solo founders, night-shift on-call devs, community servers. | Enterprise stakeholders, executive war rooms, incident retro reviews. |

---

## 3. System Architecture & Tech Stack

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
│  Deployed as Isolated Container: `container_name: pocketsre-core` (Zero Python Collisions)  │
│  Runs independently on separate OCI compute instance (same OCI VCN subnet / Tailscale)      │
│  Ingress: Cloudflare Tunnels (cloudflared) or static NGINX reverse proxy (SSL/DNS secured)  │
│  Foundation: Bootstrapped from Project Yuki's battle-tested AI router & health pollers      │
│                                                                                             │
│  • Web Framework: FastAPI (Async event router, webhook listener, SSE /stream)               │
│  • Data Contracts: Pydantic v2 (Strict action schemas & runtime parameter validation)       │
│  • Configuration: .env (Secrets) + config.py (Declarative policies, RBAC, integrity rules)  │
│  • Persistent Storage: NeonDB (Serverless PostgreSQL with connection pooling & 4m keepalive)│
│  • Knowledge Transfer Engine: Markdown architecture doc ingestion & topology context RAG    │
│  • Pluggable LLM Router: Dual-Key Google Gemini (Demo) + OpenAI SDK (Self-Hosted/vLLM/Ollama│
│  • Discord Voice Pipeline: SSRC Demux + Opus RTP + Sarvam Bulbul/Saaras + Code-Mixing Engine│
│  • Decision Engine: Gemini Decision 1 (Decisions API, 200 RPM / 10K RPD free) — pluggable  │
│    provider abstraction reserved for local decision models (e.g. Laya, Ollama-hosted)      │
│  • Out-of-Band Remote SSH: Paramiko SSH Client (Mounts private key /app/.ssh/id_ed25519)    │
│  • Autonomous Repair: Pluggable SWE Engine (Devin API Demo + Local OpenCode Runner)         │
│  • Budget Governor: Thread-safe spend tracker enforcing hard $5.00 limit                   │
└───────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                │
                                                │ Remote SSH over OCI Private Network / Tailscale
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                 OCI VM 2: TARGET MONITORED INFRASTRUCTURE (Project Yuki VM)                 │
│  Host OS: Ubuntu Linux (Dedicated Compute Instance on OCI VCN)                              │
│  Zero Kiwi Agent Processes Installed Locally (Standard OpenSSH Server Only)                 │
│                                                                                             │
│  • Unprivileged System User: `pocketsre` (/etc/sudoers.d/pocketsre whitelisted commands)    │
│  • Target Containers: `yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`, `yuki-telegram-bot`, `yuki-redis` │
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
    │   • Server-Sent Events (/stream)│                   │   • Kiwi voice clips & chat     │
    │   • Live audit log & spend gauge│                   │   • Signed Magic-Link Web Button│
    └─────────────────────────────────┘                   └─────────────────────────────────┘
```

### 3.1 Component Specifications
* **Hosting & Two-VM Infrastructure Topology:** Packaged and deployed as an isolated Docker container (**`container_name: pocketsre-core`** using base image **`python:3.14-slim`**) on an **independent OCI Control-Plane VM** (separate from Project Yuki's production workload VM). This models authentic enterprise DevOps and SRE best practices: an automated observability and remediation plane must never run on the workload machine it monitors, because a host crash, kernel lockup, or OOM storm on the workload host would kill the monitoring bot alongside it. Both VMs reside on the same **Oracle Cloud Infrastructure (OCI) Virtual Cloud Network (VCN)** for sub-1ms internal latency. PocketSRE connects out-of-band to Project Yuki's VM via **Paramiko 5.1+ SSH** (using direct SSH for hackathon demo agility, while architecturally supporting Tailscale Zero-Trust keyless SSH for enterprise deployments). PocketSRE's containerized deployment guarantees that its Python environment and dependencies (FastAPI, Pydantic, Discord.py) never collide with microservices on either host, maintaining an ultra-lightweight <300 MB RAM footprint. Ingress is routed via **Cloudflare Tunnels (`cloudflared`)** or static NGINX reverse proxy (`/api/pocketsre`).
* **Backend Core & Runtime:** **Python 3.14+** running **FastAPI 0.165+** (with **Uvicorn 0.54+**). Takes full advantage of Python 3.14's deferred evaluation of annotations (PEP 649) for near-instant schema bootstrap, official free-threaded CPython execution (PEP 779 / no-GIL), t-strings (PEP 750), and native Zstandard compression (`compression.zstd`, PEP 784) for high-speed log ingestion and Server-Sent Events (`/stream`).
* **Runtime Validation:** **Pydantic v2.14+**. Enforces strict schemas on all agent actions, tool calls, and runbook parameters with zero runtime overhead.
* **Persistent Storage & Incident Memory:** **NeonDB (Serverless PostgreSQL)**. Stores incident records, immutable audit logs, budget ledger, and the **Learned Playbooks Experience Store (`learned_playbooks`)**. Supports 64 to 500+ concurrent connections effortlessly. Maintained always-awake with a background ping (`SELECT 1;`) every 4 minutes on idle, with an optional local JSON file cache acting as a local offline backup buffer.
* **Operator Surface:** **Discord API (`discord.py` 2.7+)**. Rich interactive embeds, audio clip delivery, native Discord Role RBAC, and **Signed Magic-Link URL buttons** pointing to the mobile web console.
* **Pluggable Reasoning LLM Engine (Dual-SDK Abstraction):**
  * **Google Gemini API (`google-genai` 3.6+):** Primary driver for the hackathon live demo, utilizing Gemini Flash Lite (15 RPM, 500 RPD) with automated dual-key rotation on HTTP 429 quota exhaustion.
  * **OpenAI-Compatible Standard (`openai` Python SDK):** Standardized interface allowing enterprise responders to pair PocketSRE with internal **self-hosted LLMs (vLLM, Ollama, LocalAI, TGI)** running inside their private VPC or behind Tailscale (e.g. Llama-3-70B, Qwen-2.5-Coder), as well as private Azure OpenAI endpoints. Completely resolves enterprise data privacy, GDPR, and sovereign perimeter mandates—ensuring proprietary code, infra docs, and stack traces never leave the company network.
* **Documentation & Infra Knowledge Store:** Ingests markdown architecture diagrams, service relationship maps, and incident playbooks into NeonDB (`infra_knowledge_docs`). Injects relevant topology context into triage reasoning to ground PocketSRE in private infrastructure specifics (UNIX socket paths, internal ports, upstream APIs).
* **Project Yuki Foundation Modules:** Directly adapts Project Yuki's battle-tested core modules—specifically the `APIKeyPool` multi-key rotation router, exponential backoff handler, and asynchronous presence poller—accelerating MVP development and guaranteeing high reliability during the 12-hour build.
* **Discord Voice Pipeline & Multi-Language Mirroring Engine:** Implements Discord's Voice Gateway protocol: outbounds stream 48kHz PCM through FFmpeg into Opus RTP UDP packets; inbounds demux speaker SSRC identifiers and decode Opus frames to PCM via `discord-ext-voice-receive` for **Sarvam Saaras STT**, powered by the **Multi-Language Mirroring Engine** (pure English, pure Malayalam/Hindi, and adaptive Manglish/Hinglish via Sarvam, with fallback via Microsoft `edge-tts`).
* **Decision API Layer:** **Gemini Decision 1 (`gemini-decision-1` via the Decisions API, `v1beta`)** is the primary classifier — purpose-built binary/categorical/rubric verdicts (is-real-incident + which-service + severity) with zero output tokens, on the free tier (200 RPM / 10K RPD per project). The decision call sits behind a `DECISION_PROVIDER` abstraction (`"gemini_decision"` default) with a reserved slot for **local decision models** — e.g. **Laya** (421M non-autoregressive decision model) or Ollama-hosted small models — wired via a configurable `DECISION_BASE_URL` for air-gapped/edge deployment. Alert verdicts degrade gracefully to strict keyword heuristics when no decision backend is reachable.
* **Audio Synthesis:** **Sarvam AI (Bulbul v4)** for pure and code-mixed speech (English, Malayalam, Hindi), with Microsoft **`edge-tts`** as a zero-cost, zero-API-key fallback.
* **Pluggable Autonomous SWE Engine:** **Devin API (`POST /v1/sessions`)** (Cognition AI - Demo Primary) with swappable support for local/air-gapped autonomous agents (**OpenCode**, **SWE-agent**, or local containerized runners) via a unified `AutonomousSweProvider` interface.
* **Project Tracking:** **GitHub Issues REST API** (PAT) + **Linear GraphQL API**.
* **Safe Cloud Runner:** **Paramiko 5.1+ SSH**. Connects to OCI using a dedicated non-root user (`pocketsre`) with strict sudoers restrictions.
* **Web Mission Control:** **Vite 8.3+ + React 19.3+ (Vanilla CSS)**. Ultra-lightweight dashboard synchronized via SSE.
* **Extended Access Plugins:** Modular abstraction for enterprise infrastructure integrations: **Tailscale** (Zero-Trust peer telemetry, DERP latency mapping, keyless Tailscale SSH) and **Terraform / OpenTofu** (state drift auditing, plan diff generation, and GitOps PR dispatch with Zero-Destroy safety invariants).

### 3.2 Configuration Architecture & Secret Management
PocketSRE strictly decouples sensitive credentials from declarative policies and custom domain rules:
* **`.env` (Private Secrets Only):**
  * Contains exclusively API keys and private keys: `DISCORD_BOT_TOKEN`, `GEMINI_API_KEY_PRIMARY`, `GEMINI_API_KEY_FALLBACK`, `OPENAI_API_KEY`, `OPENAI_BASE_URL` (optional: for self-hosted vLLM, Ollama, or LocalAI), `SWE_AGENT_PROVIDER` (`"devin"` or `"local_opencode"`), `DEVIN_API_KEY`, `LOCAL_SWE_ENDPOINT`, `NEON_DATABASE_URL`, `OCI_SSH_KEY_PATH`, `LINEAR_API_KEY`, `JWT_SECRET`.
* **`config.py` (Declarative Policies, Rules & Non-Secrets):**
  * **AI Provider & SWE Engine Selection:**
    ```python
    AI_PROVIDER = "gemini"  # Options: "gemini" (Demo Google GenAI), "openai_compatible" (Self-Hosted vLLM/Ollama/Azure)
    OPENAI_MODEL_NAME = "llama-3-70b-instruct"  # Used when AI_PROVIDER == "openai_compatible"
    KNOWLEDGE_INGESTION_ENABLED = True
    SWE_AGENT_PROVIDER = "devin"  # Options: "devin" (Cognition AI - Demo Primary), "local_opencode" (Local Harness), "generic_webhook"
    LOCAL_SWE_ENDPOINT = "http://localhost:8080/v1/remediate"
    DECISION_PROVIDER = "gemini_decision"  # Options: "gemini_decision" (Decisions API, free tier), "local" (Laya / Ollama via DECISION_BASE_URL), "keywords" (no model)
    DECISION_BASE_URL = None  # e.g. "http://localhost:11434" for local decision models
    ```
  * **Infrastructure Targets:** Pinned container names (`CONTAINER_TARGET = "yuki-core-api"`), SSH ports, and remote log paths.
  * **RBAC Role Mapping:** Maps Discord roles to permissible actions:
    ```python
    ROLE_PERMISSIONS = {
        "SRE-Lead": ["*"],
        "DevOps": ["RESTART_YUKI_CORE", "RESTART_HORIZ_CLIENT", "FETCH_LOGS_CORE_API", "FETCH_LOGS_HORIZ_CLIENT", "PRUNE_DISK"],
        "Junior-Dev": ["FETCH_LOGS_CORE_API", "FETCH_LOGS_HORIZ_CLIENT", "STATUS", "CHAT"]
    }
    AUTONOMY_POLICY_MODE = "DESTRUCTIVE_ONLY"  # Options: DESTRUCTIVE_ONLY, UNKNOWN_ONLY, STRICT_CONFIRMATION
    EXECUTION_PRIVILEGE_MODE = "NON_ROOT"      # Options: NON_ROOT (Default / Recommended), FULL_ROOT (NOT RECOMMENDED / HIGH RISK)
    ```
  * **Custom Production Integrity Rules:** Enforces domain-specific pre-flight guardrails before container lifecycle commands are executed (e.g., checking Yuki's `/presence/central` flags like `restart_recommended`, verifying `maintenance_mode`, checking connection drain timeouts).

---

## 4. Mandatory Features (Core MVP Scope)

### 4.1 Multi-Source Incident Detection & Ingestion

PocketSRE employs a dual-channel detection topology combining proactive application-level polling with reactive host-level alerting:

1. **Reactive Host/Infra Alerting (Discord Webhook Monitor):**
   * **Inbound Alert Webhook:** `https://discord.com/api/webhooks/1516923595903864963/03DE8KxXouAORIWNIxe6zHtGuVEGka6HV4nVpwKebVLJNuFBRFOzZaLD8VHwARO_JLk0`
   * **Mechanism:** Inside the target VM, low-level watchdog daemons emit critical infrastructure status alerts (within ~2 minutes of an incident or system event) directly to this Discord Webhook.
   * **PocketSRE Ingestion:** PocketSRE's `discord.py` bot monitors the receiving text channel directly via an `on_message` listener, parsing alert payloads instantly to trigger sub-second reactive incident triage without polling latency.

2. **Proactive Application & Subsystem Telemetry (Presence Poller):**
   * **Endpoints:** Polls all 4 Yuki presence endpoints every 15–30 seconds via `httpx`:
     - `https://yuki-net.ivin.site/presence/central` (`service: "core-chat-api"` -> container `yuki-core-api`)
     - `https://yuki-net.ivin.site/presence/discord` (`service: "yuki-discord-bot"`)
     - `https://yuki-net.ivin.site/presence/horiz` (`service: "yuki-horiz-client"`)
     - `https://yuki-net.ivin.site/presence/telegram` (`service: "yuki-telegram-bot"`)
   * **Presence Payloads:**
     ```json
     // /presence/central
     {"uptime_seconds":168736,"gate_mode":"ACCEPTING","db_status":"ok","redis_status":"ok","flags":{"deploy_ready":true,"restart_recommended":false,"maintenance_mode":false},"status":"online","service":"core-chat-api","app_version":"6.4.2","commit_sha":"d21460dd5a9c560a2993423f7246051a0e5ec7ac","degraded_subsystems":[]}

     // /presence/discord, /horiz, /telegram
     {"status": "online", "service": "yuki-discord-bot", "uptime_seconds": 168775, "platform_connection_state": "connected", "flags": {"deploy_ready": true, "restart_recommended": false, "maintenance_mode": false}, "app_version": "2.3.2", "commit_sha": "ad0fa5f012ded1c94a4e0ca0f605f26715224de2", "degraded_subsystems": []}
     ```
   * **Deterministic Incident Trigger Rules:**
     - HTTP status != 200 or connection timeout (> 5.0s)
     - `status != "online"` (e.g. `"offline"`, `"degraded"`)
     - `db_status != "ok"` or `redis_status != "ok"`
     - `flags.restart_recommended == true` or `flags.maintenance_mode == true`
     - `degraded_subsystems` list is non-empty (`len > 0`)
     - `platform_connection_state != "connected"` (for gateway bots)

3. **1:1 Service-to-Container Name Resolution:**
   * The `service` name exposed in presence payloads and alert summaries maps directly to Docker container names on the target VM:
     - `core-chat-api` / `yuki-core` -> `yuki-core-api`
     - `yuki-horiz-client` / `horiz-connector` -> `yuki-horiz-client`
     - `yuki-discord-bot` -> `yuki-discord-bot`
     - `yuki-telegram-bot` -> `yuki-telegram-bot`
     - `yuki-redis` -> `yuki-redis`
   * This gives the triage engine immediate precision: it knows exactly which container requires `docker logs`, `docker inspect`, or `docker restart`.

4. **Investigation Scope (Hackathon MVP vs. Future Extensibility):**
   * **Hackathon MVP:** Investigation (both proactive and reactive) checks these 4 presence endpoints + executes bounded SSH commands via Paramiko.
   * **Future Extensibility:** Production roadmap includes broader integrations: Sentry webhooks (`POST /webhook/sentry`), Generic JSON (`POST /webhook/generic`), Tailscale mesh telemetry, and Terraform drift checks.

5. **Infra Knowledge Base Ingestion (`docs/infra/`):**
   * PocketSRE loads markdown documentation from `docs/infra/` (e.g. `yuki_architecture.md`) directly into LLM prompts on demand, providing instant ground truth on internal ports, PostgreSQL UNIX sockets, and Redis brokers without requiring an external vector DB.

### 4.2 Sub-40ms Reflex Triage & Blast Radius Evaluation
* **Reflex Decision Triage:** Fast classification into `CODE_REGRESSION`, `RESOURCE_STARVATION`, `INFRA_OFFLINE`, or `TRANSIENT_BLIP`.
* **Blast Radius Calculation:** Extracts affected user sessions directly from telemetry (`payload["user_count"]`) or calculates WebSocket drop deltas from Yuki presence metrics.

### 4.3 Discord Role-Based Access Control (RBAC & IAM)
* **`@SRE-Lead` / `@Admin`:** Authorized to execute all destructive runbooks (restarts, rollbacks, Devin dispatches).
* **`@Junior-Dev` / `@Viewer`:** Permitted to view telemetry and chat; blocked from executing production mutations.
* **Implementation Rule:** Role checks must be guarded with `@app_commands.guild_only()` and use `getattr(interaction.user, "roles", [])` to prevent DM-related crashes.

### 4.4 Bounded Safe Infrastructure Execution & Privilege Modes
PocketSRE provides an architecturally governed execution pipeline designed around least-privilege principles, while allowing teams to configure privilege boundaries based on their operational risk tolerance. SRE runbooks are executed remotely from the independent **PocketSRE Control-Plane VM** over SSH (using Paramiko) to the **Target Project Yuki VM**, authenticating via an unprivileged system user (`pocketsre`) with an Ed25519 key pair. This guarantees strict out-of-band separation between the SRE orchestrator and the monitored workload.

#### 4.4.1 Dual Privilege Modes: `NON_ROOT` vs `FULL_ROOT` (Configurable Gating)
Configured via `EXECUTION_PRIVILEGE_MODE` in `config.py`:
* **`NON_ROOT` (Default & Strongly Recommended):**  
  PocketSRE connects to cloud infrastructure exclusively via an unprivileged system user (`pocketsre`). Root-level commands (`sudo`) are strictly restricted to the whitelisted runbook binaries in `/etc/sudoers.d/pocketsre`. Recommended for enterprise, production, and shared multi-tenant hosts.
* **`FULL_ROOT` (Optional / Explicitly Marked `NOT RECOMMENDED / HIGH RISK`):**  
  For solo founders, homelabs, staging VMs, or legacy monoliths requiring host-level systemd daemon management or raw disk inspection, PocketSRE can be granted unrestricted sudo permissions (`NOPASSWD: ALL`).
* **Defense-in-Depth Invariants (Active Even Under `FULL_ROOT` Mode):**  
  Even if full root access is granted to PocketSRE, the agent **never behaves as an ungoverned black box**. Four un-bypassable software guardrails remain active:
  1. **Approval Policy Invariant:** Root privileges do *not* bypass human gating. Under `DESTRUCTIVE_ONLY`, PocketSRE can run root diagnostics (`dmesg`, `journalctl -u postgres`, `iotop`) autonomously, but **any mutating root command strictly requires explicit human sign-off via Discord or the Web Console**.
  2. **Gateway Catastrophic Blacklist:** An un-bypassable gateway regex rejection filter intercepts and blocks destructive commands (`rm -rf /`, `mkfs`, raw block device writes, `chmod 777 /`) before they ever reach the SSH runner.
  3. **Prominent UI Warning Banner:** Every Discord embed and web console card generated under root mode displays a high-visibility badge:  
     `⚠️ [ROOT PRIVILEGE ACTIVE - HIGH RISK MODE]`.
  4. **Immutable Audit Trail:** Every root command, exit code, and stdout/stderr output is committed to NeonDB's `audit_logs` with `actor_role: "SRE-Lead (Root Elevated)"`.

#### 4.4.2 Pre-Flight Production Integrity Checks
In high-integrity production systems (like Project Yuki), containers cannot be naively killed or restarted on a whim without risking data or session corruption. Before executing any container restart, PocketSRE evaluates declarative integrity rules defined in `config.py`:
* **Telemetry State Check:** Inspects `/presence/central` flags:
  * Verifies `maintenance_mode == false`.
  * Verifies if `restart_recommended == true` or if active sessions have safely dropped/drained.
* **Graceful Drain & Cooldown:** Enforces a brief drain period or retry threshold before issuing hard lifecycle mutations, preventing cascading connection storms.

#### Restricted Sudoers Configuration (`/etc/sudoers.d/pocketsre`):
```bash
# Container Lifecycle (Strictly Pinned to Yuki Containers)
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-discord-bot
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-telegram-bot
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-horiz-client
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-core-api
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-redis

pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-discord-bot
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-telegram-bot
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-horiz-client
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-core-api
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-redis

pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-discord-bot
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-telegram-bot
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-horiz-client
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-core-api
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-redis

# Container Read-Only Diagnostics & Logs (Any Options / Tail Counts)
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker logs *
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker inspect *
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker top *

# Global Docker Telemetry & Pruning
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker ps
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker ps -a
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stats --no-stream
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker system prune -f

# Host Ingress & Web Server (NGINX)
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/systemctl status nginx
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/nginx -t
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u nginx *

# Host Docker Daemon Diagnostics
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/systemctl status docker
pocketsre ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u docker *
```

#### Typed Execution Enum (Infrastructure SSH Whitelist):
```python
class SafeRunbookAction(str, Enum):
    # Lifecycle mutations
    RESTART_DISCORD_BOT = "/usr/bin/docker restart yuki-discord-bot"
    RESTART_TELEGRAM_BOT = "/usr/bin/docker restart yuki-telegram-bot"
    RESTART_HORIZ_CLIENT = "/usr/bin/docker restart yuki-horiz-client"
    RESTART_CORE_API = "/usr/bin/docker restart yuki-core-api"
    RESTART_REDIS = "/usr/bin/docker restart yuki-redis"
    # Diagnostics & logs
    FETCH_LOGS_DISCORD = "/usr/bin/docker logs --tail 50 yuki-discord-bot"
    FETCH_LOGS_TELEGRAM = "/usr/bin/docker logs --tail 50 yuki-telegram-bot"
    FETCH_LOGS_HORIZ = "/usr/bin/docker logs --tail 50 yuki-horiz-client"
    FETCH_LOGS_CORE_API = "/usr/bin/docker logs --tail 50 yuki-core-api"
    FETCH_LOGS_REDIS = "/usr/bin/docker logs --tail 50 yuki-redis"
    # Global & ingress
    DOCKER_STATS = "/usr/bin/docker stats --no-stream"
    PRUNE_DISK = "/usr/bin/docker system prune -f"
    RESTART_NGINX = "/usr/bin/systemctl restart nginx"
```

### 4.5 The Signed Magic-Link Web Console (Eliminating Discord UI Bugs)
To prevent the notorious Discord UI component traps (3-second timeouts, zombie views on bot restart, and mobile caching bugs), PocketSRE provides a **Signed Magic-Link Pattern**:
* **Mechanism:** Alongside the alert embed, Discord delivers a single URL link button: `[🚨 Open Incident Console]`.
* **Zero-Timeout Guarantee:** Link buttons (`ButtonStyle.link`) invoke zero Discord API callbacks. They are standard URLs that **cannot timeout, cannot expire in memory, and never throw `"Interaction failed"`**. Callback action cards acknowledge immediately, display an in-progress state while the runbook runs, and disable with a Console/`/approve` fallback when their 10-minute Discord view lifetime ends.
* **Cryptographic JWT Authentication:**
  ```python
  def generate_magic_link(user_id: str, role: str, incident_id: str) -> str:
      payload = {
          "sub": user_id,
          "role": role,
          "inc": incident_id,
          "exp": int(time.time()) + 900 # 15 minutes
      }
      token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
      return f"https://yuki-net.ivin.site/console?token={token}&inc={incident_id}"
  ```
* **Mobile In-App Experience:** Clicking the link opens your lightweight Vite web console directly inside the phone's browser or Discord's in-app webview sheet. Users can tail live Docker logs, trigger container restarts, or dispatch Devin with full web responsiveness and zero Discord UI constraints.

### 4.6 Pluggable Autonomous SWE Dispatch (Devin Primary Demo & Local OpenCode Harness)
PocketSRE decouples incident orchestration from any single proprietary code repair engine through a unified provider contract (`AutonomousSweProvider`):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PLUGGABLE AUTONOMOUS SWE ENGINE                                 │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ Provider A: Cognition AI Devin (Demo)    │ Provider B: Local OpenCode / Private Agent  │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • Primary driver for HackaThoni demo     │ • Air-gapped on-premise alternative         │
│ • Cloud-hosted sandbox & PR synthesis    │ • Connects to local runner / OpenCode CLI   │
│ • Real-time interactive session URL      │ • Dispatches via `POST /v1/remediate`       │
│ • Dispatched via official `POST /v3` API │ • Works directly within local git workspace │
│ • Cross-linked to Linear `#YUK-104`      │ • Zero external network calls (Air-gapped)  │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

* **Devin Integration (Demo Showcase):**  
  Dispatches code regressions directly to the Cognition AI Devin API with minimal isolated error context (traceback, failing commit SHA, culprit file). Devin clones the repository, reproduces the failure in a clean cloud sandbox, synthesizes a fix, and generates a GitHub Pull Request.
* **Local Agent Swap (OpenCode / SWE-agent / OpenHands):**  
  For sovereign or air-gapped enterprise deployments where proprietary source code cannot be dispatched to external cloud environments, PocketSRE allows swapping the backend to a locally running agent harness (such as **OpenCode**, **SWE-agent**, or custom toolchains wired to an internal LLM). PocketSRE emits a standardized JSON payload over HTTP (`POST /v1/remediate` on `LOCAL_SWE_ENDPOINT`) or dispatches a local sub-process runner, keeping all git mutations and code analysis entirely within the customer's private infrastructure.
* **Deterministic Demo Resilience:**  
  While the architecture supports swappable backends, **the live houseboat demonstration remains 100% focused on Devin**. Includes a deterministic local fallback stub to ensure the presentation never stalls if Devin cloud VM provisioning experiences latency.
* **Integrated Issue Tracking:**  
  Regardless of the chosen SWE provider, PocketSRE automatically cross-links the session to **Linear** (`#YUK-104`) and **GitHub Issues**, maintaining unified incident traceability.

### 4.7 Discord Voice Intelligence & Conversational Code-Mixing Pipeline (Track 02 Foundation)
To preserve Discord as the single source of truth for identity, alerts, and RBAC without re-inventing fragile web voice widgets, PocketSRE implements an advanced, protocol-level Discord Voice Architecture powered by Sarvam AI:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DISCORD VOICE BOT ARCHITECTURE & MEDIA LAYER                    │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ 1. Gateway Signaling                     │ 2. UDP RTP Media Transport                  │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • Main Gateway: wss://gateway.discord.gg │ • Media: Raw encrypted UDP socket           │
│   (Authenticates session & voice state)  │ • Encryption: XSalsa20_Poly1305 / ChaCha20  │
│ • Voice Gateway: wss://*.discord.media   │ • Audio Encoding: 48 kHz Opus frames (20ms) │
│   (Negotiates UDP endpoint & SSRC keys)  │ • Speaker Demux: Distinct SSRC IDs per user │
├──────────────────────────────────────────┴─────────────────────────────────────────────┤
│ 3. Media Processing Pipeline                                                           │
│ • Outbound (Speaking via Kiwi/Vikram): Sarvam Bulbul -> 48kHz PCM -> Opus -> Encrypted │
│ • Inbound (Listening): UDP RTP -> Libsodium Decrypt -> Libopus PCM -> VAD Silence      │
│   Detection -> Sarvam Saaras Streaming STT (saaras:v4) -> Code-Mixed Mirroring -> Triage│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 4.7.1 Technical Protocol: Is Live Voice Really Possible for Discord Bots?
Yes. Discord bots natively support full-duplex voice communication through the Discord Voice Gateway protocol:
1. **Outbound Transmission (Bot Speaking — Native & Battle-Tested):**  
   Standard `discord.py` connects via `voice_channel.connect()` and plays synthesized audio directly using `voice_client.play(discord.FFmpegPCMAudio(source))`. The audio is encoded into 48 kHz Opus packets and streamed over encrypted UDP to Discord's media server.
2. **Inbound Reception (Bot Listening — Supported via `discord-ext-voice-receive`):**  
   While `discord.py` omits built-in inbound audio decoding to avoid shipping native C libraries, the Discord protocol actively streams incoming voice packets from all channel members to connected bots. PocketSRE leverages `discord-ext-voice-receive` to capture incoming audio:
   * **SSRC Demuxing:** Discord assigns each speaking user a unique 32-bit Synchronization Source (SSRC) identifier, allowing PocketSRE to distinguish who is speaking (e.g., verifying if the speaker holds the `@SRE-Lead` role).
   * **Decryption & Opus Decoding:** Packets are decrypted via Libsodium (`PyNaCl`) and decoded through `libopus` into raw 48 kHz 16-bit PCM audio.
   * **Voice Activity Detection (VAD):** A silence tracker detects conversational pauses (default: 500ms threshold), segmenting speech into distinct command utterances.

#### 4.7.2 The Multi-Language Mirroring Engine (Pure English, Pure Indic & Adaptive Code-Mixing)
PocketSRE delivers full linguistic flexibility across voice notes and live calls. Pure languages—**especially English** as the primary DevOps standard—are foundational, first-class supported modes. Code-mixing is an adaptive conversational feature, not a forced constraint:
* **Pure English In $\rightarrow$ Pure English Out (Core Baseline):** Standard, professional SRE incident narration synthesized via `bulbul:v4-flash` (`en-IN` / `shubh_enhi_ads`) or `en-IN-PrabhatNeural`. When an engineer speaks English, PocketSRE responds strictly in crisp, accurate English without any synthetic code-mixing.
* **Pure Malayalam In $\rightarrow$ Pure Malayalam Out:** Fluent native Malayalam incident alerts and answers synthesized via `bulbul:v3` (`target_language_code="ml-IN"`, speaker: `priya` or `shubh`).
* **Pure Hindi In $\rightarrow$ Pure Hindi Out:** Formal, boardroom-ready Hindi incident reports synthesized via `bulbul:v4-flash` or `bulbul:v3` (`hi-IN`).
* **Adaptive Code-Mixing Feature (Manglish & Hinglish):** Responders are never forced into either pure literary Malayalam or pure English. When engineers naturally blend technical English terms into local sentence structure, Sarvam Saaras STT (`saaras:v4`) accurately parses the command and mirrors the dialect:
  * *Avatar A (Kiwi - Companion SRE):* *"Pinne entha senpai! Njan ippothanne yuki-core-api logs check cheythu restart cheyyaam. Emergency console-il link ayachittund!"* (Empathetic prosody, warm, calming 2 AM crisis companion).
  * *Avatar B (Vikram - Corporate SRE Lead):* *"Yuki core logs inspect cheythu. DB socket connection failure aanu root cause. Emergency console link generate cheythittund, review cheythu approve cheyyuka."* (Authoritative, calm, objective, boardroom-ready).
* **Zero-Cost Fallback:** If Sarvam credits deplete, routes seamlessly to Microsoft `edge-tts` (`en-IN-NeerjaNeural` for English, `ml-IN-SobhanaNeural` for Malayalam, `hi-IN-SwaraNeural` for Hindi).

#### 4.7.3 Staged Engineering Discipline
To eliminate any risk of demonstration failure during the hackathon:
* **Stage 1 (Hours 1–4):** Complete text-only triage, RBAC, and OCI SSH runbooks.
* **Stage 2 (Hours 5–7):** Discord Async Voice Notes (Mode B). Completely immune to WebRTC packet loss because audio files upload reliably over standard HTTP/TCP.
* **Stage 3 (Hours 8–10):** Live Discord Voice Channel Call (Mode C). Activated inside `#incident-war-room` only after Stage 2 is verified 100% rock-solid.

### 4.8 Hard Budget Governor & Spend Circuit Breaker
* Enforces a hard spending cap of **\$5.00** per incident or testing cycle.
* Pre-flight checks prevent agent execution if costs exceed the threshold, locking automated triggers until manual override.

### 4.9 Immutable Audit Logging
* Records every action to NeonDB and an append-only `audit_log.jsonl` with timestamps, actor roles, actions, parameters, and latencies.

### 4.10 Proactive Health Pulse Check
* Responders can check system health at any time (`@PocketSRE status`, `/pocketsre status`, or voice inquiry directed to Kiwi or Vikram).
* PocketSRE queries `/presence/central`, reads OCI memory, and returns an instant health card with current spend.

### 4.11 Adaptive Incident Memory & Self-Learning Playbooks (Experience Engine)
PocketSRE eliminates the operational overhead of hardcoding static runbook rules for every microservice quirk by observing and learning from human SRE actions:
* **Pattern Capture on Lead Resolution:** When an authorized lead (`@SRE-Lead`) executes or approves a remediation action (e.g., approving `docker restart yuki-horiz-client` or container restart after an alert showing `platform_not_connected` on Project Yuki's Hori-Z connector), PocketSRE monitors the service and verifies that health recovers (`200 OK` on `/presence/central`).
* **Fingerprinting & Persistent Storage:** Upon confirmed recovery, PocketSRE normalizes and hashes the error signature (service name + error code + key message tokens) and persists the pattern in NeonDB's `learned_playbooks` table:
  * **Fields:** `pattern_hash`, `service_name`, `error_signature`, `action_taken`, `parameters`, `learned_from` (lead user ID), `confidence_score` (starts at 1, increments with repeated successful resolutions), `success_count`, `last_triggered_at`.
* **Dual Autonomy Execution Model:**
  1. **Suggest Mode (Default / Low-to-Medium Confidence):** When a recurring incident matches a learned pattern, PocketSRE immediately surfaces the proven solution in Discord and the web console:  
     *“I detected `platform_not_connected` on Yuki Hori-Z connector. SRE Lead @Ivin previously resolved this with a container restart (confidence: 94%, 3 successful resolutions). Would you like me to execute `docker restart yuki-horiz-client`?”* (Surfaces 1-tap approval button; voiced in Kiwi's empathetic or Vikram's corporate tone).
  2. **Full Autonomy Mode (`FULL_AUTONOMY=true` or High Confidence):** When enabled by an SRE Lead or when a learned pattern's `confidence_score >= 3` with zero regressions, PocketSRE autonomously executes the whitelisted safe runbook immediately, confirms service health recovery, and notifies the channel post-facto:  
     *“⚡ Auto-resolved `platform_not_connected` on Hori-Z connector using Learned Playbook #104 (verified 3x by Lead). Uptime restored in 420ms.”*
* **Integrity Guardrail Precedence:** Learned playbooks **never override** hardcoded safety invariants in `config.py`. If a learned action attempts a restart while Yuki's `/presence/central` has `maintenance_mode: true` or is outside the sudoers whitelist, PocketSRE rejects execution and defers to manual human intervention.

### 4.12 Configurable Autonomy Policies (Role-Aware Execution Matrix)
Rather than enforcing a rigid, one-size-fits-all behavior, PocketSRE provides a declarative autonomy policy spectrum configured in `config.py` (or toggled on the dashboard):
* **`DESTRUCTIVE_ONLY` (Default & Recommended):**  
  PocketSRE autonomously runs non-mutating diagnostic commands (`df -h`, `free -m`, `docker inspect`, reading logs) to rapidly construct context. It **strictly pauses and requests human authorization** before executing any state-mutating action (container restarts, disk pruning, or Devin PR merges).
* **`UNKNOWN_ONLY` (Playbook Autonomy):**  
  Whitelisted static runbooks and high-confidence learned playbooks (`confidence_score >= 3`) execute autonomously without human prompting. PocketSRE only pauses for authorization when an incident is novel, ambiguous, or requires an ad-hoc command.
* **`STRICT_CONFIRMATION` (Zero-Trust Compliance):**  
  Zero autonomy. Every single action—even a read-only memory check or known container restart—requires explicit 1-tap human authorization. Ideal for regulated or high-compliance enterprise environments.
* **Role-Based Adaptation:**  
  Autonomy policies bind dynamically to the active user's verified Discord role:
  * **`@SRE-Lead`:** Operates under `DESTRUCTIVE_ONLY` or `UNKNOWN_ONLY`, and holds the exclusive authority to unlock the Break-Glass Emergency Console.
  * **`@Junior-Dev`:** Strictly locked to `STRICT_CONFIRMATION` or read-only triage; completely blocked from executing mutations or unlocking emergency console access without senior delegation.

### 4.13 Radical Transparency: The Analyst Hand-Off Dossier & Break-Glass Emergency Console
In mission-critical SRE, "black-box" AI agents that fail silently or hallucinate are rejected by senior engineers. PocketSRE treats **Radical Transparency** as a primary product differentiator, implementing a two-tiered escalation pattern when it reaches an autonomy ceiling:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TWO-TIERED ESCALATION COMMUNICATION                             │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ Tier 1: Discord Notification             │ Tier 2: Emergency Web Console               │
│ (Concise Executive Summary)              │ (In-Depth Analyst Dossier + Command Bar)    │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • Noise-free alert embed in chat         │ • Tapping [🚨 Open Emergency Console] opens │
│ • 2-line incident symptom diagnosis      │   signed magic-link webview on mobile phone │
│ • Clear statement of autonomy ceiling    │ • Complete 4-Pillar Analyst Hand-off Dossier│
│ • Single un-timeoutable action link:     │ • 1-tap Diagnostic Action Pills             │
│   [🚨 Open Emergency Console]            │ • Interactive Ad-Hoc Bash Command Runner    │
│ • Optional voice note (Kiwi or Vikram)   │ • Live stdout/stderr SSE stream (/stream)   │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

#### The 4-Pillar Analyst Hand-Off Dossier (Generated in <800ms)
When an escalation condition triggers (e.g. repeated failure of an approved fix, unknown host socket corruption, or required root/admin privileges beyond `pocketsre`), Gemini Flash Lite synthesizes an in-depth SRE briefing displayed at the top of the Emergency Console:
1. **Telemetry Observations:** Ingested error signatures, port checks, and active connection drop deltas.
2. **Trial Audit (What PocketSRE Tried & Results):** An append-only ledger detailing every diagnostic command or runbook attempted, execution timestamps, exit codes, and stdout snippets.
3. **The Autonomy Boundary (Why PocketSRE Stopped):** The exact reason autonomous remediation halted (e.g. *"Host database socket locked; remediation requires `systemctl restart postgresql` which is outside `pocketsre` non-root whitelist"*).
4. **Human Recommendation:** Prescriptive next steps suggested by the AI based on the failed attempts.

#### Break-Glass Mobile Command Dispatcher (12-Hour Feasible)
To ensure 100% demo stability on budget mobile devices and avoid the fragile 6-hour trap of building a full `xterm.js` Web PTY terminal:
* **Diagnostic Action Pills:** 1-tap quick buttons for PocketSRE's recommended triage checks (`[df -h]`, `[free -m]`, `[docker stats]`, `[docker inspect yuki-core-api]`).
* **Ad-Hoc Command Bar:** A single-line interactive bash prompt on the phone webview: `[ Enter bash command... ] [ Run ]`.
* **Root Shell & Sudo Elevation Pipeline:**
  * When executing under `NON_ROOT` mode, the console provides an **Elevate to Sudo** toggle: the SRE Lead enters their sudo passphrase on the phone webview, passed via TLS to Paramiko as `sudo -S -p '' <cmd>`. Passphrases reside strictly in ephemeral memory for the 15-minute token lifetime and are never persisted to disk.
  * When executing under `FULL_ROOT` mode, commands execute with elevated permissions directly after human sign-off on the phone screen.
* **Live SSE Monospace Viewer:** Streams remote execution stdout/stderr directly to the mobile screen with zero buffering or character limits.
* **Security Guardrails:** Executed under `pocketsre`, filtered against a catastrophic blacklist (`rm -rf /`, `mkfs`, raw block writes), and immutably recorded in NeonDB's `audit_logs`.

### 4.14 Extended Access Plugin Architecture (Tailscale & Terraform Integrations)
To interface safely with complex enterprise environments without causing out-of-band state corruption, PocketSRE incorporates a modular **Extended Access Plugin Architecture**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        EXTENDED ACCESS PLUGIN ARCHITECTURE                             │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ Tailscale Zero-Trust Plugin              │ Terraform / IaC Anti-Drift Plugin           │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • Telemetry: `tailscale status --json`   │ • Telemetry: `terraform plan -detailed-code`│
│   (Derives peer latency & DERP relays)   │   (Detects out-of-band cloud state drift)   │
│ • Execution: Keyless Tailscale SSH       │ • Safe Write A: GitOps PR via Devin/GitHub  │
│   (Zero static .ssh/id_* private keys)   │   (Human-reviewed branch merge in CI/CD)    │
│ • Safe Write: Node Tag Quarantine        │ • Safe Write B: Targeted Emergency Apply    │
│   (Isolates flapping node via ACL API)   │   (Strictly enforces `destroy == 0`)        │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

#### 4.14.1 Pluggable Base Interface (`ExtendedAccessPlugin`)
All enterprise connectors adhere to an abstract contract:
```python
class ExtendedAccessPlugin(ABC):
    plugin_name: str
    
    @abstractmethod
    async def gather_diagnostics(self, incident_context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect read-only telemetry, mesh status, or state drift."""
        pass
        
    @abstractmethod
    async def validate_safe_action(self, proposed_action: Dict[str, Any]) -> bool:
        """Enforce guardrails (Zero-Destroy invariant, sudoers checks)."""
        pass
        
    @abstractmethod
    async def execute_action(self, authorized_action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bounded mutation over Tailscale SSH or Terraform API."""
        pass
```

#### 4.14.2 Tailscale Zero-Trust Plugin
* **Mesh Telemetry & Rapid Triage:**  
  PocketSRE queries the local Tailscale daemon (`tailscale status --json`) or control plane API. It derives node reachability, peer-to-peer connection modes, and DERP relay paths in <20ms, allowing PocketSRE to instantly determine whether an outage is a hypervisor/host failure or an internal process deadlock.
* **Keyless Tailscale SSH:**  
  Eliminates the risk of static private keys (`id_ed25519`) stored on disk. SSH sessions authenticate machine-to-machine through Tailscale ACLs (`tag:pocketsre` $\rightarrow$ `tag:prod-server`), enforced cryptographically via WireGuard.
* **Bounded Safe Write (Mesh Quarantine):**  
  In the event of severe network flapping or compromise, PocketSRE provides a 1-tap action to apply `tag:quarantine` via the Tailscale API, cleanly isolating the host from the private mesh without touching host iptables.

#### 4.14.3 Terraform / IaC Anti-Drift Plugin (Safe Cloud Mutations)
In modern cloud engineering, manual bash fixes risk **Terraform State Drift** (where out-of-band changes get clobbered on the next pipeline run). PocketSRE prevents state drift through an IaC-aware execution model:
* **Drift & State Auditing (Read-Only):**  
  PocketSRE inspects `.tfstate` or Terraform Cloud / Spacelift APIs by running `terraform plan -detailed-exitcode` in read-only mode. Exit code `2` indicates out-of-band cloud drift, which PocketSRE highlights inside the Analyst Dossier.
* **Safe Write Pattern A: The GitOps Pull Request (Non-Emergency Standard):**  
  Instead of mutating cloud resources directly, PocketSRE branches the infrastructure repo and opens an automated Pull Request via Devin/GitHub (e.g. updating `variables.tf` to scale instance sizes or adjust memory limits). CI/CD (Atlantis/GitHub Actions) executes `terraform plan`, posts the diff to Discord, and awaits 1-tap SRE Lead merge approval.
* **Safe Write Pattern B: Targeted Emergency Apply (The "Zero-Destroy Invariant"):**  
  When an immediate cloud write is mandatory (e.g. provisioning a failover DNS record or resizing an OCI block volume during a critical P1 outage):
  1. PocketSRE executes a targeted plan: `terraform plan -target=module.yuki_compute -out=tfplan`.
  2. **The Zero-Destroy Invariant:** PocketSRE parses the plan JSON and evaluates:
     ```python
     if plan["resource_changes"]["destroy"] > 0:
         raise UnsafePlanException("Destructive plans are strictly forbidden in automated applies!")
     ```
  3. If and only if `destroy == 0`, PocketSRE requests SRE Lead authorization and executes `terraform apply "tfplan"`, ensuring zero accidental resource deletions.

### 4.15 Documentation & Infrastructure Knowledge Transfer Engine
To solve the fundamental enterprise dilemma—*"How does PocketSRE understand our specific infrastructure topology, service boundaries, and internal runbooks without hardcoded rules?"*—PocketSRE implements a lightweight, zero-friction **Knowledge Transfer Ingestion Engine**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE TRANSFER INGESTION PIPELINE                           │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ 1. Ingestion Sources                     │ 2. Chunking & Indexing (NeonDB)             │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • Signed Web Console: Markdown upload    │ • Semantic header splitting (H2/H3 bounds)  │
│ • Discord: `/pocketsre learn-infra <file>`│ • Tagging: service_name, doc_type, sockets  │
│ • Local Repo Sync: `/docs/infra/` mount  │ • Stored in table `infra_knowledge_docs`    │
├──────────────────────────────────────────┴─────────────────────────────────────────────┤
│ 3. Incident Triage Grounding (Context Injection in <15ms)                              │
│ • Query: Service match (`yuki-core-api`) or keyword tags (`database`, `socket`, `nginx`)   │
│ • Prompt Context: Injects exact architecture facts (host mounts, ports, runbooks)      │
│ • Result: Eliminates hallucinated generic bash; guarantees topology-accurate triage    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 4.15.1 Multi-Channel Ingestion Workflows
1. **Signed Web Console Upload (`POST /api/knowledge/upload`):**  
   SRE Leads can upload internal documentation (`ARCHITECTURE.md`, `TOPOLOGY.md`, `RUNBOOKS.md`, `docker-compose.yml`) directly from their phone or laptop via the Signed Web Console.
2. **Discord Channel Ingestion (`/pocketsre learn-infra`):**  
   Engineers can attach markdown guides directly in Discord `#general-ops`. PocketSRE parses the document, validates structure, and acknowledges with a summary card detailing indexed services.
3. **Automated Directory Sync:**  
   On startup or via webhook, PocketSRE reads markdown documentation located in `/docs/infra` or the target repository, creating an instant local knowledge baseline.

#### 4.15.2 Semantic Chunking & NeonDB Knowledge Store
* Documents are split into semantic chunks based on markdown headings (`## Service: <name>`, `### Dependencies`, `### Known Failure Modes`).
* Each chunk is persisted to NeonDB in `infra_knowledge_docs` with metadata:
  * `service_name`: Target service (e.g. `yuki-core-api`, `yuki-horiz-client`).
  * `doc_type`: `TOPOLOGY`, `RUNBOOK`, `SERVICE_SPEC`, or `POSTMORTEM`.
  * `content_md`: Extracted ground-truth text.
  * `tags`: Array of keywords (`socket`, `port_8000`, `postgres_socket`, `systemd`).
* For the 12-hour hackathon, fast indexed lookup on `(service_name, tags)` or PostgreSQL full-text search (`to_tsvector`) provides sub-15ms retrieval without requiring complex embedding pipeline infrastructure.

#### 4.15.3 Incident Triage Context Injection (Grounding the LLM)
When an incident is ingested (e.g. `yuki-core-api` reporting socket errors), PocketSRE's reflex engine queries `infra_knowledge_docs` for relevant architecture context:
```markdown
[INFRASTRUCTURE GROUND TRUTH - yuki-core-api]
• Service: FastAPI modular monolith container running on OCI VM.
• Socket Mount: Connects to host PostgreSQL UNIX socket at /var/run/postgresql/.s.PGSQL.5432.
• Port & Ingress: Internal port 8000 reverse-proxied by host NGINX (/presence/central).
• Known Failure Mode: If database connection fails with "Connection refused (.s.PGSQL.5432)", host postgresql service must be restarted via systemd or socket directory permissions adjusted (requires root).
```
This injected context ensures that PocketSRE immediately recognizes why a container restart alone cannot resolve the issue, preventing useless retry loops and directly informing the 4-Pillar Escalation Dossier.

---

### 4.16 Pluggable Multi-Provider AI Architecture & Enterprise Privacy Sovereignty
Enterprise security standards (SOC2, GDPR, HIPAA) often forbid sending proprietary infrastructure topology, internal hostnames, and application stack traces to third-party public cloud APIs. To address this requirement while maintaining exceptional hackathon demo agility, PocketSRE features a **Pluggable Multi-Provider AI Engine**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PLUGGABLE MULTI-PROVIDER AI ENGINE                              │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ Provider A: Google GenAI (Demo Primary)  │ Provider B: OpenAI-Compatible SDK (Private) │
├──────────────────────────────────────────┼─────────────────────────────────────────────┤
│ • SDK: `google-genai` Python SDK         │ • SDK: Standard `openai` Python SDK         │
│ • Model: Gemini Flash Lite               │ • Configurable: `base_url` + `api_key`      │
│ • Dual-Key Rotation on HTTP 429          │ • Targets: Self-Hosted vLLM, Ollama,        │
│ • Multimodal voice & vision ingestion    │   LocalAI, TGI, or Azure OpenAI             │
│ • Zero-cost, high-velocity hackathon demo│ • 100% Air-Gapped / Sovereign Enterprise    │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

#### 4.16.1 Unified Dual-SDK Abstraction
PocketSRE implements a clean provider factory (`ai_provider.py`):
* **`AI_PROVIDER = "gemini"`:** Uses Google's official `google-genai` SDK with dual API keys for high-speed, cost-effective multimodal incident reasoning during the live hackathon presentation.
* **`AI_PROVIDER = "openai_compatible"`:** Uses the official `openai` Python SDK, dynamically binding to custom enterprise endpoints (`OPENAI_BASE_URL="http://vllm.internal.mesh:8000/v1"`). Works out-of-the-box with **vLLM**, **Ollama**, **LocalAI**, or **Azure OpenAI Service**.

#### 4.16.2 The Enterprise Zero-Leakage Guarantee
When configured in `openai_compatible` mode with an on-premises or VPC-internal model (e.g. self-hosted Llama-3-70B or Qwen-2.5-Coder running on private GPUs or via Tailscale):
* **Zero External Calls:** Telemetry, logs, stack traces, and uploaded architecture documentation **never traverse public internet gateways**.
* **Air-Gapped Operation:** All inference runs within the customer's private security perimeter, fully satisfying strict enterprise data governance and compliance audits.

#### 4.16.3 Foundation Modules Reused from Project Yuki
To guarantee rock-solid stability and save 3+ hours of repetitive scaffolding during the 12-hour hackathon, PocketSRE's AI foundation directly adapts battle-tested modules from **Project Yuki**:
1. **`APIKeyPool` & Key Rotation Manager:** Yuki's resilient multi-key pool with automated round-robin rotation, exponential backoff, and instantaneous failover upon HTTP 429 quota exhaustion.
2. **Resilient HTTP Client & Retry Wrappers:** Yuki's async singleton connection pool and timeout-handling decorators.
3. **Health Poller & Telemetry Pipeline:** Yuki's `/presence/central` poller pattern, adapted to monitor internal container health.

---

## 5. Optional Features (Post-MVP Scope)

### 5.1 One-Click Blameless Post-Mortem Generator (Linear & Notion)
* Auto-synthesizes an enterprise Markdown retrospective upon incident resolution.
* Exports to Linear as an issue comment/sub-task and to Notion via REST API (`POST https://api.notion.com/v1/pages`).

### 5.2 Spoken Passphrase / Voice PIN with Side-Effect Warning
* Requires spoken passphrase authorization (*"Authorize Alpha-Seven-Niner"*) for high-blast-radius actions, explicitly stating side effects beforehand.

### 5.3 Live Single-Page Mission Control Dashboard & Calm Incident Console
* **Calm Mobile-First Incident Console (`/console/`):** Designed for high-stress on-call triage:
  * Incident header with severity, status, service, summary, and copyable incident ID
  * Prominent "What should I do next?" section surfacing a single primary recommended action (never defaulting to destructive commands)
  * Grouped action taxonomy: Recommended, Safe diagnostics, Recovery actions, and Advanced/Host actions behind progressive disclosure
  * Pre-flight availability filters disabling invalid actions with explanatory tooltips (e.g., service journal limited to nginx/docker)
  * Confirmation modal for mutating operations displaying target service, side-effect warning, and explicit Cancel / Confirm buttons
  * Compact result cards with ANSI stripping (`stripAnsi`), scrollable terminal code blocks, and copy-to-clipboard
  * Structured API error formatting preventing raw object leakage (`[object Object]`)
  * Clear empty states for action history and audit events
* **Operational Mission Control Overview (`/console/mission-control.html`):**
  * Top operational summary row (overall system state, monitored services status breakdown, open incidents, spend)
  * Granular presence cards distinguishing Healthy, Degraded, Unreachable, No Coverage, and Not Configured states with collapsible probe payloads
  * Null-safe budget governor displays replacing nulls with "Not configured" / "—" (never `$null`)
  * Streaming audit feed via Server-Sent Events (`/stream`) with friendly empty state

### 5.4 GUI-Based Onboarding & Configuration Wizard (SaaS-Style Setup)
* **Description:** A visual, web-based onboarding wizard on the Vite dashboard that allows engineering teams to configure PocketSRE like a modern SaaS platform:
  * Interactive inputs for setting target container names, SSH credentials, and health check URLs without editing `.env` or `config.py` manually.
  * Visual RBAC Role Mapping matrix (drag-and-drop assigning Discord/Slack roles to permissible runbook actions).
  * Visual toggle for custom production integrity rules (e.g., toggling "Strict Pre-flight Checks" or "Auto-Drain WebSocket connections").

---

## 6. Data Contracts & Pydantic Schemas

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class IncidentSeverity(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"

class IncidentClass(str, Enum):
    CODE_REGRESSION = "CODE_REGRESSION"
    RESOURCE_STARVATION = "RESOURCE_STARVATION"
    INFRA_OFFLINE = "INFRA_OFFLINE"
    TRANSIENT_BLIP = "TRANSIENT_BLIP"

class RunbookAction(str, Enum):
    RESTART_YUKI_CORE = "/usr/bin/docker restart yuki-core-api"
    RESTART_HORIZ_CLIENT = "/usr/bin/docker restart yuki-horiz-client"
    FETCH_LOGS_CORE_API = "/usr/bin/docker logs --tail 50 yuki-core-api"
    FETCH_LOGS_HORIZ_CLIENT = "/usr/bin/docker logs --tail 50 yuki-horiz-client"
    PRUNE_DISK = "/usr/bin/docker system prune -f"
    RESTART_NGINX = "/usr/bin/systemctl restart nginx"
    DISPATCH_DEVIN = "dispatch_devin_agent"
    GENERATE_POSTMORTEM = "generate_postmortem"

class IncidentPayload(BaseModel):
    incident_id: str
    source: str = Field(description="sentry, presence_poller, or generic")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    error_message: str
    stack_trace: Optional[str] = None
    affected_users: int = 0
    inferred_class: IncidentClass = IncidentClass.CODE_REGRESSION
    severity: IncidentSeverity = IncidentSeverity.P2_HIGH

class AgentActionRequest(BaseModel):
    incident_id: str
    action: RunbookAction
    actor_id: str
    actor_role: str
    authorized: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AuditLogEntry(BaseModel):
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    incident_id: str
    actor: str
    actor_role: str
    action: RunbookAction
    result: str
    duration_ms: int
    cost_usd: float = 0.00

class LearnedPlaybook(BaseModel):
    id: Optional[int] = None
    pattern_hash: str = Field(description="SHA256 hash of service + normalized error")
    service_name: str
    error_signature: str
    recommended_action: RunbookAction
    parameters: Dict[str, Any] = Field(default_factory=dict)
    learned_from: str = Field(description="Discord ID of senior engineer who authorized it")
    confidence_score: int = 1
    success_count: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered_at: datetime = Field(default_factory=datetime.utcnow)

class PlaybookResolutionSource(str, Enum):
    STATIC_CONFIG = "STATIC_CONFIG"
    LEARNED_MEMORY = "LEARNED_MEMORY"
    LLM_REASONING = "LLM_REASONING"

class AutonomyPolicyMode(str, Enum):
    DESTRUCTIVE_ONLY = "DESTRUCTIVE_ONLY"
    UNKNOWN_ONLY = "UNKNOWN_ONLY"
    STRICT_CONFIRMATION = "STRICT_CONFIRMATION"

class IncidentTrial(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_type: str = Field(description="DIAGNOSTIC or RUNBOOK")
    command_executed: str
    exit_code: int
    stdout_snippet: str
    result: str

class EscalationDossier(BaseModel):
    incident_id: str
    service: str
    severity: IncidentSeverity
    telemetry_observations: List[str]
    trials_attempted: List[IncidentTrial]
    autonomy_boundary_reason: str
    recommended_first_action: str
    break_glass_unlocked: bool = True
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionPrivilegeMode(str, Enum):
    NON_ROOT = "NON_ROOT"
    FULL_ROOT = "FULL_ROOT"

class BreakGlassCommandRequest(BaseModel):
    incident_id: str
    actor_id: str
    actor_role: str
    jwt_token: str
    raw_command: str
    require_sudo: bool = False
    sudo_passphrase: Optional[str] = None
    privilege_mode: ExecutionPrivilegeMode = ExecutionPrivilegeMode.NON_ROOT

class TailscalePeerStatus(BaseModel):
    node_id: str
    hostname: str
    ip_addresses: List[str]
    online: bool
    direct_connection: bool
    derp_region: Optional[str] = None
    latency_ms: float = 0.0

class IaCResourceChange(BaseModel):
    address: str
    action: str  # create, update, delete, no-op
    resource_type: str

class IaCPlanSummary(BaseModel):
    add: int = 0
    change: int = 0
    destroy: int = 0
    zero_destroy_verified: bool = False
    resource_changes: List[IaCResourceChange] = Field(default_factory=list)

class ExtendedPluginActionRequest(BaseModel):
    plugin_name: str
    incident_id: str
    action_type: str
    target_resource: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    authorized_by: str

class AIProviderType(str, Enum):
    GEMINI = "gemini"
    OPENAI_COMPATIBLE = "openai_compatible"

class AIProviderConfig(BaseModel):
    provider_type: AIProviderType = AIProviderType.GEMINI
    model_name: str = "gemini-2.0-flash-lite"
    base_url: Optional[str] = None
    api_key_primary: str
    api_key_fallback: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 1024

class InfraDocumentType(str, Enum):
    TOPOLOGY = "TOPOLOGY"
    RUNBOOK = "RUNBOOK"
    SERVICE_SPEC = "SERVICE_SPEC"
    POSTMORTEM = "POSTMORTEM"

class InfraKnowledgeDoc(BaseModel):
    id: Optional[int] = None
    service_name: str
    doc_type: InfraDocumentType = InfraDocumentType.TOPOLOGY
    title: str
    content_md: str
    tags: List[str] = Field(default_factory=list)
    uploaded_by: str = "system"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class KnowledgeUploadRequest(BaseModel):
    service_name: str
    doc_type: InfraDocumentType = InfraDocumentType.TOPOLOGY
    title: str
    raw_markdown: str
    tags: List[str] = Field(default_factory=list)
    uploaded_by: str

class KnowledgeContextInjection(BaseModel):
    service_name: str
    matched_chunks: List[str]
    retrieval_duration_ms: float

class SweAgentProviderType(str, Enum):
    DEVIN = "devin"
    LOCAL_OPENCODE = "local_opencode"
    GENERIC_WEBHOOK = "generic_webhook"

class SweRemediationRequest(BaseModel):
    incident_id: str
    provider: SweAgentProviderType = SweAgentProviderType.DEVIN
    service_name: str
    repo_url: str
    commit_sha: str
    error_traceback: str
    culprit_file: str
    prompt: str

class SweRemediationSession(BaseModel):
    session_id: str
    provider: SweAgentProviderType
    status: str
    web_url: Optional[str] = None
    pr_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 7. Incident Handling Workflows

### 7.1 Scenario A: Container / Process Crash (Infra in Control)
1. **Trigger:** `yuki-core-api` container terminates on OCI.
2. **Ingest:** Presence poller detects timeout on `/presence/central`.
3. **Triage:** Classified as `RESOURCE_STARVATION` in <40ms.
4. **Alert:** Discord bot delivers an embed, audio clip, and `[🚨 Open Incident Console]` link button to `#yuki-alerts`.
5. **Authorization:** SRE Lead opens the signed magic-link to tap `[⚡ Restart Yuki Core]` on the web console, or replies `@PocketSRE approve` in Discord.
6. **Pre-flight Check:** PocketSRE checks `config.py` rules and `/presence/central` flags (ensures `maintenance_mode == false`).
7. **Execution:** Restricted SSH runner executes `/usr/bin/docker restart yuki-core-api` on OCI.
8. **Verification:** Poller confirms `200 OK`. Voice confirmation synthesized via active avatar (Kiwi or Vikram).

### 7.2 Scenario B: Code Deployment Bug (Application Regression)
1. **Trigger:** New deploy causes unhandled `TypeError` in `auth.py`.
2. **Ingest:** Sentry webhook fires to `/webhook/sentry`.
3. **Triage:** Dual-Key Gemini Flash Lite extracts traceback and commit SHA.
4. **Alert:** PocketSRE reports regression and recommends autonomous code fix (configured to Devin API for live presentation, with swappable local OpenCode harness support).
5. **Authorization:** SRE Lead taps `[🤖 Dispatch Devin Fix]` on mobile console (or `[🤖 Dispatch Local SWE Fix]`).
6. **Execution:** Dispatches session via selected SWE provider (`DevinProvider` or `LocalOpenCodeProvider`), logs Linear issue `#YUK-104`, opens GitHub issue.
7. **Resolution:** Devin (or local agent) synthesizes patch, executes test verification, and links PR to Discord.

### 7.3 Scenario C: Host / Network Unreachable (Honest Autonomy Boundary)
1. **Trigger:** OCI VM network interface drops or host crashes.
2. **Ingest:** Both SSH port 22 and HTTP port 443 time out after 3 retries.
3. **Diagnosis:** Local internet verified, OCI IP unreachable.
4. **Honest Reporting:** PocketSRE states clearly:  
   *“I cannot reach the OCI host via SSH or HTTP. The VM appears powered off or network-isolated. This is beyond autonomous runbooks—please check the Oracle Cloud web console!”* (Delivered in crisp pure English, or mirrored native Indic / Manglish voice note via Kiwi or Vikram, matching the responder's language).

### 7.4 Scenario D: Learned Incident Auto-Remediation (Experience Retrieval)
1. **Trigger:** Project Yuki's Hori-Z connector emits alert: `platform_not_connected: failed to sync presence`.
2. **Ingest & Fingerprint:** PocketSRE computes hash `(service="yuki-horiz-client", error="platform_not_connected")` and queries NeonDB `learned_playbooks`.
3. **Pattern Match:** Match retrieved with `confidence_score=4`, originally learned from SRE Lead `@Ivin` with recommended action `RESTART_HORIZ_CONNECTOR`.
4. **Action Branching:**
   * *Suggest Mode:* PocketSRE delivers Discord alert: *"Learned Playbook Match: Platform connector desync is typically resolved by restarting container. [⚡ Apply Learned Fix]"*. Lead taps once to execute.
   * *Full Autonomy Mode:* PocketSRE executes `/usr/bin/docker restart yuki-horiz-client` over Paramiko SSH, verifies `/presence` returns `200 OK`, and notifies channel post-facto.
5. **Reinforcement:** Increments `success_count` and updates `last_triggered_at` in NeonDB.

### 7.5 Scenario E: Autonomy Ceiling & Break-Glass Hand-Off (Radical Transparency)
1. **Trigger:** `yuki-core-api` emits continuous alerts: `FATAL: could not connect to server: Connection refused (/var/run/postgresql/.s.PGSQL.5432)`.
2. **Autonomous Diagnostic & Safe Trial:**
   * Under `DESTRUCTIVE_ONLY` policy, PocketSRE autonomously runs `docker logs --tail 20 yuki-core-api` and records an `IncidentTrial`.
   * PocketSRE executes whitelisted restart `RESTART_YUKI_CORE`. Health poller on `/presence/central` still returns `504 Gateway Timeout`.
3. **Autonomy Ceiling Encountered:**
   * PocketSRE detects that the crash is due to a locked host PostgreSQL UNIX socket on the OCI VM.
   * Remediating a host-level service socket requires administrative root access (`systemctl restart postgresql`), which is strictly forbidden under `pocketsre`'s non-root sandbox.
4. **Two-Tiered Notification & Dossier Generation:**
   * Gemini Flash Lite generates the 4-Pillar Analyst Escalation Dossier in 620ms.
   * **Discord Channel:** Receives a concise executive alert card:  
     *“🚨 BREAK-GLASS ESCALATION: Yuki core database socket locked on host. 1 safe container restart attempted without recovery. Host root remediation required. [🚨 Open Emergency Console]”*
   * **Active Avatar Voice Clip:** Companion voice (Kiwi) chimes: *"Senpai, I tried restarting the container, but the host database socket is locked. I've hit my safety limit so I don't break anything. Full investigation dossier is ready on your emergency console!"* (or Vikram's concise corporate briefing).
5. **Mobile Break-Glass Console Hand-Off:**
   * SRE Lead opens the signed magic-link on their mobile browser.
   * **Top Screen:** Shows the comprehensive Analyst Dossier detailing exact timestamps, the failed container restart exit code, and why PocketSRE refused to guess.
   * **Bottom Screen:** Unlocks the Break-Glass Command Bar. The Lead taps the suggested action pill or types `sudo systemctl restart postgresql && docker restart yuki-core-api`.
6. **Execution & Restoration:**
   * Command executes over SSH with live SSE terminal logs streaming to the phone screen. Health poller confirms `200 OK`.
   * Complete trial ledger, human command trace, and resolution duration are committed to NeonDB `audit_logs`.

### 7.6 Scenario F: Knowledge-Augmented Outage Diagnosis (Context Ingestion in Action)
1. **Trigger:** `yuki-core-api` container restarts in loop; logs emit: `alembic.util.exc.CommandError: Can't locate revision identified by 'a1b2c3d4'`.
2. **Telemetry Ingest:** PocketSRE captures the unhandled database migration exception.
3. **Knowledge Store Query:** PocketSRE's reflex engine queries `infra_knowledge_docs` for `service="yuki-core-api"` and tags `["migration", "alembic", "database"]`.
4. **Ground-Truth Retrieval (<15ms):** Ingested `ARCHITECTURE.md` chunk is retrieved:
   *"Yuki core uses Alembic migrations located in backend/alembic. Database migrations are mounted from host /opt/yuki/migrations. If revision mismatch occurs after git pull, run alembic stamp head or roll back commit."*
5. **Contextual Action:**
   * PocketSRE bypasses naive container restarts (knowing that restarts cannot resolve missing migration heads).
   * Surfaces an actionable diagnosis to the Discord war room:
     *“Alembic migration mismatch detected on `yuki-core-api`. According to your ingested architecture doc, this happens when migrations are out of sync with the mounted volume. Recommending Devin branch rollback or manual alembic stamp.”*
   * Avoids wasted autonomous restarts and saves time and API budget.

---

## 8. Expected Technical Failures & Hardened Mitigations

To guarantee 100% demo stability on the houseboat, the following edge cases are strictly mitigated:

| Failure Mode ID | Risk Description | Root Cause | Hardened Production Mitigation |
|---|---|---|---|
| **FAIL-1.1** | **3-Second Discord Timeout** | Discord aborts interactions if unacknowledged within 3.0s | **Line 1 Deferral / Magic Links:** Execute `await interaction.response.defer()` as line 1, and use Signed Magic-Link buttons (`ButtonStyle.link`) which have zero Discord API callback timeouts. |
| **FAIL-1.2** | **DM / User `AttributeError`** | `interaction.user` in DMs has no `.roles` attribute | Add `@app_commands.guild_only()` to all slash commands and use `getattr(interaction.user, "roles", [])` in interaction handlers. |
| **FAIL-2.1** | **Discord Voice UDP Packet Loss** | Unstable cellular hotspot causes Opus audio frame loss during live voice call | **Graceful Mode B Fallback:** Kiwi detects UDP jitter or VAD timeouts and prompts the user to switch to Discord Voice Notes (Mode B), which upload reliably over HTTP/TCP with zero packet loss. |
| **FAIL-2.2** | **Target Host Crash & Python Collision** | Co-locating an SRE bot on the monitored host risks bot termination during OOM storms, and running stray scripts pollutes Python dependencies | **Two-VM Out-of-Band Topology & Containerization:** PocketSRE is hosted on a separate OCI Control-Plane VM inside an isolated `container_name: pocketsre-core` container, executing SRE actions strictly via remote SSH. Even if Yuki's VM experiences a kernel panic or CPU freeze, PocketSRE stays online, diagnoses the failure, and alerts engineers. |
| **FAIL-3.1** | **Sudoers Non-Interactive & Modern Syntax** | Modern Ubuntu (sudo 1.9+) rejects obsolete `requiretty` directive and disallows non-trailing wildcards in argument lists | Omit deprecated `requiretty`, use trailing wildcards (`/usr/bin/docker logs *`) for read-only telemetry, and validate syntax with `visudo -cf`. |
| **FAIL-3.2** | **Binary Path Mismatch** | Sudo rejects command if path is not absolute | Pin absolute paths strictly in Python's enum (`/usr/bin/docker restart yuki-core-api`, `/usr/bin/docker restart yuki-horiz-client`). |
| **FAIL-3.3** | **Unverified Lifecycle Restarts & Name Drift** | Naive container cycling violating Yuki's production integrity rules | Pin `container_name: yuki-core-api` and `container_name: yuki-horiz-client` in `docker-compose.yml`, AND enforce declarative pre-flight integrity checks in `config.py` (checking `/presence/central` flags before issuing container restarts). |
| **FAIL-3.4** | **SSH Host Key Rejection** | Paramiko aborts on unknown host key | Enforce `client.set_missing_host_key_policy(paramiko.AutoAddPolicy())`. |
| **FAIL-4.1** | **Devin 90–240s Stage Latency** | Devin VM provisioning exceeds 3-minute pitch window | **Two-Tiered Fast-Path:** Fire Devin asynchronously in background while displaying real-time AST test verification locally; maintain pre-warmed PR branch as contingency. |
| **FAIL-4.2** | **Gemini 429 Quota Exhaustion** | 15 RPM free tier limit hit during rapid testing | **Dual-Key Rotation:** Automatically failover to backup Gemini API key upon HTTP 429. |
| **FAIL-4.3** | **AI Provider Outage / Key Lockout** | Gemini public API 500 error or complete quota depletion | **Multi-Provider Failover (Yuki Foundation):** Automatically failover from Gemini primary key to fallback key, and if public APIs fail, route inference to local/private OpenAI-compatible endpoint. |
| **FAIL-5.1** | **NeonDB Cold Start Delay** | Serverless compute auto-suspends after 5m idle | Ping NeonDB with `SELECT 1;` every 4 minutes on idle; write audit logs via `BackgroundTasks`. |
| **FAIL-5.2** | **Knowledge Context Overflow** | Uploaded architecture doc exceeds LLM prompt token window | **Semantic Chunking:** Split docs along H2/H3 headings and only inject the top-3 matching chunks ($<1,000$ tokens) into the triage prompt. |
| **FAIL-6.1** | **IaC State Drift Collision** | Out-of-band manual changes overwrite Terraform state | Enforce Zero-Destroy Invariant (`destroy == 0`) before any targeted apply; default all non-urgent mutations to GitOps PRs. |
| **FAIL-6.2** | **Tailscale DERP Relay Spike** | P2P NAT traversal fails, routing traffic over transatlantic DERP | Evaluate `direct_connection` and latency in pre-flight diagnostics; fallback automatically to Cloudflare Tunnel if latency > 300ms. |

---

## 9. Legal Pre-Hackathon Setup Checklist (What to Do Before Saturday)

In standard competitive hackathons (MLH, Devfolio, Cognition AI), **pre-coding product features is prohibited**, but **pre-provisioning accounts, API keys, databases, bot tokens, and configuring cloud infrastructure is 100% legal, encouraged, and standard practice**.

Completing this checklist before Saturday morning saves **3 to 4 hours of pure administrative friction**:

### 9.1 Discord Developer Portal & Server Prep
* [x] Create Discord Application: **`PocketSRE`** at `discord.com/developers/applications`.
* [x] Upload avatar image and copy Bot Token to `.env` (`DISCORD_BOT_TOKEN`).
* [x] Under **Bot > Privileged Gateway Intents**, enable **`Message Content Intent`**, **`Server Members Intent`**, and **`Presence Intent`**.
* [x] Under **Bot / OAuth2**, toggle OFF **`Requires OAuth2 Code Grant`** (critical to avoid OAuth2 code exchange modal errors).
* [x] Generate Direct OAuth2 Bot URL with permissions (`permissions=8&scope=bot%20applications.commands`).
* [x] Invite bot to dedicated Discord server: **`PocketSRE Incident War Room`** (Completed & Verified!).
* [ ] Create Server Roles:
  * **`@SRE-Lead`** (assign to primary personal account).
  * **`@Junior-Dev`** (assign to secondary test account to demo RBAC).
* [ ] Create channels: `#yuki-alerts`, `#incident-console`, `#general-ops`.

### 9.2 NeonDB Cloud Database Prep
* [ ] Create free PostgreSQL project at `console.neon.tech` (e.g., `kiwi-sre-prod`).
* [ ] Copy the **Pooled Connection String** (`postgres://...@ep-xxxx-pooler.region.neon.tech/neondb?sslmode=require`).
* [ ] Run initial table creation DDL via Neon SQL editor (`incidents`, `audit_logs`, `budget_ledger`, `learned_playbooks`):
  ```sql
  CREATE TABLE IF NOT EXISTS incidents (
      id VARCHAR(64) PRIMARY KEY,
      service_name VARCHAR(64) NOT NULL,
      status VARCHAR(32) NOT NULL,
      severity VARCHAR(16) NOT NULL,
      error_message TEXT,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      resolved_at TIMESTAMP WITH TIME ZONE
  );

  CREATE TABLE IF NOT EXISTS audit_logs (
      id SERIAL PRIMARY KEY,
      incident_id VARCHAR(64) REFERENCES incidents(id),
      actor_id VARCHAR(64) NOT NULL,
      actor_role VARCHAR(32) NOT NULL,
      action_type VARCHAR(64) NOT NULL,
      status VARCHAR(32) NOT NULL,
      timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  CREATE TABLE IF NOT EXISTS budget_ledger (
      id SERIAL PRIMARY KEY,
      incident_id VARCHAR(64),
      amount_spent NUMERIC(6,4) DEFAULT 0.0000,
      timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  CREATE TABLE IF NOT EXISTS learned_playbooks (
      id SERIAL PRIMARY KEY,
      pattern_hash VARCHAR(64) UNIQUE NOT NULL,
      service_name VARCHAR(64) NOT NULL,
      error_signature TEXT NOT NULL,
      recommended_action VARCHAR(64) NOT NULL,
      parameters JSONB DEFAULT '{}'::jsonb,
      learned_from VARCHAR(64) NOT NULL,
      confidence_score INT DEFAULT 1,
      success_count INT DEFAULT 1,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      last_triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  CREATE TABLE IF NOT EXISTS infra_knowledge_docs (
      id SERIAL PRIMARY KEY,
      service_name VARCHAR(64) NOT NULL,
      doc_type VARCHAR(32) NOT NULL,
      title VARCHAR(128) NOT NULL,
      content_md TEXT NOT NULL,
      tags TEXT[] DEFAULT '{}',
      uploaded_by VARCHAR(64) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  ```

### 9.3 Oracle Cloud (OCI) Two-VM Infrastructure Prep

To simulate genuine enterprise SRE operations, PocketSRE uses a **Two-VM Architecture** on the same OCI Virtual Cloud Network (VCN):
* **VM 1 (PocketSRE Control-Plane VM):** Runs PocketSRE's isolated `pocketsre-core` container, Discord bot, and API router.
* **VM 2 (Project Yuki Workload VM):** Runs Yuki's production services (`yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`, `yuki-telegram-bot`, `yuki-redis`, PostgreSQL, NGINX).

#### 9.3.1 Target Workload VM Prep (Project Yuki VM)
* [ ] Create dedicated non-root user `pocketsre` on the Yuki OCI instance: `sudo adduser --disabled-password --gecos "" pocketsre`.
* [ ] Add PocketSRE's SSH public key (`pocketsre_bot_ed25519.pub`) to `/home/pocketsre/.ssh/authorized_keys`.
* [ ] Configure `/etc/sudoers.d/pocketsre` on Yuki VM with comprehensive whitelisted docker/systemctl commands:
  ```text
  # Container Lifecycle (Restart, Stop, Start)
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-discord-bot
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-telegram-bot
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-horiz-client
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-core-api
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker restart yuki-redis
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-discord-bot
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-telegram-bot
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-horiz-client
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-core-api
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker start yuki-redis
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-discord-bot
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-telegram-bot
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-horiz-client
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-core-api
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stop yuki-redis

  # Container Read-Only Diagnostics & Logs (Any Options / Tail Counts)
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker logs *
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker inspect *
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker top *

  # Global Telemetry & Cleanup
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker ps
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker ps -a
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker stats --no-stream
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/docker system prune -f
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/systemctl status nginx
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/nginx -t
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u nginx *
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/systemctl status docker
  pocketsre ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u docker *
  ```
* [ ] Verify container names in Yuki's `docker-compose.yml` are pinned to `yuki-core-api`, `yuki-horiz-client`, `yuki-discord-bot`, `yuki-telegram-bot`, and `yuki-redis`.

#### 9.3.2 PocketSRE Control-Plane VM Prep (PocketSRE Host)
* [ ] Place SSH private key (`pocketsre_bot_ed25519`) in `~/.ssh/pocketsre_bot_ed25519` (chmod 600) to allow remote access to Yuki's VM.
* [ ] Configure PocketSRE's dedicated container in `docker-compose.yml` (`container_name: pocketsre-core`) so it runs completely isolated from host Python microservices:
  ```yaml
  pocketsre-core:
    container_name: pocketsre-core
    build:
      context: ./pocketsre-backend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - ~/.ssh/pocketsre_bot_ed25519:/app/.ssh/pocketsre_bot_ed25519:ro
      - ./docs/infra:/app/docs/infra:ro
    env_file:
      - .env
  ```
* [ ] Test connection from PocketSRE VM / container to Yuki VM over the OCI private network (or public IP):
  ```bash
  ssh -i ~/.ssh/pocketsre_bot_ed25519 pocketsre@<YUKI_VM_IP> 'sudo /usr/bin/docker logs --tail 5 yuki-core-api'
  ssh -i ~/.ssh/pocketsre_bot_ed25519 pocketsre@<YUKI_VM_IP> 'sudo /usr/bin/docker logs --tail 5 yuki-redis'
  ```
  *(Verify both connect in under 1 second without prompting for a password).*

### 9.4 Ingress, DNS, & Cloudflare Tunnel Prep
* [ ] Configure Cloudflare Tunnel (`cloudflared`) or add an NGINX route on your existing domain (e.g. public route `https://pocketsre.ivin.site/console` pointing to the Vite web console, and `/api/pocketsre` pointing to the FastAPI backend).
* [ ] Verify HTTPS SSL certificate is valid and active so webhook destinations never break during the sprint.

### 9.5 API Keys & Integration Provisioning
* [ ] **Google Gemini API:** Generate 2 API keys from Google AI Studio (`GEMINI_API_KEY_PRIMARY` and `GEMINI_API_KEY_FALLBACK`).
* [ ] **OpenAI / Self-Hosted Inference Endpoint:** (Optional): Verify local Ollama (`ollama serve`) or internal vLLM endpoint (`OPENAI_BASE_URL`) if demoing air-gapped private model execution.
* [ ] **Pre-seed Infra Knowledge Documentation:** Create sample `docs/infra/yuki_architecture.md` containing Yuki container topology, PostgreSQL socket paths, and internal ports for knowledge transfer testing.
* [ ] **Project Yuki Foundation Assets:** Stage Project Yuki's battle-tested `APIKeyPool` multi-key rotation and rate-limit backoff code to bootstrap the AI provider router in Hour 1.
* [ ] **Linear:** Create free workspace `pocketsre-incidents` on `linear.app`. Set default team key to `YUK` (or `KIW` to match `#YUK-104`). Generate Personal API Key in settings. Note the Team ID.
* [ ] **GitHub:** Generate Personal Access Token (PAT) with `repo` scope. Note test repo target.
* [ ] **Sentry:** Create free Sentry project. Note webhook endpoint settings or export standard crash JSON fixture.
* [ ] **Audio/TTS:** Verify Python `edge-tts` works locally (`edge-tts --text "Hello Senpai" --write-media test.mp3`). If Sarvam AI provides credentials before Saturday, test endpoint via curl.

---

## 10. 12-Hour Hackathon Implementation Notes

* **Target Infrastructure & Control Topology:** Pre-seed Project Yuki’s existing OCI VM as the monitored target, and deploy PocketSRE in an isolated `container_name: pocketsre-core` container on an independent OCI Control-Plane VM on the same OCI network (connecting remotely via SSH or Tailscale).
* **Project Yuki Code Foundation (Strategic Velocity):** PocketSRE adapts proven core components from Project Yuki—specifically the multi-key AI provider router (`APIKeyPool`), exponential backoff handlers, and asynchronous health pollers. Reusing these rock-solid primitives saves 3+ hours of repetitive scaffolding, freeing up precious hackathon time to perfect the mobile magic-link UX, self-learning playbooks, and break-glass execution.
* **Deterministic Stubs:** Wrap Devin and Linear calls in deterministic fallback stubs to protect against houseboat cell drops.
* **Code Freeze at Hour 10:** The final 2 hours are reserved exclusively for desk-side demonstration rehearsal and verifying the air-gapped mock incident trigger script (`./scripts/inject_mock_incident.sh`).

---
*Document Version: 1.14.0 (PocketSRE Platform, Dual Avatars: Kiwi & Vikram, Pure Language & Adaptive Code-Mixing Architecture, Track 02 Lock)*  
*Target Event: HackaThoni 2026 (Alappuzha, Kerala) | Primary Track: Track 02 — VOICE & LANGUAGE ("Beyond English")*  
*Author: Ivin Titus & The Antigravity Swarm*
