# Vorbereitung Betreuer-Treffen — 2026-05-05

## Was ist das Projekt?

Wir messen die **Cold-Start-Latenz** von 9 Cloud-AI-APIs, die zusammen eine
Voice-Pipeline bilden: Sprache rein (STT) → Text verarbeiten (LLM) → Sprache raus (TTS).

**Cold-Start** heisst: Jede Messung baut eine komplett neue Verbindung auf —
kein Connection Pooling, kein Warm-Cache. Das simuliert den Moment, wenn ein
Nutzer "Hey Alexa" sagt und eine neue Session beginnt.

**Vantage Point:** AWS EC2 t3.small in Frankfurt (eu-central-1).
Fix, reproduzierbar, keine WLAN-Schwankungen.

**Kampagne:** 100 Messungen pro Provider, alle 3 Stunden, 14 Tage lang.
Ergibt ~100.800 Datenpunkte.

---

## Die zwei Beispiel-Provider

Wir erklaeren alles an **Deepgram STT** und **Azure STT** — beide nutzen
WebSocket, aber mit voellig unterschiedlichem Ergebnis:

| | Deepgram | Azure |
|---|---------|-------|
| **Region** | USA (Anycast) | Italien (Italy North) |
| **Ping RTT** | ~102ms | ~11ms |
| **Protokoll** | WebSocket (Standard) | WebSocket (proprietaer) |
| **connect_ms** | ~337ms | ~265ms |
| **TTFT** | ~463ms | ~1718ms |

Auf den ersten Blick paradox: Azure ist **10x naeher**, hat aber **4x laengere TTFT**.
Die drei Layer erklaeren warum.

---

## Layer 1: Infrastruktur — "Wie weit weg ist der Server?"

### Was wird gemessen?

| Messung | Was passiert | Werkzeug |
|---------|-------------|----------|
| **DNS** | Hostname → IP-Adresse aufloesen | `dig` / Python `dns.resolver` |
| **Ping** | ICMP-Paket hin und zurueck = 1 RTT | `ping` |
| **TLS** | Verbindung aufbauen, Handshake-Dauer messen | `curl` mit Timing |
| **Traceroute** | Welchen Weg nehmen die Pakete? Wie viele Hops? | `traceroute` |

### Wie entsteht ein Layer-1-Datensatz?

Automatisch per Cron-Job auf EC2:
- **Alle 6 Stunden:** DNS + Ping fuer alle 9 Endpoints
- **Taeglich 05:30 UTC:** DNS + Ping + TLS + Traceroute (ausfuehrlich)

Das Python-Skript (`measurements/layer1/run.py`) iteriert ueber alle 9 Hosts
aus `measurements/config.py` und schreibt JSONL-Dateien nach `data/layer1/`.

### Beispieldaten

**Deepgram (USA):**
```
Hostname: api.deepgram.com
DNS: 6 IPs (Anycast — mehrere Standorte weltweit)
Ping: 102ms (Frankfurt → USA)
Traceroute: ~15 Hops, ueber DE-CIX → Tier-1-Provider → USA
```

**Azure (Italien):**
```
Hostname: italynorth.stt.speech.microsoft.com
DNS: 3 IPs
Ping: 11ms (Frankfurt → Norditalien, ~800km)
Traceroute: ~8 Hops, innerhalb Europas
```

### Was sagt uns das?

- Deepgram ist ~10x weiter entfernt als Azure (102ms vs. 11ms RTT)
- Jedes Mal, wenn ein Paket hin und zurueck muss (ein "Roundtrip"),
  kostet das bei Deepgram 102ms, bei Azure nur 11ms
- Die Frage ist: Wie oft muss ein Paket hin und zurueck, bevor die
  Verbindung steht? → Das beantwortet Layer 2

---

## Layer 2: Paketaufzeichnung — "Was passiert auf der Leitung?"

### Was wird gemessen?

Wir zeichnen mit `tcpdump` **jedes einzelne Paket** auf, das zwischen EC2
und dem API-Server hin- und herfliegt. Dann analysieren wir die Aufzeichnung
mit `tshark` (Kommandozeilen-Wireshark).

### Wie entsteht ein Layer-2-Datensatz?

Manuell auf EC2 (einmalig, nicht per Cron):
1. `tcpdump` starten, filtert auf den Ziel-Host
2. Einen einzelnen Layer-3-API-Call ausfuehren (n=1)
3. `tcpdump` stoppen → .pcap-Datei gespeichert
4. `tshark` analysiert die Paketzeiten

Automatisiert via `measurements/layer2/capture_all.py` fuer alle 9 Provider.

### Die Paket-Timeline: Deepgram (USA, WebSocket)

Jede Zeile ist ein Paket. C→S = Client zum Server, S→C = Server zum Client.

```
    0.00 ms  C→S  SYN                    ← Schritt 1: TCP-Handshake
  101.83 ms  S→C  SYN-ACK               ← Server antwortet → 1 RTT = 102ms
  101.89 ms  C→S  ACK                    ← TCP steht (3-Way-Handshake)

  102.73 ms  C→S  DATA(517B)             ← Schritt 2: TLS-Handshake
                                            Client schickt "ClientHello" (Verschluesselung starten)
  206.45 ms  S→C  DATA(2896B+782B)       ← Server antwortet mit Zertifikat → 1 RTT = 104ms
  208.50 ms  C→S  DATA(80B)              ← Client bestaetigt → TLS steht

  208.83 ms  C→S  DATA(458B)             ← Schritt 3: WebSocket-Upgrade
                                            HTTP-Request: "Upgrade: websocket"
                                            URL enthaelt ALLE Einstellungen:
                                            model=nova-3, encoding=linear16, sample_rate=16000
  310.49 ms  S→C  DATA(79B)              ← Server: "HTTP 101 Switching Protocols" → 1 RTT = 102ms
  330.13 ms  S→C  DATA(618B)             ← Server: JSON {"type":"connected"}

  331.04 ms  C→S  DATA(1448B,1448B,...)  ← Audio-Upload beginnt!
```

**Zusammenfassung Deepgram:**
- **3 Roundtrips** (TCP + TLS + WebSocket), jeweils ~102ms
- 3 × 102ms = ~306ms bis die Verbindung steht
- connect_ms gemessen in Layer 3: **337ms** ← passt!

### Die Paket-Timeline: Azure (Italien, WebSocket + proprietaeres Protokoll)

```
    0.00 ms  C→S  SYN                    ← Schritt 1: TCP-Handshake
   11.44 ms  S→C  SYN-ACK               ← 1 RTT = 11ms (nah!)
   11.49 ms  C→S  ACK                    ← TCP steht

   12.25 ms  C→S  DATA(517B)             ← Schritt 2: TLS-Handshake (ClientHello)
   25.27 ms  S→C  DATA(2896B+1491B)      ← ServerHello + Zertifikat → 1 RTT = 13ms
   27.13 ms  C→S  DATA(80B)              ← TLS steht

   27.36 ms  C→S  DATA(503B)             ← Schritt 3: WebSocket-Upgrade
   38.57 ms  S→C  DATA(158B)             ← HTTP 101 → 1 RTT = 11ms
                                            WebSocket steht — aber Azure ist noch nicht bereit!

   ~39 ms    C→S  speech.config           ← Schritt 4: Azures proprietaeres Protokoll
                                            JSON mit: Python-Version, Betriebssystem,
                                            Audio-Format (16kHz, 16-bit, Mono),
                                            Mikrofon-Typ, SDK-Version
                                            (siehe Code: stt_azure.py → _build_speech_config())

  262.75 ms  S→C  DATA(269B)             ← Server antwortet erst nach ~224ms!
                                            Azure laedt Sprachmodell, prueft API-Key,
                                            richtet Audio-Pipeline ein

  263.42 ms  C→S  DATA(477B)             ← Audio-Upload beginnt!
```

**Zusammenfassung Azure:**
- **3 Roundtrips** fuer TCP + TLS + WebSocket = ~33ms (fast nichts!)
- **Dann ~224ms Wartezeit** auf den Server (Session-Setup)
- Gesamt: 33ms + 224ms = ~257ms
- connect_ms gemessen in Layer 3: **265ms** ← passt!

### Die Submetriken von connect_ms

Aus den Paket-Timelines koennen wir connect_ms in drei Teile zerlegen:

| Submetrik | Was | Deepgram | Azure |
|-----------|-----|---------|-------|
| `tcp_hs_ms` | TCP SYN → SYN-ACK (1 RTT) | 102ms | 11ms |
| `tls_hs_ms` | TLS ClientHello → Finished | 106ms | 16ms |
| `proto_setup_ms` | WebSocket + alles Weitere | 123ms | 237ms |
| **connect_ms** | **Summe** | **337ms** | **265ms** |

**Warum ist proto_setup_ms bei Azure so hoch?**
- Deepgram: WebSocket-Upgrade + fertig (1 RTT). Alle Einstellungen in der URL.
- Azure: WebSocket-Upgrade (1 RTT) + speech.config senden + 224ms Server-Setup.
  Azure hat ein proprietaeres Anwendungsprotokoll, das viele Infos braucht,
  bevor es Audio akzeptiert.

**Referenz:** Das Paper "Layered Performance Analysis of TLS 1.3 Handshakes"
(arXiv 2603.11006) macht exakt die gleiche Zerlegung: TCP → TLS → Application Delay.
Unser `proto_setup_ms` entspricht ihrem "TLS-to-Application Delay".

---

## Layer 3: API-Latenz — "Was spuert der Nutzer?"

### Was wird gemessen?

Fuer jeden Provider: Neue Verbindung aufbauen → festen Input senden →
Antwort empfangen → Zeiten messen. Alles in Python, ohne SDK.

### Wie entsteht ein Layer-3-Datensatz?

Automatisch per Cron-Job auf EC2, alle 3 Stunden:
1. `run.py` importiert das Provider-Modul (z.B. `stt_deepgram.py`)
2. Fuer jeden der 9 Provider: 100x `measure_once()` aufrufen
3. Jede Messung baut eine NEUE TCP+TLS+WebSocket-Verbindung auf
4. Ergebnisse als JSONL nach `data/layer3/2026-05-04_12h.jsonl`

### Was misst measure_once() genau?

**STT (am Beispiel Deepgram):**

```python
# 1. Verbindung aufbauen (= connect_ms)
t_start = time.perf_counter()
ws = await websocket_connect("wss://api.deepgram.com/v1/listen?model=nova-3&...")
t_connected = time.perf_counter()
connect_ms = (t_connected - t_start) * 1000    # z.B. 337ms

# 2. Audio senden (PCM-Daten aus sample.wav)
await ws.send(pcm_data)           # "Good morning, I would like to know..."
await ws.send(finalize_message)

# 3. Auf Transkript warten (= TTFT)
t_first_result = time.perf_counter()  # Erstes is_final-Segment empfangen
ttft_ms = (t_first_result - t_start_sending) * 1000   # z.B. 463ms

# 4. Alle Segmente sammeln (= total_ms)
# Deepgram sendet mehrere is_final-Segmente: "Good" + "morning I would like..."
total_ms = (t_last_segment - t_start) * 1000    # z.B. 4143ms
```

### Die Metriken

| Metrik | Was sie misst | Beispiel Deepgram |
|--------|-------------|-------------------|
| `connect_ms` | TCP SYN → Verbindung bereit | 337ms |
| `ttft_ms` | Beginn Audio-Senden → erstes Ergebnis | 463ms |
| `total_ms` | Gesamtdauer inkl. aller Segmente | 4143ms |

### Warum misst connect_ms SEPARAT?

Im Code wird connect_ms mit einer eigenen TCP+TLS-Probe gemessen
(separate Verbindung, die sofort geschlossen wird). Das isoliert den
reinen Verbindungsaufbau von der API-Verarbeitung.

In der PCAP sieht man deshalb ZWEI Verbindungen:
1. Erste Verbindung: die connect_ms-Probe (SYN → verbunden → sofort zu)
2. Zweite Verbindung: der eigentliche API-Call

### Beispiel-Datensatz (JSONL)

```json
{
  "ts": "2026-05-04T12:01:23+00:00",
  "tag": "12h",
  "run": 0,
  "metric": "stt_ttft",
  "api": "deepgram",
  "connect_ms": 337.1,
  "send_ms": 102.8,
  "ttft_ms": 462.8,
  "total_ms": 4143.4,
  "transcript_len": 78
}
```

---

## Cross-Layer-Korrelation — Das Hauptergebnis

Die drei Layer greifen ineinander. Hier die Korrelation:

### Deepgram (USA, Anycast)

```
Layer 1:  Ping RTT                    = 102ms
Layer 2:  TCP-Handshake               = 101.8ms  ← stimmt ueberein ✓
Layer 2:  Protokoll braucht 3 RTTs    → 3 × 102ms = ~306ms
Layer 3:  connect_ms                  = 337ms    ← passt ✓
Layer 3:  TTFT                        = 463ms
          → Verarbeitungszeit         = 463 - 337 = 126ms
```

**Netzwerk: 337ms (73%), Verarbeitung: 126ms (27%)**

### Azure (Italien, Italy North)

```
Layer 1:  Ping RTT                    = 11ms
Layer 2:  TCP-Handshake               = 11.4ms   ← stimmt ueberein ✓
Layer 2:  Protokoll braucht 3 RTTs    → 3 × 11ms = ~33ms
Layer 2:  + Server-Session-Setup      = ~224ms
Layer 3:  connect_ms                  = 265ms    ← passt (33 + 224 ≈ 265) ✓
Layer 3:  TTFT                        = 1718ms
          → Verarbeitungszeit         = 1718 - 265 = 1453ms
```

**Netzwerk: 33ms (2%), Server-Setup: 224ms (13%), Verarbeitung: 1453ms (85%)**

### Was bedeutet das?

1. **Layer-1-RTT validiert Layer-2-TCP-Handshake** — Ping ≈ SYN→SYN-ACK. Gut.

2. **RTT × Protokoll-RTTs ≈ connect_ms** — aber nur fuer den Netzwerkanteil.
   Bei Azure kommt Server-Verarbeitung hinzu, die nicht durch RTT erklaerbar ist.

3. **Netzwerk ist bei US-Providern dominant** (Deepgram: 73% Netzwerk),
   bei EU-Providern vernachlaessigbar (Azure: 2% Netzwerk).
   Aber Azure hat trotzdem hoehere TTFT wegen langsamer Verarbeitung.

4. **Netzwerklatenz ist der physikalische Boden** — Verarbeitungszeit kann ein
   Provider optimieren (schnelleres Modell, bessere Hardware), aber RTT
   Frankfurt→USA bleibt bei ~100ms. Das ist Physik.

---

## Haeufige Prof-Fragen und Antworten

### "Warum Cold-Start und nicht Warm-Start?"
Jedes neue Gespraech ("Hey Alexa") ist ein Cold-Start. Warm-Start (persistente
Verbindung) waere unrealistisch optimistisch. Cold-Start ist der Worst Case
und in der Praxis bei jeder neuen Session der Normalfall.

### "Warum diese 9 Provider?"
- Jede Kategorie hat EU + USA (geografische Varianz)
- STT: alle WebSocket, kein SDK (methodische Konsistenz)
- LLM: alle OpenAI-kompatibles HTTPS+SSE
- Groq: LPU-Spezialchip vs. GPU (Hardware-Varianz)
- Intra-Provider-Vergleiche: Deepgram STT vs. TTS, OpenAI LLM vs. TTS

### "Warum nicht AssemblyAI?"
AssemblyAI erfordert Echtzeit-Pacing: Audio muss in Echtzeit gestreamt werden
(5s Audio = 5s senden). Deepgram/Rev.ai/Azure akzeptieren Audio-Dump (alles
sofort senden). TTFT waere bei AssemblyAI nicht vergleichbar → ersetzt durch Rev.ai.

### "Ist connect_ms eine reine Netzwerkmetrik?"
Nein — und das ist eine wichtige Erkenntnis. connect_ms misst die Zeit bis
die Applikation Daten senden kann. Bei Deepgram ist das fast nur Netzwerk
(3 RTTs). Bei Azure steckt ~224ms Server-Setup drin. Die Zerlegung in
tcp_hs_ms + tls_hs_ms + proto_setup_ms macht das sichtbar.

### "Was ist die Contribution?"
1. Cross-Layer-Korrelation: Ping × Protokoll-RTTs ≈ connect_ms (fuer den Netzwerkanteil)
2. Zerlegung connect_ms in Submetriken (tcp_hs, tls_hs, proto_setup)
3. Latenzbudget-Analyse: Wie viel % geht fuer Netzwerk drauf vs. Verarbeitung?
4. Quantitativer Provider-Vergleich mit >100.000 Datenpunkten ueber 14 Tage

### "Kennt ihr verwandte Arbeiten?"
- **Palumbo et al. (2021):** 14-Tage-Kampagne zu AWS+Azure, fast identisches Setup,
  aber misst nur Netzwerk-RTT, nicht API-Level.
- **arXiv 2603.11006 (2026):** Zerlegt TLS-Handshake in 5 Schichten — gleiche
  Logik wie unsere Submetriken.
- **"Building Enterprise Voice Agents" (arXiv, 2026):** Nutzt Deepgram STT in
  der gleichen Pipeline, misst P50 ~947ms. Unsere Arbeit erklaert, woher das kommt.

### "Wie stellt ihr sicher, dass die Messung fair ist?"
- Feste Inputs: Alle STT-Provider bekommen exakt die gleiche WAV-Datei
- Gleiche Methodik: Alle STT-Provider nutzen Raw WebSocket (kein SDK)
- Gleicher Vantage Point: Alles von derselben EC2-Instanz
- Cold-Start: Jede Messung mit neuer Verbindung (kein Caching-Vorteil)
- n=100 pro Slot: Statistisch belastbar (p50, p95, p99)
