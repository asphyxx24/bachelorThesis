# Implementierungsplan

Dieses Dokument beschreibt alle Schritte die noch umgesetzt werden müssen,
bevor die Hauptmesskampagne starten kann.

---

## Status-Legende
- [ ] Offen
- [~] In Arbeit
- [x] Erledigt

---

## 0. Voraussetzung: GitHub konsolidieren

- [x] `git remote -v` — `asphyxx24` ist primärer Remote
- [x] Lokaler Stand auf `asphyxx24` gepusht
- [x] `papagaiAI`-Account wird ignoriert

---

## 1. Repository-Struktur bereinigen

- [x] `measurements/layer1_infra/` → `measurements/layer1/`
- [x] `measurements/layer3_latency/` → `measurements/layer3/`
- [x] `measurements/layer2/` existiert (war `layer2_streaming/`)
- [x] `scripts/` entfernt
- [x] `data/archive/` erstellt
- [x] Alle Import-Pfade angepasst
- [x] `stt.py` → `stt_deepgram.py`, `tts.py` → `tts_deepgram.py`, `llm.py` → `llm_openai.py`
- [ ] Alte Daten in `data/archive/` verschieben (Phase 5)

---

## 2. sample.wav erstellen

- [x] `fixtures/` aufgelöst — Anleitung liegt in `measurements/layer3/SAMPLE_WAV.md`
- [x] ElevenLabs und `create_sample.py` entfernt
- [ ] **Anton:** Englische Sprachaufnahme machen (~5 Sekunden)
  - Text: *"Good morning. I would like to know the current weather forecast for Frankfurt."*
  - `ffmpeg -i recording.wav -ar 16000 -ac 1 measurements/layer3/sample.wav`
- [ ] Validierung: Deepgram-Testlauf → `transcript_len > 0`

---

## 3. .env.example bereinigen

- [x] ElevenLabs + Requesty Keys entfernt
- [x] Neue Provider-Keys dokumentiert:

```
DEEPGRAM_API_KEY=
ASSEMBLYAI_API_KEY=
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=germanywestcentral
OPENAI_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=
```

---

## 4. API-Keys beschaffen

| Provider | URL | Kosten | Status |
|----------|-----|--------|--------|
| Deepgram | account.deepgram.com | $0 ($200 Startguthaben) | [ ] |
| AssemblyAI | assemblyai.com | $0 ($50 Startguthaben) | [ ] |
| Groq | console.groq.com | $0 (Free Tier) | [ ] |
| Azure | portal.azure.com | ~$10,74 (STT + TTS) | [ ] |
| OpenAI | platform.openai.com | ~$10 aufladen | [ ] |
| Mistral | console.mistral.ai | ~$5 aufladen | [ ] |

**Gesamtkosten: ~$25**

---

## 5. Layer-3-Module schreiben

**Messdesign (festgelegt):**
- Cold-Start: Neue TCP+TLS-Verbindung pro Messung
- STT: Raw WebSocket für alle 3 Provider (kein SDK, auch nicht für Azure)
- Messwerte: `connect_ms`, `ttft_ms`/`ttfa_ms`, `total_ms`

**Feste Inputs:**
- STT Audio: `measurements/layer3/sample.wav`
- LLM Prompt: *"Reply in one short sentence: What is the capital of Germany?"*
- TTS Text: *"Good morning! How can I assist you today?"* (~38 Zeichen)

**Dateien** (alle in `measurements/layer3/`):

| Datei | Was | Protokoll | Status |
|-------|-----|-----------|--------|
| `stt_deepgram.py` | Deepgram Nova-3 | WebSocket (raw) | bereinigen |
| `stt_assemblyai.py` | AssemblyAI Universal-2 | WebSocket (raw) | neu |
| `stt_azure.py` | Azure STT (DE) | WebSocket (raw, kein SDK) | neu |
| `llm_openai.py` | OpenAI gpt-4o-mini | HTTPS+SSE | neu schreiben (alter Code war Requesty) |
| `llm_groq.py` | Groq llama-3.1-8b-instant | HTTPS+SSE | neu |
| `llm_mistral.py` | Mistral mistral-small-3.2 | HTTPS+SSE | neu |
| `tts_deepgram.py` | Deepgram TTS Aura-2 | HTTPS Streaming | neu schreiben (alter Code war ElevenLabs) |
| `tts_openai.py` | OpenAI TTS tts-1 | HTTPS Streaming | neu |
| `tts_azure.py` | Azure TTS Neural (DE) | HTTPS Streaming | neu |

- [ ] `run.py` aktualisieren: alle 9 Module einbinden

---

## 6. Layer-2-Capture-Skript schreiben

- [ ] `measurements/layer2/capture.py` erstellen
- [ ] Test: Einzelcapture mit Deepgram

---

## 7. AWS EC2 aufsetzen

- [ ] EC2 t3.small in eu-central-1 erstellen
- [ ] Security Group: SSH (Port 22) von eigenem IP
- [ ] Repo klonen von `github.com/asphyxx24/bachelorThesis`
- [ ] Python-Umgebung + Dependencies installieren
- [ ] `.env` anlegen und Keys eintragen
- [ ] SSH-Verbindung testen

---

## 8. Cron-Jobs konfigurieren

- [ ] Cron-Jobs auf EC2 einrichten (Details in `notes/migration_plan.md`)
- [ ] Testlauf: Manuell alle 3 Layer einmal starten
- [ ] Logs prüfen nach erstem automatischen Lauf

---

## 9. Kampagne starten (14 Tage)

**Startbedingungen — alle müssen erfüllt sein:**
- [ ] EC2 läuft, SSH-Zugang funktioniert
- [ ] `sample.wav` aufgenommen und validiert (`transcript_len > 0`)
- [ ] Alle 6 API-Keys in `.env` eingetragen
- [ ] Alle 9 Layer-3-Module implementiert und per `--dry-run` getestet
- [ ] Cron-Jobs aktiv

**Kampagne läuft automatisch** — täglich Git-Sync prüfen ob Daten ankommen.

---

## 10. Analyse-Notebooks (nach Kampagne)

| Notebook | Inhalt |
|----------|--------|
| `analysis/layer1_infrastructure.ipynb` | DNS-Varianz, Ping-RTT, TLS-Handshake, AS-Pfade |
| `analysis/layer3_all_providers.ipynb` | p50/p95/p99 aller 9 Provider |
| `analysis/layer3_daytime_trends.ipynb` | Latenz nach Tageszeit / Wochentag |
| `analysis/layer1_vs_layer3_correlation.ipynb` | Ping RTT × 3 ≈ connect_ms? (Kernbefund) |
| `analysis/layer3_e2e_pipeline.ipynb` | E2E-Chain: STT + LLM + TTS Gesamtlatenz |
| `analysis/layer2_protocol.ipynb` | 3-RTT-Overhead, Protokollvergleich aus PCAP |
