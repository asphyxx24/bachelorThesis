# Bachelorarbeit — Messinfrastruktur (Neuaufbau)

> **Stand 2026-06-23: Vollkampagne, abgeschlossen (56/56), Code eingefroren.** Methodik und Skripte sind gebaut; die
> Layer-3-Kampagne läuft seit 2026-06-16 auf EC2 `i-0f8f6d2414cecebb8` (Code eingefroren auf Commit
> `f9e6dc8`), 56 von 56 Slots (A4) gelandet, Vollkampagne abgeschlossen (56/56). **Layer 3 läuft slotweise** (8 UTC-Slots/Tag);
> **Layer 1 war eine EINMALIGE Momentaufnahme** (2026-06-16, kein Slotbetrieb). Nächste Phase: Auswertung,
> Statistik, Folien. Lebende Referenz + Status: **`NEUANFANG.md`**, Einstieg **`HANDOFF.md`**. Alles Frühere
> liegt in **`archived/`** (nur Nachschlagewerk). Leitprinzip: **erst Methodik schriftlich, dann Code, dann messen.**

**Arbeitstitel (nicht angemeldet, frei änderbar — IN ÜBERARBEITUNG):** Kandidaten in **`notes/arbeitstitel.md`**
(neutral-deskriptiv, Rigor-Signal; „Engine"/„Backend" bewusst NICHT im Titel wegen Modellgrößen-Confound —
die verteidigbare Aussage ist die *negative*: „Netznähe erklärt die Latenzspreizung nicht"). Auswahl steht noch aus.
**Autor:** Anton Rusik · **Betreuer:** Prof. Dr. Matthias Wählisch, TU Dresden
**Vantage Point:** AWS EC2 `eu-central-1` (Frankfurt)

## Warum der Neuanfang

Prof. Wählisch: inhaltlich ausreichend, aber er **vertraut den Daten nicht**, weil Methodik/Setup/
Struktur nicht dargelegt sind (u.a. „3 Anbieter mit niedriger Layer-1-Latenz, nicht erklärt"). Es ist
ein Dokumentations-/Verständnisproblem, kein „Zahlen falsch"-Problem. Begründung + erhaltenes Wissen
(Reframe, Audit-Spec, Provider-Rationale) stehen in `NEUANFANG.md`.

## Forschungsfrage

> In welchem Maße erklären Netzwerk- und Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region)
> — *im Vergleich zur Backend-Verarbeitung der Engine* — die Latenzunterschiede zwischen kommerziellen
> Cloud-AI-APIs (STT, LLM, TTS) aus EU-Perspektive, und wie wirkt sich die Provider-Wahl auf die
> Gesamtlatenz einer sequenziellen Cold-Start-Voice-Pipeline aus?

In beide Richtungen beantwortbar — „Netzwerk erklärt *weniger* als die Engine" ist eine gültige Antwort.

## Contribution

- **C1 (Kern) — „Backend statt Geografie":** Aus EU-Sicht dominiert die Backend-Verarbeitung (HW+Modell), nicht die
  Netznähe. Die wasserdichte Aussage ist die *negative*: Netznähe erklärt die Latenzspreizung nicht.
  **Schärfster Beleg — LLM bei identischer Edge-RTT:** OpenAI/Groq/Mistral terminieren *alle* bei Cloudflare
  Frankfurt (AS13335, ~1 ms RTT). Das ist für **100 % des LLM-Traffics** gemessen und ASN-belegt (je Provider
  2 CF-IPs ~50/50, alle AS13335 ~1 ms, nicht mehr per ASN unterstellt; Belege `data/audit_20260618/l1_rtt_per_ip.md`
  + `asn_per_ip.md`). Trotzdem streut LLM-`ttft` in der Voll-Kampagne (Vollkampagne, abgeschlossen (56/56), A4, success-only)
  **~67 → 279 → 487 ms (~7,3×, gepoolt 8,3×; groq < mistral < openai; connect-inkl.; Bootstrap-CI noch ausstehend)** —
  gleiches Netz, die Differenz kann nicht Netznähe sein (per-IP invariant; EU-Mistral sogar langsamer als
  US-Groq → Geografie-Ordnung invertiert). Der finale Faktor (~7,3×, gepoolt 8,3×) ist sogar **größer** als
  der Pilot — Ordnung identisch, der Kernbefund wird dadurch **stärker**. Die früher zitierten **75/268/476 ms**
  sind der Predeploy-Pilot (n=200, 2 Slots) und reproduzieren aus keinem Kampagnen-Datensatz. **Zweiter Beleg:**
  Azure **schnellstes TTS** (`ttfa` ~94 ms); das gilt gegenüber Deepgram (US-Transit, `ttfa` ~516 ms). OpenAI-TTS
  terminiert AUCH bei Cloudflare-FRA (AS13335, connect ~1 ms — identical edge wie OpenAI-LLM) und ist damit eine
  **zweite identical-edge-Instanz**, die C1 zusätzlich stützt: trotz ~1 ms connect liegt `ttfa` bei ~942 ms
  (connect-exkl. ~941 ms, ≈ reines Backend).
  **STT (ehrlich):** auf der fairen Metrik `ttfp` ist Azure **nicht** langsamster — die früher behauptete
  „Azure-STT-Endpointing-Inversion" war ein **Dump-Artefakt (Bulk-Compute)** und wird **nicht** als Backend-Beleg
  geführt. S. `setup/messprotokoll.md` → „STT-Primärmetrik".
- **C2 — Drei-Schichten-Methodik + Cloudflare-/Edge-Grenze.**
- **C3 (Methoden-Baustein) — Ping-basierte connect-Klassen-Heuristik** (`r` bewusst **nicht** als Gütemaß).

## Drei-Schichten-Architektur

- **Layer 1 (Infrastruktur):** DNS, RTT/Ping (**TCP primär**, ICMP zur Validierung), TLS, Traceroute
  → misst Netznähe zum **Host**. **Maßgeblich ist nur der EC2-Lauf** (ts 2026-06-16, RTT ~1 ms CF / ~11 ms Azure
  / ~140 ms US). `data/layer1/` im Repo enthält zusätzlich einen macOS-Dev-Lauf (RTT ~17–21 ms), der **nicht**
  in die Auswertung darf (kein Vantage-Stempel im Record, nur an der RTT-Größenordnung unterscheidbar; Audit H4).
- **Layer 2 (Paketaufzeichnung):** tcpdump/PCAP (`measurements/layer2/`). **Eichung durchgeführt
  (2026-06-16):** App-`tcp_handshake_ms` = Wire-SYN→SYN-ACK auf **~0,1 ms** genau (Azure 11 ms & Deepgram
  139 ms) → der **Connect-Timer** ist paket-validiert. **Wichtig (Audit H2):** die Eichung deckt NUR den
  Connect-Timer (`tcp_handshake`), NICHT `ttft`/`ttfa` — diese starten erst beim Request-Absenden im
  httpx/websockets-Stack und nutzen denselben `perf_counter`-Mechanismus, sind aber nicht direkt paket-geeicht.
  Richere Zusatzinfo (IAT/Retransmits) = Analyse-Phase.
- **Layer 3 (API-Latenz):** Cold-Start — atomare connect-Submetriken + `ttft`/`ttfa`/`total`
  → misst Engine-Verarbeitung über die volle **URL**.

## Provider-Matrix (gleiche 9, alle 3 Kategorien — Rationale in `setup/anbieter_auswahl.md`)

| Kategorie | Anbieter | Modell | Region (deklariert) | Protokoll |
|-----------|----------|--------|---------------------|-----------|
| STT | Deepgram | Nova-3 | USA (Multi-DC, DNS-Round-Robin) | WebSocket |
| STT | Rev.ai | English | USA | WebSocket |
| STT | Azure | Standard Neural | Italien (Italy North) | WebSocket |
| LLM | OpenAI | gpt-4o-mini | USA (GPU) | HTTPS + SSE |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS + SSE |
| LLM | Mistral | mistral-small-2603 | EU / Frankreich | HTTPS + SSE |
| TTS | Deepgram | Aura-2 | USA (Multi-DC, DNS-Round-Robin) | HTTPS Streaming |
| TTS | OpenAI | tts-1 | USA | HTTPS Streaming |
| TTS | Azure | Standard Neural | Italien (Italy North) | HTTPS Streaming |

## Messdesign (Kurzfassung — Details in `setup/messprotokoll.md`)

- **Cold-Start:** jede Messung neue TCP+TLS-Verbindung, kein Pooling. STT ohne SDK (raw WebSocket).
- **Feste Inputs** je Kategorie (fairer Vergleich).
- **Kampagne:** 7 Tage × **8 UTC-Slots** (`00/03/06/09/12/15/18/21h`) × **n=100**, **interleaved**
  (Round-Robin, Startreihenfolge je Runde rotieren) = 56 Slots, 5.600/Endpunkt, 50.400 gesamt.
- **`connect_ms` abgeschafft** → atomare Submetriken (`tcp_handshake_ms`, `tls_handshake_ms`,
  `ws_upgrade_ms`); „connect total" nur abgeleitete Summe.

## Metrik-Asymmetrie (war die zentrale Verwirrungsquelle — explizit deklariert)

- **STT-Primärmetrik: `ttfp`** (Time-to-first-**Partial**, erstes Live-Wort) ab **erstem Audio-Chunk**
  (nach Connect) → **connect-EXKLUSIV**, endpointing-frei. Audio wird **1×-realtime** gestreamt (Pacing),
  sonst liefert Deepgram kein Interim. `ttft` (Stream-Ende-Final, deepgram=letztes Segment) bleibt **sekundär**.
  User-perceived STT-Cold-Start = `connect_total + stt_ttfp`. Details: `setup/messprotokoll.md`.
- **LLM/TTS:** `ttft`/`ttfa` ab **Request-Absenden** über frische Verbindung → **connect-INKLUSIV**.
- **E2E** zählt connect **nicht doppelt**: STT trägt connect + ttfp, LLM/TTS tragen nur ttft/ttfa.

## Wichtige Dateien

| Datei | Inhalt |
|-------|--------|
| `HANDOFF.md` | **⭐ Hier einsteigen** — aktueller Stand + To-dos (Campaign-Check, Arbeitstitel, Statistik, Folien) |
| `notes/arbeitstitel.md` | Titel-Kandidaten (Favorit + Alternativen) — Auswahl steht noch aus |
| `NEUANFANG.md` | **Lebende Referenz** — Warum/Was/Reihenfolge + aktueller Status |
| `data/audit_20260618/VERDICT.md` | **Maßgebliches Voll-Audit-Urteil** (2026-06-18, 72 Agenten, 85 Befunde; GO-mit-Auflagen). Plus `l1_rtt_per_ip.md` + `asn_per_ip.md` als Beleg-Artefakte. *gitignored* (Konklusionen gehören in `setup/*.md`) |
| `data/audit_20260616/VERDICT.md` | Älteres Audit-Urteil (3 Runden, 2026-06-16) + Echtdaten-Belege; *gitignored* |
| `setup/deployment.md` | EC2-Betrieb (Instanz, Slot-Cron, Stop-Plan) |
| `setup/anbieter_auswahl.md` | Welche Anbieter je Dienst, mit Begründung |
| `setup/api_endpunkte.md` | Verifizierte Hosts, URLs, Pfade, Auth-Methoden |
| `setup/messprotokoll.md` | **Methodik** — alle 3 Layer, Metriken, Kampagne, Fehlerbehandlung |
| `setup/mess_kommandos.md` | Welcher Befehl misst was (CLI/Skript je Layer) |
| `archived/` | Altes Material (Skripte, Daten, Notebooks, Audit) — nur Referenz |

## Commands

| Command | Wann | Zweck |
|---------|------|-------|
| `/prime` | Session-Start | Liest Stand + git log, kurzes Briefing |
| `/handoff` | Session-Ende | Aktualisiert den Arbeitsstand |
| `/write` | Schreib-Phase | Thesis-Abschnitte schreiben/überarbeiten |
| `/explain <Thema>` | Jederzeit | Konzept/Entscheidung verständlich erklären |
| `/analyze` | Falls nötig | Analyse-/Notebook-Unterstützung |
