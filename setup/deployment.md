# Deployment & Kampagnen-Betrieb

> Angelegt: 2026-06-15 · Teil des Neuaufbaus (s. `../NEUANFANG.md`, `messprotokoll.md`, `mess_kommandos.md`)
>
> Wie und wo die Layer-3-Messkampagne läuft, wie man sie prüft/stoppt, und welche Belege der Pilot
> geliefert hat. Operative Detail-Notiz für Reproduzierbarkeit + den eigenen Überblick.

## Vantage Point (Instanz)

| | |
|---|---|
| Instanz-ID | `i-0f8f6d2414cecebb8` |
| Typ | **c6i.large** (non-burstable, A6 — kein CPU-Credit-Throttling, das ms-Timer verfälscht) |
| Region/AZ | `eu-central-1b` (Frankfurt) |
| Image | Ubuntu 24.04.4 LTS (`ami-042dc8681de073ac4`), Kernel 6.17.x-aws |
| Laufzeit-Stack | Python 3.12, **OpenSSL 3.0.13** (echtes OpenSSL → TLS-Version belastbar, A1 ✓) |
| AWS-Account | `365916940756` (User `claude`); CLI lokal: `.venv/bin/aws` |
| Zugang | `ssh -i ~/.ssh/thesis-ec2 ubuntu@<public-ip>` (Key-Pair in AWS = `thesis-ec2`) |
| Code-Ort | `~/thesis/` (per tar-Pipe übertragen, inkl. `.git` → git-Provenienz im `run_meta`) |
| Zeitbasis | chrony (Amazon Time Sync), Zeitzone **UTC** → cron-Slots UTC-korrekt |

> **Public IP wechselt bei stop/start** (keine Elastic IP). Aktuelle IP:
> `.venv/bin/aws ec2 describe-instances --region eu-central-1 --instance-ids i-0f8f6d2414cecebb8 --query 'Reservations[].Instances[].PublicIpAddress' --output text`

## Wie die Kampagne läuft

- **cron** (aktiv + enabled) feuert die **8 UTC-Slots** `00/03/06/09/12/15/18/21h`, je `run.py --n 100 --tag HHh`.
- Jeder Slot: interleaved Round-Robin über alle 9 Endpunkte, 100 Runden, 1,5 s Delay → ~52 min/Slot (passt in den 3-h-Takt; Slot-Deadline 150 min als Sicherheitsnetz).
- **flock** (`/tmp/layer3.lock`) verhindert überlappende Slots; **Per-Call-Timeout** (75 s) verhindert, dass ein hängender Call den Slot einfriert.
- **Daten:** `~/thesis/data/layer3/campaign/<tag>_<ts>.jsonl` (1. Zeile `run_meta`, je Call ein Record, letzte Zeile `run_end`). **Log:** `~/thesis/data/layer3/cron.log`.
- **Kampagnen-Start:** 2026-06-15, erster Slot 21:00 UTC. Ziel: 7 Tage × 8 Slots = 56 Slots.

cron-Zeile (je Slot):
```bash
0 H * * * cd /home/ubuntu/thesis && flock -n /tmp/layer3.lock .venv/bin/python -u measurements/layer3/run.py --n 100 --tag HHh >> /home/ubuntu/thesis/data/layer3/cron.log 2>&1
```

## Pilot-Belege (2026-06-15, n=3, aus Frankfurt) — Kernthese live bestätigt

| Endpunkt | TCP-RTT (FRA) | Einordnung |
|----------|--------------|------------|
| Mistral / OpenAI / Groq (LLM+TTS) | **~1–2 ms** | Cloudflare-**Edge** in FRA (Terminierung, nicht Backend) |
| Azure STT/TTS | **~11–12 ms** | echtes EU-RZ (Italy North), **kein** CDN-AS |
| Deepgram / Rev.ai | **~137–139 ms** | echtes US-Backend |

- **STT/TTS-Inversion (C1):** Azure auf `ttft` **langsamster STT** (~1721 ms) aber `ttfa` **schnellster TTS** (~254 ms) — gleiche Region/RTT, gegensätzliches Ergebnis → „Region erklärt Latenz" falsifiziert. *(Diese STT-Zahl ist `ttft` = inkl. Endpointing-Stille-Warten; ab 2026-06-16 ist STT-Primärmetrik `ttfp` + Realtime-Pacing, das den Anteil zerlegt — s. `AUDIT_stt_methodik_2026-06-16.md`. Die 4 Pilot-/Kampagnen-Slots 15./16.6. nutzen noch den alten STT-Code → STT-seitig verworfen, Neumessung.)*
- **A1:** auf EC2 echtes OpenSSL → **6× TLS 1.3**, rev.ai **TLS 1.2** (der eine echte 1.2-Host, kein LibreSSL-Artefakt).
- **A6:** `cpu_steal 37→37` über den Slot → **kein** burstable-Throttling (c6i.large empirisch belegt).
- **Rev.ai-Billing:** Wall-Clock ~2 s/Call → **15-s-Boden** greift → ~15 s/Call → **~1.400 min** für die volle Kampagne.

## Budget-/Key-Status (alle 6 Accounts startklar)

| Anbieter | Status |
|----------|--------|
| Deepgram (STT+TTS) | $200-Gratisguthaben (deckt ~$11) |
| OpenAI (LLM+TTS) | $5 Prepaid (deckt ~$4) |
| Azure (STT+TTS) | Azure-for-Students $100/12 Mon. (deckt ~$12), S0 Italy North |
| Mistral (LLM) | Free Experiment (1 Mrd Tokens/Monat) |
| Groq (LLM) | Free-Tier reicht (interleaved ~5 RPM); Karte optional |
| Rev.ai (STT) | **~2.040 min geladen** (540 + 1.500) → deckt ~1.400 min |

> Test-Keys liegen in `~/thesis/.env` (gitignored) und werden vom Nutzer rotiert.

## Betrieb: prüfen & stoppen

```bash
# Fortschritt prüfen (SSH):
tail ~/thesis/data/layer3/cron.log
ls ~/thesis/data/layer3/campaign/                 # eine Datei je Slot

# Nach ~7 Tagen (Ziel ~2026-06-22): Kampagne stoppen
crontab -r                                         # cron-Slots entfernen
# Instanz stoppen (Billing aus) bzw. terminieren:
.venv/bin/aws ec2 stop-instances --region eu-central-1 --instance-ids i-0f8f6d2414cecebb8
```

- **Kosten:** c6i.large ~$0,09/h × 24/7 ≈ **~$15 / 7 Tage** (vom $200-Guthaben).
- **Alte Instanz `i-045a2d0eeb338b290`** (t3.small, stopped) kann terminiert werden (EBS freigeben).

## Offene Punkte

- **Daten-Validierung per ultracode** (Messfehler/Methodik gegen ECHTE Slot-Daten) — sinnvoll ab ~1 Tag Daten (Diurnal-Abdeckung).
- **Layer 2 (PCAP):** separater Capture (N≈30 Cold-Starts/Provider) — jederzeit auf derselben EC2 nachholbar.
- **WER (A14):** sample.wav-Provenienz + Referenz/Normalisierung klären, bevor WER ausgewertet wird.
