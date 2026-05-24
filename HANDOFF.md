# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-24 (Session: NB 00 Data Quality + Aufbereitung neu, Ersatzmessungen auf EC2)

## Letzter Stand

**Notebook 00 (Data Quality) abgeschlossen.** Datensatz ist makellos aufbereitet,
alle Anomalien dokumentiert in `data/processed/known_anomalies.md`. EC2 wurde
kurz hochgefahren fuer drei Ersatzmessungen (TLS, TCP-Ping, DNSSEC), danach wieder
gestoppt.

**Datenmenge (nach Aufbereitungs-Fix):**
- Layer 3: 42.016 STT + 37.734 LLM + 43.489 TTS Erfolge + 7.261 Errors
- Layer 1: 819 ping, 819 dns, 162 tls (alt, leer), 162 traceroute
- Layer 1 Extra (neu am 24.05.): tls.csv (7×5), ping_tcp.csv (7×10), dnssec.csv (7)
- Layer 2: 10 PCAP-Dateien (lokal, fuer NB 02)

**Datenqualitaet (nach Fix):**
- 0 % NaN in allen Layer-3-Dateien (vorher 4,3 / 2,4 / 1,0 %)
- Rev.ai STT: **neue Erkenntnis** 10,16 % Fehlerrate (1.473 Connection-Failures
  waren frueher als stille NaN verborgen, jetzt in errors)
- Mistral LLM: 4,79 % Fehler, 6 dokumentierte Stress-Slots
- Groq LLM: 34,97 % Fehler (Free-Tier-RPM-Limit, gleichmaessig verteilt)
- Alle anderen Provider: <0,1 % Fehler

**Kosten (tatsaechlich, 18 Tage):**
- Deepgram (STT+TTS): $21,33 von $200 Guthaben
- Rev.ai: $10,67 von $10,98 Budget
- Azure (STT+TTS): $27,90 von $100 Kredit
- OpenAI (LLM+TTS): $8,28 von $10 Prepaid
- Groq + Mistral: $0 (Free Tier)
- AWS EC2: ~$13 von $120 Free Credits
- **Gesamt API: ~$68**

## Aktuelle Fokus-Aufgabe

**Phase 10: Analyse** — Notebook 00 fertig, Notebook 01 (Layer-1-Infrastruktur)
ist der naechste Schritt. Es kann jetzt die neuen `data/layer1_extra/`-Dateien
ebenso nutzen wie die bestehenden Layer-1-CSVs.

**Master-Plan fuer die Analyse:** `notes/analysis_plan.md`
**Anomalien-Doku (Pflichtlektuere vor jedem neuen NB):** `data/processed/known_anomalies.md`

Voraussetzungen sind erfuellt:
- jupyter, matplotlib, seaborn, scipy, dnspython installiert
- Wireshark/tshark noch offen (erst fuer Notebook 02 noetig)

## Entscheidungen und Fixes

### Session 2026-05-24
- **Notebook 00 (Data Quality)** in `analysis/00_data_quality.ipynb` aufgesetzt und ausgefuehrt.
- **`analysis/_helpers.py`** zentralisiert Provider-Map, Farben, Datenlader fuer alle Notebooks.
- **`data/process_raw_data.py` gefixt** (4 Bugs, siehe `known_anomalies.md` Abschnitt 1):
  - Slot-Summary-Zeilen ueberspringen
  - `error=""` ohne Timing als Error werten
  - `api`-Naming auch in errors via `API_RENAME` normalisieren
  - Rev.ai-Pings mit `packet_loss=100` statt skip
- **EC2 kurz hochgefahren** fuer drei Ersatzmessungen (Layer-1-TLS war zu 100% NaN):
  - `data/layer1_extra/tls.csv` — TLS-Handshake, Versionen, Ciphers, ALPN (7 Endpoints x 5 Runs)
  - `data/layer1_extra/ping_tcp.csv` — TCP-SYN-Ping (funktioniert auch fuer Rev.ai)
  - `data/layer1_extra/dnssec.csv` — DNSSEC-Status pro Zone
  - EC2 danach wieder gestoppt (Kosten ~2 Cent).
- **Neue Befunde aus Aufbereitung + Ersatzmessungen:**
  - Rev.ai STT hat 10,16% Fehlerrate (vorher 0% verborgen in NaN)
  - Rev.ai ist einziger Provider mit **TLS 1.2** statt TLS 1.3 → 2-RTT-Handshake erklaert ~140ms Mehr-Overhead
  - Keiner der 6 Provider-Hauptzonen ist DNSSEC-signiert (Antwort auf Prof-Punkt 1)
  - OpenAI/Groq/Mistral haben 1-2ms RTT aus EC2 Frankfurt → vermutlich Cloudflare-Edge im selben RZ
- **Anomalien-Dokumentation** in `data/processed/known_anomalies.md` — Pflichtlektuere fuer alle nachfolgenden Notebooks.

### Session 2026-05-22
- **Kampagne gestoppt:** Alle Cron-Jobs per `crontab -r` entfernt.
- **Finaler Sync:** 10 Dateien committed und gepusht (commit `093f510`).
- **EC2 gestoppt:** `i-045a2d0eeb338b290` ist im Zustand `stopped`. Analyse laeuft lokal.
- **Groq-Analyse:** Rate-Limiting war konstant (67/100 pro Slot, nicht zufaellig) →
  erklaerbar durch 30-RPM-Limit des Free Tiers; als Befund dokumentierbar.
- **Datenaufbereitung erledigt:** `data/process_raw_data.py` erzeugt 8 saubere
  Dateien in `data/processed/` (4 Parquet fuer Layer 3, 4 CSV fuer Layer 1).
  Backup der Rohdaten in `data/raw_backup/` (lokal, nicht in Git).
- **PCAP-Dateien lokal:** EC2 kurz hochgefahren, alle 9 PCAP-Files
  (`data/layer2/capture_*.pcap`) heruntergeladen, EC2 wieder gestoppt.
- **Prof-Punkte aus Treffen:** DNSSEC, Visualisierungen, Gegenpruefen, andere IPs
  in PCAP, Kommunikationsmatrix — alle in `notes/analysis_plan.md` zugeordnet.
- **Analyse-PRP erstellt:** `notes/analysis_plan.md` ist das Master-Dokument
  fuer die gesamte Analyse-Phase.

### Session 2026-05-04
- **Cron-Fix:** `SHELL=/bin/bash` in Crontab — `source` funktioniert nicht in
  `/bin/sh` (Cron-Default). Cron-Jobs liefen ab 03.05. abends leer, ab 04.05. 12:00 UTC behoben.
- **Layer-2 Captures:** tcpdump + Layer-3-Call fuer alle 9 Provider. Automatisiert
  via `measurements/layer2/capture_all.py`. Analyse via `measurements/layer2/analyze_pcaps.py`.
- **Cross-Layer-Korrelation bestaetigt:** Deepgram: 3×102ms RTT ≈ 310ms ≈ 337ms connect_ms.
  Azure: 11ms RTT × ~23 Protokoll-RTTs ≈ 264ms ≈ 265ms connect_ms.

### Session 2026-05-03
- **AssemblyAI → Rev.ai:** AssemblyAIs Streaming-API erfordert Echtzeit-Pacing,
  was die TTFT-Messung inkonsistent mit Deepgram/Azure machte. Rev.ai akzeptiert
  Audio-Dump → konsistente Methodik ueber alle 3 STT-Provider.
- **chain.py gestrichen:** E2E-Gesamtlatenz wird rechnerisch aus Einzelmessungen
  addiert, nicht separat gemessen. Validierung am Ende durch ein paar manuelle
  Pipeline-Runs.
- **Rev.ai Kosten:** $0.003/min (nicht $0.005 wie urspruenglich geschaetzt).
  3.000 Minuten fuer $9.99 gekauft + $0.99 Free Tier = $10.98 Budget.
- **Deepgram TTS Modell:** `aura-2-asteria-en` (Modellname braucht Voice-Suffix)
- **Deepgram STT Fix:** Server sendet mehrere `is_final`-Segmente. Code sammelt
  jetzt alle Segmente statt beim ersten abzubrechen.
- **Python 3.10 Kompatibilitaet:** `asyncio.timeout` (3.11+) durch `asyncio.wait_for`
  ersetzt, `float | None` Type-Hints entfernt.

## AWS EC2 Instanz

| Eigenschaft | Wert |
|-------------|------|
| Instance ID | `i-045a2d0eeb338b290` |
| Typ | t3.small (2 vCPU, 2 GB RAM) |
| Region | eu-central-1 (Frankfurt) |
| IP | bei Neustart neue IP (zuletzt 2026-05-24: `63.178.41.35`) |
| Status | **STOPPED** (seit 2026-05-24, nach Ersatzmessungen) |
| SSH | `ssh -i ~/.ssh/thesis-key.pem ubuntu@<aktuelle-IP>` |
| Repo | `~/thesis` (via SSH Deploy Key, Push-berechtigt) |

## Provider-Matrix (FINAL)

| Kategorie | Provider | Modell | Region | Protokoll |
|-----------|----------|--------|--------|-----------|
| STT | Deepgram | Nova-3 | USA (Anycast) | WebSocket |
| STT | Rev.ai | English | USA | WebSocket |
| STT | Azure | Standard Neural | Italien (Italy North) | WebSocket |
| LLM | OpenAI | gpt-4o-mini | USA | HTTPS+SSE |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS+SSE |
| LLM | Mistral | mistral-small-2603 | EU/Frankreich | HTTPS+SSE |
| TTS | Deepgram | Aura-2 (asteria) | USA (Anycast) | HTTPS Streaming |
| TTS | OpenAI | tts-1 | USA | HTTPS Streaming |
| TTS | Azure | Neural (Jenny) | Italien (Italy North) | HTTPS Streaming |

## Offene Schritte

1. ~~Alte Kampagne stoppen (ops.papagei.ai)~~
2. ~~Layer-2 Captures auf EC2~~ — erledigt (2026-05-04)
3. ~~Betreuer-Treffen~~ — Dienstag 2026-05-05
4. ~~Kampagne Monitoring~~ — abgeschlossen
5. ~~Kampagne stoppen + EC2 stoppen~~ — erledigt (2026-05-22)
6. ~~NB 00 Data Quality + Aufbereitungs-Fix + Ersatzmessungen~~ — erledigt (2026-05-24)
7. **NB 01 Layer-1-Infrastruktur** (DNS/Ping/TLS/Traceroute + DNSSEC + Anycast-Analyse) — **NAECHSTE AUFGABE**
8. **NB 02 PCAP & Kommunikationsmatrix** (braucht Wireshark/tshark, Prof-Punkte 5+6)
9. **NB 03-05** Layer-3 STT/LLM/TTS
10. **NB 06** Cross-Layer-Korrelation (Kernbefund)
11. **NB 07** End-to-End-Pipeline
12. **E2E-Validierung** (manuelle Pipeline-Runs, 1 Tag)
13. **Thesis schreiben** (~3-4 Wochen)

## Relevante Dateien

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Projektkontext, Forschungsfrage, Messdesign |
| `HANDOFF.md` | Dieser Arbeitsstand |
| `notes/implementation_plan.md` | Vollstaendige Checkliste (Phase 0-12) |
| `notes/cost_analysis.md` | Kostenanalyse pro Provider |
| `notes/briefing_prof.md` | Briefing fuer Prof. Waelisch (Was/Warum/Wie) |
| `measurements/layer3/MODULE_PLAN.md` | Technischer Plan der 9 Module |
| `measurements/layer2/README.md` | Anleitung fuer Layer-2 Captures |
| `measurements/layer2/capture_all.py` | Automatisiertes tcpdump fuer alle 9 Provider |
| `measurements/layer2/analyze_pcaps.py` | tshark-Analyse der PCAP-Dateien |
| `data/layer2/analysis_summary.json` | Layer-2 Analyse-Ergebnisse (JSON) |
| `measurements/config.py` | Endpoints aller 9 Provider |
| `measurements/layer1_extra/` | Ersatzmess-Skripte (TLS, TCP-Ping, DNSSEC) |
| `.env.example` | Benoetigte Umgebungsvariablen |
| `analysis/_helpers.py` | Zentrale Provider-Map + Farben + Datenlader |
| `analysis/00_data_quality.ipynb` | Notebook 00 (erledigt) |
| `data/processed/known_anomalies.md` | **Pflichtlektuere** vor jedem neuen NB |
| `data/layer1_extra/` | tls.csv, ping_tcp.csv, dnssec.csv (Ersatzmessungen 24.05.) |
