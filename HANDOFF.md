# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-22 (Session: Kampagne gestoppt, EC2 gestoppt, Analyse-Phase beginnt)

## Letzter Stand

**Kampagne abgeschlossen.** Gelaufen von 2026-05-04 12:00 UTC bis 2026-05-22 12:00 UTC (18 Tage, 4 Tage laenger als geplant).
Alle Cron-Jobs deaktiviert, EC2-Instanz gestoppt. Alle Daten lokal und auf GitHub vorhanden.

**Finale Datenmenge:**
- Layer 3: 145 Slots, 128.580 Messungen gesamt, 123.019 erfolgreich
- Layer 1: 91 Dateien (DNS, Ping, TLS, Traceroute)
- Layer 2: 10 PCAP-Analysen (alle 9 Provider)

**Datenqualitaet:**
- 7 von 9 Providern: 0-0,1% Fehlerrate (perfekt)
- Groq: 34% Fehler (HTTP 429, Free-Tier 30-RPM-Limit) — aber gleichmaessig verteilt (67/100 pro Slot, kein Slot leer), 9.452 valide Messungen, voll nutzbar
- Mistral: 4,3% Fehler (HTTP 429, Kapazitaet), 13.762 valide Messungen

**Kosten (tatsaechlich, 18 Tage):**
- Deepgram (STT+TTS): $21,33 von $200 Guthaben
- Rev.ai: $10,67 von $10,98 Budget
- Azure (STT+TTS): $27,90 von $100 Kredit
- OpenAI (LLM+TTS): $8,28 von $10 Prepaid
- Groq + Mistral: $0 (Free Tier)
- AWS EC2: ~$13 von $120 Free Credits
- **Gesamt API: ~$68**

## Aktuelle Fokus-Aufgabe

**Phase 10: Analyse** — Jupyter Notebooks lokal aufsetzen und Daten auswerten.

Reihenfolge:
1. Python-Umgebung lokal einrichten (Jupyter, pandas, matplotlib, scipy)
2. `analysis/layer3_all_providers.ipynb` — p50/p95/p99 aller 9 Provider
3. `analysis/layer3_daytime_trends.ipynb` — Latenz nach Tageszeit / Wochentag
4. `analysis/layer1_infrastructure.ipynb` — DNS-Varianz, Ping-RTT, TLS
5. `analysis/layer1_vs_layer3_correlation.ipynb` — Ping RTT x 3 ≈ connect_ms (Kernbefund)
6. E2E-Validierung (manuelle Pipeline-Runs, ~1 Tag)
7. Thesis schreiben (~3-4 Wochen)

## Entscheidungen und Fixes

### Session 2026-05-22
- **Kampagne gestoppt:** Alle Cron-Jobs per `crontab -r` entfernt.
- **Finaler Sync:** 10 Dateien committed und gepusht (commit `093f510`).
- **EC2 gestoppt:** `i-045a2d0eeb338b290` ist im Zustand `stopped`. Analyse laeuft lokal.
- **Groq-Analyse:** Rate-Limiting war konstant (67/100 pro Slot, nicht zufaellig) →
  erklaerbar durch 30-RPM-Limit des Free Tiers; als Befund dokumentierbar.

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
| IP | `35.159.112.40` (bei Neustart neue IP) |
| Status | **STOPPED** (seit 2026-05-22) |
| SSH | `ssh -i ~/.ssh/thesis-key.pem ubuntu@35.159.112.40` |
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
6. **Analyse** in Jupyter Notebooks (Phase 10) — **NAECHSTE AUFGABE**
7. **E2E-Validierung** (manuelle Pipeline-Runs, 1 Tag)
8. **Thesis schreiben** (~3-4 Wochen)

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
| `.env.example` | Benoetigte Umgebungsvariablen |
| `analysis/` | Jupyter Notebooks fuer Phase 10 |
