# Analyse-Plan (PRP) — Bachelorarbeit

> Erstellt: 2026-05-22 | Status: vor Analyse-Phase, Datenaufbereitung abgeschlossen
>
> Dieses Dokument ist die Arbeitsgrundlage fuer die gesamte Analyse-Phase.
> Es ist so geschrieben, dass eine neue Session damit nahtlos weiterarbeiten kann —
> alle relevanten Dateipfade, Methoden, erwartete Outputs und offene Fragen sind hier.

---

## 1. Kontext (Wer das hier liest)

Die Messkampagne ist abgeschlossen. 18 Tage Cold-Start-Messungen aus AWS EC2 Frankfurt
gegen 9 kommerzielle Cloud-AI-APIs (STT, LLM, TTS). Die Rohdaten sind in `data/processed/`
aufbereitet (Parquet/CSV). Die EC2-Instanz ist gestoppt, alle Analysen laufen lokal.

**Forschungsfrage:** Welche Netzwerk- und Infrastruktureigenschaften erklaeren die
Latenzunterschiede zwischen Providern, und wie wirkt die Providerwahl auf die
sequentielle Voice-Pipeline-Latenz?

**Kernbefund-Hypothese:** `ping_avg_ms × N_RTTs ≈ connect_ms` — Layer-1-Messungen
sagen Layer-3-Verbindungsaufbau voraus, wobei `N_RTTs` providerspezifisch ist
(WebSocket vs. HTTPS, Anycast vs. EU-direkt).

---

## 2. Datengrundlage

### Verarbeitete Daten (Analyse-Eingaben)
```
data/processed/
├── layer3_stt.parquet       43.910 Zeilen — deepgram, revai, azure
├── layer3_llm.parquet       38.677 Zeilen — openai, groq, mistral
├── layer3_tts.parquet       43.933 Zeilen — deepgram, openai, azure
├── layer3_errors.parquet     5.704 Zeilen — alle Fehlerzeilen
├── layer1_ping.csv             728 Zeilen — RTT alle 6h, 9 Endpoints
├── layer1_dns.csv              819 Zeilen — DNS alle 6h, 9 Endpoints
├── layer1_tls.csv              162 Zeilen — TLS-Handshake taeglich
└── layer1_traceroute.csv       162 Zeilen — Traceroute taeglich
```

### Rohdaten (nicht direkt verwenden — nur fuer Spotchecks)
```
data/layer3/         145 JSONL-Dateien — Layer-3 Rohmessungen
data/layer1/          91 JSONL-Dateien — Layer-1 Rohmessungen
data/layer2/          10 PCAP-Dateien + 1 analysis_summary.json
data/raw_backup/      Backup aller Rohdaten (nicht im Git)
```

### Wichtige Detailpunkte zu den Daten

- **Groq:** 9.452 erfolgreiche Messungen von 14.382, 34% HTTP 429 (Rate Limit). Fehler
  sind gleichmaessig ueber alle Slots verteilt (67/100 pro Slot konstant), nichts fehlt
  systematisch. Befund: Free-Tier-Limit ist Teil der Providercharakterisierung.
- **Mistral:** 4.3% Fehler, ebenfalls gleichmaessig verteilt.
- **Alle anderen:** ~0% Fehler.
- **Zeitabdeckung:** 145 Slots ohne Luecken, 2026-05-04 12:00 UTC bis 2026-05-22 12:00 UTC.
- **`run`-Spalte** in den Layer-3-Dateien: laufende Nummer innerhalb eines Slots,
  fuer Warm-up-/Drift-Analyse.

---

## 3. Provider-Mapping (Joinschluessel fuer Cross-Layer-Analysen)

```python
PROVIDER_TO_ENDPOINT = {
    # STT
    ("STT", "deepgram"): "api.deepgram.com",
    ("STT", "revai"):    "api.rev.ai",
    ("STT", "azure"):    "italynorth.stt.speech.microsoft.com",
    # LLM
    ("LLM", "openai"):   "api.openai.com",
    ("LLM", "groq"):     "api.groq.com",
    ("LLM", "mistral"):  "api.mistral.ai",
    # TTS
    ("TTS", "deepgram"): "api.deepgram.com",
    ("TTS", "openai"):   "api.openai.com",
    ("TTS", "azure"):    "italynorth.tts.speech.microsoft.com",
}
```

Diese Map kommt in ein Helper-Modul `analysis/_helpers.py`, damit alle Notebooks
sie gleich nutzen.

---

## 4. Werkzeuge

### Bereits installiert
- Python 3.12, pandas 2.x, pyarrow

### Noch zu installieren
- `jupyter`, `matplotlib`, `seaborn`, `scipy` — Notebook + Plots + Statistik
- `dnspython` — fuer DNSSEC-Checks (Punkt 1 vom Prof)
- `tshark` (Wireshark-Installation) — fuer PCAP-Analyse (Punkt 5+6 vom Prof).
  Auf Windows: Wireshark.org installieren, `tshark.exe` muss in PATH sein.
- Optional: `pyasn` oder `ipinfo` Python-Client — fuer ASN-Lookups in der
  Kommunikationsmatrix. Alternative: einmaliges Skript mit curl gegen ipinfo.io.

### Installations-Befehl
```bash
pip install jupyter matplotlib seaborn scipy dnspython
# tshark: Wireshark separat ueber wireshark.org/download installieren
```

---

## 5. Notebook-Struktur (Uebersicht)

> Status-Stand 2026-05-24: 4 von 8 Notebooks fertig. Detail-Befunde siehe `analysis/README.md`.

```
analysis/
├── _helpers.py                          [FERTIG] Provider-Map, Farben, Lader
├── _pcap_helpers.py                     [FERTIG] tshark + ASN-Lookup
├── 00_data_quality.ipynb                [FERTIG] Sanity-Check, 4 Bugs gefixt
├── 01_layer1_infrastructure.ipynb       [FERTIG] DNS/Ping/TLS/TR/DNSSEC
├── 02_pcap_communication.ipynb          [FERTIG] IPs/ASNs/Submetriken/Heatmap
├── 03_layer3_stt.ipynb                  [FERTIG] STT — Deepgram bester, Azure langsamster
├── 04_layer3_llm.ipynb                  [OFFEN]  LLM-Vergleich + Token-Rate
├── 05_layer3_tts.ipynb                  [OFFEN]  TTS-Vergleich
├── 06_cross_layer_correlation.ipynb     [OFFEN]  Kernbefund (Direkt vs Cloudflare-fronted)
└── 07_e2e_pipeline.ipynb                [OFFEN]  27 Kombinationen, 1-Sek-Budget
```

Empfohlene Reihenfolge: **00 → 01 → 02 → 03 → 04 → 05 → 06 → 07**.
Begruendung: Each Notebook nutzt Ergebnisse der vorherigen. Die Layer-3-Kategorien
(03/04/05) sind untereinander unabhaengig und koennen parallelisiert werden.

---

## 6. Detail-Plan pro Notebook

### Notebook 00 — Data Quality

**Ziel:** Sicherstellen, dass die processed-Dateien sauber und konsistent sind, bevor
wir damit arbeiten.

**Eingaben:** Alle Dateien in `data/processed/`

**Checks:**
- Anzahl Zeilen pro Provider — passt zu erwartetem Volumen?
- Zeitstempel-Bereich — alle 18 Tage abgedeckt?
- Missing Values pro Spalte
- Numerische Wertebereiche plausibel? (z.B. `connect_ms ∈ [1, 5000]`,
  `ttft_ms > connect_ms` immer wahr?)
- Verteilung der Fehler nach Provider und Stunde
- `run`-Sequenz pro Slot vollstaendig?

**Ausgabe:** Ein Notebook mit knapper Tabelle "alles OK / Auffaelligkeiten",
keine Grafiken fuer die Thesis — nur Validierung.

---

### Notebook 01 — Layer 1 Infrastruktur

**Ziel:** Charakterisiere die Netzwerk-Infrastruktur zu jedem der 9 Endpoints aus
EC2-Frankfurt-Sicht. Liefert den "Layer-1-Baseline" gegen den Layer 3 verglichen wird.

**Eingaben:**
- `data/processed/layer1_ping.csv`
- `data/processed/layer1_dns.csv`
- `data/processed/layer1_tls.csv`
- `data/processed/layer1_traceroute.csv`

**Analysen:**

**1.1 Ping-RTT-Charakterisierung**
- Pro Endpoint: Median, Min, Max, Std der RTT ueber 18 Tage
- Tabelle: Endpoint × Region-Hypothese × gemessene RTT
- Plot: Boxplot RTT pro Endpoint, sortiert nach Median
- **Wichtig:** Rev.ai blockiert ICMP (`packet_loss=100`) — Plot beruecksichtigt das
- Plot: RTT-Zeitreihe pro Endpoint ueber 18 Tage — Stabilitaet?

**1.2 DNS / Anycast-Analyse**
- Pro Endpoint: Wie oft wechselt die primaere IP ueber 18 Tage?
- Deepgram (Anycast) sollte rotieren, andere stabil
- Tabelle: Endpoint × unique IPs × `anycast_likely`

**1.3 TLS-Handshake-Zeit**
- Pro Endpoint: Median Handshake-Zeit
- Korrelation mit Ping-RTT (TLS = ~1 RTT)
- Tabelle: Endpoint × handshake_ms × tls_version

**1.4 Traceroute / ASN-Analyse**
- Pro Endpoint: AS-Path, Hop-Count, geografisches Routing
- Tabelle: Endpoint × AS-Path × destination_reached
- Identifiziere Transit-Netze (z.B. AS6461 Zayo)

**1.5 DNSSEC (Prof-Punkt 1)**
- Einmal-Skript: `dig +dnssec <endpoint>` fuer alle 9 Endpoints
- Pruefen ob DNSSEC-Records (DS, RRSIG) vorhanden sind
- Tabelle: Endpoint × DNSSEC-Status (aktiv/inaktiv) × Validierungslatenz-Estimate

**Ausgaben fuer die Thesis:**
- Tabelle: "Infrastruktur-Profil der 9 Endpoints" (RTT, IPs, TLS, ASN, DNSSEC)
- Plot: Ping-RTT-Verteilung (Boxplot)
- Plot: RTT-Zeitreihe ueber 18 Tage

---

### Notebook 02 — PCAP & Kommunikationsmatrix (Prof-Punkte 5+6)

**Ziel:** Aus den 9 PCAP-Dateien alle kontaktierten IPs extrahieren, ASN-mappen,
und eine Kommunikationsmatrix erstellen, die zeigt welche Infrastruktur tatsaechlich
hinter jedem Provider steckt.

**Eingaben:** 9 PCAP-Dateien in `data/layer2/capture_*_20260504_1125.pcap`

**Voraussetzung:** `tshark` installiert.

**Vorgehen:**

**2.1 IP-Extraktion mit tshark**
- Pro PCAP: `tshark -r file.pcap -T fields -e ip.dst -e ip.src -e tcp.dstport -e _ws.col.Protocol`
- Filter: nur ausgehende Verbindungen von der EC2-IP
- Pro Provider: Liste aller unique Destination-IPs + Paketanzahl

**2.2 ASN-Lookup**
- Fuer jede unique IP: ASN und ASN-Name nachschlagen
- Quelle: ipinfo.io API (kostenlos, 50k requests/Monat) oder lokale pyasn-DB
- Tabelle: IP → ASN → ASN-Name → Land

**2.3 Submetriken pro Provider (aus bestehender analysis_summary.json + Verfeinerung)**
- TCP-Handshake-Zeit (1 RTT)
- TLS-Handshake-Zeit
- "App-Data-Start" — Zeit bis erste Application-Layer-Bytes (WebSocket-Upgrade /
  HTTP-Response-Header)
- Anzahl Protokoll-RTTs bis Verbindung sendebereit

**2.4 Kommunikationsmatrix**
- Heatmap: 9 Provider × N angetroffene ASNs
- Zellen-Farbe: Paketanzahl (logarithmisch) oder binaer (kontaktiert ja/nein)
- Erwartete Erkenntnisse:
  - Welche Provider nutzen CDNs? (Cloudflare AS13335, Fastly AS54113, Akamai)
  - Sitzt OpenAI/Mistral wirklich wo sie behaupten?
  - Welche Provider haben Multi-IP-Architektur (Anycast)?

**2.5 Andere IPs / Nebenkommunikation (Prof-Punkt 5)**
- Pro Provider: Gibt es IPs ausserhalb der Haupt-Verbindung? (z.B. Auth-Server,
  Telemetrie-Endpoints, CDN-Assets)
- Tabelle: Provider × IP × Funktion (Vermutung aus Port/Reverse-DNS)

**Ausgaben fuer die Thesis:**
- Tabelle: Pro Provider die wichtigsten ASNs + Funktion
- **Plot: Kommunikationsmatrix als Heatmap (Provider × ASN)** — Schluesselgrafik
- Tabelle: Submetriken-Aufschluesselung von `connect_ms` (TCP/TLS/App-Data)
- Diskussion: Wo geht der "EU-Traffic" wirklich hin?

---

### Notebook 03 — Layer 3 STT

**Ziel:** STT-Provider miteinander vergleichen, Latenz-Charakteristika herausarbeiten,
Erklaerungen liefern.

**Eingaben:** `data/processed/layer3_stt.parquet`

**Analysen:**

**3.1 Deskriptive Statistik**
- Pro Provider: p50/p90/p95/p99/Mean/Std fuer `connect_ms`, `send_ms`, `ttft_ms`, `total_ms`
- Tabelle als Hauptergebnis

**3.2 Verteilungen visualisieren**
- **Violin-Plot:** Verteilung `ttft_ms` pro Provider — zeigt Median + Bimodalitaet
- **CDF-Plot:** Kumulative Verteilung — sofort ablesbar "X% der Calls unter Y ms"
- **Box-Plot:** Robuste Vergleichsdarstellung mit Whiskers

**3.3 Zeitliche Stabilitaet**
- **Heatmap:** Median `ttft_ms` nach Stunde (0-23) × Wochentag (Mo-So) pro Provider
- **Linienplot:** Median `ttft_ms` ueber die 18 Tage — Drift erkennbar?

**3.4 Warm-up-Analyse**
- Scatter: `run`-Nummer (0-99) innerhalb Slot vs `ttft_ms` — werden spaetere
  Messungen schneller? (TCP-Caching, DNS-Caching auf EC2-Seite)
- Erwartung: Sollte konstant sein, weil neue TCP-Verbindung pro Run

**3.5 connect_ms vs ttft_ms**
- Scatter: Wie stark dominiert die Verbindungsphase die Gesamtlatenz?
- Pro Provider: Anteil `connect_ms / ttft_ms`

**Ausgaben fuer die Thesis:**
- Statistik-Tabelle (p50/p95/p99 pro Provider)
- Violin- oder CDF-Plot der TTFT-Verteilungen
- Heatmap zeitlicher Stabilitaet
- Befund: Wer ist schnellste/langsamste STT-API, warum?

---

### Notebook 04 — Layer 3 LLM

**Ziel:** Analog zu STT, mit LLM-spezifischen Eigenheiten.

**Eingaben:** `data/processed/layer3_llm.parquet`

**LLM-Besonderheiten:**
- `ttft_ms` = Time to First Token
- `ttl_ms` = Time to Last Token (gesamte Antwortdauer)
- `headers_ms` = Zeit bis HTTP-Response-Header (vor SSE-Stream-Start)
- Daraus berechnen: **Token-Rate** = `output_tokens / (ttl - ttft)`

**Analysen:**

**4.1 Deskriptive Statistik** — wie 3.1, plus `ttl_ms` und Token-Rate

**4.2 Verteilungen** — wie 3.2 fuer `ttft_ms` und `ttl_ms`

**4.3 Token-Rate-Vergleich**
- Groq sollte hier extrem stark sein (LPU-Hardware)
- Box-Plot: Token-Rate pro Provider
- Tabelle: Median Token-Rate

**4.4 Zeitliche Stabilitaet** — wie 3.3

**4.5 Fehleranalyse (wichtig fuer Groq)**
- Plot: Erfolgsrate pro Slot ueber 18 Tage — konstant 67/100 fuer Groq?
- Diskussion: Free-Tier-Rate-Limit als Produktcharakteristik

**4.6 Modellgroessen-Kontext**
- Tabelle: Provider × Modell × ungefaehre Parameter-Anzahl × beobachtete Latenz
- Interpretation: Ist OpenAIs hoehere Latenz durch groesseres Modell erklaerbar?

**Ausgaben fuer die Thesis:**
- Statistik-Tabelle (incl. Token-Rate)
- Verteilungs-Plot
- Erfolgsraten-Plot (Groq-Phaenomen)
- Diskussion: Latenz vs Modellgroesse vs Hardware

---

### Notebook 05 — Layer 3 TTS

**Ziel:** Analog zu STT, mit TTS-spezifischen Eigenheiten.

**Eingaben:** `data/processed/layer3_tts.parquet`

**TTS-Besonderheiten:**
- `ttfa_ms` = Time to First Audio — Streaming-relevant
- `total_ms` = Gesamtdauer bis Audio vollstaendig
- Audio-Bytes sind in Roh aber nicht in processed (kann ergaenzt werden falls noetig)

**Analysen:**

**5.1 Deskriptive Statistik** — Fokus auf `ttfa_ms`

**5.2 Verteilungen** — Violin, CDF, Box-Plot

**5.3 connect_ms-Anteil**
- TTS hat die kuerzesten total_ms — wie gross ist der Verbindungs-Overhead?
- Pro Provider: `connect_ms / ttfa_ms` Verhaeltnis

**5.4 Zeitliche Stabilitaet** — wie 3.3

**5.5 Azure-Phaenomen**
- Azure TTS Italy North hat den niedrigsten `ttfa_ms` aller Provider
- Plot/Diskussion: Ist das Netzwerk-Effekt (EU-Region) oder Engine-Effekt?
- Vergleich `ttfa - connect`: Wenn Verarbeitungszeit aehnlich → Netzwerk-Effekt

**Ausgaben fuer die Thesis:**
- Statistik-Tabelle
- Verteilungs-Plot
- Diskussion: Warum ist EU-TTS so viel schneller?

---

### Notebook 06 — Cross-Layer-Korrelation (KERNBEFUND, Prof-Punkt 4)

**Ziel:** Die Hauptthese der Arbeit empirisch belegen: Layer-1-Messungen erklaeren
Layer-3-Verhalten. Provider-spezifische `N_RTTs` aus Layer 2 fliessen ein.

**Eingaben:**
- `data/processed/layer1_ping.csv`
- `data/processed/layer3_stt|llm|tts.parquet` (alle drei)
- `data/layer2/analysis_summary.json` (fuer N_RTTs pro Provider)

**Analysen:**

**6.1 Layer 1 × Layer 3 — primaere Korrelation**
- Pro Provider: Aggregiere Layer-1-Ping (Median pro Tag) und Layer-3-`connect_ms`
  (Median pro Tag)
- **Scatterplot:** X-Achse `ping_avg_ms × N_RTTs`, Y-Achse `connect_ms`
- Erwartung: Punkte auf Diagonale (y=x), Abweichungen sind providerspezifisch
- Berechne R² und Regressionssteigung pro Provider und global
- **Tabelle:**
  | Provider | Ping (Median) | N_RTTs | Erwartet | Gemessen | Differenz | Erklaerung |
  |----------|--------------|--------|----------|----------|-----------|------------|

**6.2 Layer 2 × Layer 3 — Submetriken-Validierung**
- Pro Provider: PCAP-Submetriken `tcp_hs + tls_hs + proto_setup` vs Layer-3 `connect_ms`
- **Stacked-Bar:** Pro Provider die Submetriken stapeln + gemessene `connect_ms` daneben
- Pruefe: Summieren die Submetriken zu `connect_ms`?

**6.3 Provider-Klassifikation**
- 2D-Plot: X = Ping-RTT (Netzwerk), Y = `connect_ms - ping×N_RTTs` (Server-Overhead)
- Vier Quadranten:
  - Niedriges Ping + niedriger Overhead: optimal (Azure EU)
  - Niedriges Ping + hoher Overhead: Server-Bottleneck
  - Hohes Ping + niedriger Overhead: Distanz-Problem
  - Hohes Ping + hoher Overhead: schlechteste Kombination (Rev.ai?)

**6.4 Vorhersage-Test**
- Modell: `connect_ms_pred = ping × N_RTTs + base_overhead`
- Berechne MAE und MAPE pro Provider
- **Wenn Korrelation hoch:** Layer-1-Messungen sagen Layer-3-Performance vorher
  → praktischer Mehrwert fuer Provider-Auswahl ohne API-Test

**Ausgaben fuer die Thesis:**
- **Haupt-Scatterplot der Korrelation** — die zentrale Grafik der Arbeit
- Stacked-Bar mit Submetriken
- Quadranten-Plot der Provider-Klassifikation
- R²-Tabelle und Interpretation

---

### Notebook 07 — End-to-End-Pipeline

**Ziel:** Die sequentielle Voice-Pipeline (STT → LLM → TTS) latenzmaessig durchrechnen
und zeigen, wie die Providerwahl die Gesamtlatenz beeinflusst.

**Eingaben:** `layer3_stt.parquet`, `layer3_llm.parquet`, `layer3_tts.parquet`

**Analysen:**

**7.1 Pipeline-Modell**
- E2E-Latenz = `stt_ttft + stt_processing + llm_ttft + llm_processing + tts_ttfa`
- Vereinfachung: E2E ≈ `stt_total + llm_ttft + tts_ttfa` (User hoert wann das erste Audio kommt)
- Berechne fuer alle 27 Kombinationen (3 STT × 3 LLM × 3 TTS) den Median und p95

**7.2 Beste/Schlechteste Pipeline**
- **Tabelle:** Top 5 schnellste Kombinationen, Top 5 langsamste
- **Stacked-Bar:** Top 5 Pipelines — Beitrag jedes Layers zur Gesamtlatenz

**7.3 1-Sekunden-Budget**
- Das 1-Sekunden-Budget fuer Voice-Interaktion (Industry-Standard)
- Wie viele Kombinationen liegen unter 1s am Median? Am p95?
- **Plot:** Horizontale Balken, sortiert, mit 1s-Linie markiert

**7.4 Bottleneck-Analyse**
- Pro Pipeline: Welcher Layer dominiert? Wo ist Optimierungspotenzial?
- Wenn LLM dominiert: Modell-Wechsel hilft mehr als Provider-Wechsel
- Wenn Connect-Phase dominiert: EU-Hosting hilft

**7.5 Realitaetscheck**
- Sequentielle Addition ist Obergrenze (echte Pipelines koennen parallelisieren).
- Validierung durch manuelle Pipeline-Runs (Phase 11 im implementation_plan).

**Ausgaben fuer die Thesis:**
- Vollstaendige 27-Zeilen-Tabelle der Kombinationen
- Top-/Bottom-5-Vergleich
- 1-Sekunden-Budget-Plot
- Empfehlung: Welche Provider-Kombination fuer EU-User?

---

## 7. Prof-Punkte → Notebook-Zuordnung

| Prof-Punkt | Wo behandelt | Status |
|------------|--------------|--------|
| 1. DNSSEC | NB 01, §5 + `data/layer1_extra/dnssec.csv` | **erledigt** (0/6 Hauptzonen signiert) |
| 2. Visualisierungen | NB 01-03 fertig (13 Plots), NB 04-07 ausstehend | teilweise erledigt |
| 3. Rohdaten aufbereiten | `data/process_raw_data.py` (am 24.05. zusaetzlich gefixt) | erledigt |
| 4. Gegenpruefen | NB 00 (Quality), NB 02 (TLS Cross-Check PCAP vs Lokal) | teilweise erledigt — NB 06 fehlt |
| 5. Andere IPs in PCAP | NB 02, §3 | **erledigt** (0/9 mit Nebenkommunikation) |
| 6. Kommunikationsmatrix | NB 02, §2 + `figures/02_communication_matrix.pdf` | **erledigt** |

**Bonus-Befunde aus dieser Phase (ueber Prof-Punkte hinaus):**
- Cloudflare-Fronting fuer 4/9 Provider (DNS + PCAP-Bestaetigung)
- Rev.ai TLS 1.2 als einziger Provider → +140 ms Connect-Overhead-Erklaerung
- STT-Engine schlaegt Netzwerk-Region: Deepgram-Nova-3 in US schlaegt Azure-Italy

---

## 8. Offene Fragen / Entscheidungen waehrend der Analyse

Diese Fragen lassen sich erst beim Plotten/Analysieren beantworten:

1. **Mistral als "EU-Provider":** Stellt sich raus, dass Mistral durch US-CDN
   geroutet wird? Dann ist das ein wichtiger Befund.
2. **OpenAI/Microsoft-Verflechtung:** Faehrt OpenAI-Traffic durch Azure-ASNs?
   Das waere ein Architektur-Hinweis.
3. **Anycast-Routing-Stabilitaet:** Wechselt Deepgrams IP nur zwischen Messungen
   (alle 6h Layer 1) oder auch innerhalb von Slots?
4. **TLS 1.3 vs 1.2:** Nutzen alle Provider TLS 1.3? Hat das messbare Latenz-Auswirkung?
5. **`N_RTTs` Definition:** Aus PCAP-Analyse messbar als "Anzahl Roundtrips bis erste
   App-Data nach Connect", aber bei WebSocket vs HTTPS unterscheidet sich was als
   "ready" zaehlt. Pro Provider in NB 02 sauber definieren.

---

## 9. Datei-Outputs der Analyse

Am Ende der Analyse sollten existieren:

```
analysis/
├── figures/                         Alle Plot-Exports (PNG + PDF, beides!)
│   ├── 01_ping_rtt_boxplot.{png,pdf}
│   ├── 01_dns_anycast_table.{png,pdf}
│   ├── 02_communication_matrix.{png,pdf}      <- Schluesselgrafik
│   ├── 02_submetrics_stacked.{png,pdf}
│   ├── 03_stt_violin.{png,pdf}
│   ├── 04_llm_token_rate.{png,pdf}
│   ├── 04_groq_error_rate.{png,pdf}
│   ├── 05_tts_cdf.{png,pdf}
│   ├── 06_cross_layer_scatter.{png,pdf}       <- Kernbefund
│   ├── 06_provider_quadrants.{png,pdf}
│   ├── 07_e2e_pipeline_ranking.{png,pdf}
│   └── 07_one_second_budget.{png,pdf}
└── tables/                          Alle Tabellen als CSV/LaTeX
    ├── 01_infrastructure_profile.csv
    ├── 02_asn_mapping.csv
    ├── 03_stt_statistics.csv
    ├── 04_llm_statistics.csv
    ├── 05_tts_statistics.csv
    ├── 06_correlation_results.csv
    └── 07_pipeline_combinations.csv
```

**Konvention:** Alle Plots in PNG (Notebook-Vorschau) und PDF (Thesis-Embed)
exportieren — `plt.savefig(..., bbox_inches='tight')` mit beiden Formaten.

---

## 10. Fuer die naechste Session

**Wenn du diese Datei liest und gerade keinen Kontext hast:**

1. Pruefe Tooling: `pip install jupyter matplotlib seaborn scipy dnspython`, dann
   `tshark --version` testen (falls Fehler: Wireshark installieren).
2. Schaue in `HANDOFF.md` fuer den allerletzten Stand.
3. Wenn noch kein Notebook existiert: Starte mit `00_data_quality.ipynb`
   (Reihenfolge oben).
4. Wenn Notebooks teilweise existieren: Pruefe welches als letztes
   bearbeitet wurde (Modified Date) und fahre dort fort.
5. Diese Datei ist der Master-Plan. Aenderungen am Plan hier eintragen,
   damit naechste Sessions konsistent weitermachen.

**Status-Tracking pro Notebook:** Wenn ein Notebook abgeschlossen ist,
in HANDOFF.md aufnehmen mit dem Hauptbefund (1 Satz).

---

## 11. Was nicht in diesem Plan steht

- **Schreibphase:** Wird separat geplant, wenn Analyse fertig ist (~3 Wochen
  vor Abgabe).
- **E2E-Validierung:** Manuelle Pipeline-Runs zur Verifikation der rechnerischen
  Addition (Phase 11 im implementation_plan.md). Wird nach NB 07 angesetzt.
- **Layer-2-Tiefenanalyse fuer weitere Slots:** Wir haben nur einen PCAP-Slot
  pro Provider (vom 2026-05-04). Falls die Analyse Inkonsistenzen zeigt, koennte
  ein zweiter Capture-Lauf sinnvoll sein — EC2 dafuer nochmal hochfahren.
