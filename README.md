# Bachelorarbeit — Messinfrastruktur

**Titel:** Kommerzielle Cloud-AI-APIs unter der Lupe: Netzwerk-, Protokoll- und Latenzanalyse einer Echtzeit-Voice-Pipeline

**Autor:** Anton Rusik
**Betreuer:** Prof. Dr. Matthias Wählisch, TU Dresden
**Vantage Point:** AWS EC2 eu-central-1 (Frankfurt)

---

## Forschungsfrage

> Welche Netzwerk- und Infrastruktureigenschaften (RTT, Protokoll, Hosting-Region) erklären
> die beobachteten Latenzunterschiede zwischen kommerziellen Cloud-AI-APIs (STT, LLM, TTS)
> aus EU-Perspektive?

## Provider-Matrix

| Kategorie | Provider | Modell | Region | Protokoll |
|-----------|----------|--------|--------|-----------|
| STT | Deepgram | Nova-3 | USA (Anycast) | WebSocket |
| STT | AssemblyAI | Universal-2 | USA | WebSocket |
| STT | Azure | Standard Neural | Deutschland | WebSocket |
| LLM | OpenAI | gpt-4o-mini | USA | HTTPS+SSE |
| LLM | Groq | llama-3.1-8b-instant | USA (LPU) | HTTPS+SSE |
| LLM | Mistral | mistral-small-3.2 | EU/Frankreich | HTTPS+SSE |
| TTS | Deepgram | Aura-2 | USA (Anycast) | HTTPS Streaming |
| TTS | OpenAI | tts-1 | USA | HTTPS Streaming |
| TTS | Azure | Standard Neural | Deutschland | HTTPS Streaming |

## Drei-Schichten-Architektur

```
Layer 1 (Infrastruktur)     DNS, Ping, TLS, Traceroute
       |
Layer 2 (Paketaufzeichnung) tcpdump/PCAP — Handshake-Analyse
       |
Layer 3 (API-Latenz)        Cold-Start: connect_ms, ttft_ms, total_ms
```

## Verzeichnisstruktur

```
measurements/
  layer1/          Layer 1: DNS, Ping, Traceroute, TLS
  layer2/          Layer 2: Paket-Captures
  layer3/          Layer 3: 9 Provider-Module (STT, LLM, TTS)
  lib/             Shared: JSONL-Output, Statistik
  config.py        Alle Provider-Endpoints

data/              Messergebnisse (JSONL)
  layer1/
  layer2/
  layer3/
  archive/         Alte explorative Messungen

analysis/          Jupyter Notebooks
notes/             Forschungsnotizen, Implementierungsplan
```

## Schnellstart

```bash
pip install -r requirements.txt
cp .env.example .env
# API-Keys in .env eintragen

# Layer 1 testen (keine Keys noetig)
python measurements/layer1/run.py --dry-run

# Layer 3 testen (Keys noetig)
python measurements/layer3/run.py --n 3 --dry-run
```

## Datenformat

Alle Messergebnisse als JSONL (JSON Lines) — eine Zeile pro Messung:

```json
{"ts":"2026-05-15T09:05:01Z","tag":"09h","run":0,"api":"deepgram","metric":"stt_ttft","connect_ms":312.1,"ttft_ms":245.3,"total_ms":260.5}
```
