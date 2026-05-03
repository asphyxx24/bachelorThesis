"""Azure STT Messung — WebSocket Streaming (Italy North, proprietaeres Protokoll).

Azure Speech verwendet ein Mischformat aus Text- und Binaer-Messages:
- Text: Header-Block + JSON-Body (speech.config, speech.phrase, etc.)
- Binary: 2-Byte Header-Laenge + Header-Block + Audio-Daten

Cold-Start: Jede Messung baut eine neue WebSocket-Verbindung auf.
"""

import asyncio
import json
import ssl
import struct
import time
import uuid
import wave
from pathlib import Path

import certifi
from websockets.asyncio.client import connect as ws_connect

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

_WS_URL = (
    "wss://italynorth.stt.speech.microsoft.com"
    "/speech/recognition/conversation/cognitiveservices/v1"
    "?language=en-US&format=detailed"
)
CHUNK_SIZE = 4096


def load_pcm(wav_path: Path) -> bytes:
    with wave.open(str(wav_path), "rb") as wf:
        return wf.readframes(wf.getnframes())


def _ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _build_speech_config(request_id: str) -> str:
    headers = (
        f"Path: speech.config\r\n"
        f"X-RequestId: {request_id}\r\n"
        f"X-Timestamp: {_ts()}\r\n"
        f"Content-Type: application/json\r\n"
        f"\r\n"
    )
    body = json.dumps({
        "context": {
            "system": {"version": "1.0.00000"},
            "os": {"platform": "Python", "name": "Python", "version": "3.10"},
            "audio": {
                "source": {
                    "bitspersample": 16,
                    "channelcount": 1,
                    "connectivity": "Unknown",
                    "manufacturer": "Speech SDK",
                    "model": "Speech SDK",
                    "samplerate": 16000,
                    "type": "Microphones",
                }
            },
        }
    })
    return headers + body


def _build_audio_message(request_id: str, audio_data: bytes) -> bytes:
    header_str = (
        f"Path: audio\r\n"
        f"X-RequestId: {request_id}\r\n"
        f"X-Timestamp: {_ts()}\r\n"
        f"Content-Type: audio/x-wav\r\n"
    )
    header_bytes = header_str.encode("ascii")
    header_len = struct.pack(">H", len(header_bytes))
    return header_len + header_bytes + audio_data


async def measure_once(api_key: str, pcm_data: bytes) -> dict:
    request_id = str(uuid.uuid4()).replace("-", "")
    t_total_start = time.perf_counter()

    try:
        t_ws_start = time.perf_counter()
        async with ws_connect(
            _WS_URL,
            additional_headers={"Ocp-Apim-Subscription-Key": api_key},
            ssl=_SSL_CTX,
            open_timeout=10,
            close_timeout=5,
        ) as ws:
            t_ws_connected = time.perf_counter()
            connect_ms = (t_ws_connected - t_ws_start) * 1000

            await ws.send(_build_speech_config(request_id))

            t_first_chunk = None
            chunks = [pcm_data[i:i + CHUNK_SIZE] for i in range(0, len(pcm_data), CHUNK_SIZE)]
            for chunk in chunks:
                if t_first_chunk is None:
                    t_first_chunk = time.perf_counter()
                await ws.send(_build_audio_message(request_id, chunk))

            # Empty audio message signals end of audio
            await ws.send(_build_audio_message(request_id, b""))
            t_send_done = time.perf_counter()
            send_ms = (t_send_done - (t_first_chunk or t_send_done)) * 1000

            t_final = None
            transcript = ""

            async def _recv_final():
                nonlocal t_final, transcript
                async for raw in ws:
                    if isinstance(raw, bytes):
                        continue
                    if "speech.phrase" in raw:
                        body_start = raw.find("\r\n\r\n")
                        if body_start == -1:
                            continue
                        body = json.loads(raw[body_start + 4:])
                        if body.get("RecognitionStatus") == "Success":
                            t_final = time.perf_counter()
                            transcript = body.get("DisplayText", "")
                            return

            await asyncio.wait_for(_recv_final(), timeout=20)

            if t_final is None or t_first_chunk is None:
                return {"error": "no_final_result"}

            return {
                "connect_ms": round(connect_ms, 1),
                "send_ms": round(send_ms, 1),
                "ttft_ms": round((t_final - t_first_chunk) * 1000, 1),
                "total_ms": round((t_final - t_total_start) * 1000, 1),
                "transcript_len": len(transcript),
            }

    except TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)[:120]}
