# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-02 (Session: AWS-Migration & Neustart)

## Letzter Stand

Phase 0–2 abgeschlossen. Repo umstrukturiert, ElevenLabs/Requesty komplett entfernt,
neue Provider-Matrix finalisiert. Code für die 9 Provider-Module ist noch NICHT geschrieben.

**Erledigte Phasen:**
- [x] Phase 0: GitHub — `asphyxx24` ist primärer Remote, alles gepusht
- [x] Phase 1: Repo-Struktur — Ordner umbenannt, `scripts/` entfernt, `data/archive/` angelegt
- [x] Phase 2: Fixture — ElevenLabs raus, Anleitung für manuelle WAV-Aufnahme unter `measurements/layer3/SAMPLE_WAV.md`

## Aktuelle Fokus-Aufgabe

**Phase 3: API-Keys beschaffen** (manuell durch Anton)
Dann Phase 4: 9 Provider-Module implementieren, dann Phase 5: alte Daten archivieren.

Vor Phase 4 muss Anton:
1. `sample.wav` aufnehmen (Anleitung in `measurements/layer3/SAMPLE_WAV.md`)
2. API-Keys registrieren (Liste in `notes/implementation_plan.md`, Abschnitt 4)

## Letzte Entscheidungen (2026-05-02)

**Provider-Matrix (FINAL):**

| Kategorie | Provider 1 | Provider 2 | Provider 3 |
|-----------|-----------|-----------|-----------|
| STT | Deepgram Nova-3 (USA, WS) | AssemblyAI Universal-2 (USA, WS) | Azure STT (DE, WS) |
| LLM | OpenAI gpt-4o-mini (USA, SSE) | Groq llama-3.1-8b (USA/LPU, SSE) | Mistral small-3.2 (EU/FR, SSE) |
| TTS | Deepgram Aura-2 (USA, HTTPS) | OpenAI tts-1 (USA, HTTPS) | Azure TTS (DE, HTTPS) |

**Entscheidungen:**
- ElevenLabs raus (kein Key, zu teuer)
- Cartesia raus (Free Tier zu klein, $39/Monat)
- Anthropic raus → Mistral rein (EU-Hosting, geographischer Kontrast)
- Speechmatics raus → Azure rein (Germany West Central Endpoint, deckt STT+TTS)
- Amazon Polly: nur als optionaler Exkurs, nicht Hauptprovider
- Alle STT-Provider: Raw WebSocket, kein SDK (auch Azure)
- sample.wav: manuelle Aufnahme statt TTS-generiert
- Cold-Start-Methodik bestätigt und begründet

**Messdesign:**
- Feste Inputs pro Kategorie (gleich für alle Provider)
- STT Audio: "Good morning. I would like to know the current weather forecast for Frankfurt."
- LLM Prompt: "Reply in one short sentence: What is the capital of Germany?"
- TTS Text: "Good morning! How can I assist you today?"
- n=100 pro Zeitschlitz, 8 Slots/Tag, 14 Tage Kampagne

## Offene Fragen / Blockaden

- API-Keys noch nicht registriert (6 Konten nötig)
- sample.wav noch nicht aufgenommen
- AWS EC2 noch nicht aufgesetzt (Anton hat AWS CLI konfiguriert für eigenen Account)
- Alte Messkampagne auf ops.papagei.ai läuft noch (Layer 1 + Layer 3 Daten kommen rein) — muss irgendwann gestoppt werden
- Phase 5 (alte Daten archivieren) noch nicht gemacht

## Relevante Dateien

- `notes/implementation_plan.md` — Vollständige Checkliste aller offenen Schritte
- `notes/migration_plan.md` — Methodik, Provider-Matrix, Kosten, Zeitplan (Detail-Referenz)
- `notes/layer2_first_capture.md` — POC Layer-2-Capture Deepgram (weiterhin relevant)
- `measurements/layer3/SAMPLE_WAV.md` — Anleitung für die WAV-Aufnahme
