# Layer 3 — Modulplan (9 Provider)

> Technischer Plan fuer die Implementierung aller 9 Messmodule.
> Module werden NICHT implementiert bevor dieser Plan reviewed ist.

---

## Interface-Vertrag

Jedes Modul exportiert eine asynchrone Funktion:

```python
async def measure_once(...) -> dict
```

**Erfolg:** Dict mit Messwerten (mindestens `connect_ms`, `total_ms`)
**Fehler:** Dict mit `{"error": "..."}`

### Gemeinsame Messwerte

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `connect_ms` | float | TCP+TLS(+WS) Handshake |
| `total_ms` | float | Gesamtdauer Request bis letzte Antwort |

### STT-spezifisch

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `send_ms` | float | Dauer Audio-Upload |
| `ttft_ms` | float | Erster Chunk bis finales Transkript |
| `transcript_len` | int | Laenge des Transkripts |

### LLM-spezifisch

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `headers_ms` | float | Request bis HTTP-Response-Header |
| `ttft_ms` | float | Request bis erster Content-Chunk |
| `ttl_ms` | float | Request bis letzter Chunk ([DONE]) |
| `token_count` | int | Anzahl empfangener Chunks |
| `response_len` | int | Laenge der Antwort in Zeichen |

### TTS-spezifisch

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `ttfa_ms` | float | Request bis erste Audio-Bytes |
| `audio_bytes` | int | Empfangene Audio-Bytes total |
| `text_len` | int | Laenge des Input-Textes |

---

## Cold-Start-Methodik

Jedes Modul MUSS:

1. **Neue TCP+TLS-Verbindung** pro Messung (kein Connection Pooling)
   - STT: Neuer WebSocket pro Call
   - LLM/TTS: Neuer `httpx.AsyncClient()` pro Call (NICHT als Context-Variable wiederverwenden)
2. `connect_ms` separat messen (Zeitpunkt TCP-Connect bis Verbindung bereit)
3. Timeouts setzen: 30s fuer HTTP, 20s fuer WebSocket-Empfang

---

## Feste Inputs

```python
# STT — alle 3 Module
SAMPLE_WAV = Path(__file__).parent / "sample.wav"

# LLM — alle 3 Module
TEST_PROMPT = "Reply in one short sentence: What is the capital of Germany?"
MAX_TOKENS = 50

# TTS — alle 3 Module
TEST_TEXT = "Good morning! How can I assist you today?"
```

---

## Module im Detail

### STT (WebSocket, Raw — kein SDK)

#### 1. `stt_deepgram.py` — EXISTIERT, bereinigt

- Endpoint: `wss://api.deepgram.com/v1/listen`
- Auth: `Authorization: Token {key}` Header
- Protokoll: WebSocket, Audio als PCM-Chunks, JSON-Response
- Sprache: `language=en` (korrigiert von `de`)
- Status: **Bereit** (nur language-Fix angewendet)

#### 2. `stt_revai.py` — IMPLEMENTIERT (ersetzt AssemblyAI)

- Endpoint: `wss://api.rev.ai/speechtotext/v1/stream`
- Auth: `?access_token={key}` Query-Parameter
- Query-Params: `&content_type=audio/x-raw;layout=interleaved;rate=16000;format=S16LE;channels=1`
- Protokoll: WebSocket, Audio-Dump (raw binary, kein Pacing noetig)
- Ablauf:
  1. WS oeffnen, auf `{"type": "connected"}` warten
  2. PCM-Chunks als binary Frames senden (kein Base64)
  3. `"EOS"` als Text-Message senden
  4. Auf `{"type": "final"}` warten
- Hinweis: AssemblyAI wurde ersetzt, weil dessen Streaming-API Echtzeit-Pacing
  erfordert — Audio muss so langsam gesendet werden wie es aufgenommen wurde.
  Das machte die TTFT-Messung inkonsistent mit Deepgram/Azure (Audio-Dump).
  Rev.ai akzeptiert Audio-Dump wie Deepgram und Azure.

#### 3. `stt_azure.py` — IMPLEMENTIERT

- Endpoint: `wss://italynorth.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1`
- Auth: `Ocp-Apim-Subscription-Key: {key}` Header
- Query-Params: `?language=en-US&format=detailed`
- Protokoll: WebSocket, proprietaeres Binaerprotokoll
- Ablauf:
  1. WS oeffnen mit Auth-Header und Query-Params
  2. Speech-Config als Textmessage senden (JSON)
  3. Audio-Header senden (Binary), dann Audio-Chunks
  4. Auf `speech.phrase` Message mit `RecognitionStatus: Success` warten
- Besonderheit: Azure nutzt ein Mischformat (Text + Binary Messages)
- Referenz: Microsoft Speech SDK WebSocket Protocol Docs

### LLM (HTTPS + SSE)

Alle 3 LLM-Module folgen dem gleichen Muster (OpenAI-kompatible API):

```python
async def measure_once(api_key: str, base_url: str, model: str) -> dict:
    # 1. Neuer httpx.AsyncClient (Cold-Start)
    # 2. POST /chat/completions mit stream=true
    # 3. SSE parsen: data: {...} Zeilen
    # 4. Zeitmessung: headers_ms, ttft_ms (erster content), ttl_ms ([DONE])
```

#### 4. `llm_openai.py` — IMPLEMENTIERT

- Base URL: `https://api.openai.com/v1`
- Model: `gpt-4o-mini`
- Auth: `Authorization: Bearer {key}`

#### 5. `llm_groq.py` — IMPLEMENTIERT

- Base URL: `https://api.groq.com/openai/v1`
- Model: `llama-3.1-8b-instant`
- Auth: `Authorization: Bearer {key}`
- Hinweis: Groq ist OpenAI-kompatibel, gleiche SSE-Struktur

#### 6. `llm_mistral.py` — IMPLEMENTIERT

- Base URL: `https://api.mistral.ai/v1`
- Model: `mistral-small-2603`
- Auth: `Authorization: Bearer {key}`
- Hinweis: Mistral ist OpenAI-kompatibel, gleiche SSE-Struktur

### TTS (HTTPS Streaming)

#### 7. `tts_deepgram.py` — IMPLEMENTIERT

- Endpoint: `https://api.deepgram.com/v1/speak?model=aura-2-asteria-en&encoding=mp3`
- Auth: `Authorization: Token {key}`
- Method: POST, Body = Raw Text (Content-Type: text/plain)
- Response: Audio-Stream (chunked)
- connect_ms: Bis HTTP-Response-Header empfangen

#### 8. `tts_openai.py` — IMPLEMENTIERT

- Endpoint: `https://api.openai.com/v1/audio/speech`
- Auth: `Authorization: Bearer {key}`
- Method: POST, Body = JSON `{"model": "tts-1", "voice": "alloy", "input": "..."}`
- Response: Audio-Stream (chunked)

#### 9. `tts_azure.py` — IMPLEMENTIERT

- Endpoint: `https://italynorth.tts.speech.microsoft.com/cognitiveservices/v1`
- Auth: `Ocp-Apim-Subscription-Key: {key}`
- Method: POST, Body = SSML
- Headers: `Content-Type: application/ssml+xml`, `X-Microsoft-OutputFormat: audio-16khz-128kbitrate-mono-mp3`
- SSML-Template:
  ```xml
  <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='en-US-JennyNeural'>Good morning! How can I assist you today?</voice>
  </speak>
  ```

---

## Abhängigkeiten

```
# requirements.txt — bereits vorhanden
websockets     # STT WebSocket
httpx          # LLM + TTS HTTP
python-dotenv  # .env laden
certifi        # SSL-Zertifikate
```

Pruefen ob `websockets` und `httpx` in requirements.txt stehen.

---

## Implementierungsreihenfolge (Empfehlung)

1. **LLM-Module** zuerst (einfachstes Pattern, alle OpenAI-kompatibel)
   - llm_openai.py → llm_groq.py → llm_mistral.py
   - Koennen sofort getestet werden (kein Audio noetig)
2. **TTS-Module** (HTTP Streaming, mittlere Komplexitaet)
   - tts_deepgram.py → tts_openai.py → tts_azure.py (SSML)
3. **STT-Module** (WebSocket, hoechste Komplexitaet)
   - stt_deepgram.py existiert schon
   - stt_revai.py (Audio-Dump, gleiche Methodik wie Deepgram)
   - stt_azure.py (proprietaeres Binaerprotokoll, am komplexesten)
4. **chain.py** neu schreiben (nachdem alle Module fertig sind)
5. **run.py** finalisieren (Testlaeufe)
