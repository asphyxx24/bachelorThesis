# API-Endpunkte & Hostnames (verifiziert)

> Angelegt: 2026-06-14 · Teil des Neuaufbaus (s. `../NEUANFANG.md`, `anbieter_auswahl.md`)
>
> **Quelle der Genauigkeit:** Pfade, Query-Parameter und Auth-Methoden sind aus den real
> funktionierenden (archivierten) Mess-Skripten extrahiert (`archived/measurements/layer3/*.py`,
> `archived/measurements/config.py`) — also aus Code, der nachweislich erfolgreich verbunden hat,
> nicht aus dem Gedächtnis. Die Hostnames wurden am **2026-06-14** zusätzlich live per DNS aufgelöst.
>
> ⚠️ **Vor der neuen Kampagne erneut gegen die offiziellen Provider-Docs prüfen** — Modell-Versionen
> und Default-Endpunkte können sich ändern. Diese Datei ist der Startpunkt, nicht das letzte Wort.

---

## STT (Speech-to-Text) — WebSocket

### Deepgram (Nova-3)
- **WS-URL:** `wss://api.deepgram.com/v1/listen`
- **Query:** `?model=nova-3&language=en&encoding=linear16&sample_rate=16000&punctuate=true&interim_results=true`
- **`interim_results=true`** liefert Live-Wörter (Interim-`Results`) für die STT-Primärmetrik **`ttfp`**
  (Time-to-first-Partial, endpointing-frei — s. `messprotokoll.md` → „STT-Primärmetrik: ttfp").
- **Auth:** Header `Authorization: Token <API_KEY>`
- **Audio:** rohe PCM-Frames (linear16, 16 kHz), Chunk-Größe 4096 B
- **Host:** `api.deepgram.com`

### Rev.ai (English)
- **WS-URL:** `wss://api.rev.ai/speechtotext/v1/stream`
- **Query:** `?content_type=audio/x-raw;layout=interleaved;rate=16000;format=S16LE;channels=1`
- **Auth:** Query-Parameter `&access_token=<API_KEY>`
- **Audio:** PCM S16LE, 16 kHz, mono, Chunk 4096 B
- **Host:** `api.rev.ai`

### Azure (Standard Neural, Italy North)
- **WS-URL:** `wss://italynorth.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1`
- **Auth:** Header `Ocp-Apim-Subscription-Key: <API_KEY>`
- **Protokoll-Detail:** Microsoft-Speech-Framing — Nachrichten mit `Path: speech.config` (Konfig)
  und `Path: audio` (Audio, `Content-Type: audio/x-wav`)
- **Host:** `italynorth.stt.speech.microsoft.com`

---

## LLM (Large Language Model) — HTTPS + SSE (Server-Sent Events, gestreamt)

Alle drei sprechen das **OpenAI-kompatible** `/chat/completions`-Schema, `stream: true`, `max_tokens: 50`.

### OpenAI (gpt-4o-mini)
- **URL:** `https://api.openai.com/v1/chat/completions`
- **Modell (gepinnt):** `gpt-4o-mini-2024-07-18` (datierter Snapshot statt rollendem Alias `gpt-4o-mini`, s. Modell-Pinning A2)
- **Auth:** Header `Authorization: Bearer <API_KEY>`
- **Host:** `api.openai.com`

### Groq (llama-3.1-8b-instant)
- **URL:** `https://api.groq.com/openai/v1/chat/completions`  ← beachte den `/openai`-Präfix
- **Auth:** Header `Authorization: Bearer <API_KEY>`
- **Host:** `api.groq.com`

### Mistral (mistral-small-2603)
- **URL:** `https://api.mistral.ai/v1/chat/completions`
- **Auth:** Header `Authorization: Bearer <API_KEY>`
- **Host:** `api.mistral.ai`

---

## TTS (Text-to-Speech) — HTTPS Streaming

### Deepgram (Aura-2)
- **URL:** `https://api.deepgram.com/v1/speak?model=aura-2-asteria-en&encoding=mp3`
- **Auth:** Header `Authorization: Token <API_KEY>`
- **Host:** `api.deepgram.com`

### OpenAI (tts-1)
- **URL:** `https://api.openai.com/v1/audio/speech`
- **Body (gepinnt, A8):** `{"model":"tts-1","input":"<fester Text>","voice":"alloy","response_format":"mp3"}`
  — `response_format` **explizit `mp3`** (gleicher **Container** wie Deepgram/Azure). **ABER nur der Container
  ist gepinnt, nicht die Bitrate** (Azure 48 kbit/s, Deepgram/OpenAI Provider-Default → `audio_bytes` ~3,6×
  verschieden). Daher: **`ttfa` ist fair** (erstes Audio-Byte, mengen-unabhängig), `total_ms`/`audio_bytes`
  cross-provider **nicht**; `audio_bytes` nur Erfolgs-Gate. Bitrate ist nicht bei allen Anbietern angleichbar.
- **Auth:** Header `Authorization: Bearer <API_KEY>`
- **Host:** `api.openai.com`

### Azure (Standard Neural, Italy North)
- **URL:** `https://italynorth.tts.speech.microsoft.com/cognitiveservices/v1`
- **Auth:** Header `Ocp-Apim-Subscription-Key: <API_KEY>`
- **Body:** SSML, Stimme `en-US-JennyNeural`
- **Host:** `italynorth.tts.speech.microsoft.com`

---

## Modell-Pinning & Abrufdatum (A2)

> **Reproduzierbarkeit:** Modell-IDs sind teils rollende Aliase — still aktualisierte Backends würden
> den Headline-Befund unbemerkt nicht-reproduzierbar machen. Entscheidung (2026-06-15): **datierte
> Snapshots verwenden, wo verfügbar**; alle übrigen bleiben notgedrungen rollend und werden als
> **Limitation** benannt. **Zusätzlich loggt jeder LLM-Run das vom Server zurückgemeldete
> `effective_model`** (aus `chunk.model` im SSE) → Drift wird *erkennbar*, nicht nur befürchtet.

| Kategorie | Anbieter | Angefragte Modell-ID | Typ | datierter Snapshot? |
|-----------|----------|----------------------|-----|---------------------|
| STT | Deepgram | `nova-3` | **rollend** | nein verfügbar → Limitation |
| STT | Rev.ai | `english` (Stream-Profil) | **rollend** | nein verfügbar → Limitation |
| STT | Azure | Standard Neural (Endpoint-gebunden, keine Modell-ID im Request) | **rollend** | nein → Limitation |
| LLM | OpenAI | `gpt-4o-mini-2024-07-18` | **gepinnt** ✓ | ja |
| LLM | Groq | `llama-3.1-8b-instant` | **rollend** | nein verfügbar → Limitation |
| LLM | Mistral | `mistral-small-2603` | **gepinnt** ✓ | ja (Datum im Alias) |
| TTS | Deepgram | `aura-2-asteria-en` | **rollend** | nein verfügbar → Limitation |
| TTS | OpenAI | `tts-1` | **rollend** | nein verfügbar → Limitation |
| TTS | Azure | Voice `en-US-JennyNeural` | **rollend** (serverseitig versioniert) | nein → Limitation |

- **Abrufdatum der IDs:** 2026-06-15 (gegen Provider-Docs zu verifizieren vor Kampagnenstart).
- **Logging-Pflicht (in die L3-Skripte, A2 + A5):** angefragte ID **und** — wo verfügbar —
  zurückgemeldete ID/Version pro Run roh ins JSONL (LLM: `chunk.model`; STT/TTS: opportunistisch
  Response-Header). So ist je Sample belegbar, welche Modell-Version tatsächlich bedient hat.

## Host-Übersicht & DNS-Auflösung (Stand 2026-06-14)

7 eindeutige Hosts (Deepgram und OpenAI je für STT/TTS bzw. LLM/TTS doppelt genutzt):

| Host | Aufgelöste IPs / CNAME (2026-06-14) | erste Einordnung* |
|------|-------------------------------------|-------------------|
| `api.deepgram.com` | CNAME `api.sv1.deepgram.com` → `208.184.56.200` | Multi-DC, kurz-TTL-Round-Robin (`md1`/`sac1`/`sv1`); IP = AS6461 (Zayo)-Transit, **nicht** dediziert |
| `api.rev.ai` | `52.36.23.89`, `52.32.160.52`, `32.186.17.136` | AWS-Range (US-West/Oregon) |
| `italynorth.stt.speech.microsoft.com` | → `*.italynorth.cloudapp.azure.com` → `4.232.100.212` | Azure Italy North |
| `api.openai.com` | `172.66.0.243`, `162.159.140.245` | Cloudflare-Range |
| `api.groq.com` | `172.64.149.20`, `104.18.38.236` | Cloudflare-Range |
| `api.mistral.ai` | `172.66.2.203`, `162.159.142.207` | Cloudflare-Range |
| `italynorth.tts.speech.microsoft.com` | → `*.italynorth.cloudapp.azure.com` → `4.232.100.220` | Azure Italy North |

> *Die „erste Einordnung" ist nur eine grobe IP-Range-Beobachtung, **noch keine Layer-1-Analyse**.
> Dass OpenAI/Groq/Mistral in Cloudflare-Ranges auflösen, ist genau die Stelle, an der die spätere
> Layer-1-/Edge-Auflösung ansetzen wird (Anycast/Edge vs. tatsächlicher Backend-Standort). Bewusst
> hier nur als Rohbeobachtung festgehalten, nicht gedeutet.

> **TLS-Fußnote (rev.ai):** `api.rev.ai` ist der **einzige** der 7 Hosts, der nur **TLS 1.2** aushandelt
> (die übrigen 6 sprechen TLS 1.3) — ein echter Server-Befund, kein Mess-Artefakt. ⚠️ **Nicht** über
> macOS-Python belegen: dessen LibreSSL-Bindung cappt auf TLS 1.2 und meldet *alle* Hosts fälschlich als
> 1.2 (s. A1). Die TLS-Version wird ausschließlich auf der EC2 (echtes OpenSSL) bzw. via
> `openssl s_client` verifiziert.

## Terminierung (Edge/Host) — Klassifikation (A3)

> **Single Source of Truth** für den zentralen Erklärschritt (Prof-Einwand „3 Anbieter mit ~1 ms RTT").
> Klassifikator-Definition + Begründung: `messprotokoll.md` (§Layer 1 — Endpunkt-Terminierung).
> **Edge-terminiert** gdw. **(a) TCP-RTT ≈ 1–2 ms aus FRA ∧ (b) IP in CDN-ASN ∧ (c) traceroute bricht
> am CDN ab** — sonst **Host**. ⚠️ Werte unten sind aus DNS/ASN **vorläufig**; RTT + traceroute werden
> auf der EC2 bestätigt.

| Endpunkt (Host) | ASN / Org (vorläufig) | TCP-RTT FRA (vorläufig) | **Terminierung** | Begründung |
|-----------------|-----------------------|-------------------------|------------------|------------|
| `api.deepgram.com` | AS6461 Zayo / AS174 Cogent (Multi-DC) | ~102–148 ms | **Host** | hohe RTT (a✗), kein CDN-AS (b✗) — trotz „Anycast"-Label |
| `api.rev.ai` | AS16509 Amazon (US-Oregon) | US, hoch (zu messen) | **Host** | AWS-Backend, kein CDN-AS |
| `italynorth.stt.speech.microsoft.com` | AS8075 Microsoft (Italy North) | ~12 ms | **Host** | echtes EU-RZ, **kein** CDN-AS (b✗) — niedrige RTT ist real |
| `italynorth.tts.speech.microsoft.com` | AS8075 Microsoft (Italy North) | ~12 ms | **Host** | echtes EU-RZ, **kein** CDN-AS (b✗) — niedrige RTT ist real |
| `api.openai.com` | AS13335 Cloudflare | ~1–2 ms (zu bestätigen) | **Edge** | CDN-AS (b✓) + ~1 ms (a✓); Backend hinter Edge unbekannt |
| `api.groq.com` | AS13335 Cloudflare | ~1–2 ms (zu bestätigen) | **Edge** | CDN-AS (b✓) + ~1 ms (a✓); Backend hinter Edge unbekannt |
| `api.mistral.ai` | AS13335 Cloudflare | ~1–2 ms (zu bestätigen) | **Edge** | CDN-AS (b✓) + ~1 ms (a✓); **EU-Backend RTT-maskiert** (Limitation) |

> **Lesart:** Niedrige RTT bedeutet **nicht** automatisch „Edge" — Azure (Italy North) hat ~12 ms und ist
> **Host** (echtes EU-RZ, kein CDN-AS). Genau diese Trennung trägt die STT/TTS-Inversion: Azures Vorsprung
> ist realer Backend-Standort, kein Edge-Artefakt. Umgekehrt ist Deepgram trotz „Anycast"-Label **Host**
> (RTT zu hoch). Bei den drei Cloudflare-Edge-Anbietern misst die RTT den FRA-Edge, **nicht** das Backend
> → Backend-Region via RTT nicht bestimmbar (betrifft v.a. Mistral als EU-LLM; s. Limitations).

## DNS-Resolver für Layer 1 (Multi-Resolver-Vergleich)

`8.8.8.8` (Google) · `1.1.1.1` (Cloudflare) · `9.9.9.9` (Quad9)

## Mess-Konstanten (aus altem Setup, überprüfbar)

- **Delay zwischen Einzelmessungen (Rate-Limit-Schutz):** 1,5 s
- **LLM `max_tokens`:** 50
- **Audio-Chunk-Größe (STT):** 4096 B
