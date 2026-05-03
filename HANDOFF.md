# Handoff — Aktueller Arbeitsstand

> Letzte Aktualisierung: 2026-05-03, 16:00 (Session: Module implementiert, EC2 aufgesetzt, Kampagne gestartet)

## Letzter Stand

Alle 9 Provider-Module implementiert, getestet und auf AWS EC2 Frankfurt deployed.
Messkampagne laeuft seit 2026-05-03 per Cron-Job (Layer 1 + Layer 3, 14 Tage).
Git-Sync pusht taeglich um 02:00 UTC — morgens `git pull` zeigt neue Daten.

## Aktuelle Fokus-Aufgabe

**Kampagne laeuft automatisch.** Naechste manuelle Aufgabe: Layer-2 Captures auf EC2
(tcpdump waehrend eines Layer-3-Laufs, ein paar pro Provider). Kann jederzeit
waehrend der Kampagne gemacht werden.

## Entscheidungen dieser Session

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

1. **Alte Kampagne stoppen** (ops.papagei.ai) — Anton, Montag
2. **Layer-2 Captures** auf EC2 (manuell, waehrend Kampagne)
3. **Analyse** in Jupyter Notebooks (nach Kampagne, ~2 Wochen)
4. **E2E-Validierung** (manuelle Pipeline-Runs, 1 Tag)
5. **Thesis schreiben** (~3-4 Wochen)

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
| `measurements/config.py` | Endpoints aller 9 Provider |
| `.env.example` | Benoetigte Umgebungsvariablen |
