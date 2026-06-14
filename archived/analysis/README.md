# Analyse — Quick-Reference

> Pflichtlektuere bevor du in einem Notebook etwas aenderst:
> 1. `data/processed/known_anomalies.md` (Caveats, Bugs, Stress-Slots)
> 2. `notes/analysis_plan.md` (Master-Plan, Notebook-Konzepte)
>
> Status-Stand: 2026-05-26, 8 von 8 Notebooks fertig. Analyse-Phase abgeschlossen.

## Struktur

```
analysis/
├── _helpers.py                Provider-Map, Farben, Lader, save_figure/save_table
├── _pcap_helpers.py           tshark-Wrapper + ASN-Lookup via Team-Cymru-DNS
├── 00_data_quality.ipynb      [FERTIG] Vor-Analyse-Datenqualitaet
├── 01_layer1_infrastructure.ipynb  [FERTIG] DNS/Ping/TLS/Traceroute/DNSSEC
├── 02_pcap_communication.ipynb     [FERTIG] PCAP → IPs/ASNs/Submetriken
├── 03_layer3_stt.ipynb        [FERTIG] STT-Vergleich (Deepgram, Rev.ai, Azure)
├── 04_layer3_llm.ipynb        [FERTIG] LLM-Vergleich (OpenAI, Groq, Mistral)
├── 05_layer3_tts.ipynb        [FERTIG] TTS-Vergleich (Deepgram, OpenAI, Azure)
├── 06_cross_layer_correlation.ipynb  [FERTIG] Kernbefund-Korrelation
├── 07_e2e_pipeline.ipynb      [FERTIG] Sequentielle Pipeline-Latenz
├── figures/                   PNG + PDF Exports (Ordner 01–07 pro Notebook)
└── tables/                    CSV Exports fuer die Thesis
```

## Reihenfolge

`00 → 01 → 02 → 03 → 04 → 05 → 06 → 07`. NBs 03/04/05 sind unter sich unabhaengig, brauchen aber 00-02 als Voraussetzung. NB 06 baut auf 01/02/03/04/05 auf.

## Notebooks im Detail (was sie tun + welche Befunde sie erbracht haben)

### NB 00 — Data Quality
**Zweck:** Sanity-Check der `data/processed/`-Dateien vor jeder inhaltlichen Analyse.

**Befunde der Session 2026-05-24:**
- 4 Bugs in `data/process_raw_data.py` aufgedeckt und gefixt: Slot-Summary-Zeilen, `error=""`-Erkennung, `api`-Naming in Errors, Rev.ai-Ping-Filter
- Nach Fix: 0 % NaN in allen Layer-3-Dateien
- **Neuer Befund:** Rev.ai STT hat 10,16 % Connection-Failure-Rate (war frueher in NaN versteckt)
- Mistral hat 6 Stress-Slots (HTTP-429-Wellen) — dokumentiert in `known_anomalies.md`

### NB 01 — Layer-1-Infrastruktur
**Zweck:** Charakterisiere Netzwerk-Eigenschaften pro Endpoint (RTT, DNS, TLS, Traceroute, DNSSEC).

**Eingaben:** `data/processed/layer1_*.csv` + `data/layer1_extra/*.csv` (TLS, TCP-Ping, DNSSEC am 24.05. auf EC2 nacherhoben)

**Befunde:**
- Drei RTT-Klassen: ~1-2 ms (Cloudflare-fronted), ~10-16 ms (Azure EU), ~140 ms (Deepgram/Rev.ai US)
- **Rev.ai = einziger TLS 1.2** → 2-RTT-Handshake erklaert +140 ms gegenueber TLS 1.3
- **0 von 6 Provider-Zonen DNSSEC-signiert** (Antwort auf Prof-Punkt 1)
- Deepgram echtes Anycast (9 unique IPs), Rev.ai AWS-NLB (19 IPs), Azure single-IP

**Outputs:** `figures/01_ping_rtt_*`, `01_tls_handshake`, `tables/01_infrastructure_profile.csv`

### NB 02 — PCAP & Kommunikationsmatrix
**Zweck:** Aus den 9 PCAPs alle kontaktierten IPs + ASNs extrahieren, Submetriken-Zerlegung.

**Eingaben:** `data/layer2/capture_*.pcap` (9 Dateien vom 08.06.) + `data/layer2/analysis_summary.json`

**Befunde:**
- 4 ASNs decken alle 9 Provider ab: Cloudflare (4×), Microsoft (2×), 123NET (Deepgram, 2×), Amazon (Rev.ai)
- **Null Nebenkommunikation** in keinem PCAP (Prof-Punkt 5: APIs sind transparent)
- TLS Cross-Check PCAP vs Lokal: 100 % identisch (Konfiguration stabil ueber 3 Wochen)
- **Methodischer Schluesselbefund:** `connect ≈ RTT × N_RTTs` funktioniert sauber bei Direkthosting (Deepgram, Rev.ai, Azure), aber NICHT bei Cloudflare-fronted Providern (Edge-RTT verbirgt Backend)

**Outputs:** `figures/02_communication_matrix`, `02_submetrics_stacked`, `tables/02_pcap_communication_profile.csv`

### NB 03 — Layer-3 STT-Vergleich
**Zweck:** Deepgram vs Rev.ai vs Azure: Quantile, Verteilungen, Zeitverhalten, Connect/Server-Anteil.

**Eingaben:** `data/processed/layer3_stt.parquet` (16.227 Erfolge)

**Befunde (ueberraschend!):**
- Deepgram trotz US-Hosting **schnellster** in TTFT (575 ms median)
- Azure trotz EU-Hosting **langsamster** (1715 ms median, 97 % Server-Processing)
- Rev.ai im Mittelfeld (1420 ms), Schwaeche in beiden Phasen
- Cold-Start-Methodik validiert (Warm-up-slopes nahe 0)
- Keine Tageszeit-/Wochenvariation

**Implikation fuer Thesis:** "EU = schnell" ist eine naive Annahme. EU-Region hilft beim Connect, nicht bei der User-facing TTFT — dort dominiert die Engine.

**Outputs:** `figures/03_stt_violin`, `03_stt_cdf`, `03_stt_heatmap_zeit`, `03_stt_drift`, `03_stt_warmup`, `03_stt_connect_anteil`, `tables/03_stt_statistics.csv`

### NB 04 — Layer-3 LLM
**Zweck:** OpenAI vs Groq vs Mistral. Spezifika: `headers_ms`, `ttl_ms`, Token-Rate, Groq-Rate-Limit als Befund.

**Eingaben:** `data/processed/layer3_llm.parquet` (14.729 Erfolge)

**Befunde:**
- **Groq LPU**: `gen_ms` p50 = 7 ms vs Mistral 31 ms vs OpenAI 89 ms → Faktor 13× Hardware-Unterschied
- Groq 32,9 % HTTP-429-Fehler (Free-Tier 30 RPM) — Produktcharakteristik, kein Qualitaetsproblem
- Mistral 3 Stress-Slots mit <50 Runs (Worst Case: 15 Runs, 2026-06-04 15h)
- Alle LLM-Provider Cloudflare-fronted → connect ~9 ms, TTFT bestimmt durch Backend-Inferenz

**Outputs:** `figures/04_llm/` (8 Plots), `tables/04_llm_statistics.csv`

### NB 05 — Layer-3 TTS
**Zweck:** Deepgram vs OpenAI vs Azure. Fokus auf `ttfa_ms` (connect-inklusiv).

**Befunde:**
- **Azure TTFA 67 ms** gewinnt klar (EU-Region + schnelle Engine) — Inversion zu STT
- OpenAI TTS trotz Cloudflare-Edge-Naehe (connect 9 ms) langsamster (ttfa 954 ms, Backend dominiert)
- TTS-Cold-Start-Architektur: `connect_ms` via separate Verbindung → `ttfa` enthaelt connect der echten Request-Verbindung

**Outputs:** `figures/05_tts/` (7 Plots), `tables/05_tts_statistics.csv`

### NB 06 — Cross-Layer-Korrelation (KERNBEFUND)
**Zweck:** Hauptthese der Arbeit empirisch belegen: Layer-1 erklaert Layer-3.

**Befunde:**
- `connect_ms ≈ N_RTTs × ping_median + k` mit **slope 1.006, k 10.7 ms, r = 0.999** (4 direkte TLS-1.3-Punkte; r wegen n=4 nicht als Gütemaß lesen)
- N_RTTs: HTTPS TLS1.3 = 2, WebSocket TLS1.3 = 3, WebSocket TLS1.2 (Rev.ai) = 4 (+1 RTT Penalty = +153 ms)
- Cloudflare-fronted: Modell bricht — Edge-RTT ~1 ms, aber Backend-Latenz nicht messbar
- k ≈ 5–26 ms = Python/Kernel-Software-Overhead (distanzunabhaengig)

**Outputs:** `figures/06_cross_layer/` (5 Plots), `tables/06_cross_layer_master.csv`

### NB 07 — E2E-Pipeline
**Zweck:** Alle 27 Provider-Kombinationen (3 STT × 3 LLM × 3 TTS) rechnerisch durchspielen, 1-Sekunden-Budget pruefen.

**Befunde:**
- **0/27 Kombinationen** unterschreiten das 1-Sekunden-Budget im Cold-Start
- Beste Kombination Streaming: Deepgram+Groq+Azure = **1 134 ms**
- STT dominiert in allen 27 Kombinationen (Ø 67 % der E2E-Latenz)
- Mit persistenten Verbindungen (Warm): Deepgram+Groq+Azure ≈ **666 ms** (unter 1s)
- Cold-Start ist ein reines Session-Start-Problem; in Produktion erreichbar

**Outputs:** `figures/07_e2e/` (4 Plots), `tables/07_pipeline_combinations.csv`

## Tools

- Python 3.12 + pandas/pyarrow/scipy/matplotlib/seaborn/dnspython
- Jupyter via `python -m jupyter nbconvert --to notebook --execute <nb>.ipynb --inplace`
- Wireshark 4.6 (tshark unter `C:\Program Files\Wireshark\tshark.exe`, von `_pcap_helpers.py` automatisch gefunden)
- AWS CLI v2 (fuer EC2-Start/-Stop bei Ersatzmessungen)

## Konventionen

- Alle Plots werden via `save_figure(fig, 'NN_name')` als PNG (Notebook-Vorschau) + PDF (LaTeX-Embed) exportiert.
- Tabellen via `save_table(df, 'NN_name')` als CSV.
- Provider-Map zentral in `_helpers.py:PROVIDER_TO_ENDPOINT` — bei Aenderungen dort, nicht in den Notebooks.
- Konsistente Farben pro Provider via `_helpers.py:PROVIDER_COLORS`.
