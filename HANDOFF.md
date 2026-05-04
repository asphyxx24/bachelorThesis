# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-04, 15:00 (Session: Cron-Fix, Layer-2 Captures, Kampagne laeuft)

## Letzter Stand

Kampagne laeuft seit 2026-05-04 12:00 UTC korrekt (erster Datensatz: `2026-05-04_12h.jsonl`).
Cron-Jobs waren vom 03.05. abends bis 04.05. mittags defekt (`source` in `/bin/sh`),
gefixt durch `SHELL=/bin/bash` in der Crontab. Verlorene Slots: ~6 (ca. 1 Tag).
Kampagne sollte daher bis ~2026-05-18 laufen statt 2026-05-17.

Layer-2 Captures fuer alle 9 Provider durchgefuehrt und analysiert (tshark).
Cross-Layer-Korrelation bestaetigt: RTT × Protokoll-RTTs ≈ connect_ms.

## Aktuelle Fokus-Aufgabe

**Kampagne laeuft automatisch.** Naechste Aufgabe: Betreuer-Treffen (Dienstag 2026-05-05),
danach Monitoring bis Kampagnenende. Analyse beginnt nach ~2026-05-18.

## Entscheidungen und Fixes

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
| IP | `35.159.112.40` |
| OS | Ubuntu 22.04, Python 3.10 |
| SSH | `ssh -i ~/.ssh/thesis-key.pem ubuntu@35.159.112.40` |
| Repo | `~/thesis` (via SSH Deploy Key, Push-berechtigt) |
| Logs | `~/thesis/logs/layer3.log`, `layer1.log`, `git-sync.log` |

## Cron-Jobs (UTC)

```
# Layer 3: alle 3h, n=100, 9 Provider
0 0,3,6,9,12,15,18,21 * * *

# Layer 1: alle 6h background, taeglich 05:30 full
0 */6 * * *      (background: DNS + Ping)
30 5 * * *        (full: + TLS + Traceroute)

# Git-Sync: taeglich 02:00
0 2 * * *
```

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

## Erste Ergebnisse (EC2 Frankfurt, n=3)

**STT:**
| Provider | connect_ms | TTFT | Region |
|----------|-----------|------|--------|
| Deepgram | ~390ms | 472ms | USA (Anycast) |
| Rev.ai | ~600ms | 1463ms | USA |
| Azure | ~55ms | 1719ms | Italien |

**LLM:**
| Provider | connect_ms | TTFT | TTL |
|----------|-----------|------|-----|
| Groq | ~15ms | 56ms | 62ms |
| Mistral | ~13ms | 301ms | 329ms |
| OpenAI | ~10ms | 1402ms | 1575ms |

**TTS:**
| Provider | connect_ms | TTFA | Region |
|----------|-----------|------|--------|
| Azure | ~37ms | 194ms | Italien |
| Deepgram | ~306ms | 419ms | USA (Anycast) |
| OpenAI | ~15ms | 1272ms | USA |

## Monitoring

- **Passiv:** Morgens `git pull` — neue JSONL-Dateien in `data/layer3/`? → alles OK
- **Aktiv:** `ssh -i ~/.ssh/thesis-key.pem ubuntu@35.159.112.40 "tail -20 ~/thesis/logs/layer3.log"`

## Offene Schritte

1. ~~Alte Kampagne stoppen (ops.papagei.ai)~~ — **Anton, noch offen!**
2. ~~Layer-2 Captures auf EC2~~ — erledigt (2026-05-04)
3. **Betreuer-Treffen** — Dienstag 2026-05-05
4. **Kampagne Monitoring** — taeglich `git pull`, bis ~2026-05-18
5. **Analyse** in Jupyter Notebooks (nach Kampagne)
6. **E2E-Validierung** (manuelle Pipeline-Runs, 1 Tag)
7. **Thesis schreiben** (~3-4 Wochen)

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
