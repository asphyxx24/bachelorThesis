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
- **Software-Voraussetzung (Reproduzierbarkeit, A1):** Alle Messungen laufen auf der EC2 (Ubuntu) mit
  **echtem OpenSSL 3.x**. macOS-Python ist gegen **LibreSSL 2.8.3** gelinkt und meldet TLS-Versionen
  systematisch falsch (alle Hosts als TLS 1.2 statt 1.3) → **`tls_version` wird ausschließlich auf der
  EC2 erhoben**, der Mac dient nur der Skript-Entwicklung. Pro Messung wird `ssl.OPENSSL_VERSION`
  mitgeloggt (LibreSSL-Zeilen sind verwerfbar); Details + Cross-Check in `mess_kommandos.md` (Layer-1-TLS).
- **Instanz-Typ (A6): `c6i.large` — bewusst NICHT-burstable.** Begründung: Burstable-Typen (`t2`/`t3`,
  wie die **alte** `t3.small`) laufen auf CPU-Credits; bei Credit-Erschöpfung drosselt AWS die CPU →
  ms-Latenz-Timer springen **ohne Netz-Ursache** (= unerklärte Varianz, die der Prof bemängelt).
  `c6i.large` (2 vCPU Intel Ice Lake, 4 GiB) hat garantierte CPU und reicht für die netzwerk-gebundene
  Mess-Last (Alternative `m6i.large` = mehr RAM, hier unnötig). **AMI, Kernel, vCPU, EBS-Typ, AZ werden
  fixiert** und im `run_meta` festgehalten (s. A5); **CPU-Steal-Time** pro Slot wird mitgeloggt → das
  Fehlen von Throttling wird **empirisch belegt**, nicht nur behauptet.
- **IP-Version: durchgängig IPv4 (alle Schichten).** Mehrere Hosts (OpenAI/Groq/Mistral hinter
  Cloudflare) sind **dual-stack** (A- *und* AAAA-Record). Layer 1 misst über `gethostbyname` ohnehin
  IPv4; **Layer 3 wird ebenfalls auf IPv4 gezwungen** (httpx mit `local_address="0.0.0.0"`). Begründung:
  Nur so messen **alle Schichten dieselbe Adresse/denselben Pfad** — sonst verglichen die Cross-Layer-
  Brücke (`connect_total_ms ≈ N_RTTs × ping`) und die Edge-/Host-Klassifikation (ASN/Traceroute auf der
  IPv4) eine **andere** IP als der eigentliche Mess-Request. Im ersten Echtlauf wählte httpx unkontrolliert
  **IPv6** (`2606:4700:…`), während Layer 1 die IPv4 (`104.18.…`) maß — genau diese Inkonsistenz schließt
  das Erzwingen. **Limitation (Diskussion):** Ein Dual-Stack-Client im Feld nähme evtl. IPv6 (Happy
  Eyeballs); wir messen bewusst den IPv4-Pfad. Zum **selben** CDN-Edge ist die Latenz über v4 vs. v6
  praktisch gleich, und die untersuchten Effekte (Engine vs. Geografie) sind um Größenordnungen größer →
  Konsistenz wiegt schwerer als die Adressfamilien-Wahl. Keiner der 9 Hosts ist IPv6-only, das Erzwingen
  ist also für alle sicher.

## Drei-Schichten-Architektur

- **Layer 1 (Infrastruktur):** DNS, RTT/Ping, TLS-Handshake, Traceroute → misst die **Netzwerk-Nähe**
  zum **Host**.
- **Layer 2 (Paketaufzeichnung):** tcpdump/PCAP → belegt die Protokoll-Struktur (Handshake-Abfolge).
- **Layer 3 (API-Latenz):** Cold-Start — Verbindungsaufbau in **atomaren Submetriken**
  (`tcp_handshake_ms`, `tls_handshake_ms`, `ws_upgrade_ms`) + Erste-Ausgabe-Metrik + `total_ms` → misst
  die **Engine-Verarbeitung** über die volle **URL**. Erste-Ausgabe-Metrik: STT **`ttfp`** (Time-to-first-
  Partial, primär) bzw. `ttft`/`ttfa` (LLM/TTS). *(Sammel-`connect_ms` abgeschafft — s. Layer-3-Abschnitt.)*

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
   `connect_total_ms` in Layer 3 zerlegt (`tcp_handshake_ms`). Layer 1 und Layer 3 sprechen damit
   dieselbe Sprache; die Cross-Layer-Argumentation (`connect_total_ms ≈ N_RTTs × ping`) wird konsistent.

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

## Layer 1 — Endpunkt-Terminierung (Edge vs. Host) — der zentrale Erklärschritt (A3)

### Warum dieser Schritt existiert (Prof-Einwand)

Der schärfste offene Einwand war: **„Drei Anbieter mit sehr niedriger Layer-1-RTT aus Frankfurt — nicht
erklärt."** Antwort: Bei einem Teil der Endpunkte (OpenAI, Groq, Mistral) terminiert die TCP-Verbindung
an einem **CDN-Edge-Knoten (Cloudflare) in/nahe Frankfurt**, nicht am eigentlichen Backend. Die ~1-ms-RTT
ist dann eine **reale Infrastruktur-Eigenschaft des Edge**, kein Messfehler — und sie sagt **nichts** über
die Distanz zum echten Verarbeitungs-Backend. Dieser Schritt **belegt pro Endpunkt**, wo die Verbindung
physisch terminiert, und macht damit aus einer unerklärten Zahl einen dokumentierten Befund (Contribution C2).

### Klassifikator (Konjunktion — alle drei Bedingungen müssen erfüllt sein)

Ein Endpunkt gilt als **Edge-terminiert** genau dann, wenn **(a) ∧ (b) ∧ (c)**:

| Bedingung | Operationalisierung | Werkzeug |
|-----------|---------------------|----------|
| **(a)** TCP-RTT ≈ **1–2 ms** aus FRA | gemessener Minimal-TCP-Ping (Port 443) liegt im einstelligen ms-Bereich | Layer-1-TCP-Ping (rev.ai blockt ICMP → **TCP** ist der Beleg) |
| **(b)** Ziel-IP in **CDN-ASN** | aufgelöste IP gehört zu Cloudflare **AS13335** (bzw. anderem CDN-AS) | ASN-/Whois-Lookup (Team-Cymru, s. `mess_kommandos.md`) |
| **(c)** traceroute **bricht am CDN ab** | letzte sichtbaren Hops sind CDN-Infrastruktur, kein Durchstich zum Backend | `traceroute` (+ TCP-SYN-Variante `-T -p 443`) |

Sonst gilt der Endpunkt als **Host-terminiert** (Verbindung endet am realen Backend des Providers).

### Wichtige Präzisierungen (damit der Befund verteidigbar ist)

- **Die ~1-ms-RTT ist der Terminierungs-Nachweis, nicht der IP-Besitz.** Argumentiert wird über die
  *gemessene Latenz* + AS + Route, nicht darüber, „wem die IP gehört".
- **Niedrige RTT ≠ automatisch Edge.** Azure Italy North hat eine **niedrige** RTT (~12 ms), ist aber
  **Host** — weil es das echte EU-Rechenzentrum ist (AS8075 Microsoft, **kein** CDN-AS → Bedingung (b)
  scheitert). Genau das macht die STT/TTS-Inversion glaubwürdig: Azures Vorsprung ist **realer**
  Backend-Standort, kein Edge-Artefakt.
- **Hohe RTT ≠ automatisch Host, aber hier eindeutig:** Deepgram trägt zwar historisch ein
  „Anycast"-Label, misst aber **~102–148 ms** → Bedingung (a) scheitert → **Host** (Multi-DC-Round-Robin,
  s. `anbieter_auswahl.md` / A9).
- **Konsequenz für die Cross-Layer-Brücke:** Bei Edge-terminierten Anbietern ist `connect ≈ N×ping`
  **tautologisch** (gleicher Knoten) und zählt **nicht** als Beleg → nur host-terminierte Anbieter
  stützen die Brücke (s. Audit B). Bei Edge-Anbietern misst die RTT den FRA-Edge, **nicht** das Backend
  → die Backend-Region ist via RTT **nicht** bestimmbar (Limitation, betrifft v.a. Mistral als EU-LLM).

### Ergebnis-Artefakt

Die Klassifikation jedes Endpunkts steht als **feste Spalte „Terminierung (Edge/Host)"** in
`api_endpunkte.md` (§Terminierung) = **Single Source of Truth**. Die Werte dort sind aus den
DNS-/ASN-Beobachtungen **vorläufig** gesetzt und werden auf der EC2 per TCP-Ping + traceroute **bestätigt**.

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
| **STT** | **erstem Audio-Chunk** (nach dem Connect) | **exklusiv** | **`stt_ttfp_ms` = `t_first_partial − t_first_chunk` (PRIMÄR)** · `stt_ttft_ms` = `t_first_final − t_first_chunk` (sekundär) |
| **LLM** | **Absenden des Requests** (frische Verbindung) | **inklusiv** | `llm_ttft_ms` = `t_first_token − t_request` |
| **TTS** | **Absenden des Requests** (frische Verbindung) | **inklusiv** | `tts_ttfa_ms` = `t_first_audio − t_request` |

- **STT misst Netz-Roundtrip + Engine-Reaktion** (Connect ist abgezogen, separat in den Submetriken; der
  in `ttfp` verbleibende ~1-RTT-Netzanteil ist via Layer-1-RTT herausrechenbar — keine *reine* Rechenzeit).
  → User-perceived STT-Cold-Start bis erstes Wort = `connect_total_ms + stt_ttfp_ms` (Primär; in der
  Auswertung addiert). Variante „bis Final" = `connect_total_ms + stt_ttft_ms` (enthält Endpointing).
- **LLM/TTS messen connect-inklusiv** — das `ttft`/`ttfa` enthält den Verbindungsaufbau bereits.
  Die Submetriken oben werden hier als **separate Referenzmessung** (Wegwerf-Socket) zusätzlich erhoben,
  damit man den connect-Anteil bei Bedarf herausrechnen kann.

> **Konsequenz für die E2E-Pipeline:** `stt_connect + stt_ttfp + llm_ttft + tts_ttfa` zählt connect
> **nicht doppelt** — STT trägt connect + ttfp (post-connect, endpointing-frei), LLM/TTS tragen nur
> ttft/ttfa (connect bereits enthalten). Cross-Provider wird **nie** rohes connect verglichen, sondern
> nur der user-perceived Cold-Start je Phase.

### Metriken je Kategorie (vollständig)

| Metrik | STT | LLM | TTS | Bedeutung |
|--------|:---:|:---:|:---:|-----------|
| Submetriken (s. o.) | ✓ | ✓ (Referenz) | ✓ (Referenz) | Verbindungsaufbau, atomar |
| `ttfp_ms` (Time-to-first-Partial) | ✓ (**primär**) | — | — | STT: Zeit bis erstes Live-Wort (endpointing-frei) |
| `*_ttft_ms` / `ttfa_ms` | ✓ (sekundär) | ✓ | ✓ | Zeit bis erstes Token/Audio (STT-ttft enthält Endpointing) |
| `total_ms` | ✓ | ✓ | ✓ | Dauer bis Antwort vollständig |
| `ttl_ms` (Time to Last Token) | — | ✓ | — | nur LLM |

#### Primär- vs. Sekundärmetrik — Output-Mengen-Confound (A8)

- **Primär (Engine-Metrik): `ttft`/`ttfa`.** Zeit bis zum **ersten** Token/Audio ist von der Output-**Menge**
  **unabhängig** → fairer Engine-Vergleich. Feste Inputs standardisieren nur die **Eingabe**; die
  Ausgabemenge ist es **nicht** (`max_tokens=50` ist Obergrenze, kein Fixwert).
- **Sekundär: `total_ms`/`ttl_ms`.** Skalieren mit der Output-Menge — ein wortkarges Modell „gewinnt"
  durch Knappheit, nicht durch Geschwindigkeit. Daher nur sekundär bzw. **pro Token normalisiert**
  (`ttl_ms / output_tokens`) berichten; die rohe Output-Menge wird mitgespeichert (A10/A11).
- **TTS-Inversion vom Output-Mengen-Confound nicht betroffen** (`ttfa` = erstes Audio, mengen-unabhängig);
  die TTS-Format-Achse ist über mp3-Pinning aller drei TTS-Anbieter geschlossen (s. `api_endpunkte.md`, A8).

#### STT-Primärmetrik: `ttfp` (Time-to-first-PARTIAL) + Realtime-Pacing — und warum

> Vollständige Anbieter-Recherche + Belege: **`AUDIT_stt_methodik_2026-06-16.md`**.
> Diese Entscheidung wurde adversarisch gegengeprüft (ultracode, 2026-06-16, 23 Befunde) und danach
> korrigiert — die hier stehende Fassung ist die geprüfte. Kurzfassung:

**Das Problem (Endpointing-Confound).** STT-`ttft` ist *Time-to-first-FINAL* — die Zeit bis das erste
**finalisierte** Transkript kommt. Ein Provider erklärt einen Satz aber erst dann für „final", wenn er
**eine feste Stille-Spanne abgewartet** hat (Endpointing / Voice-Activity-Detection). Diese Wartezeit ist
**Provider-Politik, keine Rechenzeit.** Empirisch im Pilot: Azure-`ttft` war **rock-konstant ~1722 ms**
(CV 0,9 % über 400 Calls) — eine solche Konstanz ist **stark konsistent mit einem festen Timer** (Stille-
Countdown), nicht mit Engine-Last. Stärkster Beleg: bei **identischem Input** schwankt Deepgram um
**CV ~104 %** (0,4–3,7 s) — die Konstanz ist also **provider-spezifisch**, kein Input-Artefakt. `ttft`
vergleicht damit Engine **+** unterschiedliche Stille-Politik in einer Zahl → als Engine-Maß **unfair**.

**Warum wir das Endpointing NICHT angleichen können** (das wäre der naheliegende Fix gewesen):

| Provider | Endpointing einstellbar? | Befund |
|----------|--------------------------|--------|
| Deepgram | (kein fester Timer) | finalisiert auf `CloseStream`/Stream-Ende; bei Realtime-Audio emittiert es vorher Interims |
| Rev.ai | **nein** | kein dokumentierter Parameter auf dem Streaming-Endpunkt |
| Azure | **nur über das SDK** | `Speech_SegmentationSilenceTimeoutMs` ist **ausschließlich** im Azure-**SDK** dokumentiert, **nicht** im rohen WebSocket-Protokoll, das diese Arbeit (bewusst, Cold-Start ohne SDK) nutzt → über unsere Verbindung **nicht erreichbar**; Azure läuft auf server-seitigen Defaults |

Ein faires „alle warten gleich lang" ist damit **technisch unmöglich**, ohne das Cold-Start-/Kein-SDK-Design
zu brechen (das wäre ein größerer Methodik-Bruch als der Confound selbst).

**Die Lösung: `ttfp` (erstes Live-Wort), gemessen unter Realtime-Pacing.** Statt das Warten anzugleichen,
**messen wir davor**: die Zeit bis zum **ersten Interim-/Partial-Transkript** (Deepgram: erstes `Results`;
Rev.ai: erstes `partial`; Azure: erstes `speech.hypothesis`). Das erste Live-Wort kommt **vor** der Stille-
Wartezeit → es enthält das Endpointing **per Konstruktion nicht**.
- **Realtime-Pacing (zwingend):** Das Audio wird im **1×-Echtzeit-Takt** gestreamt (~128 ms je 4096-B-Chunk),
  Senden und Empfangen laufen **parallel**. Grund: nur bei echtzeit-eintreffendem Audio liefern **alle drei**
  Provider echte Interims — beim Audio-**Dump** sendet Deepgram vor dem Final keins, dann wäre Deepgrams `ttfp`
  sein **Final** (anderer Meilenstein als Azures/Rev.ais Teilwort → unfairer Cross-Provider-Vergleich). Pacing
  macht den Meilenstein bei allen gleich (echtes erstes Interim) **und** entspricht dem Echtzeit-Voice-Thema.
  *(Belegt im Smoke-Test: Audit-Feld `ttfp_is_final=False` bei allen dreien — das erste Wort ist überall ein
  echtes Interim, nicht das Final.)*
- **Symmetrisch zu TTS-`ttfa`** (erstes Audio) und LLM-`ttft` (erstes Token): „Zeit bis erstes Ausgabe-Element".

**Zwei ehrliche Grenzen von `ttfp` (explizit deklariert, nicht weggeredet):**
1. **Endpointing-frei, aber nicht *politik*-frei.** Wann ein Provider sein erstes Interim sendet (Puffer-Tiefe,
   Konfidenzschwelle, Batch-Granularität) ist selbst Provider-Politik. `ttfp` entfernt den *Stille-Timer*-
   Confound, nicht jeden Politik-Anteil → **kleine** `ttfp`-Unterschiede nicht als Engine-Tempo überinterpretieren.
2. **`ttfp` enthält ~1 In-Band-RTT** (Audio hin + Partial zurück). Es ist „**Netz-Roundtrip + Engine-Reaktion**",
   **nicht** reine Rechenzeit. Für *Engine*-Aussagen im Cross-Provider-Vergleich ist der RTT-Anteil
   (via Layer-1-RTT / `tcp_handshake_ms`) **herauszurechnen** — auf der STT-Achse sitzt Azure in der EU (~11 ms),
   die US-Anbieter bei ~138 ms; ein nackter `ttfp`-Rang würde **Geografie** mit Engine verwechseln.

**`ttft` (final) bleibt Sekundärmetrik — ehrlich beschriftet** („Time-to-first-final, **enthält Endpointing**").
Die Differenz **`ttft − ttfp`** macht die Stille-Wartezeit **sichtbar/quantifizierbar** (eigenes Teilergebnis
statt Störgröße) — das ist der eigentliche diagnostische Wert von `ttfp`.

**Belegmessung (Entwicklungs-Smoke 2026-06-16, n=1/Provider — auf dem *Mac*, NICHT dem Vantage-Point EC2,
nur zur Methoden-Illustration; verbindliche Zahlen liefert die EC2-Kampagne):**

| Provider | RTT (FRA) | `ttfp` (erstes Interim) | `ttft` (final, paced) | erstes Wort |
|----------|-----------|-------------------------|-----------------------|-------------|
| Azure (EU, Italy North) | ~11 ms | ~1093 ms | ~5074 ms | „good" (Interim) |
| Deepgram (US) | ~138 ms | ~1045 ms | ~4812 ms | „Good" (Interim) |
| Rev.ai (US) | ~138 ms | ~1563 ms | ~5264 ms | „good" (Interim) |

> *(Unter Pacing liegt `ttft` ~5 s, weil das Final erst nach dem ~4,84-s-Audiostrom + Stille-Warten kommt;
> die Endpointing-Wartezeit wird in der Auswertung als `ttft − audio_upload_ms` isoliert, alle Rohzeiten je
> Call gespeichert.)*

> **Korrekte C1-Logik (geprüft — frühere „Azure ist der schnellste STT"-Formulierung war falsch):**
> Ein Cross-Provider-`ttfp`-Rang taugt **nicht** als Engine-Beleg, weil er den RTT-/Geografie-Anteil enthält
> (Azure ist in-Region begünstigt). Der wasserdichte Beleg für **„Engine/Backend schlägt Geografie"** ist die
> **Inversion *innerhalb* von Azure** auf `ttft`/`ttfa`: **gleicher** Anbieter, **gleiches** RZ, **gleiche**
> ~11 ms RTT — STT langsam (`ttft`), TTS schnell (`ttfa`). Da Geografie hier **konstant gehalten** ist, *kann*
> die Differenz nicht Geografie sein → sie **muss** Backend sein. `ttfp` ist dabei das **Diagnose-Werkzeug**,
> das Azures STT-Langsamkeit **zerlegt** (`ttft − ttfp` = Stille-Warten = Backend-Politik) — es **erklärt** die
> Inversion, es **ersetzt** sie nicht durch ein cross-provider Tempo-Ranking. So bleibt C1 intakt und ist
> sauberer belegt. (Konsistent mit `CLAUDE.md` C1; Details `AUDIT_stt_methodik_2026-06-16.md`.)

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
- **Modell-Version je Run (A2):** angefragte Modell-ID **und** die vom Server zurückgemeldete
  `effective_model` (LLM: `chunk.model` aus dem SSE; STT/TTS: opportunistisch aus Response-Headern) →
  stiller Backend-Drift wird sample-genau erkennbar statt unbemerkt. Pinning-Status je Endpunkt:
  `api_endpunkte.md` (§Modell-Pinning).
- **TTS:** Audio-Byte-Zahl / Dauer,
- **Slot-`tag`** explizit mitschreiben → Gruppierung nach `tag`, nicht nach Timestamp-Stunde (verhindert
  den Phantom-Slot, A12),
- **Fehler-/Fehlschlag-Marker** je Run → Grundlage für die Verfügbarkeits-Dimension (A8).
- **Verbundene Ziel-IP je Run (A5):** direkt nach dem Connect `sock.getpeername()[0]` als `resolved_ip`
  ins JSONL — **Kosten ~null, sample-genau**. Ohne sie ist über 56 Slots nicht belegbar, **welcher**
  (Cloudflare-/Deepgram-)Edge bzw. DC ein Latenz-Sample bedient hat → blockiert sonst den
  Edge-vs-Backend-Beleg (A3) und erklärt die Deepgram-RTT-Streuung (A9).
- **HTTP-Version je Run (A5):** `response.http_version` roh mitschreiben (robuster als das Pinnen von
  `httpx[http2]`).

### Run-Metadaten je Slot (`run_meta`-Record, A5/A6)

Pro Slot-Lauf **ein** zusätzlicher `run_meta`-Record (einmalig, nicht pro Messung) macht jeden Slot
reproduzier- und zuordenbar:

- `git_commit` (Skript-Stand), `python_version` + **Lockfile-Hash** (bzw. `pip freeze`),
- `instance_id`, `instance_type`, `ami_id`, `kernel`, `iface`, `region`/`az`, `delay_s`,
- **CPU-Steal-Time** (`/proc/stat`) zu Slot-Beginn/-Ende → belegt empirisch, dass kein burstable-Throttling
  die ms-Timer verfälscht (s. A6),
- `ssl.OPENSSL_VERSION` (LibreSSL-Slots sofort verwerfbar, s. A1), `chronyc tracking`-Schnappschuss
  (Zeitbasis, s. Audit D).

> **Lockfile-Pflicht:** `requirements.txt` (`>=`) reicht **nicht** für Reproduktion → ein Lockfile
> (`uv.lock` bzw. eingefrorenes `pip freeze`) wird **committet**; sein Hash steht im `run_meta`.

### Fehlerbehandlung

- Jeder Run wird als **Erfolg/Fehlschlag** markiert (Timeout, Verbindungsabbruch, leerer Output).
- „Erfolg" verlangt **inhaltlich gültigen Output** (z. B. LLM-Output ≥ Mindest-Tokenzahl), nicht nur
  „Verbindung stand" — sonst zählen quasi-leere Antworten fälschlich als schnell (A10).
- Fehlschläge werden **gezählt und gespeichert**, nicht still verworfen → Verfügbarkeit ist eine eigene
  Auswertungsdimension, kein blinder Fleck.

### Erfolgskriterien & Timeouts je Kategorie (A7)

Ohne fixe Schwellen ist „Verfügbarkeit X %" nicht reproduzierbar/angreifbar → hier festgeschrieben:

| Kategorie | Connect-Timeout | Response-Timeout | Mindest-Output für „Erfolg" |
|-----------|-----------------|------------------|------------------------------|
| **STT** | 10 s | **30 s** | nicht-leeres **Final**-Transkript (getrimmt ≥ 1 Wort) |
| **LLM** | 10 s | **30 s** | getrimmter Text **≥ 1 Wort** **und** **≥ 3 SSE-Content-Chunks** (fängt Degeneration, A10) |
| **TTS** | 10 s | **30 s** | Audio-Body **≥ 1.000 Bytes** (dekodierbar, nicht-leer) |

- **Timeout-Asymmetrie vereinheitlicht (A7):** alter Lauf hatte STT 20 s vs LLM/TTS 30 s ohne Begründung
  → **einheitlich 30 s** Response-Timeout (großzügiger Hang-Fang, **keine** Erwartungs-Latenz; echte ttft
  liegt weit darunter). Connect-Timeout einheitlich 10 s.
- **Schwellen sind nachträglich justierbar:** Da Roh-Text, Chunk-Zahl und Byte-Zahl **vollständig**
  gespeichert werden (A5/A10), kann die Erfolgsdefinition in der Analyse verschärft/gelockert werden,
  **ohne** neu zu messen. Die Tabelle ist der **Default**, nicht in Stein.
- **Fehler-Enum (roh je Run gespeichert):** `timeout` · `connection_reset` · `http_4xx` · `http_5xx` ·
  `empty_output` · `degenerate_output` (Output < Schwelle). → Grundlage der Verfügbarkeits-/Joint-Completion-Dimension (A8).

---

## Kampagnen-Design (Stand 2026-06-14, vorläufig)

### Eckdaten

- **Dauer:** 7 Tage (volle Woche inkl. Wochenende — deckt Wochentag/Wochenende ab).
- **Slots:** 8 pro Tag, alle 3 h.
- **n pro Slot/Endpunkt:** 100 (komfortabel für Median/p50/p90 je Slot; 50 wäre Minimum für Mediane).
  Für **p95/p99 reicht n=100 je Slot nicht** → nur gepoolt über alle 56 Slots, s. §Aggregation & Inferenz (A4).
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

---

## Aggregation & Inferenz (A4)

> Ohne festgeschriebene Regel ist die Headline („Deepgram < Azure") **nicht reproduzierbar definiert** —
> verschiedene Aggregationen liefern verschiedene Zahlen. Dieser Abschnitt legt die **eine** Regel fest
> und gibt jeder Zahl ein Konfidenzintervall (die Punktschätzer-Angriffsfläche des Prüfers).

### (a) Aggregationsregel — wie aus 5.600 Zahlen EINE wird

**Headline = Median der Slot-Mediane** (zweistufig): pro (Endpunkt × Slot-`tag`) den Median über die
~700 Runs (7 Tage × 100) bilden → 8 Slot-Mediane; **Median dieser 8** = Headline-Zahl je Endpunkt.

- **Warum nicht gepoolt:** Ein gepoolter Median über alle ~5.600 gewichtet Slots mit mehr **erfolgreichen**
  Runs stärker — d.h. Tageszeiten mit besserer Verfügbarkeit ziehen die Zahl. Bei Anbietern mit
  tageszeitabhängigem Ausfall (Groq ~33 % zu US-Stoßzeiten) verschönert das die Zahl. Der zweistufige
  Median gibt **jeder Tageszeit gleiches Gewicht** → robust gegen das Verfügbarkeits-Confound (A8).
- **Sensitivität:** Der **gepoolte Median** wird zusätzlich berichtet. Stimmen beide überein → Befund
  robust; laufen sie auseinander → das ist selbst ein (diurnal-/ausfall-)Befund.
- **Diurnal-Profil:** Die 8 Slot-Mediane (über 7 Tage) sind zugleich das **Tageszeit-Profil** je Endpunkt
  (Auswerteachse für US-Backend-Last, s. Audit D).

### (b) Perzentile — ehrlicher Anspruch

- **p50/p90:** slot-aufgelöst belastbar (genug Runs je Slot).
- **p95:** nur **gepoolt** (über alle 56 Slots) + Bootstrap-CI — nicht slot-weise (zu wenig Runs).
- **p99:** **nicht** aus n=100 je Slot behaupten (p99 von 100 ≈ das Maximum) → nur über **alle 56 Slots**
  gepoolt, oder explizit als **Limitation** benennen.
- **Faustregel** (festgeschrieben): ein Perzentil q ist erst stabil, wenn `n·(1−q) ≥ 5–10`.
- Verteilungen sind rechtsschief (CV ~87 % in der Vorkampagne) → **Bootstrap**-CI statt t-Intervall.

### (c) Konfidenzintervalle & Vergleiche — gegen nackte Punktschätzer

- **Jede** berichtete Median-/Perzentil-Zahl bekommt ein **Bootstrap-95%-CI**.
- **Cross-Provider „X schneller als Y"** primär über **Differenz-Bootstrap** bzw. **Mann-Whitney-U** —
  **nicht** über „die CIs überlappen sich nicht" (disjunkte CIs sind ein schwächerer Test).
- Die Aussage **„X gewinnt in N/56 Slots"** wird als **Slot-Median-Vorzeichentest** gekennzeichnet
  (auf Slot-Median-Ebene), nicht als Roh-Run-Vergleich — die rohen Tails überlappen.

### Werkzeuge

`numpy`/`scipy` für Mediane/Perzentile/Mann-Whitney; eigener Bootstrap (Resampling der Slot-Mediane bzw.
gepoolten Runs, ≥10.000 Resamples). In `requirements.txt` sicherstellen.

---

## E2E-Auswertung (Pipeline-Gesamtlatenz, A6/A8-Bezug)

> Nicht Median-Addition über die drei Phasen (alter Fehler), sondern echte Faltung + Verfügbarkeit.

- **Monte-Carlo-Faltung** statt Median-Summe: pro Pipeline-Kandidat (STT×LLM×TTS) aus den empirischen
  Verteilungen ziehen → E2E-Verteilung mit p50/p90/p95 **+ CI** (statt drei addierter Punktschätzer).
- **Joint-Completion / Pareto-Front:** Latenz **gegen** Zuverlässigkeit (Ausfallrate) auftragen — ein
  „Gewinner" wird erst **nach** der Front benannt (Groq ist schnell, aber ~33 % Ausfall → nicht pauschal
  „beste Pipeline").

---

> Offene Abschnitte (folgen): konkrete Instanz-Werte beim Start eintragen (Instanz-ID, Account, AMI,
> Interface — Typ `c6i.large` und die zu erfassenden Felder stehen bereits, s. Vantage Point + `run_meta`/A5),
> Scheduler-Konkretisierung (cron/systemd-Unit), Validierungs-/Reproduktionsplan.
