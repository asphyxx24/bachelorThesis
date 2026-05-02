# Bachelorarbeit — Messinfrastruktur

@HANDOFF.md

**Titel:** Kommerzielle Cloud-AI-APIs unter der Lupe: Netzwerk-, Protokoll- und Latenzanalyse einer Echtzeit-Voice-Pipeline
**Autor:** Anton Rusik | **Betreuer:** Prof. Dr. Matthias Wählisch, TU Dresden
**Vantage Point:** AWS EC2 eu-central-1 (Frankfurt) | **Deadline:** ~2–4 Monate (ab April 2026)

## Forschungsfrage

Welche Netzwerk- und Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region) erklären
die beobachteten Latenzunterschiede zwischen kommerziellen Cloud-AI-APIs (STT, LLM, TTS)
aus EU-Perspektive — und wie beeinflusst die Provider-Wahl die Gesamtlatenz einer
sequenziellen Voice-Pipeline?

## Drei-Schichten-Architektur

- **Schicht 1 (Infrastruktur):** DNS, Ping, TLS, Traceroute — 9 Provider — 712+ Dateien in `data/layer1/`
- **Schicht 2 (Streaming):** Paket-Captures — 1 POC-PCAP (Deepgram, `data/layer2/`) — kein vollständiger Datensatz
- **Schicht 3 (Latenz):** connect_ms / ttft_ms / total_ms — 69k+ Records in `data/layer3/` (davon ~17k Requesty-Records deprecated, siehe `data/layer3/README.md`)

## Provider-Matrix (FINAL, Stand 2026-03-31)

| Kategorie | Provider | Protokoll | Endpoint |
|-----------|----------|-----------|---------|
| STT | Deepgram | WebSocket | `api.deepgram.com` |
| STT | AssemblyAI | WebSocket | `api.assemblyai.com` |
| STT | Speechmatics | WebSocket | `eu2.rt.speechmatics.com` |
| LLM | OpenAI | HTTPS + SSE | `api.openai.com` |
| LLM | Groq | HTTPS + SSE | `api.groq.com` |
| LLM | Anthropic | HTTPS + SSE | `api.anthropic.com` |
| TTS | ElevenLabs | HTTPS Streaming | `api.elevenlabs.io` |
| TTS | Cartesia | WebSocket | `api.cartesia.ai` |
| TTS | Amazon Polly | AWS SDK (HTTPS) | `polly.eu-central-1.amazonaws.com` |

Alle 9 Provider in `measurements/config.py` konfiguriert. Detaillierte Begründung: `notes/anbieter_auswahl.md`.

## Aktueller Stand

**Done:**
- Layer 1: 28-Tage-Kampagne abgeschlossen (alle 9 Provider, DNS/Ping/TLS)
- Layer 3: 28-Tage-Kampagne mit Deepgram (STT) + ElevenLabs (TTS), ~17.000 Messungen pro Provider (≈590/Tag × 29 Tage) — p99-Schätzungen statistisch belastbar. LLM-Daten vorhanden aber veraltet (siehe Bekannte Probleme)
- Layer 2: 1 POC-Capture (Deepgram, 2026-04-08) — Methodik validiert, 3-RTT-Overhead dokumentiert

**Bekannte Probleme (methodisch):**
- `transcript_len=0` in allen STT-Daten — Timing-Werte (connect_ms, ttft_ms) sind trotzdem valide, aber angreifbar
- Layer-3-LLM-Daten stammen von Requesty (API-Proxy → Gemini 2.5 Flash), nicht von den finalen Providern (OpenAI/Groq/Anthropic). Requesty wurde aus der Provider-Matrix entfernt. Diese Daten sind für die finale Thesis nicht verwendbar — LLM-Messungen müssen mit direkten Providern neu durchgeführt werden.
- Layer 3 hat nur 2 von 9 finalen Providern mit validen Daten (AssemblyAI/Speechmatics/OpenAI/Groq/Anthropic/Cartesia/Polly fehlen noch)
- Layer 2: 1 Capture ist kein statistischer Datensatz
- Layer-1 TLS-Daten: `http_version` war bis 31.03. ein Format-Bug (`"%(http_version)s"` literal), ab 01.04. korrekt. Für Protokoll-Analysen nur Daten ab 2026-04-01 verwenden.

**Offene TODOs:**
- API-Keys für 6 neue Provider beschaffen (siehe `notes/anbieter_auswahl.md`)
- Messcode für 6 neue Provider schreiben
- `fixtures/sample.wav` mit echter englischer Sprache ersetzen (`fixtures/create_sample.py`)
- AWS-Migration: Messinfrastruktur von Arbeits-Account auf eigenen Account (gleiche Region `eu-central-1`)
- Weitere Analysis-Notebooks: Tageszeit-Trends, Cross-Layer, E2E-Pipeline, Layer-2-Protokoll

## Betreuer-Feedback (2026-04-09, Prof. Wählisch)

Hauptkritik: **"Methodik unklar"** — Was genau wird gemessen? Warum Cold-Start? Was ist die Contribution?
Kernproblem: Das Framing fehlt, nicht die Daten selbst.

## JSONL-Datenformat

```json
// Layer 3
{"ts":"2026-04-01T09:05:01Z","tag":"09h","run":0,"api":"deepgram","metric":"stt_ttft","ttft_ms":245.3,"total_ms":260.5,"connect_ms":312.1,"transcript_len":0}

// Layer 1
{"ts":"2026-04-01T09:00:00Z","endpoint":"api.deepgram.com","type":"ping","data":{"avg_ms":2.3,"min_ms":1.2,"max_ms":4.5}}
```

## Custom Commands

| Command | Bereich | Zweck |
|---------|---------|-------|
| `/coach` | Planung | Wo stehe ich? Was ist als nächstes? |
| `/status` | Planung | Fakten: Dateien, Provider, offene TODOs |
| `/thesis-check` | Planung | Wissenschaftlicher Gesamtcheck: Roter Faden, Lücken |
| `/prof` | Planung | Prof. Wählisch simulieren — Methodik-Review |
| `/analyze` | Ausführung | Jupyter Notebook Analyse-Unterstützung |
| `/write` | Ausführung | Thesis-Abschnitte schreiben oder überarbeiten |
| `/explain <Thema>` | Erklärung | Konzept oder Entscheidung verständlich erklären |
| `/handoff` | Session-Ende | HANDOFF.md aktualisieren (Arbeitsstand festhalten) |

Workflow-Guide: `WORKFLOW.md`
