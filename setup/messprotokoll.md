# Messprotokoll (Methodik)

> Angelegt: 2026-06-14 · Teil des Neuaufbaus (s. `../NEUANFANG.md`, `anbieter_auswahl.md`,
> `api_endpunkte.md`, `mess_kommandos.md`)
>
> Dieses Dokument beschreibt **was genau gemessen wird, wie und warum** — die nachvollziehbare
> Methodik, die der Prof bisher vermisst hat. Es wächst Schritt für Schritt mit dem Neuaufbau.

## Vantage Point

- **Ort:** AWS EC2, Region `eu-central-1` (Frankfurt) — feste Mess-Instanz, dokumentiert mit
  Account, Instanz-ID, Region und Zeitzone (UTC) zum Messzeitpunkt.
- **Begründung:** EU-Perspektive ist die Forschungsfrage. Frankfurt ist ein zentraler EU-Internet-Knoten.

## Drei-Schichten-Architektur

- **Layer 1 (Infrastruktur):** DNS, RTT/Ping, TLS-Handshake, Traceroute → misst die **Netzwerk-Nähe**
  zum **Host**.
- **Layer 2 (Paketaufzeichnung):** tcpdump/PCAP → belegt die Protokoll-Struktur (Handshake-Abfolge).
- **Layer 3 (API-Latenz):** Cold-Start — Verbindungsaufbau in **atomaren Submetriken**
  (`tcp_handshake_ms`, `tls_handshake_ms`, `ws_upgrade_ms`) + `ttft_ms`/`ttfa_ms` + `total_ms` → misst
  die **Engine-Verarbeitung** über die volle **URL**. *(Sammel-`connect_ms` abgeschafft — s. Layer-3-Abschnitt.)*

---

## Layer 1 — RTT-Messung (Ping-Strategie)

### Entscheidung: TCP-Ping als primäre Metrik, ICMP als Validierung

| Metrik | Gemessen bei | Rolle |
|--------|-------------|-------|
| **TCP-Ping (Port 443)** | **allen 9 Endpunkten** | **primär** — die vergleichbare RTT-Spalte für alle Auswertungen |
| ICMP-Ping | nur den Endpunkten, die ICMP beantworten | sekundär — Literatur-Anschluss + Cross-Check gegen TCP |

### Begründung

1. **Vergleichbarkeit (Hauptgrund):** Eine faire Cross-Provider-Tabelle braucht **eine** Messgröße.
   ICMP wird von mehreren CDN-/Cloud-gehosteten Endpunkten geblockt (nicht alle 9 antworten auf
   `ping`). Würde man ICMP für einen Teil und TCP für den Rest mischen, vergliche man zwei
   verschiedene Größen — angreifbar. TCP-Ping funktioniert bei **allen 9**, weil jeder API-Endpunkt
   per Definition TCP auf Port 443 annehmen muss (sonst keine Verbindung möglich).

2. **Misst den relevanten Port:** TCP-Ping (SYN auf 443 → SYN-ACK) trifft **denselben Port wie die
   echte API-Verbindung**, nicht einen ICMP-Nebenkanal, den manche Anbieter abweichend behandeln.

3. **Konsistenz mit Layer 3:** TCP-Ping misst SYN→SYN-ACK = **1 RTT** — exakt die Größe, in die sich
   `connect_ms` in Layer 3 zerlegt (`tcp_hs_ms`). Layer 1 und Layer 3 sprechen damit dieselbe Sprache;
   die Cross-Layer-Argumentation (`connect_ms ≈ N_RTTs × ping`) wird konsistent.

### Rolle von ICMP (warum nicht ganz weglassen)

- **Literatur-Anschluss:** „RTT per Ping" meint in der Literatur meist ICMP — sollte sichtbar sein.
- **Validierung (Clou):** Bei den Endpunkten, wo **beide** Methoden funktionieren, wird gezeigt, dass
  `tcp_ping ≈ icmp_ping`. Damit ist belegt, dass TCP-Ping ein gültiger RTT-Proxy ist — und darf für
  die ICMP-Verweigerer guten Gewissens als alleinige Quelle dienen. Das ist eine **Selbst-Validierung
  der Methode**, kein blinder Fleck.

### Caveat (Anycast/Edge — bewusst getrennt dokumentiert)

TCP- wie ICMP-Ping messen die RTT zu der IP, auf die der Hostname auflöst. Bei Anycast-/CDN-Endpunkten
(z. B. Cloudflare-Ranges, s. `api_endpunkte.md`) ist das ein **Edge-Knoten nahe Frankfurt**, nicht das
eigentliche Backend. Niedrige Layer-1-RTTs sind dort eine **reale Infrastruktur-Eigenschaft**, kein
Messfehler. Die genaue Edge-vs-Backend-Auflösung erfolgt im separaten Layer-1-Endpunkt-Schritt.

### Prof-Einzeiler

> „Ich messe RTT per TCP-Handshake auf Port 443, weil das (a) bei allen Anbietern funktioniert — ICMP
> wird von mehreren CDN-Endpunkten geblockt —, (b) denselben Port wie die echte API-Verbindung trifft
> und (c) direkt der `tcp_hs`-Submetrik aus Layer 3 entspricht. ICMP messe ich zusätzlich, wo möglich,
> um zu zeigen, dass beide RTTs übereinstimmen."

---

## Layer 2 — Paketaufzeichnung (PCAP)

### Zweck — und warum es NICHT redundant zu Layer 3 ist

Layer 2 schneidet den **vollständigen Paketaustausch von N≈30 Cold-Start-Calls** pro Anbieter mit.
Es misst zwar teils dasselbe wie Layer 3 (den TCP-Handshake), hat aber eine **Doppelrolle** — und nur
*ein* Teil überlappt:

1. **Überlappung (Handshake-RTT) → Eichung, kein zweiter Beweis.** Layer 3 misst den Handshake mit
   App-Timern, Layer 2 auf der **Leitung** (Kernel-Zeitstempel). Stimmen beide überein, ist die
   Layer-3-Instrumentierung **kalibriert/validiert** — das ist die Grundlage, die alle Layer-3-Zahlen
   vertrauenswürdig macht (genau das Vertrauensproblem des Profs), **nicht** ein zweiter unabhängiger Beweis.
2. **Das Mehr (alles außer der RTT) → echte Zusatzinfo, die Layer 3 NICHT sehen kann:**
   Retransmissions, Anzahl Round-Trips bis „App kann senden" (belegt `connect ≈ N×RTT` mit echten
   Paketen), **Inter-Arrival-Times** der Antwort-Pakete (wire-level-Blick aufs Token-Pacing),
   Paketgrößen/Burst-Muster.

→ Würde Layer 2 *nur* die Handshake-RTT liefern, wäre es fast redundant (reine Eichung). Erst Punkt 2
macht es zu eigenständigem Erkenntnisgewinn. **Beides getrennt benennen** — Eichung vs. Zusatzinfo —,
dann ist Layer 2 weder überverkauft noch überflüssig.

### „Nur Dumping" — bewusst getrennt von der Analyse

Layer 2 selbst ist **reines Mitschneiden** (`tcpdump`). Es werden **keine** Metriken währenddessen
berechnet. Alle Größen (Handshake-RTT, Inter-Arrival-Time, Paketgrößen, Retransmits …) entstehen
**nachgelagert** aus dem gespeicherten `.pcap`. Diese Trennung ist Absicht: Das Roh-PCAP konserviert den
**kompletten** Zeitverlauf, sodass auch **später** auftauchende Fragen ohne Neumessung beantwortbar
sind. Genau das ist der Vorteil gegenüber vorab aggregierten Zahlen.

### Capture-Vorgehen

Pro Anbieter: tcpdump starten → **N≈30 Cold-Start-Calls** nacheinander ausführen (jeder mit frischer
Verbindung) → tcpdump stoppen → **eine** `.pcap`-Datei speichern. Jede neue Verbindung hat einen neuen
Source-Port → in der Analyse werden die N Handshakes am 4-Tupel (src-ip/src-port/dst-ip/dst-port)
getrennt. So liefert ein PCAP eine **Verteilung** von N wire-level-Handshakes statt eines Einzelsamples.
tcpdump läuft mit Host-Filter und **vollständigen** Paketen (kein Snap-Cut):

```bash
sudo tcpdump -i <iface> -w data/layer2/capture_<provider>_<YYYYMMDD_HHMM>.pcap \
     host <provider-host> -s 0 -c 200000
```

- `-i <iface>`: Netzwerk-Interface des Vantage Points (auf der alten EC2: `ens5` — **auf der neuen
  Instanz vor dem Lauf verifizieren**, z. B. via `ip -br link`).
- `host <provider-host>`: filtert exakt auf den jeweiligen API-Host (s. `api_endpunkte.md`).
- `-s 0`: ganze Pakete (volle Header + Payload-Längen, nötig für Paketgrößen/IAT).
- `-c 200000`: nur Sicherheits-Backstop — gestoppt wird per SIGTERM, sobald die N Calls durch sind.
  (Höher als beim alten n=1-Lauf, weil N≈30 Calls inkl. STT-Audio deutlich mehr Pakete erzeugen.)

### TLS-1.3-Caveat → Analyse auf TCP-Ebene

TLS 1.3 **verschlüsselt** große Teile des Handshakes. Die PCAP-Analyse arbeitet daher auf **TCP-Ebene**
(SYN/SYN-ACK/ACK-Flags, Sequenznummern, Paket-Timing) — nicht auf entschlüsseltem TLS-Inhalt. Das
reicht für Handshake-Struktur, RTT und Timing vollständig aus.

### Aus dem PCAP ableitbare Größen (in der Analyse)

| Größe | Wie abgeleitet | Wozu |
|-------|----------------|------|
| `tcp_handshake_ms` (SYN → SYN-ACK) | Zeitdiff der beiden Pakete | **unabhängiger Check** des Layer-1-TCP-Pings & der Layer-3-`tcp_handshake_ms` |
| Anzahl Round-Trips bis „erste App-Daten" | Paketabfolge bis erstes Server-Data-Paket | belegt die `connect`-Struktur (wie viele RTTs der Aufbau wirklich kostet) |
| **Inter-Arrival-Time (IAT)** | Differenz aufeinanderfolgender Paket-Zeitstempel (`frame.time_relative`) | Jitter, Server-Verarbeitungslücken; **bei Antwort-Paketen** ein netzwerk-seitiger Blick auf das Token-/Chunk-Pacing (komplementär zu Layer-3-`ttft`) |
| Paketgrößen | `tcp.len` je Paket | Burst-Muster, Payload-Verteilung |
| Retransmissions / Out-of-Order | TCP-Sequenzanalyse | Verbindungsqualität auf der Route |

> **Inter-Arrival-Time** ist also **kein** separater Messlauf, sondern eine **abgeleitete** Größe aus
> dem ohnehin vollständigen Mitschnitt. (Prof-Wunsch — hiermit abgedeckt.)

### Analyse-Werkzeug

`tshark` (CLI-Variante von Wireshark) extrahiert die Felder pro Paket:
`frame.time_relative`, `ip.src`, `ip.dst`, `tcp.flags`, `tcp.len`, Ports. Daraus rechnet das
Analyse-Skript die obigen Größen. *(Alternativ ohne tshark: `scapy`/`dnspython` — s. `requirements.txt`.)*

### Ehrliche Einordnung (A9 — adressiert, nicht nur beichten)

Durch **N≈30 Captures pro Anbieter** liefert Layer 2 eine **Verteilung** wire-level-Handshake-Zeiten
und ist damit ein echter statistischer **Konsistenz-Check** gegen Layer 1 / Layer 3 — nicht mehr nur
der n=1-Schnappschuss des alten Laufs (= Audit-Punkt A9).

**Wichtige Präzisierung (so dem Prof sagen):** Layer 2 und Layer 3 messen dasselbe *Phänomen* (denselben
TCP-Handshake). Die Unabhängigkeit liegt in der **Mess-Ebene** — Kernel-Paketzeitstempel vs.
Applikations-Timer —, nicht in zwei verschiedenen Phänomenen. Korrekt formuliert ist Layer 2 also ein
**Konsistenz-/Plausibilitäts-Check** der Applikations-Timer auf der Leitung, **kein** zweiter, völlig
unabhängiger Beweis. So bleibt die Aussage verteidigbar.

---

## Layer 3 — API-Latenz (Cold-Start)

### Grundprinzip: Cold-Start

Jede einzelne Messung baut eine **frische TCP+TLS-Verbindung** auf — **kein Connection Pooling**,
kein Keep-Alive. Begründung: Wir messen den realen Overhead einer **neuen Gesprächssession** (so wie
ein Nutzer, der eine Voice-Interaktion startet). Warm-Reuse würde den Verbindungsaufbau verstecken,
der aus EU-Sicht (Distanz zum US-Backend) gerade der interessante Teil ist.

### Verbindungsaufbau in atomaren Submetriken (statt einer Sammel-`connect_ms`)

`connect_ms` als Black-Box wird **abgeschafft**. Stattdessen werden die einzelnen Phasen gemessen und
**roh gespeichert**; „connect total" ist nur noch eine bei Bedarf **abgeleitete Summe**.

| Submetrik | misst | ≈ RTT | gilt für |
|-----------|-------|-------|----------|
| `dns_ms` | Namensauflösung (separat, da oft gecacht) | — | alle |
| `tcp_handshake_ms` | SYN → SYN-ACK | 1 RTT | alle |
| `tls_handshake_ms` | ClientHello → Handshake fertig (TLS 1.3) | 1 RTT | alle |
| `ws_upgrade_ms` | WebSocket-Upgrade + Session-Init | 1 RTT | **nur STT** |
| *(abgeleitet)* `connect_total_ms` | Summe der obigen Phasen | — | in der Auswertung |

**Vorteil:** Dieselbe atomare Phase ist über **alle 9 Endpunkte vergleichbar** (z. B. `tcp_handshake_ms`
aller Anbieter). `tcp_handshake_ms` ist zudem **identisch** mit dem Layer-1-TCP-Ping → die Cross-Layer-
Brücke (`connect ≈ N_RTTs × ping`) wird transparent statt behauptet.

### Zeitmess-Semantik je Kategorie (die Asymmetrie — wichtig!)

Der entscheidende Punkt, der bisher verwirrt hat: **Ab welchem Zeitpunkt läuft die Uhr für das erste
Token/Audio?** Das ist **nicht** über alle Kategorien gleich — und das wird hier explizit deklariert:

| Kategorie | Uhr startet bei | → connect | Erste-Token-Metrik |
|-----------|-----------------|-----------|--------------------|
| **STT** | **erstem Audio-Chunk** (nach dem Connect) | **exklusiv** | `stt_ttft_ms` = `t_first_final − t_first_chunk` |
| **LLM** | **Absenden des Requests** (frische Verbindung) | **inklusiv** | `llm_ttft_ms` = `t_first_token − t_request` |
| **TTS** | **Absenden des Requests** (frische Verbindung) | **inklusiv** | `tts_ttfa_ms` = `t_first_audio − t_request` |

- **STT misst die reine Engine-Verarbeitung** (Connect ist abgezogen, separat in den Submetriken).
  → User-perceived STT-Cold-Start = `connect_total_ms + stt_ttft_ms` (erst in der Auswertung addiert).
- **LLM/TTS messen connect-inklusiv** — das `ttft`/`ttfa` enthält den Verbindungsaufbau bereits.
  Die Submetriken oben werden hier als **separate Referenzmessung** (Wegwerf-Socket) zusätzlich erhoben,
  damit man den connect-Anteil bei Bedarf herausrechnen kann.

> **Konsequenz für die E2E-Pipeline:** `stt_connect + stt_ttft + llm_ttft + tts_ttfa` zählt connect
> **nicht doppelt** — STT trägt connect + ttft (ttft ist post-connect), LLM/TTS tragen nur ttft/ttfa
> (connect bereits enthalten). Cross-Provider wird **nie** rohes connect verglichen, sondern nur der
> user-perceived Cold-Start je Phase.

### Metriken je Kategorie (vollständig)

| Metrik | STT | LLM | TTS | Bedeutung |
|--------|:---:|:---:|:---:|-----------|
| Submetriken (s. o.) | ✓ | ✓ (Referenz) | ✓ (Referenz) | Verbindungsaufbau, atomar |
| `*_ttft_ms` / `ttfa_ms` | ✓ | ✓ | ✓ | Zeit bis erstes Token/Audio |
| `total_ms` | ✓ | ✓ | ✓ | Dauer bis Antwort vollständig |
| `ttl_ms` (Time to Last Token) | — | ✓ | — | nur LLM |

### Feste Inputs (für fairen Vergleich, identisch je Kategorie)

- **STT:** `sample.wav` — „Good morning. I would like to know the current weather forecast for Frankfurt." (~5 s, PCM linear16, 16 kHz, mono)
- **LLM:** „Reply in one short sentence: What is the capital of Germany?" (`max_tokens` = 50, `stream: true`)
- **TTS:** „Good morning! How can I assist you today?"

### Rohdaten-Speicherung (Lehre aus dem alten Lauf — A10/A14)

Der alte Lauf hat Information weggeworfen und damit spätere Fragen unbeantwortbar gemacht. Diesmal wird
**pro Messung vollständig roh gespeichert**, damit WER, Output-Degeneration und Slot-Zuordnung
*ohne Neumessung* prüfbar bleiben:

- **alle Timestamps** einzeln (`t_dns`, `t_tcp`, `t_tls`, `t_ws`, `t_first_chunk`, `t_first_token/audio`, `t_last`, …) — nicht nur die Differenzen,
- **STT:** der **vollständige Transkript-String** (nicht nur die Länge) → ermöglicht WER gegen Referenz,
- **LLM:** echte **Output-Token-/Chunk-Zahl** sowie der Text → Degeneration erkennbar (A10);
  klar benennen, ob gezählt wird = SSE-Chunks oder Tokens (A11),
- **TTS:** Audio-Byte-Zahl / Dauer,
- **Slot-`tag`** explizit mitschreiben → Gruppierung nach `tag`, nicht nach Timestamp-Stunde (verhindert
  den Phantom-Slot, A12),
- **Fehler-/Fehlschlag-Marker** je Run → Grundlage für die Verfügbarkeits-Dimension (A8).

### Fehlerbehandlung

- Jeder Run wird als **Erfolg/Fehlschlag** markiert (Timeout, Verbindungsabbruch, leerer Output).
- „Erfolg" verlangt **inhaltlich gültigen Output** (z. B. LLM-Output ≥ Mindest-Tokenzahl), nicht nur
  „Verbindung stand" — sonst zählen quasi-leere Antworten fälschlich als schnell (A10).
- Fehlschläge werden **gezählt und gespeichert**, nicht still verworfen → Verfügbarkeit ist eine eigene
  Auswertungsdimension, kein blinder Fleck.

---

## Kampagnen-Design (Stand 2026-06-14, vorläufig)

### Eckdaten

- **Dauer:** 7 Tage (volle Woche inkl. Wochenende — deckt Wochentag/Wochenende ab).
- **Slots:** 8 pro Tag, alle 3 h.
- **n pro Slot/Endpunkt:** 100 (komfortabel auch für Perzentile; 50 wäre Minimum für Mediane).
- **Umfang:** 7 × 8 = **56 Slots**; 56 × 100 = **5.600 Messungen/Endpunkt**; × 9 = **50.400 gesamt**.

### Slot-Zeiten (UTC-verankert)

8 feste Slots, alle 3 h, in **UTC** — Tags `00h 03h 06h 09h 12h 15h 18h 21h`:

| Slot-`tag` | 00h | 03h | 06h | 09h | 12h | 15h | 18h | 21h |
|-----------|-----|-----|-----|-----|-----|-----|-----|-----|

- **Warum UTC:** reproduzierbar, **keine Sommerzeit-Sprünge**. Der `tag` wird ins JSONL geschrieben →
  Gruppierung **nach `tag`**, nicht nach Timestamp-Stunde (verhindert den Phantom-Slot, A12).
- **Warum volle 24-h-Abdeckung:** Der Diurnal-Effekt betrifft die **US-Backend-Last**. Die Slots müssen
  sowohl das **US-Tageshoch** (Nachmittag US-Ostküste ≈ 18–22 UTC) als auch das **US-Nachttief**
  (≈ 06–10 UTC) treffen — nicht nur EU-Bürozeiten.

### Reihenfolge innerhalb eines Slots ✅ ENTSCHIEDEN: B (Interleaved)

**Round-Robin:** pro Runde **ein** Cold-Start-Call je Anbieter, **100 Runden**. Damit sind die 9
Anbieter gleichmäßig über den Slot verstreut und sehen dieselbe Zeit-Verteilung der Netzbedingungen →
**fairer Cross-Provider-Vergleich**. *(Batch = Fallback nur, falls Rate-Limits zicken.)*

**Folgen für den Runner (relevant beim Skript-Bau):**
- Schleife: `for runde in range(100): for anbieter in reihenfolge: measure_once()` — jeder Call baut
  eine **frische** Verbindung auf (Cold-Start bleibt erhalten).
- **Startreihenfolge je Runde rotieren** → kein Anbieter misst systematisch immer „zuerst".
- Ein **Fehlschlag blockiert die Runde nicht** → Fehler markieren, weitermachen (Verfügbarkeit, A8).
- Pro Call ein JSONL-Record mit `round`-Index (+ `tag`); `MEASUREMENT_DELAY_S` wirkt zwischen Calls.
- Rate-Limit-freundlicher Nebeneffekt: zwischen zwei Calls **desselben** Anbieters liegen 8 andere Calls.

### Scheduler

`cron` oder `systemd-timer` auf der EC2, ein Trigger **alle 3 h zur vollen UTC-Slot-Stunde**. Ein
Slot-Lauf (9 × 100, ~1,5 s Delay) dauert grob **30–50 min** → passt locker in den 3-h-Abstand. Jeder
Lauf schreibt ein JSONL je Slot **plus** Start-/Ende-Timestamp und Fehlerzähler (für Verfügbarkeit, A8).

### Begründung „warum 7 Tage" (für die Folie)

Aussagekraft hängt an der **Abdeckung der drei Varianzquellen** (Run-Jitter → n; Tageszeit → Slots;
Wochentag → 7 Tage), **nicht** an der Kalenderdauer. Eine BA ist keine Trend-/Langzeitstudie → mehr als
~7–14 Tage bringt kaum Mehrwert.

> Offene Abschnitte (folgen): Hardware/Instanz-Doku des Vantage Points (Instanz-ID, Account, AMI,
> Interface), Scheduler-Konkretisierung (cron/systemd-Unit), Validierungs-/Reproduktionsplan.
