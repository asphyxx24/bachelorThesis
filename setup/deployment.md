# Deployment & Kampagnen-Betrieb

> Angelegt: 2026-06-15 · Teil des Neuaufbaus (s. `../NEUANFANG.md`, `messprotokoll.md`, `mess_kommandos.md`)
>
> Wie und wo die Layer-3-Messkampagne läuft, wie man sie prüft/stoppt, und welche Belege der Pilot
> geliefert hat. Operative Detail-Notiz für Reproduzierbarkeit + den eigenen Überblick.
>
> **Scope:** Nur **Layer 3** läuft hier slotweise (cron, 8 UTC-Slots/Tag). **Layer 1** war eine einmalige
> EC2-Momentaufnahme (RTT/DNS/ASN/Traceroute/TLS, 2026-06-16), **Layer 2** eine einmalige Handshake-Eichung
> (2026-06-16) — beide kein Slot-Betrieb. Achtung Auswertung: `data/layer1/` im Repo ist ein macOS-Dev-Lauf
> (~17–21 ms), **nicht** der EC2-Lauf (~1 ms); nur EC2-L1 verwenden (Audit H4).

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
- Jeder Slot: interleaved Round-Robin über alle 9 Endpunkte, 100 Runden, 1,5 s Delay → mit STT-Realtime-Pacing ~60–67 min/Slot (passt in den 3-h-Takt; Slot-Deadline 150 min als Sicherheitsnetz).
- **flock** (`/tmp/layer3.lock`) verhindert überlappende Slots; **Per-Call-Timeout** (75 s) verhindert, dass ein hängender Call den Slot einfriert.
- **Daten:** `~/thesis/data/layer3/campaign/<tag>_<ts>.jsonl` (1. Zeile `run_meta`, je Call ein Record, letzte Zeile `run_end`). **Log:** `~/thesis/data/layer3/cron.log`.
- **Kampagnen-NEUSTART:** 2026-06-16, erster Slot 12:00 UTC. **Slots 12h/15h liefen auf Commit `7f04770`**
  (STT `ttfp`+Pacing, F2/F3 — code-identisch zu `bccceaf`, nur docs-only commit dazwischen; `run_meta` selbst
  geprüft, `git_dirty=False`). Ab dem 18:00-Slot läuft **`f1f0d47`** (deepgram-`ttft`-Fix + IPv4-Pin + C1-Doku).
  *Hinweis:* der deepgram-`ttft`-Fix (first→last is_final) ist für diesen festen Input ein **No-Op** (200/200
  Calls = ein einziges Final-Segment), die 12h/15h-`ttft` sind also gültig. Ziel: 7 Tage × 8 Slots (~2026-06-23).
  Die 4 Slots + Pilot vom 15./16.6. (alter STT-Code, **ohne** `ttfp`) liegen in
  `data/layer3/campaign_old_predeploy_20260616/` → **verworfen**, nicht Teil der Wertungsdaten.
- **Maßgeblicher Freeze-Commit = `f9e6dc8`** (nicht `f1f0d47`). Der Layer-3-Mess-Code (`llm.py`/`tts.py`/`stt.py`/
  `run.py`/`config.py`) ist zwischen `f1f0d47` und `f9e6dc8` **identisch** (dazwischen nur Layer-2-Eichung + Doku,
  keine layer3-Datei geändert) → alle Slots ab 18h sind code-konsistent zur eingefrorenen Version. Per `git diff f1f0d47 f9e6dc8 -- measurements/layer3` belegbar.

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

- **RTT-Klassen (C2):** drei saubere Klassen (Edge ~1 ms / Azure-EU-RZ ~11 ms / US-Backend ~140 ms) live bestätigt. *(Die frühere „STT/TTS-Inversion (C1)"-Lesart mit ~1721 ms STT + ~254 ms TTS ist ÜBERHOLT: die n=3-Pilot-Zahlen sind durch die Vollkampagne ersetzt (Azure-`ttfa` ~93 ms; STT-`ttft`-Konstanz war Dump-Bulk-Compute, kein Endpointing-Timer). C1 ruht jetzt auf der LLM-Edge-Achse — s. `messprotokoll.md` → „Korrekte C1-Logik". Dieser Pilot zählt nur als RTT-/Edge-Beleg, nicht als C1-Latenzbeleg.)*
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

# Nach ~7 Tagen (Ziel ~2026-06-23): Kampagne stoppen
crontab -r                                         # cron-Slots entfernen
# Instanz stoppen (Billing aus) bzw. terminieren:
.venv/bin/aws ec2 stop-instances --region eu-central-1 --instance-ids i-0f8f6d2414cecebb8
```

- **Kosten:** c6i.large ~$0,09/h × 24/7 ≈ **~$15 / 7 Tage** (vom $200-Guthaben).
- **Alte Instanz `i-045a2d0eeb338b290`** (t3.small, stopped) kann terminiert werden (EBS freigeben).

## Offene Punkte

- **Daten-Validierung per ultracode:** ✅ erledigt — Voll-Audit 2026-06-18 (`data/audit_20260618/VERDICT.md`),
  Urteil **GO-mit-Auflagen**; Auflagen sind Doku-/Reporting-Korrekturen (s. `HANDOFF.md` §4), keine Neumessungen.
- **Layer 2 (Handshake-Eichung):** ✅ erledigt (2026-06-16, Connect-Timer paket-validiert). Offen nur die
  **richere** PCAP-Analyse (IAT/Retransmits *während* echter Calls) — Kür, jederzeit auf derselben EC2 nachholbar.
- **WER (A14):** sample.wav-Provenienz + Referenz/Normalisierung klären, bevor WER ausgewertet wird (Out-of-Scope für Latenz).
- **~2026-06-23:** Kampagne stoppen (`crontab -r` + Instanz stoppen).
