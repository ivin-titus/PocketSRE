# HackaThoni: The Houseboat Hackathon

> **Date:** 21–22 Nov 2026  
> **Location:** Alappuzha, Kerala  
> **Website:** [hackathoni.in](https://hackathoni.in)

---

## Challenge Tracks

Three directions for an overnight solo build. Choose the one that fits your idea.

---

### 01. Place & People
*The Alappuzha Challenge*

Create a practical solution to a challenge affecting Alappuzha's people, livelihoods, or environment. Start with a real local need and show how your idea could help.

**Possible Directions:**
- Backwater waste and monitoring
- Flood information
- Local services and livelihoods

---

### 02. Voice & Language
*Beyond English*

Use Sarvam's language and speech tools to make technology more useful for people who prefer Indian languages or voice interaction. Focus on natural, accessible experiences.

**Possible Directions:**
- Malayalam voice interfaces
- Multilingual assistance
- Speech-led workflows

---

### 03. Physical-World Computing
*Beyond the Screen*

Build software that understands or responds to the physical world. Work with images, movement, location, or sensor inputs instead of relying only on text prompts.

**Possible Directions:**
- Visual assistance
- Location-aware experiences
- Gesture or sensor-based control

---

## Guidelines

- **Track Selection:** Choose one primary track. Cross-track ideas are welcome.
- **Scope & Demo:** Keep the scope focused and bring a working demo.
- **Reference:** [hackathoni.in](https://hackathoni.in)

---

## 🛑 Track 02: Vision vs. Final Reality (Solo Hackathon Audit)

### 1. Target Track Intent
PocketSRE was originally conceived for **Track 02: Voice & Language ("Beyond English")** as an overnight solo build. The vision was to build a speech-first on-call SRE companion that an engineer could interact with over Discord voice notes or a live Discord voice channel in pure Malayalam, pure Hindi, or code-mixed technical jargon (Manglish/Hinglish) while on a houseboat in Alappuzha without opening a laptop.

### 2. Time-Limit Reality & Truncated Scope
Due to the strict 12-hour hackathon time limits for a solo build, development **stopped** at the foundational Discord bot and signed mobile web console stage. 

**What did NOT get built (0% complete):**
- **No Voice Input/Output:** Neither Mode B (async `.ogg` voice notes) nor Mode C (live Discord voice channel) were implemented.
- **No Sarvam AI Integration:** Neither Sarvam Saaras STT (`saaras:v4`) nor Bulbul TTS (`bulbul:v3/v4-flash`) was integrated. The API keys in configuration remain unused placeholders.
- **No Conversational Text Exchange:** The system cannot hold back-and-forth text conversations. Even simple text queries (e.g., asking `@PocketSRE Yuki de services ellam okay aano ? I just need a simple reply`) fail to yield any conversational text reply.

### 3. What Actually Landed for Track 02
The Track 02 implementation was limited exclusively to a lightweight, static **multilingual presentation layer** (`src/app/persona/presentation.py`):
- Deterministic regex and keyword matching detects whether an incoming message contains Malayalam script, Devanagari script, Manglish keywords (`aanu`, `aano`, `aayi`, `nokk`, `cheyy`), or Hinglish keywords (`hai`, `kya`, `karo`, `theek`).
- When formatting Discord embeds (status snapshots or incident alert cards), it substitutes pre-written localized titles and intro lines for Kiwi or Vikram in English, Hindi, Malayalam, Hinglish, or Manglish.
- **This is not dynamic language generation:** The bot does not generate novel Malayalam or Hindi responses. It formats fixed embed strings.

### 4. Why Development Stopped Here (Solo Build Constraints)
As an overnight solo build, delivering both a bulletproof infrastructure safety engine and an Indic voice AI pipeline in 12 hours was not feasible. Priorities had to be triaged: making the core SRE primitives real—reliable SSH command execution against the real Yuki OCI VM, restricted sudoers enforcement, signed JWT magic-link web console, presence polling, and budget limits—consumed the available build time. Attempting an unstable audio pipeline at the final hour would have resulted in fragile demo failures. Development stopped here, leaving PocketSRE as a Discord-bot + Web-Console incident response foundation with static multilingual template rendering.

