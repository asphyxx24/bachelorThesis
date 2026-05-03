# Kostenanalyse — Messkampagne

> Stand: 2026-05-03. Basiert auf aktuellen Preisen der Provider-Webseiten.
> AssemblyAI durch Rev.ai ersetzt (Grund: methodische Konsistenz).

## Kampagnen-Parameter

- **Calls pro Provider:** 11.200 (100 Calls x 8 Slots/Tag x 14 Tage)
- **STT-Input:** ~5s Audio (16kHz, Mono, WAV) pro Call
- **LLM-Input:** "Reply in one short sentence: What is the capital of Germany?" (~15 Tokens)
- **TTS-Input:** "Good morning! How can I assist you today?" (~38 Zeichen)

---

## STT — Speech-to-Text

### Deepgram Nova-3 (WebSocket Streaming)

| | Wert |
|---|---|
| Preis | $0.0048–$0.0077/min (Streaming, Pay-As-You-Go) |
| Volumen | 11.200 x 5s = 933 min |
| **Kosten** | **$4.48–$7.19** |
| Deckung | $200 Startguthaben (kein Ablauf, keine Kreditkarte nötig) |
| Quelle | deepgram.com/pricing |

### Rev.ai English (WebSocket Streaming)

| | Wert |
|---|---|
| Preis | $0.003/min, Streaming (15s Minimum pro Session) |
| Volumen | 11.200 x 15s = 2.800 Minuten |
| **Kosten** | **~$8.40** |
| Deckung | $0.99 Free + $9.99 (3.000 Min Paket) = $10.98 |
| Hinweis | 15s Minimum pro Session; ersetzt AssemblyAI (Grund: Echtzeit-Pacing-Anforderung) |
| Quelle | rev.ai/pricing |

### Azure STT (WebSocket, Italy North)

| | Wert |
|---|---|
| Preis | $1.00/h Audio (S0 Standard) |
| Volumen | 11.200 x 5s = 15.6h |
| **Kosten** | **$15.60** |
| Deckung | Azure for Students ($100 Kredit) |
| Tarif | S0 (Standard) — F0 reicht nicht (5h/Monat Limit) |
| Quelle | azure.microsoft.com/pricing/details/cognitive-services/speech-services/ |

---

## LLM — Large Language Models

### OpenAI gpt-4o-mini

| | Wert |
|---|---|
| Preis | $0.15/1M Input-Tokens, $0.60/1M Output-Tokens |
| Volumen | ~168k Input + ~168k Output Tokens |
| **Kosten** | **$0.13** |
| Deckung | Prepaid-Guthaben (Minimum $5, empfohlen $10) |
| Quelle | openai.com/api/pricing |

### Groq llama-3.1-8b-instant

| | Wert |
|---|---|
| Preis | $0.05/1M Input, $0.08/1M Output (Paid) |
| Volumen | ~168k Input + ~168k Output Tokens |
| **Kosten** | **$0.02** (Free Tier ausreichend) |
| Deckung | Free Tier (14.400 Requests/Tag, keine Kreditkarte nötig) |
| Rate-Limit (Free) | 30 RPM, 14.400 RPD — kein Problem |
| Quelle | groq.com/pricing, console.groq.com/docs/rate-limits |

### Mistral Small 4 (mistral-small-2603)

| | Wert |
|---|---|
| Preis | $0.15/1M Input, $0.60/1M Output |
| Volumen | ~168k Input + ~134k Output Tokens |
| **Kosten** | **$0.06–$0.09** (Free Tier ausreichend) |
| Deckung | Free "Experiment" Tier (~1 Mrd. Tokens/Monat, keine Kreditkarte) |
| Rate-Limit (Free) | ~1 RPS — 100 Calls pro Slot dauern ~2 min, akzeptabel |
| Hinweis | Modell-ID: mistral-small-2603, gleicher Free Tier |
| Quelle | mistral.ai/pricing |

---

## TTS — Text-to-Speech

### Deepgram Aura-2 (HTTPS Streaming)

| | Wert |
|---|---|
| Preis | $0.030/1k Zeichen |
| Volumen | 11.200 x 38 Zeichen = 425.600 Zeichen |
| **Kosten** | **$12.77** |
| Deckung | $200 Startguthaben (geteilt mit Deepgram STT) |
| Quelle | deepgram.com/pricing |

### OpenAI tts-1 (HTTPS Streaming)

| | Wert |
|---|---|
| Preis | $15.00/1M Zeichen |
| Volumen | 425.600 Zeichen |
| **Kosten** | **$7.06** |
| Deckung | Prepaid-Guthaben (geteilt mit OpenAI LLM) |
| Quelle | openai.com/api/pricing |

### Azure TTS Neural (Italy North)

| | Wert |
|---|---|
| Preis | $15.00/1M Zeichen (S0) |
| Volumen | 425.600 Zeichen |
| **Kosten** | **$0.006** (praktisch kostenlos) |
| Deckung | Azure for Students (geteilt mit Azure STT) |
| Hinweis | F0 haette gereicht (500k Zeichen/Monat), aber Ressource ist bereits S0 |
| Quelle | azure.microsoft.com/pricing/details/cognitive-services/speech-services/ |

---

## Gesamtkosten

| Provider | STT | LLM | TTS | Gesamt |
|----------|-----|-----|-----|--------|
| Deepgram | $4.48–$7.19 | — | $12.77 | **$17.25–$19.96** |
| Rev.ai | ~$8.40 | — | — | **~$8.40** |
| Azure | $15.60 | — | $0.006 | **$15.61** |
| OpenAI | — | $0.13 | $7.06 | **$7.19** |
| Groq | — | $0.02 | — | **$0.02** |
| Mistral | — | $0.06 | — | **$0.06** |
| **Summe** | | | | **~$49–$53** |

---

## Out-of-Pocket (was Anton tatsaechlich zahlen muss)

| Aktion | Betrag |
|--------|--------|
| OpenAI Prepaid aufladen | **$10** |
| Rev.ai Prepaid (3000 Min) | **$9.99** |
| Alles andere | $0 (Startguthaben / Free Tier / Azure for Students) |
| **Total** | **~$20** |

---

## Deckungsquellen

| Quelle | Verfuegbar | Verbraucht | Rest |
|--------|-----------|------------|------|
| Deepgram Startguthaben | $200 | ~$18–20 | ~$180 |
| Rev.ai Free + Prepaid | $10.98 | ~$8.40 | ~$2.58 |
| Azure for Students | $100 | ~$15.61 | ~$84 |
| OpenAI Prepaid | $10 | ~$7.19 | ~$3 |
| Groq Free Tier | unbegrenzt* | $0.02 | — |
| Mistral Free Tier | unbegrenzt* | $0.06 | — |

*Rate-limitiert, aber Volumen fuer unsere Kampagne ausreichend.

---

## Risiken und Hinweise

1. **Azure STT braucht S0** — F0 (5h/Monat) reicht nicht fuer 15.6h Audio. Bereits umgestellt.
2. **OpenAI braucht Prepaid** — ohne Guthaben HTTP 429. Minimum $5, empfohlen $10.
3. **Rev.ai 15s-Minimum** — Jede Streaming-Session wird mit mindestens 15s abgerechnet (unser Audio ist ~5s).
4. **Azure TTS Rate-Limit** — S0 erlaubt 200 TPS (kein Problem). F0 waere 20/60s gewesen.
5. **Mistral Rate-Limit (Free)** — ~1 RPS, d.h. 100 Calls pro Slot brauchen ~2 Minuten.
6. **Groq Rate-Limit (Free)** — 30 RPM, d.h. 100 Calls pro Slot brauchen ~3-4 Minuten.
