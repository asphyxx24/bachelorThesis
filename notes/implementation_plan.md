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

## Phase 6: AWS EC2 aufsetzen (ERLEDIGT)

- [x] EC2 t3.small in eu-central-1 (Frankfurt) erstellt — `i-045a2d0eeb338b290`
- [x] Security Group: SSH (Port 22) — `sg-0f8d6248567378773`
- [x] Repo geklont von `github.com/asphyxx24/bachelorThesis`
- [x] Python 3.10 venv + Dependencies installiert
- [x] `.env` per scp kopiert, alle 7 Keys funktionsfaehig
- [x] Testlauf Layer 3: alle 9 Provider, 0 Errors
- [x] Testlauf Layer 1: alle 9 Endpoints, DNS+Ping OK

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

- [x] Cron-Jobs auf EC2 eingerichtet (2026-05-03)
- [x] Testlauf: Manuell alle 9 Provider, 0 Errors
- [x] Logs geprueft, Kampagne lief sauber ueber 18 Tage
- [x] Cron-Jobs am 2026-05-22 deaktiviert (Kampagnenende)

---

## Phase 8: Kampagne (ERLEDIGT)

- [x] `sample.wav` aufgenommen und validiert
- [x] Alle API-Keys in `.env` eingetragen
- [x] Alle 9 Layer-3-Module implementiert und getestet
- [x] EC2 laeuft, SSH-Zugang funktioniert (IP: 35.159.112.40)
- [x] Cron-Jobs aktiv (2026-05-03 bis 2026-05-22)
- [x] Kampagne abgeschlossen — 18 Tage, 145 Slots, 128.580 Messungen
- [x] Datenqualitaet validiert (7/9 Provider ~0% Fehler, Groq 34% durch
      Free-Tier-Rate-Limit, Mistral 4,3%)
- [x] Tatsaechliche Kosten: ~$68 API + ~$13 AWS

---

## Phase 9: Layer-2 Captures (ERLEDIGT)

- [x] PCAP-Capture aller 9 Provider auf EC2 (2026-05-04)
- [x] Erstanalyse mit tshark (TCP/TLS-Submetriken, Inter-Paket-Zeiten)
- [x] PCAP-Dateien lokal gesichert (`data/layer2/capture_*.pcap`)
- [x] `analysis_summary.json` mit Submetriken pro Provider

Vertiefte Analyse (alle IPs/ASNs, Kommunikationsmatrix) folgt in Phase 10 —
Notebook `02_pcap_communication.ipynb`, siehe `notes/analysis_plan.md`.

---

## Phase 10: Analyse (AKTUELLE PHASE)

**Master-Plan:** `notes/analysis_plan.md` (PRP, erstellt 2026-05-22)

Acht Notebooks geplant in der Reihenfolge `00 → 01 → 02 → 03 → 04 → 05 → 06 → 07`:

| Notebook | Inhalt |
|----------|--------|
| `00_data_quality.ipynb` | Sanity-Check der processed-Daten |
| `01_layer1_infrastructure.ipynb` | DNS, Ping, TLS, Traceroute + DNSSEC |
| `02_pcap_communication.ipynb` | PCAP-Analyse, ASN-Lookup, Kommunikationsmatrix |
| `03_layer3_stt.ipynb` | STT-Vergleich |
| `04_layer3_llm.ipynb` | LLM-Vergleich (incl. Groq-Rate-Limit-Befund) |
| `05_layer3_tts.ipynb` | TTS-Vergleich |
| `06_cross_layer_correlation.ipynb` | KERNBEFUND: Ping × N_RTTs ≈ connect_ms |
| `07_e2e_pipeline.ipynb` | E2E-Pipeline, 27 Provider-Kombinationen |

Voraussetzung vor Start:
- `pip install jupyter matplotlib seaborn scipy dnspython`
- Wireshark/tshark installieren (fuer Notebook 02)

Datenaufbereitung erledigt: `data/process_raw_data.py` hat 8 saubere Dateien
in `data/processed/` erzeugt (4 Parquet fuer Layer 3, 4 CSV fuer Layer 1).

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
