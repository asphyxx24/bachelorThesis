# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-24 (Session: NB 00-03 + Aufbereitungs-Fix + Layer-1-Ersatzmessungen)

## TL;DR

Phase 10 (Analyse) zu 50 % fertig. 4 von 8 Notebooks abgeschlossen: 00 (Data Quality), 01 (Layer-1), 02 (PCAP), 03 (STT). Datenpipeline ist nach Bug-Fix sauber (0 % NaN). Drei zentrale Befunde, die ueber die urspruengliche Forschungsfrage hinausgehen:

1. **Cloudflare-Fronting** fuer 4/9 Provider (OpenAI/Groq/Mistral LLM + OpenAI TTS) — bricht die Layer-1-zu-Layer-3-Korrelation, weil RTT zum Edge gemessen wird, nicht zum Backend.
2. **Rev.ai TLS 1.2** als einziger Provider → 2-RTT-Handshake erklaert +140 ms Connect-Overhead.
3. **STT-Ueberraschung:** Deepgram (US) ist trotz hoher Connect-Latenz schneller in TTFT als Azure (EU), weil Nova-3-Engine ueberlegene Server-Processing-Zeit hat. "EU = schnell" ist eine naive Annahme.

## WICHTIG fuer naechste Session: Erst nachpruefen, dann weitermachen!

Bevor du an NB 04 (LLM) anfaengst, **arbeite diese Checkliste systematisch ab**:

### Verifikations-Checkliste

```bash
# 1. Tooling — alles installiert?
python --version                # erwartet: 3.12.x
python -c "import pandas, numpy, matplotlib, seaborn, scipy, dns; print('OK')"
"C:/Program Files/Wireshark/tshark.exe" --version | head -1   # erwartet: 4.6.x
aws --version                   # fuer EC2-Operationen, falls noetig

# 2. Datenintegritaet pruefen
python -c "
import pandas as pd
for f in ['layer3_stt','layer3_llm','layer3_tts','layer3_errors']:
    df = pd.read_parquet(f'data/processed/{f}.parquet')
    print(f'{f:20s} {len(df):>7,} Zeilen, NaN in Timing-Cols:',
          df.filter(regex='_ms$').isna().sum().sum())
"
# Erwartete Output:
# layer3_stt          42,016 Zeilen, NaN in Timing-Cols: 0
# layer3_llm          37,734 Zeilen, NaN in Timing-Cols: 0
# layer3_tts          43,489 Zeilen, NaN in Timing-Cols: 0
# layer3_errors        7,261 Zeilen, NaN in Timing-Cols: 0

# 3. Notebooks reproduzierbar — alle 4 fertigen NBs ohne Fehler ausfuehrbar?
cd analysis
for nb in 00_data_quality 01_layer1_infrastructure 02_pcap_communication 03_layer3_stt; do
    echo "=== $nb ==="
    python -m jupyter nbconvert --to notebook --execute ${nb}.ipynb --inplace 2>&1 | tail -2
done

# 4. Befunde-Plausibilitaet — stimmen die Zahlen in der Tabelle ueberein?
python -c "
import pandas as pd
print('=== STT Statistik (sollte mit NB 03 §6 uebereinstimmen) ===')
df = pd.read_csv('analysis/tables/03_stt_statistics.csv')
print(df[df['metric']=='ttft_ms'][['provider','p50','p95']].to_string(index=False))
# Erwartung:
# azure       1718.7  1725.4
# deepgram     587.0   694.2
# revai       1404.1  1547.9
"
```

**Wenn ein Schritt scheitert oder andere Zahlen kommen:** stoppe und kommuniziere mit dem User, bevor du an NB 04 weitergehst. Es koennte ein Daten-Inkonsistenz-Problem geben (z.B. process_raw_data.py wurde neu gelaufen, oder eine Datei wurde modifiziert).

### Was zusaetzlich gegenpruefen
- `analysis/README.md` lesen (Quick-Reference zu allen Notebooks + Befunden)
- `data/processed/known_anomalies.md` lesen (Bugs, Stress-Slots, Layer-1-Caveats)
- `notes/analysis_plan.md` §6 lesen (NB-Konzepte fuer 04-07)
- Spotcheck: oeffne `analysis/03_layer3_stt.ipynb` und schaue dir den Connect-Anteil-Plot (Cell `anteil`) an — der zeigt visuell die Ueberraschung "Azure langsamster trotz EU".

## Stand der Notebooks

| NB | Status | Hauptbefund | Outputs |
|----|--------|-------------|---------|
| 00 Data Quality | FERTIG | 4 Aufbereitungs-Bugs gefixt, 0 % NaN, Rev.ai 10 % Error-Rate aufgedeckt | none (Validierung) |
| 01 Layer-1 | FERTIG | Drei RTT-Klassen, Rev.ai TLS 1.2, 0/6 DNSSEC, Cloudflare-Hypothese | 3 Plots, infrastructure_profile.csv |
| 02 PCAP | FERTIG | Cloudflare 4/9, Null Nebenkommunikation, RTT-Modell bricht bei CDN | 2 Plots, communication_profile.csv |
| 03 STT | FERTIG | Deepgram TTFT schnellster trotz US, Azure langsamster trotz EU | 6 Plots, stt_statistics.csv |
| 04 LLM | OFFEN | (Erwartung: Groq Token-Rate herausragend, OpenAI variabelste) | -- |
| 05 TTS | OFFEN | (Erwartung: Azure schnellster wegen EU + einfacher Engine) | -- |
| 06 Cross-Layer | OFFEN | KERNBEFUND — Direkt vs Cloudflare-fronted getrennt behandeln | -- |
| 07 E2E-Pipeline | OFFEN | 27 Kombinationen, 1-Sek-Budget | -- |

## Aktuelle Fokus-Aufgabe

**Notebook 04: Layer-3 LLM-Vergleich.**

Eingabe: `data/processed/layer3_llm.parquet` (37.734 Erfolge, 3 Provider: openai, groq, mistral)

Spezifika gegenueber NB 03:
- LLM hat zusaetzlich `headers_ms` (TTFB Response-Header) und `ttl_ms` (Time to Last Token)
- **Token-Rate** = `output_tokens / (ttl_ms - ttft_ms)` — Groq sollte hier mit LPU-Hardware extreme Werte zeigen
- **Groq 34,97 % Fehler** (Free-Tier 30 RPM-Limit) als eigener Plot dokumentieren (NICHT als Datenqualitaets-Problem, sondern als Produktcharakteristik)
- **Mistral-Stress-Slots:** 6 Slots mit <50 Runs (HTTP-429). In zeitlicher Stabilitaets-Analyse als Auffaelligkeit markieren

Struktur entsprechend NB 03 (deskriptive Stats → Verteilung → Zeitliche Stabilitaet → Warm-up → Connect-Anteil), plus Token-Rate-Block.

Vorgeschlagene Reihenfolge nach NB 04: 05 (TTS), dann 06 (Cross-Layer, Kernbefund), dann 07 (E2E).

## Session-Historie

### Session 2026-05-24 — Phase 10 Start: NB 00-03 + Aufbereitungs-Fix + EC2-Ersatzmessungen

**Bugs in `data/process_raw_data.py` gefixt** (Details in `known_anomalies.md` §1):
1. Slot-Summary-Zeilen (mit `stats`-Feld) wurden als NaN-Erfolge verbucht → jetzt uebersprungen
2. `error=""` ohne Timing wurde uebersehen (`if '' is falsy`) → jetzt als Error klassifiziert
3. `api`-Naming in errors nicht durch `API_RENAME` (deepgram_tts/openai_tts/azure_tts/azure_stt blieben)
4. Rev.ai-Pings komplett gefiltert wegen ICMP-Block → jetzt mit `packet_loss=100, icmp_blocked=True` enthalten

**EC2 kurz hochgefahren** fuer Layer-1-Ersatzmessungen (TLS-Daten der Kampagne waren 100 % NaN):
- `data/layer1_extra/tls.csv` (7×5) — alle TLS 1.3 ausser Rev.ai (TLS 1.2)
- `data/layer1_extra/ping_tcp.csv` (7×10) — TCP-SYN-Ping, funktioniert auch bei Rev.ai
- `data/layer1_extra/dnssec.csv` (7) — 0 von 6 Hauptzonen DNSSEC-signiert
- Kosten: ~2 Cent fuer 30 Min Laufzeit

**Tools installiert:**
- jupyter, matplotlib, seaborn, scipy, dnspython (via pip)
- Wireshark 4.6 (via winget)

**Notebooks aufgesetzt und durchgelaufen:**
- `analysis/00_data_quality.ipynb` — Validierung der Aufbereitung
- `analysis/01_layer1_infrastructure.ipynb` — Layer-1-Profil pro Endpoint
- `analysis/02_pcap_communication.ipynb` — Kommunikationsmatrix + Submetriken
- `analysis/03_layer3_stt.ipynb` — STT-Vergleich
- Plus zwei Helper: `analysis/_helpers.py`, `analysis/_pcap_helpers.py`

**Drei neue zentrale Befunde fuer die Thesis:**
- Cloudflare-Fronting fuer 4 von 9 Providern (NB 01 DNS-Hypothese, NB 02 ASN-Bestaetigung)
- Rev.ai TLS 1.2 erklaert +140 ms Connect-Overhead exakt (NB 01 lokal, NB 02 PCAP)
- STT: Engine schlaegt Netzwerk — Deepgram-Nova-3 beats Azure-Italy trotz 130 ms RTT-Nachteil

### Session 2026-05-22 — Kampagne stoppen, Analyse-Phase starten
- Kampagne nach 18 Tagen beendet, alle Cron-Jobs entfernt
- EC2 gestoppt (zum ersten Mal)
- PCAP-Dateien lokal gesichert
- `notes/analysis_plan.md` als Master-Plan fuer die Analyse erstellt

### Session 2026-05-04 — Layer-2 Captures + Cross-Layer-Korrelation-Erste-Bestaetigung
- tcpdump + Layer-3-Call fuer alle 9 Provider
- Submetriken extrahiert (TCP-Handshake, TLS, App-Data-Start)
- Bestaetigt: Deepgram 3×102ms ≈ connect_ms, Azure 11ms × ~23 RTTs ≈ connect_ms

### Session 2026-05-03 — AssemblyAI → Rev.ai-Wechsel
- AssemblyAI-Streaming-API verlangt Echtzeit-Pacing → inkonsistent mit Deepgram/Azure
- Wechsel auf Rev.ai (akzeptiert Audio-Dump)
- Diverse Provider-spezifische Fixes (Deepgram TTS Modellname, STT is_final-Loop, etc.)

## Datenmenge (Stand nach Aufbereitungs-Fix)

| Layer | Datei | Zeilen | Anmerkung |
|-------|-------|-------:|-----------|
| L3 | `layer3_stt.parquet` | 42.016 | 3 Provider × ~14k |
| L3 | `layer3_llm.parquet` | 37.734 | OpenAI 14.5k, Mistral 13.8k, Groq 9.4k (Rate-Limit) |
| L3 | `layer3_tts.parquet` | 43.489 | 3 Provider × ~14.5k |
| L3 | `layer3_errors.parquet` | 7.261 | inkl. 1.473 Rev.ai Connection-Failures + 5.070 Groq 429er |
| L1 | `layer1_ping.csv` | 819 | inkl. 91 Rev.ai mit `packet_loss=100` |
| L1 | `layer1_dns.csv` | 819 | |
| L1 | `layer1_tls.csv` | 162 | **leer (NaN), ersetzt durch `data/layer1_extra/tls.csv`** |
| L1 | `layer1_traceroute.csv` | 162 | Azure/Rev.ai 0% reached (UDP-Block) |
| L1-Extra | `data/layer1_extra/tls.csv` | 35 | 7 Endpoints × 5 Runs (24.05.) |
| L1-Extra | `data/layer1_extra/ping_tcp.csv` | 7 | aggregiert (Roh: 70 Pings) |
| L1-Extra | `data/layer1_extra/dnssec.csv` | 7 | 0/6 Zonen signiert |
| L2 | `data/layer2/capture_*.pcap` | 9 Files | Single-Slot 04.05., ~50-200 KB |
| L2 | `data/layer2/analysis_summary.json` | 9 entries | Submetriken pro Provider |

## Kosten

| Provider | Verbraucht | Budget |
|----------|-----------:|-------:|
| Deepgram (STT+TTS) | $21,33 | $200 Guthaben |
| Rev.ai | $10,67 | $10,98 Budget |
| Azure (STT+TTS) | $27,90 | $100 Kredit |
| OpenAI (LLM+TTS) | $8,28 | $10 Prepaid |
| Groq + Mistral | $0 | Free Tier |
| AWS EC2 (Kampagne + Ersatzmess) | ~$13 | $120 Free Credits |
| **Gesamt API** | **~$68** | |

## AWS EC2 Instanz

| Eigenschaft | Wert |
|-------------|------|
| Instance ID | `i-045a2d0eeb338b290` |
| Typ | t3.small (2 vCPU, 2 GB RAM) |
| Region | eu-central-1 (Frankfurt) |
| IP | bei Neustart neue IP (zuletzt 2026-05-24: `63.178.41.35`) |
| Status | **STOPPED** (seit 2026-05-24) |
| SSH | `ssh -i ~/.ssh/thesis-key.pem ubuntu@<aktuelle-IP>` |
| Repo | `~/thesis` (via SSH Deploy Key, Push-berechtigt) |
| Start (AWS CLI) | `aws ec2 start-instances --instance-ids i-045a2d0eeb338b290 --region eu-central-1` |
| Stop (AWS CLI) | `aws ec2 stop-instances --instance-ids i-045a2d0eeb338b290 --region eu-central-1` |

EC2 muss nur noch hochgefahren werden, wenn weitere Vantage-Point-konsistente Messungen noetig sind (z.B. zweiter PCAP-Capture, Validierungs-E2E-Runs).

## Provider-Matrix (FINAL)

| Kategorie | Provider | Modell | Region (behauptet) | Region (real laut NB 02) | Protokoll | TLS |
|-----------|----------|--------|--------------------|--------------------------|-----------|-----|
| STT | Deepgram | Nova-3 | USA (Anycast) | US (AS 12129 / 123NET) | WebSocket | 1.3 |
| STT | Rev.ai | English | USA | US (AS 16509 / AWS Oregon) | WebSocket | **1.2** |
| STT | Azure | Standard Neural | Italien | EU (AS 8075 / Microsoft) | WebSocket | 1.3 |
| LLM | OpenAI | gpt-4o-mini | USA | **AS 13335 / Cloudflare-Edge Frankfurt** | HTTPS+SSE | 1.3 |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | **AS 13335 / Cloudflare-Edge Frankfurt** | HTTPS+SSE | 1.3 |
| LLM | Mistral | mistral-small-2603 | EU/Frankreich | **AS 13335 / Cloudflare-Edge Frankfurt** | HTTPS+SSE | 1.3 |
| TTS | Deepgram | Aura-2 (asteria) | USA (Anycast) | US (AS 12129 / 123NET) | HTTPS Streaming | 1.3 |
| TTS | OpenAI | tts-1 | USA | **AS 13335 / Cloudflare-Edge Frankfurt** | HTTPS Streaming | 1.3 |
| TTS | Azure | Neural (Jenny) | Italien | EU (AS 8075 / Microsoft) | HTTPS Streaming | 1.3 |

## Offene Schritte

1. ~~NB 00-03 + Aufbereitung + Ersatzmessungen~~ — erledigt (2026-05-24)
2. **NB 04 LLM-Vergleich** — **NAECHSTE AUFGABE** (nach Verifikations-Checkliste)
3. **NB 05 TTS-Vergleich**
4. **NB 06 Cross-Layer-Korrelation** (Kernbefund, Direkt/CDN-Klassen separat)
5. **NB 07 E2E-Pipeline** (27 Kombinationen)
6. **E2E-Validierung** (manuelle Pipeline-Runs auf EC2, 1 Tag)
7. **Thesis schreiben** (~3-4 Wochen)

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Projektkontext, Forschungsfrage, Messdesign |
| `HANDOFF.md` | Dieser Arbeitsstand |
| `analysis/README.md` | **Quick-Reference fuer alle Notebooks + Befunde** |
| `data/processed/known_anomalies.md` | **Pflichtlektuere** vor jedem neuen NB |
| `notes/analysis_plan.md` | Master-Plan fuer Phase 10 |
| `notes/implementation_plan.md` | Vollstaendige Checkliste (Phase 0-12) |
| `notes/cost_analysis.md` | Kostenanalyse pro Provider |
| `notes/briefing_prof.md` | Briefing fuer Prof. Waelisch (Was/Warum/Wie) |
| `data/process_raw_data.py` | Roh → processed Aufbereitung (am 24.05. gefixt) |
| `analysis/_helpers.py` | Provider-Map, Farben, Datenlader |
| `analysis/_pcap_helpers.py` | tshark-Wrapper + ASN-Lookup via Cymru |
| `measurements/layer1_extra/` | Ersatzmess-Skripte (TLS, TCP-Ping, DNSSEC) |
| `measurements/layer2/` | PCAP-Capture und -Analyse-Skripte |
| `data/layer1_extra/` | TLS/TCP-Ping/DNSSEC Ergebnisse vom 24.05. |
| `data/layer2/` | 9 PCAP-Dateien + analysis_summary.json |
| `data/processed/` | 4 Parquet (Layer 3) + 4 CSV (Layer 1) + known_anomalies.md |
| `analysis/figures/` | Plot-Exports (PNG + PDF) |
| `analysis/tables/` | Statistik-Tabellen als CSV |

## Wichtige Konventionen

- **Notebooks ausfuehren:** aus `analysis/`-Ordner mit `python -m jupyter nbconvert --to notebook --execute <nb>.ipynb --inplace`
- **Plots speichern:** immer via `save_figure(fig, 'NN_name')` (erzeugt PNG + PDF)
- **Tabellen speichern:** immer via `save_table(df, 'NN_name')` (CSV)
- **Provider-Identifier:** konsistent `deepgram`, `revai`, `azure`, `openai`, `groq`, `mistral` (kein `_tts`/`_stt`-Suffix). Falls Daten anders kommen: `API_RENAME` in `process_raw_data.py` oder direkt im Helper.
- **`api`-Spalte vs `endpoint`:** Layer 3 hat `api`, Layer 1 hat `endpoint`. Joinschluessel via `PROVIDER_TO_ENDPOINT` in `_helpers.py`.
- **Bei jedem neuen NB:** zuerst `known_anomalies.md` lesen, am Ende §X "Hauptbefunde" befuellen, Outputs in `figures/` + `tables/`.
