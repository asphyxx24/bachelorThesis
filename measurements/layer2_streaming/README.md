# Schicht 2: Streaming-Verhalten auf Protokollebene

Manuelle Paket-Captures und Post-hoc-Analyse.
Kann nicht sinnvoll automatisiert werden (erfordert root + SSH).

## Captures erstellen

```bash
# Auf der EC2-Instanz (root erforderlich):

# Deepgram STT (WebSocket)
sudo tcpdump -i eth0 -w capture_deepgram_$(date +%Y%m%d_%H%M).pcap \
  host api.deepgram.com -s 0 -c 10000

# Requesty LLM (HTTPS + SSE)
sudo tcpdump -i eth0 -w capture_requesty_$(date +%Y%m%d_%H%M).pcap \
  host router.requesty.ai -s 0 -c 10000

# ElevenLabs TTS (HTTPS Streaming)
sudo tcpdump -i eth0 -w capture_elevenlabs_$(date +%Y%m%d_%H%M).pcap \
  host api.elevenlabs.io -s 0 -c 10000
```

Waehrend tcpdump laeuft, parallel einen Layer-3-Messlauf starten:
```bash
python measurements/layer3_latency/run.py --n 1 --api stt --dry-run
```

## Analyse mit tshark

```bash
# Inter-Paket-Zeiten (Delta zwischen aufeinanderfolgenden Paketen)
tshark -r capture_deepgram.pcap -T fields \
  -e frame.time_delta_displayed -e frame.len -e tcp.len \
  -Y "tcp.len > 0" > ipt_deepgram.tsv

# WebSocket-Frames
tshark -r capture_deepgram.pcap -T fields \
  -e frame.time_relative -e websocket.opcode -e websocket.payload_length \
  -Y "websocket" > ws_frames_deepgram.tsv
```

## Erwartete Captures

| API | Protokoll | Captures | Zweck |
|-----|-----------|----------|-------|
| Deepgram | WebSocket | 5-10 | Audio-Upload + Transkript-Empfang |
| Requesty | HTTPS/SSE | 5-10 | Token-Delivery-Muster |
| ElevenLabs | HTTPS Streaming | 5-10 | Audio-Download-Muster |

## Output

Capture-Dateien (.pcap) und abgeleitete TSV-Dateien in `data/layer2/`.
