# Anbieter-Auswahl fuer die Messungen

> Status: ENTWURF — Entscheidung ausstehend

---

## Uebersicht

Fuer jede API-Kategorie (STT, LLM, TTS) werden mehrere Anbieter gemessen.
Ziel: Diversitaet in Infrastruktur, Protokollen und geografischem Deployment.

**Schicht 1 (Infrastruktur):** Alle Anbieter — kostet nichts (ping/traceroute/DNS).
**Schicht 3 (Latenz):** Primaere Anbieter n>=100, sekundaere n=30-50.
**E2E-Kette:** Nur die produktionsnahe Kombination (Deepgram + LLM + ElevenLabs).

---

## STT — Speech-to-Text

| Anbieter | Protokoll | Endpoint | Prioritaet | Begruendung |
|---|---|---|---|---|
| **Deepgram** | WebSocket | `api.deepgram.com` | Primaer | Produktions-STT, US-hosted, Anycast |
| **AssemblyAI** | WebSocket | `api.assemblyai.com` | Sekundaer | Gleicher Protokoll-Typ, Vergleichbarkeit |
| **OpenAI Whisper** | HTTPS (Batch) | `api.openai.com` | Sekundaer | Kein Streaming — interessanter Gegenpol |
| **Speechmatics** | WebSocket | `eu2.rt.speechmatics.com` | Optional | EU-basiert, andere Routing-Pfade |

### TODO
- [ ] AssemblyAI API-Key beschaffen (Free Tier verfuegbar?)
- [ ] Pruefen ob Speechmatics Free Tier hat
- [ ] Whisper-Endpoint testen (ist das `/v1/audio/transcriptions`?)

---

## LLM — Large Language Model

| Anbieter | Protokoll | Endpoint | Prioritaet | Begruendung |
|---|---|---|---|---|
| **OpenAI** | HTTPS + SSE | `api.openai.com` | Primaer | De-facto-Standard, Azure/Cloudflare-Infra |
| **Anthropic** | HTTPS + SSE | `api.anthropic.com` | Primaer | Gleicher Protokoll-Typ, andere Infrastruktur |
| **Groq** | HTTPS + SSE | `api.groq.com` | Primaer | LPU statt GPU — extrem niedrige TTFT |
| **Google Gemini** | HTTPS + SSE | `generativelanguage.googleapis.com` | Sekundaer | Google-eigenes Netz, direkt ohne Router |
| ~~Requesty~~ | HTTPS + SSE | `router.requesty.ai` | ~~Primaer~~ | Proxy/Router — methodisch problematisch |

### Requesty-Problem
Requesty ist ein **API-Router**, kein LLM-Provider. Traffic: EC2 → Requesty (AWS FRA) → Google Gemini.
Zwei Optionen:
1. Requesty rausnehmen, Gemini direkt messen
2. Requesty als "Proxy-Overhead-Case-Study" behalten UND Gemini direkt messen

**Entscheidung:** TODO

### TODO
- [ ] Groq API-Key beschaffen (Free Tier: 30 req/min)
- [ ] Anthropic API-Key (Free Tier verfuegbar?)
- [ ] Gemini API direkt testen (Google AI Studio Key)
- [ ] Entscheidung: Requesty behalten oder ersetzen?

---

## TTS — Text-to-Speech

| Anbieter | Protokoll | Endpoint | Prioritaet | Begruendung |
|---|---|---|---|---|
| **ElevenLabs** | HTTPS Streaming | `api.elevenlabs.io` | Primaer | Produktions-TTS, Google Cloud EU |
| **Cartesia** | WebSocket | `api.cartesia.ai` | Primaer | Anderes Protokoll (WS vs HTTP), niedrige Latenz |
| **OpenAI TTS** | HTTPS (Chunk) | `api.openai.com` | Sekundaer | Kein echtes Streaming, Vergleich |
| **Deepgram Aura** | HTTPS | `api.deepgram.com` | Sekundaer | Gleicher Host wie STT — Infrastrukturvergleich |

### TODO
- [ ] Cartesia API-Key beschaffen (Free Tier?)
- [ ] OpenAI TTS Endpoint testen (`/v1/audio/speech`)
- [ ] Deepgram Aura Messcode schreiben

---

## Zusammenfassung der Entscheidungen

| # | Entscheidung | Status | Notizen |
|---|---|---|---|
| 1 | Requesty ersetzen oder behalten? | OFFEN | Methodisch problematisch als Proxy |
| 2 | Groq aufnehmen? | OFFEN | LPU-Infrastruktur = spannender Ausreisser |
| 3 | Cartesia aufnehmen? | OFFEN | WebSocket-TTS = Protokoll-Diversitaet |
| 4 | Wie viele Anbieter gesamt? | OFFEN | Ziel: 3-4 pro Kategorie, 10-12 gesamt |
| 5 | API-Key-Budget? | OFFEN | Free Tiers pruefen |

---

## Schicht-uebergreifende Perspektive

### Protokoll-Matrix (Schicht 2)

| Protokoll | STT | LLM | TTS |
|---|---|---|---|
| **WebSocket** | Deepgram, AssemblyAI | — | Cartesia |
| **HTTPS + SSE** | — | OpenAI, Anthropic, Groq, Gemini | — |
| **HTTPS Streaming** | — | — | ElevenLabs, OpenAI TTS |
| **HTTPS Batch** | OpenAI Whisper | — | Deepgram Aura |

→ Gute Diversitaet: WebSocket bidirektional, SSE unidirektional, HTTP Streaming, HTTP Batch.

### Infrastruktur-Matrix (Schicht 1)

| Anbieter | Erwartete Infra | Region (Hypothese) |
|---|---|---|
| Deepgram | Eigene Server / Cogent | US |
| ElevenLabs | Google Cloud | EU (Frankfurt?) |
| OpenAI | Azure / Cloudflare | US oder EU |
| Anthropic | AWS / GCP | US |
| Groq | Eigene LPU-Rechenzentren | US |
| Cartesia | ? | ? |
| Gemini direkt | Google-Netz | EU oder US |

→ Traceroute + ASN-Analyse wird zeigen ob diese Hypothesen stimmen.
