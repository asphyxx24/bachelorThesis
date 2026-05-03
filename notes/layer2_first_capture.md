# Layer 2 — Erste Paket-Capture (Deepgram WebSocket)

> Status: PROOF-OF-CONCEPT — aufgenommen am 2026-04-08
> Ziel: Methodik validieren und Layer-1-Messungen unabhaengig durch Layer-2-Daten bestaetigen
>
> **Hinweis (2026-05-02):** Dieses Dokument ist ein historischer POC-Bericht.
> Die Provider-Matrix wurde seitdem geaendert (siehe `notes/migration_plan.md`).
> Der Kernbefund (3-RTT-Overhead = ~31% des Latenzbudgets) bleibt gueltig.

---

## Capture-Metadaten

| Feld | Wert |
|---|---|
| **Datei** | `data/layer2/deepgram_capture_20260408_110307.pcap` |
| **Groesse** | 367.810 Bytes (~360 KB) |
| **Pakete** | 392 |
| **Endpoint** | `api.deepgram.com` (66.103.225.58:443) |
| **Protokoll** | TLS 1.3 + WebSocket |
| **Vantage Point** | AWS EC2 eu-central-1 (Frankfurt), Interface `ens5` |
| **Tool** | `tcpdump -i ens5 -w <file> 'host api.deepgram.com'` |
| **Capture-Methode** | Live wahrend 3 paralleler `measure_once()`-Laeufe (n=3) |

**Warum Deepgram?** US-hosted (~150ms RTT laut Schicht 1) — der Anbieter mit dem hoechsten erwarteten Netzwerkanteil. Wenn man irgendwo TCP/TLS-Aufbaukosten sehen will, dann hier.

---

## Schicht-3-Ergebnisse (parallel zur Capture)

3 Messungen via `measurements/layer3_latency/run.py --api stt --n 3`:

| Run | connect_ms | ttft_ms | total_ms | transcript_len |
|---|---|---|---|---|
| 0 | 312 | 612 | 745 | **0** |
| 1 | 308 | 598 | 731 | **0** |
| 2 | 315 | 605 | 738 | **0** |

**Beobachtung 1 — Connect-Phase ist konstant ~310ms.** Das ist exakt **3x RTT** (3 * ~104ms). Erklaerung folgt in der Frame-Analyse.

**Beobachtung 2 — TTFT ist ~600ms.** Davon entfallen ~310ms auf den Verbindungsaufbau (Connect). Der Rest (~290ms) ist Audio-Upload + serverseitige Erkennung + erstes WS-Frame zurueck.

**Beobachtung 3 — `transcript_len: 0` in ALLEN Laeufen.** Methodisches Problem (siehe unten) — die Latenz wird gemessen, aber der Server liefert keine Worte. Muss vor der grossen Messkampagne geklaert werden.

---

## Cross-Validation: Schicht 1 vs. Schicht 2

Eine zentrale wissenschaftliche Frage: **Stimmen die ping-RTTs aus Schicht 1 mit dem, was ich auf der Paket-Ebene tatsaechlich sehe?**

| Metrik | Quelle | Wert |
|---|---|---|
| Ping RTT (median) | Schicht 1 (`layer1_infra/ping.py`) | **~101 ms** |
| TLS Handshake RTT | Schicht 2 (Capture) | **~103 ms** |
| TCP Handshake RTT | Schicht 2 (Capture) | **~104 ms** |

**Ergebnis: Konsistent.** Die Schicht-1-Methodik mit ICMP-Ping liefert dieselbe RTT, die ich auch auf TCP/TLS-Ebene sehe. Das ist eine **unabhaengige Validierung** der Messmethodik.

---

## TCP-Conversations

```
3 TCP-Verbindungen (eine pro Messung), alle zu 66.103.225.58:443
Quell-Ports: 41234, 41248, 41262 (jede Messung neue ephemere Verbindung)
```

| # | Pakete | Bytes | Dauer | Quell-Port |
|---|---|---|---|---|
| 1 | 132 | ~122 KB | 745 ms | 41234 |
| 2 | 128 | ~118 KB | 731 ms | 41248 |
| 3 | 132 | ~120 KB | 738 ms | 41262 |

**Beobachtung:** Jede Messung erzeugt eine **neue TCP-Verbindung** und zahlt damit den vollen Aufbau-Overhead. Das ist eine **bewusste Methodenentscheidung** (Cold-Start-Messung). In Produktion wuerde man Connection-Pooling nutzen — das messe ich bewusst NICHT, weil ich den Worst Case quantifizieren will.

---

## Frame-by-Frame: Anatomie der ersten Verbindung

```
Zeit (ms)   Richtung      Frame                                   Kommentar
─────────   ──────────    ─────────────────────────────────────   ──────────
   0.0      EC2 → DG      TCP SYN                                 Verbindungsaufbau startet
 104.2      EC2 ← DG      TCP SYN-ACK                             ─┐ RTT #1: ~104 ms
 104.3      EC2 → DG      TCP ACK                                  │  (TCP Handshake)
                                                                   │
 104.4      EC2 → DG      TLS ClientHello                          │
 208.5      EC2 ← DG      TLS ServerHello + Cert + Finished       ─┤ RTT #2: ~104 ms
 208.7      EC2 → DG      TLS Finished                             │  (TLS 1.3 Handshake)
                                                                   │
 208.9      EC2 → DG      HTTP GET /v1/listen (WS Upgrade)         │
 312.4      EC2 ← DG      HTTP 101 Switching Protocols            ─┘ RTT #3: ~104 ms
                                                                      (WebSocket Upgrade)
 312.6      EC2 → DG      WS Frame: Audio Bytes (Burst beginnt)
 ...        (Audio-Upload, ca. 100 KB in mehreren Bursts)
 612.1      EC2 ← DG      WS Frame: erstes JSON {is_final: true}
 745.3      EC2 → DG      WS Close
```

**Kernaussage:** Bevor das erste Audio-Byte ueberhaupt gesendet wird, sind **3 RTTs = 312ms** vergangen. Bei einem 1-Sekunden-Budget sind das **31% des gesamten Latenzbudgets** — und es ist noch kein einziges Audio-Sample beim Server.

| Phase | Kosten | % vom 1s-Budget |
|---|---|---|
| TCP Handshake | 1 RTT (~104 ms) | 10.4% |
| TLS 1.3 Handshake | 1 RTT (~104 ms) | 10.4% |
| WebSocket Upgrade | 1 RTT (~104 ms) | 10.4% |
| **Summe Connect** | **3 RTT (~312 ms)** | **31.2%** |
| Upload + Processing + erstes Frame | ~290 ms | 29.0% |
| Restliche WS-Frames + Close | ~133 ms | 13.3% |
| **TOTAL** | **~745 ms** | **74.5%** |

---

## Wichtige Beobachtungen

### B1 — TLS 1.3 (nicht 1.2)
Der Server unterstuetzt TLS 1.3 mit `0-RTT` Faehigkeit, aber wir nutzen es **nicht**, weil wir bewusst kalte Verbindungen messen. Mit TLS 1.3 + Resumption koennte man einen RTT sparen.

### B2 — MTU-Mismatch
- Lokales Interface `ens5`: MTU **8961** (AWS VPC Jumbo Frames)
- Tatsaechliche TCP MSS auf der Strecke: **1460 Bytes** (Standard-Internet-MTU 1500 - 40)

→ AWS routet den Traffic ueber Standard-Internet-MTU sobald die Region verlassen wird. Audio-Bursts werden in viele kleine Pakete zerteilt.

### B3 — Audio-Upload als Burst
Die ~100 KB Audio werden NICHT gleichmaessig gestreamt, sondern als einer/zwei TCP-Bursts mit Pausen dazwischen geschickt. Das ist relevant fuer Schicht 2 — `chunk_size` und Streaming-Verhalten der Client-Library beeinflussen die Charakteristik.

### B4 — Server-Response kommt erst NACH dem Upload
Deepgram liefert das erste WS-Frame mit `is_final: true` erst, nachdem der gesamte Audio-Upload abgeschlossen ist. Das war erwartet (kurzer Audio-Clip), aber bei laengeren Streams sollte man partielle Transkripte sehen — das wird in der naechsten Capture-Iteration explizit getestet.

---

## Methodisches Problem: `transcript_len: 0`

In allen 3 Laeufen liefert Deepgram `is_final: true` zurueck, aber ohne Worte. Moegliche Ursachen:

1. **Audio-Fixture stumm/zu leise:** `fixtures/sample.wav` enthaelt keinen verstaendlichen Sprachinhalt
2. **Sample-Rate-Mismatch:** Client sendet PCM in einer anderen Rate als im URL-Parameter angegeben
3. **Modell erkennt die Sprache nicht:** `nova-3` ist en-US-zentriert, falls die Fixture deutsch ist
4. **Audio zu kurz:** Deepgram liefert leere Transkripte fuer Audio < 100 ms

**Konsequenz fuer die Latenzmessung:** Die TTFT-Messung ist trotzdem valide — sie misst die Zeit bis zum ersten Server-Frame, unabhaengig vom Inhalt. ABER: Eine Messkampagne ueber 14 Tage mit `transcript_len: 0` waere wissenschaftlich angreifbar. **Vor der grossen Kampagne fixen.**

**Naechster Schritt:** `fixtures/sample.wav` mit echter englischer Sprache (z.B. "the quick brown fox jumps over the lazy dog") neu generieren und Sample-Rate-Header pruefen.

---

## IO-Statistik (1-Sekunden-Buckets)

```
Sekunde   Pakete   Bytes      Charakter
───────   ──────   ────────   ─────────────────────────
  0-1      392     367 KB     Alle 3 Messungen + Bursts
```

Alle 3 Messungen passen in eine einzige Sekunde — die kompletten 3 Connect-Tear-Down-Zyklen mit Audio-Upload und Server-Response dauerten zusammen weniger als 1s wall-clock-Zeit. Der serielle Charakter (3 unabhaengige Verbindungen sequentiell) ist trotzdem klar im Capture sichtbar (3 verschiedene Quell-Ports, getrennte SYN-FIN-Zyklen).

---

## Reproduzierbarkeit

```bash
# Auf der EC2-Instanz:
sudo tcpdump -i ens5 -w deepgram_capture.pcap 'host api.deepgram.com' &
TCPDUMP_PID=$!

cd ~/papagei.ai/measurements
.venv/bin/python -m measurements.layer3_latency.run --api stt --n 3 --tag layer2-test

sudo kill $TCPDUMP_PID

# Analyse:
tshark -r deepgram_capture.pcap -q -z conv,tcp           # TCP-Conversations
tshark -r deepgram_capture.pcap -q -z io,stat,1          # IO/Sek
tshark -r deepgram_capture.pcap -Y 'tls.handshake'       # TLS Handshake-Pakete
tshark -r deepgram_capture.pcap -Y 'websocket'           # WebSocket-Frames
```

---

## Naechste Schritte

- [x] `transcript_len: 0` Problem gefixt (sample.wav neu aufgenommen, 2026-05-03)
- [ ] Capture mit **laengerer Audio-Datei** (>10s) — partielle Transkripte sichtbar machen
- [ ] Analoger Capture fuer **Azure TTS** (HTTPS Streaming, Italy North) — Kontrast US/EU
- [ ] Analoger Capture fuer **OpenAI LLM** (HTTPS+SSE) — drittes Streaming-Pattern
- [ ] Bei der grossen Messkampagne: tcpdump im **Ring-Buffer-Modus** parallel laufen lassen
  (`tcpdump -G 3600 -W 24 -w 'capture_%H.pcap'`) — 24h Rolling Window
- [ ] Layer-1-Messung mit **TCP-Connect-RTT** statt ICMP-Ping ergaenzen (Vergleich der Methoden)

---

## Fuer das Betreuungstreffen am 2026-04-09 (HISTORISCH — Treffen war am 09.04.)

**Was zeige ich dem Prof:**

1. Die pcap-Datei selbst (`data/layer2/deepgram_capture_20260408_110307.pcap`)
2. Die obige Frame-Anatomie-Tabelle
3. Den Cross-Validation-Punkt: Schicht 1 ping-RTT == Schicht 2 TCP-Handshake-RTT
4. Die 3-RTT-Erkenntnis (31% des Budgets noch vor dem ersten Audio-Byte)
5. Das `transcript_len: 0` Problem als ehrlich kommunizierte methodische Baustelle

**Was ich vom Prof brauche:**

- Bestaetigung der Capture-Methodik (tcpdump auf ens5, eine pcap pro Provider/Tag?)
- Empfehlung zum Sampling: Permanenter Capture vs. nur waehrend Schicht-3-Laeufen?
- Frage: Wie viele Captures pro Provider sind statistisch ausreichend?
