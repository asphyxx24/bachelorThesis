# Briefing fuer Prof. Waelisch — Stand 2026-05-03

## Was messen wir?

Die **Cold-Start-Latenz** von 9 kommerziellen Cloud-AI-APIs, aufgeteilt in drei
Kategorien: Speech-to-Text (STT), Large Language Model (LLM), Text-to-Speech (TTS).

Diese drei Kategorien bilden eine **Voice-Pipeline**: Ein Nutzer spricht →
STT wandelt Sprache in Text → LLM generiert eine Antwort → TTS wandelt die
Antwort in Sprache. Jeder Schritt kostet Zeit, und wir messen wie viel.

---

## Warum Cold-Start?

Bei jedem neuen Gespraech (z.B. "Hey Alexa") wird eine neue Verbindung zum
Cloud-Server aufgebaut. Dieser Verbindungsaufbau (TCP + TLS + ggf. WebSocket)
kostet mehrere RTTs, bevor ueberhaupt ein Byte Nutzdaten fliessen kann.

**Konkret:** Bei Deepgram (USA) vergehen 3 RTTs × ~150ms = ~450ms allein fuer
den Verbindungsaufbau. Das sind 45% eines 1-Sekunden-Latenzbudgets — und es
ist noch kein Audio verarbeitet worden.

Wir messen bewusst NICHT den Warm-Start (persistente Verbindung), weil der
Cold-Start der Worst Case ist und in der Praxis bei jedem neuen Gespraech auftritt.

---

## Wie messen wir? (Drei-Schichten-Architektur)

### Layer 1: Infrastruktur — "Wie weit weg ist der Server?"

| Messung | Was | Warum |
|---------|-----|-------|
| DNS | IP-Aufloesung, TTL, Resolver-Vergleich | Zeigt Anycast, CDN-Routing, DNS-Instabilitaet |
| Ping (ICMP) | Round-Trip-Time zum Server | Baseline-RTT fuer Cross-Layer-Vergleich |
| TLS | Handshake-Dauer, Protokollversion | Zeigt Overhead durch Verschluesselung |
| Traceroute | AS-Pfad, Hop-Count | Zeigt Routing-Unterschiede EU→USA vs. EU→EU |

**Automatisiert:** Alle 6 Stunden per Cron-Job auf AWS EC2 Frankfurt.

### Layer 2: Paketaufzeichnung — "Was passiert auf der Leitung?"

Manuelles `tcpdump` waehrend eines Layer-3-Calls. Zeigt auf Paketebene:
- Wie viele RTTs kostet welches Protokoll? (WebSocket: 3 RTTs, HTTPS: 2 RTTs)
- Wo genau geht die Zeit verloren? (TCP-Handshake, TLS, Upgrade, Processing)
- Validierung: Layer-1-Ping-RTT ≈ Layer-2-TCP-Handshake-RTT?

**POC-Ergebnis (Deepgram, Frankfurt→USA):**
```
  0ms  TCP SYN           → RTT #1 (104ms)
104ms  TLS ClientHello   → RTT #2 (104ms)
208ms  WebSocket Upgrade  → RTT #3 (104ms)
312ms  Erstes Audio-Byte kann gesendet werden
```
→ 3 × RTT = 31% des 1s-Latenzbudgets nur fuer Verbindungsaufbau.

### Layer 3: API-Latenz — "Was spuert der Nutzer?"

Fuer jeden der 9 Provider: Neue Verbindung aufbauen, festen Input senden,
Antwort empfangen, Zeiten messen.

**Feste Inputs (identisch pro Kategorie fuer fairen Vergleich):**

| Kategorie | Input | Warum dieser Input |
|-----------|-------|-------------------|
| STT | WAV-Datei: "Good morning. I would like to know the current weather forecast for Frankfurt." (5s) | Realistischer Voice-Assistant-Satz, englisch, ~5s — kurz genug fuer schnelle Messung, lang genug fuer zuverlaessige Transkription |
| LLM | "Reply in one short sentence: What is the capital of Germany?" | Erzwingt kurze Antwort (~10 Tokens), minimiert Token-Generierungszeit, isoliert Netzwerk- von Rechenlatenz |
| TTS | "Good morning! How can I assist you today?" | Typischer Voice-Assistant-Satz, ~40 Zeichen, vergleichbar kurz |

**Gemessene Metriken:**

| Metrik | Bedeutung |
|--------|-----------|
| `connect_ms` | TCP+TLS(+WebSocket) Verbindungsaufbau — reiner Netzwerk-Overhead |
| `ttft_ms` (STT/LLM) | Time to First Token — wie schnell kommt die erste Antwort? |
| `ttfa_ms` (TTS) | Time to First Audio — wie schnell kommt das erste Audio-Byte? |
| `total_ms` | Gesamtdauer bis Antwort vollstaendig |

**Automatisiert:** 100 Messungen pro Provider, alle 3 Stunden, 14 Tage lang.

---

## Warum diese 9 Provider?

| Kategorie | Provider | Warum dieser Provider |
|-----------|----------|----------------------|
| **STT** | Deepgram Nova-3 | Marktfuehrer Streaming-STT, USA/Anycast, WebSocket |
| | Rev.ai | Vergleichsanbieter USA, akzeptiert Audio-Dump wie Deepgram |
| | Azure Speech | **EU-Endpoint** (Italy North, 11ms Ping) — Kontrast zu USA |
| **LLM** | OpenAI gpt-4o-mini | Referenz-LLM, groesster Anbieter |
| | Groq | **LPU-Hardware** (spezialchip) — Vergleich GPU vs. LPU |
| | Mistral | **EU-Server** (Frankreich, <1ms Ping) — Kontrast zu USA |
| **TTS** | Deepgram Aura-2 | Gleicher Anbieter wie STT — intra-provider Vergleich |
| | OpenAI tts-1 | Gleicher Anbieter wie LLM — intra-provider Vergleich |
| | Azure TTS | **EU-Endpoint** — Kontrast, gleicher Anbieter wie Azure STT |

**Auswahlkriterien:**
- Jede Kategorie hat mindestens einen EU- und einen US-Provider (geografische Varianz)
- Alle STT-Provider nutzen WebSocket-Streaming ohne SDK (methodische Konsistenz)
- Alle LLM-Provider nutzen OpenAI-kompatibles HTTPS+SSE (methodische Konsistenz)
- Kein Provider erfordert Echtzeit-Pacing (AssemblyAI wurde deshalb ersetzt)

---

## Vantage Point: Warum AWS EC2 Frankfurt?

- **Fixer, reproduzierbarer Messpunkt** — keine WLAN-Schwankungen, kein ISP-Routing
- **EU-Perspektive** — Forschungsfrage fragt explizit nach EU-Sicht
- **Nah an EU-Providern** (Azure Italy: 11ms, Mistral France: <1ms)
- **Fern von US-Providern** (Deepgram: 150ms, Rev.ai: ~150ms)
- **t3.small** (2 vCPU, 2GB RAM) — reicht fuer sequenzielle Messungen

---

## Wissenschaftlicher Beitrag

1. **Cross-Layer-Korrelation:** Layer-1 Ping × Anzahl RTTs (aus Layer 2) ≈ Layer-3 connect_ms.
   Das heisst: Die Netzwerkentfernung (messbar mit Ping) erklaert den Verbindungsaufbau-Overhead.

2. **Latenzzerlegung:** Wie viel % des 1s-Budgets geht fuer Netzwerk drauf vs. Verarbeitung?
   - Netzwerk: connect_ms (vorhersagbar durch RTT × Protokoll-RTTs)
   - Verarbeitung: ttft_ms - connect_ms (provider-spezifisch, nicht vorhersagbar)

3. **Provider-Empfehlung:** Welche Kombination minimiert die Gesamtlatenz?
   Nicht chain.py, sondern rechnerische Addition der Einzellatenzen (validiert durch
   manuelle E2E-Tests am Ende).

---

## Erste Ergebnisse (EC2 Frankfurt, n=3, Dry-Run)

### STT
| Provider | Ping RTT | connect_ms | TTFT | Region |
|----------|---------|-----------|------|--------|
| Deepgram | 150ms | 450ms | 418ms | USA (Anycast) |
| Rev.ai | blockiert | 591ms | 1452ms | USA |
| Azure | 11ms | **55ms** | 1718ms | Italien |

**Beobachtung:** Azure hat den niedrigsten connect_ms (EU-nah), aber die hoechste
TTFT — der Server braucht laenger zum Verarbeiten. Deepgram hat den hoechsten
connect_ms (USA), aber die niedrigste TTFT — schnellere Verarbeitung kompensiert
die Netzwerkentfernung.

### LLM
| Provider | Ping RTT | connect_ms | TTFT | TTL | Region |
|----------|---------|-----------|------|-----|--------|
| Groq | 1.5ms | 15ms | 73ms | 78ms | USA (Cloudflare) |
| Mistral | 0.9ms | 13ms | 463ms | 486ms | EU/Frankreich |
| OpenAI | 1.6ms | 10ms | 1195ms | 1354ms | USA (Cloudflare) |

**Beobachtung:** Alle drei haben niedrigen connect_ms (<15ms) weil sie hinter
Cloudflare sitzen (PoP in Frankfurt). Die TTFT-Unterschiede kommen fast
ausschliesslich von der Verarbeitungsgeschwindigkeit: Groq (LPU) >> Mistral >> OpenAI.

### TTS
| Provider | Ping RTT | connect_ms | TTFA | Region |
|----------|---------|-----------|------|--------|
| Azure | 11ms | 37ms | **186ms** | Italien |
| Deepgram | 150ms | 306ms | 590ms | USA (Anycast) |
| OpenAI | 1.6ms | 15ms | 1050ms | USA (Cloudflare) |

**Beobachtung:** Azure (EU) ist bei TTS am schnellsten — sowohl niedriger connect_ms
als auch niedrige Verarbeitungszeit.

---

## Methodische Entscheidungen (und Begruendung)

| Entscheidung | Begruendung |
|-------------|-------------|
| Cold-Start (neue Verbindung pro Messung) | Misst den Worst Case jeder neuen Gespraechssession |
| Raw WebSocket fuer STT (kein SDK) | SDK abstrahiert Netzwerkverhalten — wir wollen es sehen |
| Audio-Dump statt Echtzeit-Pacing (STT) | Misst reine Verarbeitungsgeschwindigkeit, konsistent ueber alle Provider |
| Feste Inputs | Fairer Vergleich — alle Provider bekommen exakt denselben Input |
| n=100 pro Slot, 8 Slots/Tag | Statistisch robust (p50/p95/p99), erfasst Tageszeiteffekte |
| 14 Tage Kampagne | Erfasst Wochentag-Effekte und langfristige Varianz |
| EC2 eu-central-1 als Vantage Point | Fix, reproduzierbar, EU-Perspektive |

---

## Messkampagne — Zeitplan (gestartet 2026-05-03)

**Vantage Point:** AWS EC2 t3.small, eu-central-1 (Frankfurt)
**Dauer:** 14 Tage (bis ~2026-05-17)

### Cron-Jobs (alle Zeiten UTC)

| Job | Zeitplan | Was passiert |
|-----|----------|-------------|
| **Layer 3** | `0 0,3,6,9,12,15,18,21` (alle 3h) | 9 Provider × n=100, Ergebnis in `data/layer3/` |
| **Layer 1 background** | `0 */6` (alle 6h) | DNS + Ping fuer alle 9 Endpoints |
| **Layer 1 full** | `30 5` (taeglich) | DNS + Ping + TLS + Traceroute |
| **Git-Sync** | `0 2` (taeglich) | `git push` — Daten erscheinen im Repo |

### Typischer Tag (UTC)

```
00:00  Layer 3 (n=100, ~30-45 Min)
02:00  Git-Sync → morgens git pull = neue Daten
03:00  Layer 3
05:30  Layer 1 full (mit Traceroute)
06:00  Layer 3 + Layer 1 background
09:00  Layer 3
12:00  Layer 3 + Layer 1 background
15:00  Layer 3
18:00  Layer 3 + Layer 1 background
21:00  Layer 3
```

### Monitoring

- **Passiv:** `git pull` — neue JSONL-Dateien da? → alles OK
- **Aktiv:** `ssh ubuntu@35.159.112.40 "tail -20 ~/thesis/logs/layer3.log"`

### Erwartetes Datenvolumen (14 Tage)

- Layer 3: 8 Slots/Tag × 9 Provider × 100 Messungen = **100.800 Records**
- Layer 1: ~4-5 Messungen/Tag × 9 Endpoints = **~630 Records**

## Naechste Schritte

1. ~~Cron-Jobs einrichten und Kampagne starten~~ — erledigt (2026-05-03)
2. Layer-2 Captures manuell auf EC2 (waehrend Kampagne, ein paar pro Provider)
3. Analyse in Jupyter Notebooks
4. E2E-Validierung: Addierte Einzellatenzen ≈ gemessene Gesamtlatenz?
5. Thesis schreiben
