# Layer 2: Paketaufzeichnung auf Protokollebene

Manuelle Paket-Captures und Post-hoc-Analyse.
Erfordert root + SSH auf der EC2-Instanz.

## Captures erstellen

```bash
# Auf der EC2-Instanz (root erforderlich):

# STT: Deepgram (WebSocket)
sudo tcpdump -i eth0 -w capture_deepgram_$(date +%Y%m%d_%H%M).pcap \
  host api.deepgram.com -s 0 -c 10000

# STT: AssemblyAI (WebSocket)
sudo tcpdump -i eth0 -w capture_assemblyai_$(date +%Y%m%d_%H%M).pcap \
  host api.assemblyai.com -s 0 -c 10000

# STT: Azure (WebSocket, Germany West Central)
sudo tcpdump -i eth0 -w capture_azure_stt_$(date +%Y%m%d_%H%M).pcap \
  host germanywestcentral.stt.speech.microsoft.com -s 0 -c 10000

# LLM: OpenAI (HTTPS+SSE)
sudo tcpdump -i eth0 -w capture_openai_$(date +%Y%m%d_%H%M).pcap \
  host api.openai.com -s 0 -c 10000

# LLM: Groq (HTTPS+SSE)
sudo tcpdump -i eth0 -w capture_groq_$(date +%Y%m%d_%H%M).pcap \
  host api.groq.com -s 0 -c 10000

# LLM: Mistral (HTTPS+SSE, EU/Frankreich)
sudo tcpdump -i eth0 -w capture_mistral_$(date +%Y%m%d_%H%M).pcap \
  host api.mistral.ai -s 0 -c 10000
```

Waehrend tcpdump laeuft, parallel einen Layer-3-Messlauf starten:
```bash
python measurements/layer3/run.py --n 1 --api stt --dry-run
```

## Analyse mit tshark

```bash
# Inter-Paket-Zeiten
tshark -r capture_deepgram.pcap -T fields \
  -e frame.time_delta_displayed -e frame.len -e tcp.len \
  -Y "tcp.len > 0" > ipt_deepgram.tsv

# WebSocket-Frames
tshark -r capture_deepgram.pcap -T fields \
  -e frame.time_relative -e websocket.opcode -e websocket.payload_length \
  -Y "websocket" > ws_frames_deepgram.tsv
```

## Erwartete Captures

| Kategorie | Provider | Protokoll | Zweck |
|-----------|----------|-----------|-------|
| STT | Deepgram | WebSocket | Audio-Upload + Transkript |
| STT | AssemblyAI | WebSocket | Vergleich: gleiche Kategorie, anderer Provider |
| STT | Azure | WebSocket | EU-Endpoint, kuerzerer Pfad |
| LLM | OpenAI | HTTPS+SSE | Token-Delivery-Muster |
| LLM | Groq | HTTPS+SSE | LPU-Hardware: anderes Streaming-Verhalten? |
| LLM | Mistral | HTTPS+SSE | EU-Endpoint: weniger RTTs |

TTS-Captures optional (HTTPS Streaming zeigt weniger Protokoll-Details als WebSocket/SSE).

## Output

Capture-Dateien (.pcap) und abgeleitete TSV-Dateien in `data/layer2/`.
