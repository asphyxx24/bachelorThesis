# Bachelorarbeit — Messinfrastruktur

@HANDOFF.md

**Titel:** Kommerzielle Cloud-AI-APIs unter der Lupe: Netzwerk-, Protokoll- und Latenzanalyse einer Echtzeit-Voice-Pipeline
**Autor:** Anton Rusik | **Betreuer:** Prof. Dr. Matthias Wählisch, TU Dresden
**Vantage Point:** AWS EC2 eu-central-1 (Frankfurt) | **Deadline:** flexibel

## Forschungsfrage

Welche Netzwerk- und Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region) erklären
die beobachteten Latenzunterschiede zwischen kommerziellen Cloud-AI-APIs (STT, LLM, TTS)
aus EU-Perspektive — und wie beeinflusst die Provider-Wahl die Gesamtlatenz einer
sequenziellen Voice-Pipeline?

## Drei-Schichten-Architektur

- **Layer 1 (Infrastruktur):** DNS, Ping, TLS, Traceroute — Code in `measurements/layer1/`
- **Layer 2 (Paketaufzeichnung):** tcpdump/PCAP — Code in `measurements/layer2/`, 1 POC-Capture vorhanden
- **Layer 3 (API-Latenz):** Cold-Start connect_ms / ttft_ms / total_ms — Code in `measurements/layer3/`

## Provider-Matrix (FINAL, Stand 2026-05-03)

| Kategorie | Provider | Modell | Region | Protokoll |
|-----------|----------|--------|--------|-----------|
| STT | Deepgram | Nova-3 | USA (Anycast) | WebSocket |
| STT | Rev.ai | English | USA | WebSocket |
| STT | Azure | Standard Neural | Italien (Italy North) | WebSocket |
| LLM | OpenAI | gpt-4o-mini | USA (GPU) | HTTPS+SSE |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS+SSE |
| LLM | Mistral | mistral-small-4 | EU/Frankreich | HTTPS+SSE |
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
- **Kampagne:** n=100 pro Zeitschlitz, 8 Slots/Tag (alle 3h), 14 Tage

## Aktueller Stand

Siehe `HANDOFF.md` für den aktuellen Session-Stand.
Siehe `notes/implementation_plan.md` für die vollständige Checkliste.
Siehe `notes/cost_analysis.md` für die detaillierte Kostenanalyse.

## Betreuer-Feedback (2026-04-09, Prof. Wählisch)

Hauptkritik: **"Methodik unklar"** — Was genau wird gemessen? Warum Cold-Start? Was ist die Contribution?
Antwort: Cold-Start misst den Overhead jeder neuen Gesprächssession. Der Beitrag ist die
Cross-Layer-Korrelation (Layer 1 Ping × 3 ≈ Layer 3 connect_ms) und die Zerlegung des
1s-Latenzbudgets in Netzwerk vs. Verarbeitung.

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
| `/prime` | Session-Start | Liest HANDOFF + git log + Datenstand, gibt kurzes Briefing |
| `/handoff` | Session-Ende | Aktualisiert HANDOFF.md mit aktuellem Arbeitsstand |
| `/analyze` | Analyse-Phase | Jupyter Notebook Analyse-Unterstützung |
| `/write` | Schreib-Phase | Thesis-Abschnitte schreiben oder überarbeiten |
| `/explain <Thema>` | Jederzeit | Konzept oder Entscheidung verständlich erklären |
