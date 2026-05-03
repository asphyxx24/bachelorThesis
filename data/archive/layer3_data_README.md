# Layer 3 — Archivierte Latency Data (vor 2026-05-02)

> **ACHTUNG:** Diese Daten stammen aus der explorativen Phase mit anderen Providern
> (Requesty, ElevenLabs). Sie sind NICHT Teil der finalen Messkampagne.
> Die aktuelle Provider-Matrix steht in `CLAUDE.md`.

## Historische Provider in diesen Daten

| `api` | Kategorie | Status |
|-------|-----------|--------|
| `deepgram` | STT | historisch (gleicher Provider, andere Methodik) |
| `elevenlabs` | TTS | **VERALTET** — durch Deepgram/OpenAI/Azure TTS ersetzt |
| `requesty` | LLM | **VERALTET** — API-Proxy (Gemini), durch OpenAI/Groq/Mistral ersetzt |
| `chain` | E2E | **VERALTET** — alte Pipeline-Komposition |

## Aktuelle Provider (Stand 2026-05-03)

Siehe `CLAUDE.md` und `HANDOFF.md` fuer die aktuelle 9-Provider-Matrix:
STT: Deepgram, Rev.ai, Azure | LLM: OpenAI, Groq, Mistral | TTS: Deepgram, OpenAI, Azure
