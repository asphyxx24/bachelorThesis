# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-26 (Session: Konsolidierung zweier Parallel-Chats + NB-03-Bug-Fix)

## TL;DR

Phase 10 (Analyse) zu **75 % fertig**: 7 von 8 Notebooks abgeschlossen (00–06), nur NB 07 (E2E-Pipeline) und die Schreibphase offen. In dieser Session wurden zwei parallele Chats zusammengefuehrt und ein **methodischer Bug in NB 03 `connect_anteil`** gefixt (`connect_ms / ttft_ms` → `connect_ms / (connect_ms + ttft_ms)`). Die qualitative Botschaft aller Befunde bleibt, nur die Prozentzahlen wurden korrigiert (74 % → 43 % bei Deepgram; 42 % → 30 % bei Rev.ai). **NB 06 (Cross-Layer-Korrelation, Kernbefund der Thesis) ist unveraendert** — die fehlerhafte Formel war reine Anzeige-Sache in NB 03 und propagiert nicht in NB 06, das `connect_median` und `ping_median` direkt aus den Rohdaten verwendet.

Drei zentrale Befunde stehen fest:

1. **Cloudflare-Fronting** fuer 4/9 Provider (OpenAI/Groq/Mistral LLM + OpenAI TTS) → die Layer-1-zu-Layer-3-Korrelation gilt nur fuer die 5 direkt-gehosteten Provider.
2. **Cross-Layer-Modell** `connect_ms ≈ N_RTTs × ping + k` mit r=0.999 fuer Direct-TLS-1.3 (Deepgram STT/TTS + Azure STT/TTS). TLS-1.2-Penalty bei Rev.ai exakt +1 RTT (~142 ms).
3. **Engine > Netzwerk bei STT**: Deepgram (US, RTT 140 ms) schlaegt Azure (EU, RTT 10 ms) in der user-perceived Cold-Start-Latenz (1024 ms vs. 1767 ms), weil Nova-3 nur 587 ms Server-Processing braucht vs. Azures 1719 ms. Bei TTS dreht sich das um (Azure 65 ms TTFA gewinnt).

---

## Was diese Session gemacht hat

1. **Verifiziert, dass NB 06 wirklich fertig ist** — alle 5 Figures (`figures/06_cross_layer/`) + `tables/06_cross_layer_master.csv` existieren, Regression reproduzierbar (`connect = 1.013 × n_rtts × ping + 8.5, r = 0.9992`).
2. **Bug in NB 03 §5 + §6 gefixt** — Details im naechsten Abschnitt.
3. **Notebook neu ausgefuehrt**, Figure `03_stt_connect_anteil.{png,pdf}` regeneriert mit korrekten Zahlen.
4. **Drei alte HANDOFF-Dateien geloescht** (`HANDOFF.md`, `HANDOFF_first.md`, `HANDOFF_second.md`) und zu dieser Datei konsolidiert.

---

## Der NB-03-Bug im Detail (damit niemand ihn nochmal einfuehrt)

**Problem:** `connect_ms` und `ttft_ms` sind im STT-Messcode (`measurements/layer3/stt_*.py`) **sequenzielle, disjunkte Phasen**:

```
t_ws_start  →  [connect_ms]  →  t_ws_connected  ≈  t_first_chunk  →  [ttft_ms]  →  t_first_final
```

`ttft_ms` startet ERST NACH dem Verbindungsaufbau. Total Cold-Start = `connect_ms + ttft_ms`.

**Frueherer Bug in NB 03 Cell `anteil` (Cell 13):**
- Stacked-Bar: `connect` + `(ttft - connect)` als zwei Bars → totale Bar-Hoehe war faelschlich `ttft_ms` statt `connect_ms + ttft_ms`.
- Label auf der Bar: `c / (c+s) = c / ttft` → Deepgram 74 % statt korrekter 43 %.

**Fix:**
```python
# alt:  server = ttft - connect          (faelschlich)
# neu:  server = ttft                    (= reine Server-Processing-Zeit)
# alt:  pct = c / ttft                   (faelschlich)
# neu:  pct = c / (c + ttft)             (korrekter Connect-Anteil)
```

**Korrigierte Zahlen (in NB 03 §6 jetzt konsistent):**

| Provider | Connect/Gesamt | Server/Gesamt | Cold-Start total |
|----------|---------------:|--------------:|-----------------:|
| azure    |  2.7 % | 97.3 % | 1767 ms |
| deepgram | 42.7 % | 57.3 % | 1024 ms |
| revai    | 29.7 % | 70.3 % | 1997 ms |

**Warum NB 05 (TTS) NICHT betroffen war:** Der TTS-Messcode misst `connect_ms` ueber eine **separate** Verbindung (`_measure_connect()`), und `ttfa_ms` startet bei `t_req` der echten Request-Verbindung — schliesst also die Connect-Zeit der Hauptverbindung mit ein. Damit ist `connect_ms / ttfa_ms` strukturell eine valide Naeherung (gleiche Architektur wie LLM). NB 05 Cell 8 ist korrekt.

**Warum NB 06 NICHT betroffen war:** NB 06 nutzt aus den Rohdaten direkt `connect_median` (pro Provider) und `ping_median` (pro Endpoint). Der buggy `connect_anteil` war reines Anzeige-Artefakt und ging nie in Berechnungen ein. `tables/06_cross_layer_master.csv` ist gueltig.

---

## Stand der Notebooks

| NB | Status | Hauptbefund | Outputs |
|----|--------|-------------|---------|
| 00 Data Quality | FERTIG | 4 Aufbereitungs-Bugs gefixt, 0 % NaN, Rev.ai 10 % Error-Rate aufgedeckt | none (Validierung) |
| 01 Layer-1 | FERTIG | Drei RTT-Klassen, Rev.ai TLS 1.2, 0/6 DNSSEC, Cloudflare-Hypothese | 3 Plots, infrastructure_profile.csv |
| 02 PCAP | FERTIG | Cloudflare 4/9, Null Nebenkommunikation, RTT-Modell bricht bei CDN | 2 Plots, communication_profile.csv |
| 03 STT | FERTIG (gefixt 26.05.) | Deepgram TTFT schnellster trotz US, Azure langsamster trotz EU | 6 Plots, stt_statistics.csv |
| 04 LLM | FERTIG | Groq LPU 13× schneller (gen_ms 7 ms vs OpenAI 89 ms); 35 % Free-Tier-Errors | 8 Plots, llm_statistics.csv |
| 05 TTS | FERTIG | Azure TTFA 65 ms gewinnt klar — Inversion zu STT | 7 Plots, tts_statistics.csv |
| 06 Cross-Layer | FERTIG | `connect ≈ N_RTTs × ping + k`, r=0.999; TLS-1.2-Penalty +142 ms | 5 Plots, cross_layer_master.csv |
| 07 E2E-Pipeline | **OFFEN** | (27 Kombinationen, 1-Sek-Budget) | -- |

---

## WICHTIG fuer naechste Session: Erst verifizieren, dann weitermachen

Bevor du an NB 07 anfaengst, **arbeite diese Checkliste systematisch ab**. Wenn ein Schritt fehlschlaegt oder andere Zahlen kommen: **stoppe und kommuniziere mit dem User**.

### Verifikations-Checkliste

```bash
# Aus dem Projekt-Root (C:\Users\anton\Desktop\bachelorThesis):

# 1. Tooling
python --version                                                  # erwartet: 3.12.x
python -c "import pandas, numpy, matplotlib, seaborn, scipy, dns; print('OK')"
"C:/Program Files/Wireshark/tshark.exe" --version | head -1       # erwartet: 4.6.x

# 2. Datenintegritaet — die 4 Parquets
python -c "
import pandas as pd
expected = {'layer3_stt':42016,'layer3_llm':37734,'layer3_tts':43489,'layer3_errors':7261}
for f,n in expected.items():
    df = pd.read_parquet(f'data/processed/{f}.parquet')
    nans = df.filter(regex='_ms$').isna().sum().sum()
    flag = 'OK' if (len(df)==n and nans==0) else 'MISMATCH'
    print(f'{f:18s} {len(df):>7,}/{n:,} Zeilen, NaN={nans} [{flag}]')
"

# 3. Notebooks reproduzierbar — alle 7 fertigen NBs ohne Fehler ausfuehrbar
cd analysis
for nb in 00_data_quality 01_layer1_infrastructure 02_pcap_communication 03_layer3_stt 04_layer3_llm 05_layer3_tts 06_cross_layer_correlation; do
    echo "=== $nb ==="
    python -m jupyter nbconvert --to notebook --execute ${nb}.ipynb --inplace 2>&1 | tail -2
done
cd ..

# 4. Statistik-Tabellen ueberpruefen (Soll-Werte)
python -c "
import pandas as pd
print('=== STT Statistik (TTFT-Quantile) ===')
df = pd.read_csv('analysis/tables/03_stt_statistics.csv')
print(df[df['metric']=='ttft_ms'][['provider','p50','p95']].to_string(index=False))
# SOLL:
# azure       1718.7  1725.4
# deepgram     587.0   694.2
# revai       1404.1  1547.9

print('\\n=== LLM Statistik (TTFT-Quantile) ===')
df = pd.read_csv('analysis/tables/04_llm_statistics.csv')
print(df[df['metric']=='ttft_ms'][['provider','p50','p95']].to_string(index=False))
# SOLL:
# groq          67.3   119.6
# mistral      232.3   933.3
# openai       526.2  1421.1

print('\\n=== TTS Statistik (TTFA-Quantile) ===')
df = pd.read_csv('analysis/tables/05_tts_statistics.csv')
print(df[df['metric']=='ttfa_ms'][['provider','p50','p95']].to_string(index=False))
# SOLL:
# azure         65.3   113.1
# deepgram     551.0   593.3
# openai       938.3  1831.6

print('\\n=== Cross-Layer Modellfit (Direct-TLS-1.3) ===')
import numpy as np
m = pd.read_csv('analysis/tables/06_cross_layer_master.csv')
d = m[(m['class']=='Direkt') & (m['tls']=='TLS 1.3')].copy()
d['predicted'] = d['n_rtts_model'] * d['ping_median']
slope, intercept = np.polyfit(d['predicted'], d['connect_median'], 1)
print(f'connect = {slope:.3f} * (N_RTTs * ping) + {intercept:.1f}, r = {np.corrcoef(d[\"predicted\"], d[\"connect_median\"])[0,1]:.4f}')
# SOLL: slope=1.013, intercept=8.5, r=0.9992
"

# 5. NB 03 Bug-Fix verifizieren — Figure und Tabelle
python -c "
import json
nb = json.load(open('analysis/03_layer3_stt.ipynb', encoding='utf-8'))
for o in nb['cells'][13]['outputs']:
    if 'text' in o: print(''.join(o['text']))
"
# SOLL: connect_share_pct fuer deepgram=42.7, revai=29.7, azure=2.7
```

### Zusaetzlich gegenpruefen

- `analysis/README.md` — Quick-Reference aller NBs (falls vorhanden; ggf. nach NB 07 aktualisieren)
- `data/processed/known_anomalies.md` — Pflichtlektuere vor jedem neuen NB (Bugs, Stress-Slots, Layer-1-Caveats)
- `notes/analysis_plan.md` §6 NB 07 — Konzept fuer das letzte Notebook

---

## Aktuelle Fokus-Aufgabe: NB 07 (E2E-Pipeline)

**Eingaben:** `layer3_stt.parquet`, `layer3_llm.parquet`, `layer3_tts.parquet`

**Modell:** `E2E ≈ stt_total + llm_ttft + tts_ttfa` (User-perceived: erstes Audio kommt an)

**Struktur (aus `notes/analysis_plan.md` §6 NB 07):**

1. **Pipeline-Modell** — fuer alle 27 Kombinationen (3 STT × 3 LLM × 3 TTS) Median und p95 berechnen. Aus Rohdaten pro Slot zufaellig samplen (oder einfach: Provider-Mediane addieren — Diskussion mit User, was wissenschaftlich sauberer ist).
2. **Top-5 / Bottom-5** — Tabelle + Stacked-Bar (Beitrag jedes Layers).
3. **1-Sekunden-Budget-Plot** — Horizontale Balken sortiert, mit 1s-Linie.
4. **Bottleneck-Analyse** — pro Kombination: welcher Layer dominiert?

**Erwartungswerte fuer die Top-Kombination (Median-Addition):**
- STT Azure (`total_ms=1768`) + LLM Groq (`ttft_ms=67`) + TTS Azure (`ttfa_ms=65`) = **1900 ms** Median
- Alle 27 Kombinationen werden voraussichtlich > 1000 ms liegen — das **1-Sek-Voice-Budget wird von keiner Cold-Start-Pipeline erreicht**. Das ist ein realer, publizierbarer Befund.

**Alternativ-Kombination (wenn STT-`ttft` statt `total` als Zielmetrik):**
- STT Deepgram (`ttft_ms=587`, schnellster TTFT) + LLM Groq (67) + TTS Azure (65) = **719 ms** — knapp unter 1s!
- Hier diskutieren: Was ist die richtige STT-Metrik fuer eine Streaming-Pipeline? Wenn das Backend schon nach dem ersten Wort an den LLM weiterleiten kann, dann `ttft`, sonst `total`. **Diese Frage mit User klaeren bevor du den Plot final renderst.**

**Vorgehen empfohlen:** NB 07 nach dem Vorbild von NB 06 strukturieren (klare Sektionen, Tabelle + Plot pro Frage). `save_figure(fig, '07_...')` legt automatisch `figures/07_e2e/` an (siehe `_helpers.py:_TOPIC_DIRS`).

---

## Drei kleinere offene Aufgaben (vor / nach NB 07)

### A) Uncommitteter Stand committen

Es gibt einen grossen uncommitteten Block aus der Parallel-Chat-Session (Figure-Reorganisation + NB 04/05/06 + Helper-Update). Empfehlung:

```bash
# Sauberen Commit machen, sobald NB 07 fertig oder spaetestens vor Schreibphase:
git add analysis/_helpers.py analysis/0*.ipynb analysis/figures/0*/ \
        analysis/tables/0[4-6]*.csv \
        notes/vorbereitung_treffen_20260505.md \
        HANDOFF.md
# (.claude/settings.local.json und zusammenfassung_prof.pdf gehoeren NICHT ins Repo,
#  selektiv stagen)
git commit -m "analyse: NB 04 LLM + NB 05 TTS + NB 06 Cross-Layer fertig, Figure-Reorg, NB 03 connect_anteil-Bug gefixt"
```

User vorher fragen, ob er den Commit selbst machen will (er macht Git-Operationen oft manuell).

### B) Prof-PDF Seite 3 Caption korrigieren

`analysis/figures/zusammenfassung_prof.pdf` (4-Seiten-Bundle fuer Prof.-Meeting). Seite 3 bindet das alte `03_stt_connect_anteil` ein und die Caption nennt die falschen 74 %. Da die korrigierte Figure jetzt in `figures/03_stt/{png,pdf}/03_stt_connect_anteil.{png,pdf}` liegt, muss das PDF entweder neu erzeugt werden oder zumindest die Caption angepasst.

User wird vor seinem naechsten Prof-Meeting damit umgehen — kein Zeitdruck dieser Session. Wenn er fragt: **die Figure ist schon korrekt, nur das Bundle-PDF zeigt noch die alte Version.** Generierungs-Skript existiert vermutlich nicht (PDF wurde manuell zusammengestellt), also entweder manuell neu einbetten oder ein kleines Python-Skript mit `pypdf`/`reportlab` schreiben.

### C) `analysis/README.md` ergaenzen (nach NB 07)

Quick-Reference aller Notebooks; sollte am Ende auch NB 07 erwaehnen. Nicht kritisch, aber hilfreich fuer Schreibphase.

---

## Kerndaten auf einen Blick (Stand 2026-05-26)

### Provider-Matrix (real, inkl. NB-02-Bestaetigung)

```
STT:
  azure_stt    Italy North (AS 8075 MS)         RTT=11ms  TLS1.3  connect=48ms   ttft=1719ms
  deepgram_stt USA (AS 12129 123NET)            RTT=140ms TLS1.3  connect=437ms  ttft=587ms
  revai_stt    USA Oregon (AS 16509 AWS)        RTT=142ms TLS1.2  connect=593ms  ttft=1404ms

LLM:
  groq_llm     Cloudflare-Edge FRA (AS 13335)   RTT=1ms   TLS1.3  connect=9ms    ttft=67ms   gen=7ms
  mistral_llm  Cloudflare-Edge FRA (AS 13335)   RTT=1ms   TLS1.3  connect=9ms    ttft=232ms  gen=33ms
  openai_llm   Cloudflare-Edge FRA (AS 13335)   RTT=1ms   TLS1.3  connect=9ms    ttft=526ms  gen=89ms

TTS:
  azure_tts    Italy North (AS 8075 MS)         RTT=11ms  TLS1.3  connect=34ms   ttfa=65ms
  deepgram_tts USA (AS 12129 123NET)            RTT=140ms TLS1.3  connect=284ms  ttfa=551ms
  openai_tts   Cloudflare-Edge FRA (AS 13335)   RTT=1ms   TLS1.3  connect=9ms    ttfa=938ms
```

### Cross-Layer-Modell (NB 06)

```
connect_ms ≈ N_RTTs × ping_median + k

Direct TLS 1.3 (4 Datenpunkte: Deepgram STT+TTS, Azure STT+TTS):
   slope = 1.013, intercept = 8.5 ms, r = 0.9992
   → das Modell `N_RTTs × ping` erklaert connect_ms nahezu perfekt.
   k ≈ 5-26 ms ist Python/Kernel-Software-Overhead, distanz-unabhaengig.

N_RTTs pro Protokoll:
   HTTPS POST Streaming + TLS 1.3:    2 RTTs   (Deepgram TTS)
   WebSocket + TLS 1.3:               3 RTTs   (Deepgram STT, Azure STT/TTS)
   WebSocket + TLS 1.2:               4 RTTs   (Rev.ai — +1 RTT TLS-1.2-Penalty = +142 ms)

CDN-fronted (Cloudflare-Edge Frankfurt — Modell bricht):
   ping zum Edge ~1-2 ms, aber connect ~9 ms (Software-Overhead dominiert)
   Backend-RTT von EC2-Frankfurt nicht messbar
   Konsequenz: Bei CDN-Providern bestimmt Backend-Inferenz die TTFT, nicht Netzwerk.
```

### NB-03-STT-Cold-Start (korrigierte Zerlegung)

```
deepgram:  connect 437 ms (43 %) + ttft 587 ms (57 %) = 1024 ms  ← schnellster
revai:     connect 593 ms (30 %) + ttft 1404 ms (70 %) = 1997 ms
azure:     connect 48 ms (3 %)   + ttft 1719 ms (97 %) = 1767 ms  ← langsamster
```

### NB-05-TTS-Cold-Start (TTFA = connect-inklusive)

```
azure:     connect 34 ms + proc 31 ms ≈ ttfa 65 ms     ← schnellster (EU + schnelle Engine)
deepgram:  connect 284 ms + proc 267 ms ≈ ttfa 551 ms
openai:    connect 9 ms + proc 929 ms ≈ ttfa 938 ms    ← CF-naehe nutzt nichts wegen langsamer Engine
```

### NB-04-LLM-Eigenheiten

- **Groq LPU**: `gen_ms` p50 = 7 ms (vs Mistral 33 ms, OpenAI 89 ms) → Faktor ~13× — Hardware-Unterschied direkt messbar.
- **Groq 34.97 % HTTP-429-Errors** (Free-Tier 30 RPM). Im Plot `04_llm_error_rates` separat dokumentiert. NICHT als Datenqualitaets-Problem behandeln, sondern als Produktcharakteristik.
- **Mistral 6 Stress-Slots** mit <50 Runs in 18 Tagen (Worst Case: 2 Runs in einem Slot, 2026-05-19 18 h). In Zeitreihen-Plots sichtbar markiert.

---

## Datenmenge

| Layer | Datei | Zeilen | Anmerkung |
|-------|-------|-------:|-----------|
| L3 | `layer3_stt.parquet` | 42.016 | 3 Provider × ~14k |
| L3 | `layer3_llm.parquet` | 37.734 | OpenAI 14.5k, Mistral 13.8k, Groq 9.4k (Rate-Limit) |
| L3 | `layer3_tts.parquet` | 43.489 | 3 Provider × ~14.5k |
| L3 | `layer3_errors.parquet` | 7.261 | 1.473 Rev.ai Connection-Fails + 5.070 Groq 429er |
| L1 | `layer1_ping.csv` | 819 | inkl. 91 Rev.ai mit `packet_loss=100` |
| L1 | `layer1_dns.csv` | 819 | |
| L1 | `layer1_tls.csv` | 162 | **leer (NaN), ersetzt durch `data/layer1_extra/tls.csv`** |
| L1 | `layer1_traceroute.csv` | 162 | Azure/Rev.ai 0 % reached (UDP-Block) |
| L1-Extra | `data/layer1_extra/tls.csv` | 35 | 7 Endpoints × 5 Runs (24.05.) |
| L1-Extra | `data/layer1_extra/ping_tcp.csv` | 7 | TCP-SYN-Ping aggregiert |
| L1-Extra | `data/layer1_extra/dnssec.csv` | 7 | 0/6 Zonen signiert |
| L2 | `data/layer2/capture_*.pcap` | 9 Files | Single-Slot 04.05., ~50-200 KB |
| L2 | `data/layer2/analysis_summary.json` | 9 entries | Submetriken (TCP/TLS/Proto) pro Provider |

---

## Figures-Struktur (aktuell)

```
analysis/figures/
├── 01_layer1/png+pdf/   3 Plots  (ping_rtt_boxplot, ping_rtt_zeitreihe, tls_handshake)
├── 02_pcap/png+pdf/     2 Plots  (communication_matrix, submetrics_stacked)
├── 03_stt/png+pdf/      6 Plots  (violin, cdf, heatmap_zeit, drift, warmup, connect_anteil*)
├── 04_llm/png+pdf/      8 Plots  (ttft_violin, ttft_cdf, gen_ms, error_rates, heatmap, drift, warmup, connect_anteil)
├── 05_tts/png+pdf/      7 Plots  (ttfa_violin, ttfa_cdf, connect_anteil, heatmap, drift, warmup, total_ms)
├── 06_cross_layer/png+pdf/  5 Plots  (scatter, tls12_penalty, pcap_submetrics_vs_l3, timeseries, quadrant)
└── zusammenfassung_prof.pdf  (4-Seiten-Bundle fuer Prof.-Meeting — S.3 nutzt OLD connect_anteil-Caption!)

*= 03_stt_connect_anteil wurde am 2026-05-26 gefixt (Bug in Anteils-Formel)
```

Convention: `save_figure(fig, 'NN_name')` legt automatisch `figures/NN_<topic>/png+pdf/` an (Logik in `_helpers.py:_TOPIC_DIRS`). NB 07 hat noch keinen Ordner — wird beim ersten `save_figure` automatisch erzeugt.

---

## AWS EC2 (nur bei Bedarf)

| Eigenschaft | Wert |
|-------------|------|
| Instance ID | `i-045a2d0eeb338b290` |
| Typ | t3.small (2 vCPU, 2 GB RAM) |
| Region | eu-central-1 (Frankfurt) |
| Status | **STOPPED** (seit 2026-05-24) |
| SSH | `ssh -i ~/.ssh/thesis-key.pem ubuntu@<aktuelle-IP-nach-Start>` |
| Repo | `~/thesis` (via SSH Deploy Key, Push-berechtigt) |
| Start | `aws ec2 start-instances --instance-ids i-045a2d0eeb338b290 --region eu-central-1` |
| Stop  | `aws ec2 stop-instances  --instance-ids i-045a2d0eeb338b290 --region eu-central-1` |

Fuer NB 07 wird EC2 **nicht** benoetigt — alle Daten lokal vorhanden. EC2 wird erst wieder fuer **Phase 11 (E2E-Validierung, manuelle Pipeline-Runs)** gestartet.

---

## Offene Schritte (Roadmap bis Thesis)

1. ~~NB 00-06 + Aufbereitungs-Fix + Bug-Fix~~ — erledigt (2026-05-26)
2. **NB 07 E2E-Pipeline** — **NAECHSTE AUFGABE** (nach Verifikations-Checkliste)
3. Drei Kleinaufgaben: Commit, Prof-PDF, README (siehe oben)
4. **Phase 11 — E2E-Validierung** (manuelle Pipeline-Runs auf EC2, 1 Tag — Sanity-Check gegen Modell)
5. **Phase 12 — Thesis schreiben** (~3-4 Wochen)

---

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Projektkontext, Forschungsfrage, Messdesign |
| `HANDOFF.md` | **Diese Datei** — aktueller Arbeitsstand |
| `analysis/README.md` | Quick-Reference aller Notebooks + Befunde (ggf. veraltet — Stand vor NB 04-06) |
| `data/processed/known_anomalies.md` | **Pflichtlektuere** vor jedem neuen NB |
| `notes/analysis_plan.md` | Master-Plan Phase 10 (NB 07 in §6) |
| `notes/implementation_plan.md` | Vollstaendige Checkliste (Phase 0-12) |
| `notes/cost_analysis.md` | Kostenanalyse pro Provider |
| `notes/briefing_prof.md` | Briefing fuer Prof. Waehlisch (Was/Warum/Wie) |
| `notes/vorbereitung_treffen_20260505.md` | Vorbereitung Prof-Meeting (untracked) |
| `data/process_raw_data.py` | Roh → processed Aufbereitung (am 24.05. gefixt) |
| `analysis/_helpers.py` | Provider-Map, Farben, Datenlader, `save_figure`, `save_table` |
| `analysis/_pcap_helpers.py` | tshark-Wrapper + ASN-Lookup via Cymru |
| `measurements/layer3/stt_*.py` | **Wichtig fuer Semantik:** `connect_ms` und `ttft_ms` sind sequenziell |
| `measurements/layer3/llm_*.py` und `tts_*.py` | `connect_ms` via separate Verbindung; `ttft/ttfa` enthaelt Connect der echten Verbindung |
| `data/layer2/analysis_summary.json` | PCAP-Submetriken alle 9 Provider |
| `data/layer1_extra/` | TLS/TCP-Ping/DNSSEC Ersatzmess (Kampagnen-TLS war NaN) |
| `analysis/tables/0[3-6]_*.csv` | Statistik-Tabellen aller fertigen NBs |

---

## Wichtige Konventionen

- **Notebooks ausfuehren:** aus `analysis/`-Ordner mit
  ```
  python -m jupyter nbconvert --to notebook --execute <nb>.ipynb --inplace
  ```
- **Plots speichern:** immer `save_figure(fig, 'NN_name')` (PNG + PDF, automatisches Topic-Routing)
- **Tabellen speichern:** immer `save_table(df, 'NN_name')` (CSV)
- **Provider-Identifier:** konsistent `deepgram`, `revai`, `azure`, `openai`, `groq`, `mistral` (kein `_tts`/`_stt`-Suffix). Falls Daten anders kommen: `API_RENAME` in `process_raw_data.py` oder direkt im Helper.
- **`api`-Spalte vs `endpoint`:** Layer 3 hat `api`, Layer 1 hat `endpoint`. Joinschluessel via `PROVIDER_TO_ENDPOINT` in `_helpers.py`.
- **Bei jedem neuen NB:** zuerst `known_anomalies.md` lesen, am Ende §X "Hauptbefunde" befuellen, Outputs in `figures/` + `tables/`.
- **NB-03-Methodik-Faustregel:** `ttft_ms` (STT) ist **post-connect**. `ttft_ms` (LLM) und `ttfa_ms` (TTS) sind **connect-inclusive** (separate Connect-Messung in den Modulen). Daher bei STT immer `connect + ttft` als Gesamt-Latenz, bei LLM/TTS ist `ttft`/`ttfa` schon das User-perceived Total.

---

## Memory-Hinweise (User-Profil)

- User ist **Anton Rusik**, Bachelorstudent, Betreuer Prof. Waehlisch (TU Dresden). Hauptkritik vom 09.04.: "Methodik unklar".
- **Kein Coding-/Netzwerk-Background** — Antworten auf Deutsch, technische Konzepte immer mit kurzem "Warum" erklaeren.
- Antworten knapp halten, keine ueberfluessigen Zusammenfassungen am Ende.
- Bei Git-Operationen: User macht Commits oft selbst, daher Vorschlag formulieren statt direkt `git commit` ausfuehren.
- Heute ist **2026-05-26**.
