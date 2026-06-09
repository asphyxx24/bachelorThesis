# Bachelorarbeit — Messinfrastruktur

@HANDOFF.md

**Arbeitstitel (Stand 2026-06-08, noch nicht angemeldet):** Engine schlägt Geografie: Netzwerk-, Protokoll- und Latenzanalyse kommerzieller Cloud-AI-APIs einer Echtzeit-Voice-Pipeline aus EU-Perspektive
**Autor:** Anton Rusik | **Betreuer:** Prof. Dr. Matthias Wählisch, TU Dresden
**Vantage Point:** AWS EC2 eu-central-1 (Frankfurt) | **Deadline:** flexibel

## Forschungsfrage

In welchem Maße erklären Netzwerk- und Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region)
— *im Vergleich zur Backend-Verarbeitung der Engine* — die Latenzunterschiede zwischen kommerziellen
Cloud-AI-APIs (STT, LLM, TTS) aus EU-Perspektive, und wie wirkt sich die Provider-Wahl auf die
Gesamtlatenz einer sequenziellen Cold-Start-Voice-Pipeline aus?

> Geschärft 2026-06-08: in *beide* Richtungen beantwortbar — „Netzwerk erklärt weniger als die Engine"
> ist eine gültige Antwort. Teilfragen + Begründung in `notes/thesis_outline.md`.

## Drei-Schichten-Architektur

- **Layer 1 (Infrastruktur):** DNS, Ping, TLS, Traceroute — Code in `measurements/layer1/`
- **Layer 2 (Paketaufzeichnung):** tcpdump/PCAP — Code in `measurements/layer2/`, Captures fuer alle 9 Provider
- **Layer 3 (API-Latenz):** Cold-Start connect_ms / ttft_ms / total_ms — Code in `measurements/layer3/`

## Provider-Matrix (FINAL, Stand 2026-05-03)

| Kategorie | Provider | Modell | Region | Protokoll |
|-----------|----------|--------|--------|-----------|
| STT | Deepgram | Nova-3 | USA (Anycast) | WebSocket |
| STT | Rev.ai | English | USA | WebSocket |
| STT | Azure | Standard Neural | Italien (Italy North) | WebSocket |
| LLM | OpenAI | gpt-4o-mini | USA (GPU) | HTTPS+SSE |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS+SSE |
| LLM | Mistral | mistral-small-2603 | EU/Frankreich | HTTPS+SSE |
| TTS | Deepgram | Aura-2 | USA (Anycast) | HTTPS Streaming |
| TTS | OpenAI | tts-1 | USA | HTTPS Streaming |
| TTS | Azure | Standard Neural | Italien (Italy North) | HTTPS Streaming |

AssemblyAI wurde durch Rev.ai ersetzt (2026-05-03): AssemblyAIs Streaming-API erfordert
Echtzeit-Pacing, was die Messmethodik inkonsistent machte. Rev.ai akzeptiert Audio-Dump
wie Deepgram und Azure.

Amazon Polly: optionaler Exkurs (Intra-Cloud-Referenz), nicht Hauptprovider.

## Messdesign

- **Cold-Start:** Jede Messung baut eine neue TCP+TLS-Verbindung auf (kein Connection Pooling)
- **Raw WebSocket:** Alle STT-Provider werden ohne SDK gemessen (auch Azure) — direkte WebSocket-Verbindung
- **Feste Inputs:** Identisch pro Kategorie für fairen Vergleich
  - STT: `measurements/layer3/sample.wav` — "Good morning. I would like to know the current weather forecast for Frankfurt." (~5s)
  - LLM: "Reply in one short sentence: What is the capital of Germany?"
  - TTS: "Good morning! How can I assist you today?"
- **Kampagne (maßgeblich):** Juni 01.–07.06.2026, n=100 pro Zeitschlitz, 8 Slots/Tag (alle 3h), 7 Tage (= 56 Slots). Gemessen aus AWS eu-central-1 (anderer Account als die Validierungs-Instanz i-045; Vantage-Point-Caveat s. `data/processed/known_anomalies.md`).

## Aktueller Stand

**Audit + Reframe abgeschlossen (2026-06-08).** Kernbefund neu gerahmt: **„Engine schlägt
Geografie"** (STT/TTS-Inversion) ist die Contribution; das Cross-Layer-Modell (r=0.999, n=4)
ist Methoden-Baustein. Alle 8 Notebooks auf Juni; Doku-Zahlen synchronisiert.
**A7 (Batch-Szenario gestrichen) erledigt 2026-06-09 — NB07 nur noch Streaming-E2E.
Nächster Schritt: restliche Welle-1-Audit-Punkte (A6 Monte-Carlo, A8 Verfügbarkeit),
dann Methodik-Kapitel schreiben.**

Siehe `HANDOFF.md` (⭐ „Hier morgen weitermachen"-Block) für Session-Stand + nächsten Schritt.
Siehe `PRUEFER_AUDIT_2026-06-08.md` (Findings) + `STANDORTBESTIMMUNG_2026-06-08.md` (Strategie/Reframe).
Siehe `notes/spickzettel_prof.md` (Prof-Gespräch) · `notes/findings.md` (Befunde) · `notes/thesis_outline.md` (Gerüst).

## Betreuer-Feedback (2026-04-09, Prof. Wählisch)

Hauptkritik: **"Methodik unklar"** — Was genau wird gemessen? Warum Cold-Start? Was ist die Contribution?
Antwort: Cold-Start misst den Overhead jeder neuen Gesprächssession. Der Beitrag ist die
Cross-Layer-Korrelation (Layer 1 Ping × 3 ≈ Layer 3 connect_ms) und die Zerlegung des
1s-Latenzbudgets in Netzwerk vs. Verarbeitung.

## Metrik-Definitionen

### connect_ms — Zerlegung in Submetriken

`connect_ms` misst die Zeit von TCP SYN bis "Applikation kann Daten senden".
Seit der Layer-2-Analyse wird connect_ms in drei Submetriken zerlegt (Werte aus dem Juni-PCAP,
`data/layer2/*_20260608_*.pcap`, n=1/Provider, STT-WebSocket):

| Submetrik | Was sie misst | Quelle | Deepgram STT | Azure STT |
|-----------|--------------|--------|--------------|-----------|
| `tcp_hs_ms` | TCP SYN → SYN-ACK (1 RTT) | Layer 2 | 148 ms | 18 ms |
| `tls_hs_ms` | TLS ClientHello → ServerHello (1 RTT) | Layer 2 | 150 ms | 13 ms |
| `proto_setup_ms` | WebSocket-Upgrade + Session-Init (1 RTT) | Layer 2 | 180 ms | 13 ms |
| **connect_ms** | **TCP+TLS+WS bis „App kann senden"** | **Layer 3 (Median)** | **425 ms (≈3 RTTs)** | **49 ms (≈3 RTTs)** |

> PCAP-Summe: Deepgram ≈ 478 ms, Azure ≈ 44 ms — deckt sich mit dem Layer-3-Median bis auf
> Deepgrams Anycast-RTT-Schwankung (PCAP-RTT 148 ms vs. Kampagnen-RTT ~138 ms).
> **Korrektur ggü. Mai-Fassung (337 / 265 ms):** Azure hat KEINEN ~224-ms-„Server"-Anteil im
> connect — das war eine Fehlinterpretation der Audio-Sendelücke. Azures STT-Connect ist ein
> sauberer ~3-RTT-Handshake (~49 ms), exakt wie der Layer-3-Median zeigt.

Referenz: "Layered Performance Analysis of TLS 1.3 Handshakes" (arXiv 2603.11006)
verwendet die gleiche Zerlegungslogik (TCP → TLS → TLS-to-Application Delay).

### Weitere Layer-3-Metriken

| Metrik | Kategorie | Bedeutung |
|--------|-----------|-----------|
| `ttft_ms` | STT, LLM | Time to First Token — connect + Verarbeitung |
| `ttfa_ms` | TTS | Time to First Audio — connect + Verarbeitung |
| `total_ms` | alle | Gesamtdauer bis Antwort vollstaendig |
| `ttl_ms` | LLM | Time to Last Token (nur LLM) |

Siehe `notes/literature.md` fuer die vollstaendige Literatursammlung.

## JSONL-Datenformat

```json
// Layer 3
{"ts":"2026-04-01T09:05:01Z","tag":"09h","run":0,"api":"deepgram","metric":"stt_ttft","ttft_ms":245.3,"total_ms":260.5,"connect_ms":312.1,"transcript_len":0}

// Layer 1
{"ts":"2026-04-01T09:00:00Z","endpoint":"api.deepgram.com","type":"ping","data":{"avg_ms":2.3,"min_ms":1.2,"max_ms":4.5}}
```

## Commands

| Command | Wann | Zweck |
|---------|------|-------|
| `/prime` | Session-Start | Liest HANDOFF + git log, gibt kurzes Briefing |
| `/handoff` | Session-Ende | Aktualisiert HANDOFF.md mit aktuellem Arbeitsstand |
| `/write` | Schreib-Phase | Thesis-Abschnitte schreiben oder überarbeiten |
| `/explain <Thema>` | Jederzeit | Konzept oder Entscheidung verständlich erklären |
| `/analyze` | Falls nötig | Jupyter Notebook Analyse-Unterstützung |
