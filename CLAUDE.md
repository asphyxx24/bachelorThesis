# Bachelorarbeit — Messinfrastruktur (Neuaufbau)

> **Stand 2026-06-14: Neuanfang.** Skripte, Setup und **alle Messungen** werden von Grund auf neu
> gebaut. Lebende Referenz + aktueller Status: **`NEUANFANG.md`**. Alles Frühere liegt in **`archived/`**
> (nur Nachschlagewerk, nicht mehr Grundlage). Leitprinzip: **erst Methodik schriftlich, dann Code,
> dann messen.**

**Arbeitstitel (nicht angemeldet, frei änderbar):** Engine schlägt Geografie: Netzwerk-, Protokoll-
und Latenzanalyse kommerzieller Cloud-AI-APIs einer Echtzeit-Voice-Pipeline aus EU-Perspektive
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

- **C1 (Kern) — „Engine schlägt Geografie":** Aus EU-Sicht dominiert die Backend-Engine, nicht die
  Netzwerknähe. Schärfster Beleg: **STT/TTS-Inversion** desselben Providers auf `ttft`/`ttfa` (Azure mit
  **gleicher** ~11 ms RTT verliert bei STT, gewinnt bei TTS → Geografie konstant gehalten, Differenz =
  Backend). **`ttfp` ist das Diagnose-Werkzeug**, das Azures STT-Nachteil als Endpointing-Stille-Warten
  zerlegt (`ttft − ttfp`) — es **erklärt** die Inversion, ist **kein** cross-provider Tempo-Ranking
  (das enthielte RTT/Geografie). S. `setup/messprotokoll.md` → „STT-Primärmetrik".
- **C2 — Drei-Schichten-Methodik + Cloudflare-/Edge-Grenze.**
- **C3 (Methoden-Baustein) — Ping-basierte connect-Klassen-Heuristik** (`r` bewusst **nicht** als Gütemaß).

## Drei-Schichten-Architektur

- **Layer 1 (Infrastruktur):** DNS, RTT/Ping (**TCP primär**, ICMP zur Validierung), TLS, Traceroute
  → misst Netzwerk-Nähe zum **Host**.
- **Layer 2 (Paketaufzeichnung):** tcpdump/PCAP, **N≈30 Cold-Starts/Anbieter** → **Eichung** der
  App-Timer (Handshake-Überlappung) + **Zusatzinfo** (Inter-Arrival-Time, Retransmits, Round-Trips),
  die Layer 3 nicht sehen kann.
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
  sonst liefert Deepgram kein Interim. `ttft` (erstes Final) bleibt **sekundär** (enthält Endpointing).
  User-perceived STT-Cold-Start = `connect_total + stt_ttfp`. Details: `setup/messprotokoll.md`.
- **LLM/TTS:** `ttft`/`ttfa` ab **Request-Absenden** über frische Verbindung → **connect-INKLUSIV**.
- **E2E** zählt connect **nicht doppelt**: STT trägt connect + ttfp, LLM/TTS tragen nur ttft/ttfa.

## Wichtige Dateien

| Datei | Inhalt |
|-------|--------|
| `NEUANFANG.md` | **Lebende Referenz** — Warum/Was/Reihenfolge + aktueller Status |
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
