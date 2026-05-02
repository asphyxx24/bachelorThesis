# Implementierungsplan

Dieses Dokument beschreibt alle Schritte die noch umgesetzt werden müssen,
bevor die Hauptmesskampagne starten kann. Der detaillierte Plan liegt unter
`.claude/plans/schau-dir-den-gesamten-robust-taco.md`.

---

## Status-Legende
- [ ] Offen
- [~] In Arbeit
- [x] Erledigt

---

## 0. Voraussetzung: GitHub konsolidieren

- [ ] `git remote -v` ausführen — prüfen welche Remotes konfiguriert sind
- [ ] Lokalen Stand auf `asphyxx24` pushen (primärer Account)
- [ ] `papagaiAI`-Account wird danach ignoriert

---

## 1. Repository-Struktur bereinigen

- [ ] `measurements/layer1_infra/` → umbenennen in `measurements/layer1/`
- [ ] `measurements/layer3/` → umbenennen in `measurements/layer3/`
- [ ] `measurements/layer2/` → neu erstellen (war bisher nicht vorhanden)
- [ ] `scripts/` → Ordner löschen (`split_requesty.py` ist nicht mehr nötig)
- [ ] `data/archive/` → erstellen für alte explorative Daten
- [ ] Alte Layer-1-Daten → `data/archive/layer1_exploratory/`
- [ ] Alte Layer-3-Daten (Deepgram + ElevenLabs) → `data/archive/layer3_exploratory/`
- [ ] Alle Import-Pfade im Code nach Umbenennung anpassen

---

## 2. fixtures/sample.wav reparieren

**Problem:** Alle bisherigen STT-Messungen haben `transcript_len=0` — die Audiodatei
wird von den Providern nicht transkribiert.

- [ ] `fixtures/create_sample.py` umschreiben: ElevenLabs raus, `gTTS` rein
- [ ] `gtts` zu `requirements.txt` hinzufügen
- [ ] Neues `sample.wav` generieren
  - Text: *"Good morning. I would like to know the current weather forecast for Frankfurt."*
  - Sprache: Englisch, ~5 Sekunden, 16kHz WAV
- [ ] Validierungstest: Deepgram-Einzelaufruf → `transcript_len > 0` prüfen
- [ ] `fixtures/sample.wav` committen

---

## 3. .env.example bereinigen

- [ ] `ELEVENLABS_API_KEY` entfernen
- [ ] `ELEVENLABS_VOICE_ID` entfernen
- [ ] `REQUESTY_API_KEY` entfernen
- [ ] `REQUESTY_BASE_URL` entfernen
- [ ] Neue Keys ergänzen (alle noch zu beschaffen):

```
# STT
DEEPGRAM_API_KEY=
ASSEMBLYAI_API_KEY=
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=germanywestcentral

# LLM
OPENAI_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=

# TTS (OpenAI und Deepgram nutzen dieselben Keys wie oben)
# Azure TTS nutzt denselben Key wie Azure STT
```

---

## 4. API-Keys beschaffen

Reihenfolge: kostenlose zuerst.

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

**Messung-Design (festgelegt):**
- Cold-Start: Neue TCP+TLS-Verbindung pro Messung
- STT: Raw WebSocket für alle 3 Provider (kein SDK, auch nicht für Azure)
- Messwerte: `connect_ms`, `ttft_ms`/`ttfa_ms`, `total_ms`

**Feste Inputs:**
- STT Audio: `fixtures/sample.wav`
- LLM Prompt: `"Reply in one short sentence: What is the capital of Germany?"`
- TTS Text: `"Good morning! How can I assist you today!"` (~38 Zeichen)

**Dateien** (alle in `measurements/layer3/`):

| Datei | Was | Protokoll | Basis |
|-------|-----|-----------|-------|
| `stt_deepgram.py` | Deepgram Nova-3 | WebSocket (raw) | umbenennen + bereinigen |
| `stt_assemblyai.py` | AssemblyAI Universal-2 | WebSocket (raw) | neu — Deepgram als Vorlage |
| `stt_azure.py` | Azure STT (DE) | WebSocket (raw) | neu — kein SDK |
| `llm_openai.py` | OpenAI gpt-4o-mini | HTTPS+SSE | neu (Requesty komplett raus) |
| `llm_groq.py` | Groq llama-3.1-8b-instant | HTTPS+SSE | neu — OpenAI-Interface |
| `llm_mistral.py` | Mistral mistral-small-3.2 | HTTPS+SSE | neu — ähnlich OpenAI |
| `tts_deepgram.py` | Deepgram TTS Aura-2 | HTTPS Streaming | umbenennen + auf TTS umschreiben |
| `tts_openai.py` | OpenAI TTS tts-1 | HTTPS Streaming | neu |
| `tts_azure.py` | Azure TTS Neural (DE) | HTTPS Streaming | neu — kein SDK |

- [ ] `run.py` aktualisieren: alle 9 Module einbinden, Requesty entfernen

---

## 6. Layer-2-Capture-Skript schreiben

- [ ] `measurements/layer2/capture.py` erstellen
  - Startet tcpdump im Hintergrund
  - Läuft parallel zu einem Layer-3-Messdurchlauf
  - Speichert PCAP-Dateien nach `data/layer2/`
  - Stoppt tcpdump sauber nach dem Durchlauf
- [ ] Test: Einzelcapture mit Deepgram

---

## 7. AWS EC2 aufsetzen

- [ ] EC2 t3.small in eu-central-1 erstellen
- [ ] Security Group: SSH (Port 22) von eigenem IP
- [ ] `scripts/setup_ec2.sh` erstellen und ausführen:
  - Python 3.11, pip, git, tcpdump, traceroute, curl, dnsutils
  - Repo klonen von `github.com/asphyxx24/<repo-name>`
  - `pip install -r requirements.txt`
  - `.env` anlegen und Keys eintragen
- [ ] SSH-Verbindung testen

---

## 8. Cron-Jobs konfigurieren

- [ ] `scripts/crontab.txt` erstellen und auf EC2 einrichten:

```cron
# Layer 1: alle 6h (background), täglich 05:30 full
0 */6 * * * cd ~/thesis && python measurements/layer1/run.py --mode background
30 5 * * * cd ~/thesis && python measurements/layer1/run.py --mode full

# Layer 3: alle 3h, alle 9 Provider, n=100
0 0,3,6,9,12,15,18,21 * * * cd ~/thesis && python measurements/layer3/run.py --n 100 --api all

# Git-Sync: täglich 01:15 UTC
15 1 * * * cd ~/thesis && git add data/ && git commit -m "data: sync $(date +%Y-%m-%d_%H%M)" && git push
```

- [ ] Testlauf: Manuell alle 3 Layer einmal starten
- [ ] Logs prüfen nach erstem automatischen Lauf

---

## 9. Kampagne starten (14 Tage)

**Startbedingungen — alle müssen erfüllt sein:**
- [ ] GitHub konsolidiert
- [ ] EC2 läuft, SSH-Zugang funktioniert
- [ ] `sample.wav` repariert (`transcript_len > 0` validiert)
- [ ] Alle 6 API-Keys in `.env` eingetragen
- [ ] Alle 9 Layer-3-Module implementiert und per `--dry-run` getestet
- [ ] Cron-Jobs aktiv

**Kampagne läuft automatisch** — täglich Git-Sync prüfen ob Daten ankommen.

---

## 10. Analyse-Notebooks (nach Kampagne)

Wird nach den 14 Tagen gemeinsam durchgeführt. Reihenfolge:

| Notebook | Inhalt |
|----------|--------|
| `analysis/layer1_infrastructure.ipynb` | DNS-Varianz, Ping-RTT, TLS-Handshake, AS-Pfade |
| `analysis/layer3_all_providers.ipynb` | p50/p95/p99 aller 9 Provider |
| `analysis/layer3_daytime_trends.ipynb` | Latenz nach Tageszeit / Wochentag |
| `analysis/layer1_vs_layer3_correlation.ipynb` | Ping RTT × 3 ≈ connect_ms? (Kernbefund) |
| `analysis/layer3_e2e_pipeline.ipynb` | E2E-Chain: STT + LLM + TTS Gesamtlatenz |
| `analysis/layer2_protocol.ipynb` | 3-RTT-Overhead, Protokollvergleich aus PCAP |
