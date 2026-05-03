# Layer 2: Paketaufzeichnung auf Protokollebene

Manuelle Paket-Captures und Post-hoc-Analyse.
Erfordert root + SSH auf der EC2-Instanz.

## Captures erstellen

```bash
# Auf der EC2-Instanz (root erforderlich):

# STT: Deepgram (WebSocket)
sudo tcpdump -i ens5 -w capture_deepgram_$(date +%Y%m%d_%H%M).pcap \
  host api.deepgram.com -s 0 -c 10000

# STT: Rev.ai (WebSocket)
sudo tcpdump -i ens5 -w capture_revai_$(date +%Y%m%d_%H%M).pcap \
  host api.rev.ai -s 0 -c 10000

# STT: Azure (WebSocket, Italy North)
sudo tcpdump -i ens5 -w capture_azure_stt_$(date +%Y%m%d_%H%M).pcap \
  host italynorth.stt.speech.microsoft.com -s 0 -c 10000

# LLM: OpenAI (HTTPS+SSE)
sudo tcpdump -i ens5 -w capture_openai_$(date +%Y%m%d_%H%M).pcap \
  host api.openai.com -s 0 -c 10000

# LLM: Groq (HTTPS+SSE)
sudo tcpdump -i ens5 -w capture_groq_$(date +%Y%m%d_%H%M).pcap \
  host api.groq.com -s 0 -c 10000

# LLM: Mistral (HTTPS+SSE)
sudo tcpdump -i ens5 -w capture_mistral_$(date +%Y%m%d_%H%M).pcap \
  host api.mistral.ai -s 0 -c 10000
```

Waehrend tcpdump laeuft, parallel einen Layer-3-Messlauf starten:
```bash
python measurements/layer3/run.py --n 1 --api stt
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
| STT | Rev.ai | WebSocket | Vergleich: gleiche Kategorie, anderer Provider |
| STT | Azure | WebSocket | EU-Endpoint (Italy North), kuerzerer Pfad |
| LLM | OpenAI | HTTPS+SSE | Token-Delivery-Muster |
| LLM | Groq | HTTPS+SSE | LPU-Hardware: anderes Streaming-Verhalten? |
| LLM | Mistral | HTTPS+SSE | EU-Endpoint (Frankreich): weniger RTTs |

TTS-Captures optional (HTTPS Streaming zeigt weniger Protokoll-Details als WebSocket/SSE).

## Output

Capture-Dateien (.pcap) und abgeleitete TSV-Dateien in `data/layer2/`.
