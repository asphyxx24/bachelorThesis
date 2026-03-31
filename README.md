# Bachelorarbeit — Messinfrastruktur

**Titel:** Kommerzielle Cloud-AI-APIs unter der Lupe: Netzwerk-, Protokoll- und Latenzanalyse einer Echtzeit-Voice-Pipeline

**Autor:** Anton Rusik
**Betreuer:** Prof. Dr. Matthias Wahlisch, TU Dresden
**Vantage Point:** AWS EC2 eu-central-1 (Frankfurt)

---

## Forschungsfrage

> Wie verhalten sich kommerzielle Cloud-AI-APIs (STT, LLM, TTS) als Internet-Dienste —
> hinsichtlich Infrastruktur, Streaming-Protokollverhalten und Tail-Latency — und welche
> Auswirkungen haben diese Eigenschaften auf eine sequenzielle Echtzeit-Pipeline?

## Messobjekte

| API | Dienst | Protokoll | Endpoint |
|-----|--------|-----------|----------|
| **Deepgram** | Speech-to-Text | WebSocket | `api.deepgram.com` |
| **Requesty** | LLM (Gemini 2.5 Flash) | HTTPS + SSE | `router.requesty.ai` |
| **ElevenLabs** | Text-to-Speech | HTTPS Streaming | `api.elevenlabs.io` |

## Drei Analyseschichten

```
Schicht 3: TAIL-LATENCY DER KETTE
  STT --> LLM --> TTS  (sequenziell, Budget <1s)
     |        |       |
Schicht 2: STREAMING-VERHALTEN
  Paketanalyse: Inter-Paket-Zeiten, Burst-Muster, TCP-Interaktion
     |        |       |
Schicht 1: INFRASTRUKTUR
  DNS, RTT, Traceroute/AS-Pfade, Protokoll-Check (TCP/QUIC, TLS)
```

## Verzeichnisstruktur

```
measurements/
  layer1_infra/       Schicht 1: DNS, Ping, Traceroute, TLS
  layer2_streaming/   Schicht 2: Paket-Captures + Analyse
  layer3_latency/     Schicht 3: STT, LLM, TTS, E2E-Kette
  lib/                Shared: JSONL-Output, Statistik

data/                 Messergebnisse (JSONL)
  layer1/
  layer2/
  layer3/

analysis/             Jupyter Notebooks, Plots (spaeter)
fixtures/             Testdaten (sample.wav)
```

## Schnellstart

```bash
# 1. Dependencies installieren
pip install -r requirements.txt

# 2. API-Keys konfigurieren
cp .env.example .env
nano .env

# 3. Schicht 1 testen (keine API-Keys noetig)
python measurements/layer1_infra/run.py --dry-run

# 4. Schicht 3 testen (API-Keys noetig)
python measurements/layer3_latency/run.py --n 3 --dry-run
```

## Datenformat

Alle Messergebnisse werden als **JSONL** (JSON Lines) gespeichert — eine JSON-Zeile pro Messung.
Jede Zeile enthaelt einen ISO-8601-Zeitstempel, den gemessenen Endpoint und die Messdaten.

Beispiel Layer 1 (Ping):
```json
{"ts":"2026-04-01T09:00:00Z","endpoint":"api.deepgram.com","type":"ping","data":{"avg_ms":2.3,"min_ms":1.2,"max_ms":4.5}}
```

Beispiel Layer 3 (STT):
```json
{"ts":"2026-04-01T09:05:01Z","tag":"09h","run":0,"api":"deepgram","metric":"stt_ttft","ttft_ms":245.3,"total_ms":260.5}
```

## Reproduzierbarkeit

- Alle Messskripte sind in diesem Repository
- Rohdaten im `data/` Verzeichnis
- Vantage Point: EU (Frankfurt), Single-Homed
- Statistische Auswertung: Python + pandas/scipy (in `analysis/`)
