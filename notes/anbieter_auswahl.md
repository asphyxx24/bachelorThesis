# Anbieter-Auswahl fuer die Messungen

> Status: FINAL — entschieden am 2026-03-31

---

## Uebersicht

9 Anbieter, 3 pro Kategorie (STT, LLM, TTS).
Auswahlkriterien: Infrastruktur-Diversitaet, Protokoll-Diversitaet, wissenschaftliche Vergleichbarkeit.

**Schicht 1 (Infrastruktur):** Alle 9 Anbieter — kostet nichts (ping/traceroute/DNS).
**Schicht 3 (Latenz):** Alle 9 Anbieter, primaer n>=100, sekundaer n=30-50.
**E2E-Kette:** Produktionsnahe Kombination (Deepgram + OpenAI + ElevenLabs).

---

## STT — Speech-to-Text

| # | Anbieter | Protokoll | Endpoint | Region (Hypothese) | Begruendung |
|---|---|---|---|---|---|
| 1 | **Deepgram** | WebSocket | `api.deepgram.com` | US (Cogent AS174) | Produktions-STT, Anycast, bestaetigt US-hosted |
| 2 | **AssemblyAI** | WebSocket | `api.assemblyai.com` | US (vermutl.) | Gleicher Protokoll-Typ wie Deepgram, A/B-Vergleich |
| 3 | **Speechmatics** | WebSocket | `eu2.rt.speechmatics.com` | EU (UK) | EU-basiert, andere Routing-Pfade als US-Anbieter |

**Protokoll-Einheitlichkeit:** Alle 3 nutzen WebSocket — erlaubt isolierten Vergleich der Infrastruktur ohne Protokoll als Confounding Variable.

**Protokoll-Kontrast:** Kommt ueber die LLM- und TTS-Kategorie (SSE, HTTP Streaming, AWS SDK).

### TODO
- [x] Deepgram API-Key vorhanden
- [ ] AssemblyAI API-Key beschaffen (Free Tier: 100h/Monat)
- [ ] Speechmatics API-Key beschaffen (Free Tier pruefen)
- [ ] AssemblyAI Messcode schreiben (lib/stt_assemblyai.py)
- [ ] Speechmatics Messcode schreiben (lib/stt_speechmatics.py)

---

## LLM — Large Language Model

| # | Anbieter | Protokoll | Endpoint | Region (Hypothese) | Begruendung |
|---|---|---|---|---|---|
| 4 | **OpenAI** | HTTPS + SSE | `api.openai.com` | US/EU (Azure/Cloudflare) | De-facto-Standard, groesste Nutzerbasis |
| 5 | **Groq** | HTTPS + SSE | `api.groq.com` | US (eigene LPU-RZ) | LPU statt GPU — extrem niedrige TTFT, Hardware-Kontrast |
| 6 | **Anthropic** | HTTPS + SSE | `api.anthropic.com` | US (AWS/GCP) | Andere Infrastruktur als OpenAI, gleicher Protokoll-Typ |

**Warum nicht Requesty?** Requesty ist ein API-Router/Proxy (EC2 → Requesty AWS FRA → upstream LLM).
Methodisch problematisch: Man misst Proxy-Overhead + upstream-Latenz vermischt.
Stattdessen messen wir die LLM-Provider direkt — saubere Messung.

**Warum nicht Gemini direkt?** Koennte als optionale 4. Messung hinzugefuegt werden, um den
Requesty-Overhead zu quantifizieren (Requesty → Gemini vs. Gemini direkt). Entscheidung: Spaeter.

**Modell-Wahl fuer Vergleichbarkeit:**
- OpenAI: `gpt-4o-mini` (schnellstes Modell)
- Groq: `llama-3.1-8b-instant` (schnellstes verfuegbares)
- Anthropic: `claude-3-5-haiku-latest` (schnellstes Modell)

### TODO
- [ ] OpenAI API-Key vorhanden (aus papagei .env)
- [ ] Groq API-Key beschaffen (Free Tier: 30 req/min, 14.400 req/Tag)
- [ ] Anthropic API-Key beschaffen (Free Tier: $5 Credits)
- [ ] Messcode fuer OpenAI SSE schreiben (lib/llm_openai.py)
- [ ] Messcode fuer Groq SSE schreiben (lib/llm_groq.py)
- [ ] Messcode fuer Anthropic SSE schreiben (lib/llm_anthropic.py)

---

## TTS — Text-to-Speech

| # | Anbieter | Protokoll | Endpoint | Region (Hypothese) | Begruendung |
|---|---|---|---|---|---|
| 7 | **ElevenLabs** | HTTPS Streaming | `api.elevenlabs.io` | EU (Google Cloud FRA) | Produktions-TTS, bestaetigt 0.7ms RTT |
| 8 | **Cartesia** | WebSocket | `api.cartesia.ai` | US (vermutl.) | Anderes Protokoll (WS vs HTTP), niedrige Latenz |
| 9 | **Amazon Polly** | AWS SDK (HTTPS) | `polly.eu-central-1.amazonaws.com` | EU (AWS FRA) | Intra-Cloud-Baseline — gleicher Provider + Region wie EC2 |

**Warum Polly statt OpenAI TTS?**
Polly ist ein AWS-Dienst in eu-central-1 — der Mess-EC2 steht ebenfalls in AWS eu-central-1.
Das gibt eine **Intra-Cloud-Baseline**: Wie schnell ist eine API wenn Messpunkt und API
beim gleichen Provider in der gleichen Region sind?

| Vergleich | Netzwerk-Pfad | Erwartete RTT |
|---|---|---|
| EC2 → ElevenLabs | AWS → Google Cloud (Cross-Provider, selbe Stadt) | ~1ms |
| EC2 → Cartesia | AWS → ? (Cross-Provider) | ? |
| EC2 → Polly | AWS → AWS (Intra-Provider, ggf. selbe AZ) | <1ms |

Wenn Polly 1ms RTT und 80ms TTFA hat, ElevenLabs 1ms RTT und 260ms TTFA,
dann ist der Unterschied reines Processing — nicht Netzwerk.

### TODO
- [x] ElevenLabs API-Key vorhanden
- [ ] Cartesia API-Key beschaffen (Free Tier pruefen)
- [ ] AWS Polly: IAM-Berechtigung pruefen (polly:SynthesizeSpeech)
- [ ] Messcode fuer Cartesia WebSocket schreiben (lib/tts_cartesia.py)
- [ ] Messcode fuer Polly schreiben (lib/tts_polly.py)

---

## Finale Anbieter-Matrix

```
        STT                 LLM                 TTS
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │ 1. Deepgram  │   │ 4. OpenAI    │   │ 7. ElevenLabs│
  │    (US, WS)  │   │    (US, SSE) │   │    (EU, HTTP)│
  │              │   │              │   │              │
  │ 2. AssemblyAI│   │ 5. Groq      │   │ 8. Cartesia  │
  │    (US, WS)  │   │    (US, SSE) │   │    (?, WS)   │
  │              │   │              │   │              │
  │ 3. Speechmat.│   │ 6. Anthropic │   │ 9. Polly     │
  │    (EU, WS)  │   │    (US, SSE) │   │    (EU, AWS) │
  └──────────────┘   └──────────────┘   └──────────────┘
```

### Schicht-1-Endpoints (Infrastruktur-Messungen)

| # | Endpoint | Kategorie |
|---|---|---|
| 1 | `api.deepgram.com` | STT |
| 2 | `api.assemblyai.com` | STT |
| 3 | `eu2.rt.speechmatics.com` | STT |
| 4 | `api.openai.com` | LLM + (TTS) |
| 5 | `api.groq.com` | LLM |
| 6 | `api.anthropic.com` | LLM |
| 7 | `api.elevenlabs.io` | TTS |
| 8 | `api.cartesia.ai` | TTS |
| 9 | `polly.eu-central-1.amazonaws.com` | TTS |

---

## Protokoll-Matrix (Schicht 2)

| Protokoll | Anbieter | Richtung | Besonderheit |
|---|---|---|---|
| **WebSocket** | Deepgram, AssemblyAI, Speechmatics, Cartesia | Bidirektional | Frame-basiert, persistente Verbindung |
| **HTTPS + SSE** | OpenAI, Groq, Anthropic | Unidirektional | Chunk-basiert, text/event-stream |
| **HTTPS Streaming** | ElevenLabs | Unidirektional | Binary Audio Stream |
| **AWS SDK (HTTPS)** | Amazon Polly | Request-Response | SigV4-Auth, kein Streaming |

4 verschiedene Delivery-Patterns — gute Grundlage fuer die Protokollanalyse.

---

## Geschaetzte API-Kosten (14-Tage-Kampagne)

| Anbieter | Free Tier | Geschaetzte Nutzung | Kosten |
|---|---|---|---|
| Deepgram | Pay-as-you-go ($200 Credit) | ~8.400 Calls | ~$8 |
| AssemblyAI | 100h/Monat | ~2.000 Calls | $0 (Free Tier) |
| Speechmatics | ? (pruefen) | ~2.000 Calls | ? |
| OpenAI | Pay-as-you-go | ~8.400 Calls | ~$5 |
| Groq | 14.400 req/Tag gratis | ~8.400 Calls | $0 (Free Tier) |
| Anthropic | $5 Free Credits | ~2.000 Calls | $0 (Free Tier) |
| ElevenLabs | 10.000 Zeichen/Monat | ~8.400 Calls | ~$7 |
| Cartesia | ? (pruefen) | ~2.000 Calls | ? |
| Amazon Polly | 5 Mio Zeichen/Monat gratis (12 Mo) | ~8.400 Calls | $0 (Free Tier) |
| **Gesamt** | | | **~$20-25** |
