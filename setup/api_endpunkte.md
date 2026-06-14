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
- **Query:** `?model=nova-3&language=en&encoding=linear16&sample_rate=16000&punctuate=true&interim_results=false`
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
- **Auth:** Header `Authorization: Bearer <API_KEY>`
- **Host:** `api.openai.com`

### Azure (Standard Neural, Italy North)
- **URL:** `https://italynorth.tts.speech.microsoft.com/cognitiveservices/v1`
- **Auth:** Header `Ocp-Apim-Subscription-Key: <API_KEY>`
- **Body:** SSML, Stimme `en-US-JennyNeural`
- **Host:** `italynorth.tts.speech.microsoft.com`

---

## Host-Übersicht & DNS-Auflösung (Stand 2026-06-14)

7 eindeutige Hosts (Deepgram und OpenAI je für STT/TTS bzw. LLM/TTS doppelt genutzt):

| Host | Aufgelöste IPs / CNAME (2026-06-14) | erste Einordnung* |
|------|-------------------------------------|-------------------|
| `api.deepgram.com` | CNAME `api.sv1.deepgram.com` → `208.184.56.200` | dedizierte Deepgram-IP |
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

## DNS-Resolver für Layer 1 (Multi-Resolver-Vergleich)

`8.8.8.8` (Google) · `1.1.1.1` (Cloudflare) · `9.9.9.9` (Quad9)

## Mess-Konstanten (aus altem Setup, überprüfbar)

- **Delay zwischen Einzelmessungen (Rate-Limit-Schutz):** 1,5 s
- **LLM `max_tokens`:** 50
- **Audio-Chunk-Größe (STT):** 4096 B
