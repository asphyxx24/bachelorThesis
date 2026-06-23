# Modul 4 — C2 (3-Schichten) & C3 (Connect-Heuristik)

**Ziel:** Die methodischen Beiträge der Arbeit (C2 und C3) benennen und gegen einen skeptischen Prüfer verteidigen — als eigenständige *Methoden*-Leistung, klar abgegrenzt vom inhaltlichen Kernbefund C1.

## 4.1 Inhaltlich vs. methodisch — die Landkarte der drei Contributions

Eine wissenschaftliche Arbeit liefert zwei Sorten von Beiträgen: **Erkenntnisse über den Gegenstand** (inhaltlich) und **Erkenntnisse darüber, wie man den Gegenstand zuverlässig untersucht** (methodisch). Dieses Projekt hat beides.

| Kennung | Typ | Aussage | Behandelt in |
|---------|-----|---------|--------------|
| **C1** | **inhaltlich** | „Backend statt Geografie" — Netznähe erklärt die Latenzspreizung **nicht** (wasserdicht ist die *negative* Aussage) | eigenes Modul |
| **C2** | **methodisch** | Drei-Schichten-Methodik + Edge/Host-Grenze — saubere Zerlegung als reproduzierbarer Beitrag | **dieses Modul** |
| **C3** | **methodisch** | Ping-basierte Connect-Klassen-Heuristik — bewusst **kein** Gütemaß | **dieses Modul** |

- **Inhaltlicher Beitrag (C1):** eine Erkenntnis *über* die gemessenen Cloud-AI-Dienste.
- **Methodische Beiträge (C2, C3):** Erkenntnisse *darüber, wie man so etwas sauber misst*. Sie sagen nichts über AI-Anbieter aus — sie sind die **Werkzeuge**, die C1 erst vertrauenswürdig machen. Und „vertrauenswürdig machen" war genau Prof. Wählischs Forderung.

> **Prüfer-Falle:** Wenn nach „dem Beitrag" gefragt wird, **nicht** C1, C2, C3 in einen Topf werfen. C1 ist der Befund, C2/C3 sind die Methode hinter dem Befund.

## 4.2 C2 — Die Drei-Schichten-Methodik

Die Kernidee: Statt API-Latenz als **eine** Zahl zu behandeln, wird sie in drei getrennte Schichten zerlegt, die jeweils **etwas anderes** messen. Die Trennung selbst ist der methodische Beitrag.

| Schicht | Misst | Werkzeuge / Größen | Ziel der Messung |
|---------|-------|--------------------|------------------|
| **Layer 1** (Infrastruktur) | Netz-Nähe zum **Host** | DNS, RTT/Ping (TCP primär, ICMP zur Validierung), TLS, Traceroute | Wo terminiert die Verbindung physisch? |
| **Layer 2** (Paketaufzeichnung) | Pakete auf der Leitung | `tcpdump`/PCAP (Kernel-Zeitstempel) | **Validiert** den Connect-Timer aus Layer 3 |
| **Layer 3** (API-Latenz) | **Engine**-Verarbeitung | Cold-Start: connect-Submetriken + `ttft`/`ttfa`/`ttfp` + `total_ms` | Wie schnell antwortet das echte Backend? |

**Begriffe (beim ersten Auftreten definiert):**

- **DNS** = Domain Name System; übersetzt Hostname → IP-Adresse.
- **RTT** (Round-Trip-Zeit) = Zeit für ein Paket zum Server und zurück.
- **TLS** = Transport Layer Security, die Transport-Verschlüsselung; hier Version 1.3.
- **Traceroute** = Verfahren, das den Weg der Pakete Hop für Hop nachverfolgt.
- **Cold-Start** = jede Messung baut eine **frische** TCP+TLS-Verbindung auf, kein Wiederverwenden (kein Pooling).
- **atomare Submetriken** = der Verbindungsaufbau in kleinste Einzelbausteine zerlegt: `tcp_handshake_ms` (SYN→SYN-ACK), `tls_handshake_ms`, bei STT zusätzlich der WebSocket-Upgrade. „connect total" ist nur die **abgeleitete** Summe.
- **`ttft`** = Zeit bis zum ersten Token (LLM), **`ttfa`** = Zeit bis zum ersten Audio (TTS), **`ttfp`** = Zeit bis zum ersten Partial (STT-Primärmetrik).
- **Engine** = die eigentliche Rechenmaschine im Backend des Anbieters (Modell + Hardware + Serving-Stack).

### Der Mehrwert: Auflösung des „1-ms-Rätsels"

Prof.-Einwand: *„Drei Anbieter mit ~1 ms Layer-1-Latenz — nicht erklärt."* ~1 ms sieht aus wie ein Messfehler. Die Zerlegung zeigt: Diese ~1 ms misst **nicht** die Distanz zum Verarbeitungs-Backend, sondern zu einem **CDN-Edge-Knoten** (Cloudflare, AS13335) nahe Frankfurt. Erst die saubere Schicht-Trennung macht aus der unerklärten Zahl einen dokumentierten Befund (Edge/Host-Grenze, Detail in Modul 6). **Die Zerlegung macht Aussagen reproduzierbar** — das ist der eigentliche C2-Beitrag.

## 4.3 Was Layer 2 ZUSÄTZLICH bringt (Kernfrage)

Auf den ersten Blick wirkt Layer 2 redundant: Der TCP-Handshake wird doch schon in Layer 1 und Layer 3 gemessen. Wozu ein dritter Blick?

**Antwort: Layer 2 liefert keine neue Messung — es VALIDIERT eine bestehende.** Konkret eicht es den **Connect-Timer** `tcp_handshake_ms` aus Layer 3.

- **Validieren** = bestätigen, dass eine andere Messung stimmt.
- **Eichen** = ein Messgerät gegen eine verlässliche Referenz abgleichen (wie eine Waage gegen ein bekanntes Gewicht).
- **Die Referenz** = die PCAP (Paketmitschrift) mit **Kernel-Zeitstempeln** — so nah an der echten Leitung wie möglich.

Das Problem, das Layer 2 löst: Ein App-Timer (`perf_counter` im Mess-Programm) misst nur, was das Programm sieht. Dass er auch das misst, was **auf der Leitung** passiert, muss bewiesen werden.

### Das Paket-Eich-Experiment (je N=30 Cold-Starts, EC2, 2026-06-16)

Verglichen wird die echte Wire-Zeit (`SYN → SYN-ACK` aus der PCAP) gegen den App-Timer — **an beiden Enden der RTT-Skala**:

| Provider | RTT-Klasse | App-`tcp_handshake` (Median) | Wire-`SYN→SYN-ACK` (Median) | Differenz |
|----------|------------|------------------------------|------------------------------|-----------|
| Azure (Italy North) | ~11 ms | 11,29 ms | 11,18 ms | **+0,11 ms** |
| Deepgram (US) | ~139 ms | 139,01 ms | 138,89 ms | **+0,12 ms** |

→ Der App-Timer trifft die echte Wire-Latenz **auf ~0,1 ms genau**, am nahen *und* am fernen Ende. Damit ist der **Connect-Timer paket-geeicht**. Der stets positive Offset (~+0,11 ms) ist die **Kernel-Returnzeit** nach dem SYN-ACK — ein erwartbarer, gerichteter Effekt, kein Rauschen. (idx0-Cold-Start-Outlier ausgeschlossen; Deepgram wire-validiert 28/30, Azure 30/30.)

**Übersetzt für den Prof:** Auf „woher weiß ich, dass deine Software-Timer stimmen?" lautet die Antwort nicht mehr „ich vertraue ihnen", sondern **„ich habe sie gegen die Pakete auf der Leitung geeicht, an beiden Enden der Skala, auf ~0,1 ms genau."** Genau das adressiert das „ich vertraue den Daten nicht" mit Daten.

### ⚠️ Reichweite der Eichung (H2 — nicht überverkaufen!)

| Geeicht (paket-validiert) | NICHT direkt paket-geeicht |
|---------------------------|----------------------------|
| `tcp_handshake_ms` (Connect-Timer, SYN→SYN-ACK) | `ttft`, `ttfa`, `ttfp` |

- Die Erste-Ausgabe-Metriken starten erst **beim Absenden des Requests** im produktiven `httpx`/`websockets`-Stack — nicht im Raw-Socket-Eichpfad.
- Sie nutzen **denselben `perf_counter`-Mechanismus** wie der validierte Connect-Timer → erben dessen Glaubwürdigkeit **indirekt**, sind aber **nicht direkt** gegen Pakete geprüft.
- **Verboten zu sagen:** „alle Layer-3-Zahlen sind paket-validiert." **Korrekt:** Connect-Teil paket-genau; `ttft`/`ttfa`/`ttfp` über den geteilten, validierten Timer.

### Layer 2 ist ein Konsistenz-Check, kein zweiter unabhängiger Beweis

Layer 2 und Layer 3 messen **dasselbe Phänomen** (denselben Handshake). Die Unabhängigkeit liegt allein in der **Mess-Ebene** (Kernel-Zeitstempel vs. App-Timer), **nicht** in zwei verschiedenen Phänomenen. Korrekt formuliert: Layer 2 ist ein **Konsistenz-/Plausibilitäts-Check** der App-Timer auf der Leitung — so bleibt die Aussage verteidigbar.

### Das „Mehr" von Layer 2 (echte Zusatzinfo, Analyse-Phase)

Layer 2 ist reines **Mitschneiden** — keine Metriken während der Aufzeichnung; alles wird **nachgelagert** aus der vollständigen PCAP abgeleitet. Daraus lässt sich gewinnen, was Layer 3 prinzipiell nicht sehen kann:

- **Inter-Arrival-Times** der Antwort-Pakete → netzwerk-seitiger Blick aufs Token-/Chunk-Pacing,
- Anzahl Round-Trips bis „App darf senden" → belegt `connect ≈ N×RTT` mit echten Paketen,
- Retransmissions / Out-of-Order → Verbindungsqualität auf der Route.

Dieser reichere Teil ist **noch offen (Analyse-Phase)** und ausdrücklich **kein Vertrauens-Blocker** — die Eichung selbst steht.

## 4.4 C3 — Die ping-basierte Connect-Heuristik

**C3** = eine **Heuristik** (praktische Faustregel), um aus einfachen Ping-Messungen die **Connect-/Verbindungsklasse** eines Endpunkts abzuschätzen (grob: in welchem Latenzbereich liegt der Verbindungsaufbau). Das Entscheidende ist **nicht** die Heuristik selbst, sondern wie **vorsichtig** sie verkauft wird.

## 4.5 Statistik-Einschub — warum `r` hier trügerisch ist

- **Korrelationskoeffizient `r`** = Zahl zwischen −1 und +1, misst, wie eng zwei Größen einem **linearen** Zusammenhang folgen. `r ≈ +1`: Punkte fast auf einer steigenden Geraden. `r ≈ 0`: kein linearer Zusammenhang.
- **Der alte Fehler (A1):** ein `r = 0,999` als **Gütemaß** verkauft — bei nur **n = 4** Punkten.

Zwei Gründe, warum das trügt:

1. **`r` ist kein Qualitätsmaß für eine Vorhersage.** Es sagt nur, wie gut die Punkte auf *einer* Geraden liegen — nicht, wie klein die tatsächlichen Vorhersagefehler sind.
2. **Hohes `r` bei n=4 ist fast nichtssagend (Überanpassung).** Mit so wenigen Punkten findet man fast immer eine Gerade, die nah an allen vieren liegt — schlicht, weil kaum Spielraum für Abweichung bleibt. Die Gerade hat sich an vier (evtl. zufällige) Punkte **angeschmiegt**, statt einen echten Zusammenhang zu beschreiben. Ein nahezu perfektes `r` aus 4 Punkten ist ein **Warnsignal**, kein Gütesiegel.

**Bessere Argumentation: der Residualfehler.**

- **Residualfehler** = die tatsächliche Abweichung der echten Werte von der vorhergesagten Geraden — also „um wie viele **Millisekunden** liege ich typischerweise daneben". Gemessen in **derselben Einheit** wie die Sache selbst.
- Ehrlich und anschaulich; behauptet nicht, mehr zu wissen, als die wenigen Datenpunkte hergeben.

## 4.6 Warum die Vorsicht eine Stärke ist

Deshalb wird **C3 bewusst NICHT als Gütemaß** verkauft, sondern nur als **grobe Heuristik** zur Klassen-Abschätzung — mit benanntem Residualfehler statt mit `r`.

| | Überverkauft (alt, A1) | Vorsichtig (neu, C3) |
|---|------------------------|----------------------|
| Argument | `r = 0,999` als Beweis | Heuristik + Residualfehler |
| n | 4 | 4 (ehrlich benannt) |
| Angreifbar? | **ja** | **nein** |

> **Merksatz:** Die Zurückhaltung wirkt bescheidener, ist aber wissenschaftlich die **stärkere** Variante, weil sie die Grenzen der eigenen Daten kennt. **Vorsicht = wissenschaftliche Stärke, kein Schwäche-Eingeständnis.**

## 4.7 Die Abgrenzung in einem Satz

- **C1 (inhaltlich):** Netznähe erklärt die Latenzspreizung nicht.
- **C2 (methodisch):** Drei-Schichten-Methodik; Herzstück = Layer 2 eicht den Connect-Timer aus Layer 3 paket-genau (aber **nur** den Connect-Timer, H2).
- **C3 (methodisch):** ping-basierte Connect-Heuristik, **bewusst vorsichtig** und **kein** Gütemaß; Residualfehler statt trügerisches `r` aus n=4.

> **Datenstand:** Alle Kampagnen-Zahlen sind **A4-Mediane über 56 von 56 Slots** (Vollkampagne, abgeschlossen; success-only); die Bootstrap-Konfidenzintervalle stehen noch aus. Die Punktschätzer sind final, die Ordnung ist stabil. Die Layer-2-Eichzahlen (Azure/Deepgram, je N=30, 2026-06-16) sind ein eigenes, abgeschlossenes Experiment.

## Prüf-Fragen

1. Was bringt Layer 2 zusätzlich zu Layer 1+3?
2. Warum ist C3 absichtlich vorsichtig formuliert?
