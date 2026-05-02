# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-02, 23:00 (Session: Keys, Kosten, Cleanup)

## Letzter Stand

Phase 0–5 abgeschlossen. Alle API-Keys eingetragen, Kostenanalyse fertig,
alte Daten archiviert, Layer-3-Code bereinigt, run.py für 9 Provider aktualisiert,
technischer Modulplan geschrieben. Code für die 8 neuen Provider-Module ist noch
NICHT geschrieben (nur stt_deepgram.py existiert als Referenzimplementation).

**Erledigte Phasen:**
- [x] Phase 0: GitHub — `asphyxx24` ist primärer Remote
- [x] Phase 1: Repo-Struktur — bereinigt, fixtures/ entfernt
- [x] Phase 2: sample.wav — aufgenommen, liegt in `measurements/layer3/sample.wav` (16kHz, Mono, 4.8s)
- [x] Phase 3: API-Keys — alle 6 Keys in `.env` eingetragen (Azure = Italy North, S0 Tier)
- [x] Phase 4: Kostenanalyse — dokumentiert in `notes/cost_analysis.md`
- [x] Phase 5: Alte Daten archiviert — 950 L1 + 228 L3 Dateien nach `data/archive/`
- [x] Phase 5b: Layer-3-Code bereinigt — falsche Module gelöscht, run.py aktualisiert

## Aktuelle Fokus-Aufgabe

**Phase 6: 8 Provider-Module implementieren** (stt_deepgram.py existiert bereits)

Technischer Plan liegt in `measurements/layer3/MODULE_PLAN.md` — dort steht für jedes
Modul Endpoint, Auth, Protokoll und Ablauf. Empfohlene Reihenfolge:
1. LLM-Module (einfachstes Pattern, alle OpenAI-kompatibel)
2. TTS-Module (HTTP Streaming)
3. STT-Module (WebSocket, am komplexesten: AssemblyAI Base64, Azure Binärprotokoll)
4. chain.py neu schreiben
5. Testläufe

## Provider-Matrix (FINAL)

| Kategorie | Provider 1 | Provider 2 | Provider 3 |
|-----------|-----------|-----------|-----------|
| STT | Deepgram Nova-3 (USA, WS) | AssemblyAI Universal-2 (USA, WS) | Azure STT (Italien/Italy North, WS) |
| LLM | OpenAI gpt-4o-mini (USA, SSE) | Groq llama-3.1-8b (USA/LPU, SSE) | Mistral Small 4 (EU/FR, SSE) |
| TTS | Deepgram Aura-2 (USA, HTTPS) | OpenAI tts-1 (USA, HTTPS) | Azure TTS (Italien/Italy North, HTTPS) |

## Entscheidungen dieser Session (2026-05-02 abends)

- **Azure Region:** Italy North statt Germany West Central (Student-Abo Policy-Einschränkung)
- **Azure Tarif:** S0 (Standard), weil F0 nur 5h STT/Monat erlaubt (wir brauchen 15.6h)
- **Mistral Modell:** Small 4 (`mistral-small-2603`) statt Small 3.2 (Deprecation umgehen)
- **Kosten:** ~$43-48 Gesamtkosten, davon $10 out-of-pocket (OpenAI Prepaid), Rest über Free Tiers und Startguthaben
- **OpenAI:** $10 Prepaid nötig (kein Free Tier), noch NICHT aufgeladen
- **Alte Kampagne:** läuft noch auf ops.papagei.ai — Anton stoppt am Montag auf Arbeit

## Was in Layer 3 aktuell liegt

```
measurements/layer3/
  stt_deepgram.py    ← existiert, bereinigt (language=en), Referenzimplementation
  run.py             ← aktualisiert für 9 Provider (dynamische Imports)
  sample.wav         ← Testdatei (16kHz, Mono, PCM, 4.8s)
  MODULE_PLAN.md     ← technischer Plan für alle 9 Module
  SAMPLE_WAV.md      ← Doku zur sample.wav
  __init__.py
```

Gelöscht (falscher Inhalt): `llm_openai.py` (war Requesty), `tts_deepgram.py` (war ElevenLabs), `chain.py` (alte Imports)

## Offene Schritte

1. **OpenAI Prepaid aufladen** ($10) — manuell durch Anton
2. **8 Provider-Module schreiben** — siehe MODULE_PLAN.md
3. **chain.py neu schreiben** — E2E-Pipeline mit allen Providern
4. **Alte Kampagne stoppen** (ops.papagei.ai) — Anton, Montag
5. **AWS EC2 aufsetzen** — eu-central-1, t3.small
6. **Cron-Jobs + Kampagne starten**

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Projektkontext, Forschungsfrage, Messdesign |
| `notes/implementation_plan.md` | Vollständige Checkliste mit Status |
| `notes/cost_analysis.md` | Detaillierte Kostenanalyse pro Provider |
| `notes/migration_plan.md` | Methodik, Provider-Begründung |
| `measurements/layer3/MODULE_PLAN.md` | Technischer Plan für 9 Module |
| `measurements/config.py` | Endpoints aller 9 Provider (Layer 1) |
| `.env.example` | Benötigte Umgebungsvariablen |
