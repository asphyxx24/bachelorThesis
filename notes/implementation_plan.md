# Implementierungsplan

Alle Schritte von Projektstart bis Thesis-Abgabe.

---

## Status-Legende
- [ ] Offen
- [~] In Arbeit
- [x] Erledigt

---

## Phase 0–4: Setup (ERLEDIGT)

<details>
<summary>Details (alles abgeschlossen)</summary>

### 0. GitHub konsolidieren
- [x] `asphyxx24` ist primaerer Remote
- [x] `papagaiAI`-Account wird ignoriert

### 1. Repository-Struktur bereinigen
- [x] Ordner umbenannt (layer1_infra → layer1, etc.)
- [x] Alte Daten nach `data/archive/` verschoben (950 L1 + 228 L3 Dateien)

### 2. sample.wav erstellen
- [x] Englische Sprachaufnahme (16kHz, Mono, PCM, ~4.8s)
- [x] Validierung: `transcript_len > 0` bei Deepgram

### 3. .env.example bereinigen
- [x] Alte Keys entfernt (ElevenLabs, Requesty)
- [x] Aktuelle Keys dokumentiert:

```
DEEPGRAM_API_KEY=
REVAI_API_KEY=
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=italynorth
OPENAI_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=
```

### 4. API-Keys beschaffen
- [x] Alle 7 Keys eingetragen und funktionsfaehig

| Provider | Kosten | Status |
|----------|--------|--------|
| Deepgram | $0 ($200 Startguthaben) | [x] |
| Rev.ai | $1 Free Tier | [x] |
| Azure | ~$10,74 (S0 Tier, Italy North) | [x] |
| OpenAI | $10 Prepaid | [x] |
| Groq | $0 (Free Tier) | [x] |
| Mistral | $0 (Free Tier) | [x] |

</details>

---

## Phase 5: Layer-3-Module (ERLEDIGT)

Alle 9 Provider-Module implementiert und per `--dry-run` getestet (2026-05-03).

| Datei | Provider | Protokoll | Status |
|-------|----------|-----------|--------|
| `stt_deepgram.py` | Deepgram Nova-3 | WebSocket (raw) | [x] |
| `stt_revai.py` | Rev.ai English | WebSocket (raw) | [x] |
| `stt_azure.py` | Azure STT (Italy North) | WebSocket (raw, kein SDK) | [x] |
| `llm_openai.py` | OpenAI gpt-4o-mini | HTTPS+SSE | [x] |
| `llm_groq.py` | Groq llama-3.1-8b-instant | HTTPS+SSE | [x] |
| `llm_mistral.py` | Mistral mistral-small-2603 | HTTPS+SSE | [x] |
| `tts_deepgram.py` | Deepgram Aura-2 | HTTPS Streaming | [x] |
| `tts_openai.py` | OpenAI tts-1 | HTTPS Streaming | [x] |
| `tts_azure.py` | Azure TTS Neural (Italy North) | HTTPS Streaming (SSML) | [x] |

- [x] `run.py` aktualisiert (9 Provider, dynamische Imports)
- [x] `MODULE_PLAN.md` geschrieben und aktualisiert
- [x] Alle Module per `--dry-run` getestet

**Messdesign:**
- Cold-Start: Neue TCP+TLS-Verbindung pro Messung (kein Connection Pooling)
- STT: Raw WebSocket fuer alle 3 Provider (kein SDK)
- Feste Inputs: Identisch pro Kategorie
- Messwerte: `connect_ms`, `ttft_ms`/`ttfa_ms`, `total_ms` + kategoriespezifische

---

## Phase 6: AWS EC2 aufsetzen

- [ ] EC2 t3.small in eu-central-1 (Frankfurt) erstellen
- [ ] Security Group: SSH (Port 22) von eigenem IP
- [ ] Repo klonen von `github.com/asphyxx24/bachelorThesis`
- [ ] Python venv + Dependencies installieren
- [ ] `.env` anlegen und alle 7 Keys eintragen
- [ ] Testlauf: `python measurements/layer3/run.py --dry-run`
- [ ] Testlauf: `python measurements/layer1/run.py --dry-run`

---

## Phase 7: Cron-Jobs konfigurieren

```cron
# Layer 1: alle 6h background, taeglich 05:30 full
0 */6 * * * cd ~/thesis && .venv/bin/python measurements/layer1/run.py --mode background
30 5 * * * cd ~/thesis && .venv/bin/python measurements/layer1/run.py --mode full

# Layer 3: alle 3h, alle 9 Provider, n=100
0 0,3,6,9,12,15,18,21 * * * cd ~/thesis && .venv/bin/python measurements/layer3/run.py --n 100 --api all

# Git-Sync: taeglich 01:15 UTC
15 1 * * * cd ~/thesis && git add data/ && git commit -m "data: sync $(date +%Y-%m-%d_%H%M)" && git push
```

- [ ] Cron-Jobs auf EC2 einrichten
- [ ] Testlauf: Manuell Layer 1 + Layer 3 einmal starten
- [ ] Logs pruefen nach erstem automatischen Lauf

---

## Phase 8: Kampagne starten (14 Tage)

**Startbedingungen:**
- [x] `sample.wav` aufgenommen und validiert
- [x] Alle API-Keys in `.env` eingetragen
- [x] Alle 9 Layer-3-Module implementiert und getestet
- [ ] EC2 laeuft, SSH-Zugang funktioniert
- [ ] Cron-Jobs aktiv

**Kampagne laeuft automatisch** — taeglich Git-Sync pruefen ob Daten ankommen.

---

## Phase 9: Layer-2 Captures (waehrend Kampagne)

Layer 2 ist kein automatischer Messlauf — manuell auf EC2 per `tcpdump`.
Ein paar gezielte Captures pro Provider reichen.

- [ ] Deepgram STT Capture (WebSocket, Audio-Upload-Pattern)
- [ ] Rev.ai STT Capture (WebSocket, Vergleich)
- [ ] Azure STT Capture (WebSocket, EU-Endpoint)
- [ ] OpenAI LLM Capture (HTTPS+SSE, Token-Delivery)
- [ ] Groq LLM Capture (HTTPS+SSE, LPU-Verhalten)
- [ ] Mistral LLM Capture (HTTPS+SSE, EU-Endpoint)
- [ ] Analyse mit tshark (Inter-Paket-Zeiten, WebSocket-Frames)

Anleitung: `measurements/layer2/README.md`
POC-Ergebnisse: `notes/layer2_first_capture.md`

---

## Phase 10: Analyse (nach Kampagne)

| Notebook | Inhalt |
|----------|--------|
| `analysis/layer1_infrastructure.ipynb` | DNS-Varianz, Ping-RTT, TLS-Handshake, AS-Pfade |
| `analysis/layer3_all_providers.ipynb` | p50/p95/p99 aller 9 Provider |
| `analysis/layer3_daytime_trends.ipynb` | Latenz nach Tageszeit / Wochentag |
| `analysis/layer1_vs_layer3_correlation.ipynb` | Ping RTT × 3 ≈ connect_ms? (Kernbefund) |
| `analysis/layer3_e2e_pipeline.ipynb` | E2E-Chain: STT + LLM + TTS Gesamtlatenz |
| `analysis/layer2_protocol.ipynb` | 3-RTT-Overhead, Protokollvergleich aus PCAP |

---

## Phase 11: E2E-Validierung (nach Analyse)

Keine eigene Messkampagne — ein paar manuelle Chain-Runs, um zu validieren,
dass die Summe der Einzellatenzen der realen Pipeline-Latenz entspricht.

- [ ] 2–3 Pipelines manuell testen (z.B. Deepgram+Groq+Azure, Azure+Mistral+Azure)
- [ ] Gemessene Gesamtlatenz mit Summe der Einzelwerte vergleichen
- [ ] Ergebnis in Thesis dokumentieren (Abschnitt Diskussion/Validierung)

---

## Phase 12: Thesis schreiben

| Kapitel | Inhalt |
|---------|--------|
| 1. Einleitung | Motivation, Forschungsfrage, Beitrag |
| 2. Hintergrund | Voice-Pipelines, Protokolle, Cloud-AI-APIs |
| 3. Methodik | 3-Schichten-Architektur, Cold-Start, Provider-Auswahl |
| 4. Implementierung | Messinfrastruktur, Module, Kampagnen-Design |
| 5. Ergebnisse | Latenzanalyse, Cross-Layer-Korrelation, E2E-Pipeline |
| 6. Diskussion | Interpretation, Limitationen, Provider-Empfehlungen |
| 7. Fazit | Zusammenfassung, Ausblick |

---

## Zeitplanung (geschaetzt, Deadline flexibel)

| Phase | Dauer |
|-------|-------|
| Phase 6–7 (EC2 + Cron) | ~2–3 Tage |
| Phase 8 (Kampagne) | 14 Tage (automatisch) |
| Phase 9 (Layer-2 Captures) | ~1 Tag (waehrend Kampagne) |
| Phase 10 (Analyse) | ~2 Wochen |
| Phase 11 (E2E-Validierung) | ~1 Tag |
| Phase 12 (Thesis schreiben) | ~3–4 Wochen |
