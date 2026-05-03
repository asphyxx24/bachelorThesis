# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-03, 11:30 (Session: Alle 9 Module implementiert)

## Letzter Stand

Phase 6 abgeschlossen: Alle 9 Provider-Module sind implementiert und getestet.
AssemblyAI wurde durch Rev.ai ersetzt (Grund: methodische Konsistenz).
OpenAI $10 Prepaid aufgeladen, alle Keys funktionsfähig.

**Erledigte Phasen:**
- [x] Phase 0: GitHub — `asphyxx24` ist primärer Remote
- [x] Phase 1: Repo-Struktur — bereinigt, fixtures/ entfernt
- [x] Phase 2: sample.wav — aufgenommen, liegt in `measurements/layer3/sample.wav` (16kHz, Mono, 4.8s)
- [x] Phase 3: API-Keys — alle 6 Keys in `.env` eingetragen (Azure = Italy North, S0 Tier)
- [x] Phase 4: Kostenanalyse — dokumentiert in `notes/cost_analysis.md`
- [x] Phase 5: Alte Daten archiviert — 950 L1 + 228 L3 Dateien nach `data/archive/`
- [x] Phase 5b: Layer-3-Code bereinigt — falsche Module gelöscht, run.py aktualisiert
- [x] Phase 6: Alle 9 Provider-Module implementiert und per Dry-Run verifiziert

## Aktuelle Fokus-Aufgabe

**Phase 6: AWS EC2 aufsetzen** (eu-central-1, t3.small)

## Provider-Matrix (FINAL, Stand 2026-05-03)

| Kategorie | Provider 1 | Provider 2 | Provider 3 |
|-----------|-----------|-----------|-----------|
| STT | Deepgram Nova-3 (USA, WS) | Rev.ai English (USA, WS) | Azure STT (Italien/Italy North, WS) |
| LLM | OpenAI gpt-4o-mini (USA, SSE) | Groq llama-3.1-8b (USA/LPU, SSE) | Mistral Small 4 (EU/FR, SSE) |
| TTS | Deepgram Aura-2 (USA, HTTPS) | OpenAI tts-1 (USA, HTTPS) | Azure TTS (Italien/Italy North, HTTPS) |

## Entscheidungen dieser Session (2026-05-03)

- **AssemblyAI → Rev.ai:** AssemblyAIs Streaming-API erfordert Echtzeit-Pacing (Audio muss so langsam
  gesendet werden wie es aufgenommen wurde). Das machte die TTFT-Messung inkonsistent mit Deepgram
  und Azure, die Audio-Dump akzeptieren. Rev.ai akzeptiert ebenfalls Audio-Dump → konsistente Methodik.
- **OpenAI Prepaid:** $10 aufgeladen, LLM und TTS Module funktionieren
- **Deepgram TTS Modell:** `aura-2-asteria-en` (nicht `aura-2-en` — Modellname braucht Voice-Suffix)
- **SSL-Fix:** `_measure_connect()` fängt SSLError beim Close ab (Deepgram sendet Daten nach Close-Notify)
- **Rev.ai Free Tier:** $1 Startguthaben (reicht für Entwicklung/Tests)

## Erste Messergebnisse (Dry-Run, n=3, lokal Windows, nicht AWS)

**STT (WebSocket, Audio-Dump):**
| Provider | connect_ms | TTFT p50 | Region |
|----------|-----------|----------|--------|
| Deepgram | ~810ms | 752ms | USA (Anycast) |
| Rev.ai | ~858ms | 1687ms | USA |
| Azure | ~290ms | 1758ms | Italien |

**LLM (HTTPS+SSE):**
| Provider | connect_ms | TTFT p50 | TTL p50 |
|----------|-----------|----------|---------|
| Groq | ~60ms | 137ms | 143ms |
| Mistral | ~46ms | 276ms | 307ms |
| OpenAI | ~62ms | 827ms | 940ms |

**TTS (HTTPS Streaming):**
| Provider | connect_ms | TTFA p50 | total_ms |
|----------|-----------|----------|----------|
| Azure | ~99ms | 196ms | 820ms |
| OpenAI | ~42ms | 1105ms | 2048ms |
| Deepgram | ~271ms | 1455ms | 2333ms |

## Was in Layer 3 aktuell liegt

```
measurements/layer3/
  stt_deepgram.py    ← STT Deepgram Nova-3 (WebSocket)
  stt_revai.py       ← STT Rev.ai (WebSocket) — NEU, ersetzt AssemblyAI
  stt_azure.py       ← STT Azure Italy North (WebSocket, Binärprotokoll)
  llm_openai.py      ← LLM OpenAI gpt-4o-mini (HTTPS+SSE)
  llm_groq.py        ← LLM Groq Llama-3.1-8b (HTTPS+SSE)
  llm_mistral.py     ← LLM Mistral Small 4 (HTTPS+SSE)
  tts_deepgram.py    ← TTS Deepgram Aura-2 (HTTPS Streaming)
  tts_openai.py      ← TTS OpenAI tts-1 (HTTPS Streaming)
  tts_azure.py       ← TTS Azure Neural Voice (HTTPS Streaming, SSML)
  run.py             ← Batch-Runner für alle 9 Provider
  sample.wav         ← Testdatei (16kHz, Mono, PCM, 4.8s)
  MODULE_PLAN.md     ← Technischer Plan (alle 9 Module, aktualisiert)
  SAMPLE_WAV.md      ← Doku zur sample.wav
  __init__.py
```

Gelöscht: `stt_assemblyai.py` (durch `stt_revai.py` ersetzt)

## Offene Schritte

1. **Alte Kampagne stoppen** (ops.papagei.ai) — Anton, Montag
2. **AWS EC2 aufsetzen** — eu-central-1, t3.small
3. **Cron-Jobs + Kampagne starten** (14 Tage)
4. **Layer-2 Captures** (manuell auf EC2, waehrend Kampagne)
5. **E2E-Validierung** (nach Analyse, ein paar manuelle Pipeline-Runs)

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Projektkontext, Forschungsfrage, Messdesign |
| `HANDOFF.md` | Dieser Arbeitsstand |
| `notes/implementation_plan.md` | Vollständige Checkliste mit Status |
| `notes/cost_analysis.md` | Detaillierte Kostenanalyse pro Provider |
| `measurements/layer3/MODULE_PLAN.md` | Technischer Plan für 9 Module |
| `measurements/config.py` | Endpoints aller 9 Provider (Layer 1) |
| `.env.example` | Benötigte Umgebungsvariablen |
