"""Deepgram STT Messung — WebSocket Streaming.

Sendet eine WAV-Datei (PCM 16-bit, 16kHz, Mono) als Audio-Chunks
ueber WebSocket an Deepgram und misst die Zeit bis zum finalen Transkript.

Metrik: TTFT = t(erster Audio-Chunk gesendet) -> t(is_final=true empfangen)
"""

import asyncio
import json
import ssl
import time
import wave
from pathlib import Path

import certifi
from websockets.asyncio.client import connect as ws_connect

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

DEEPGRAM_WS_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-3&language=en&encoding=linear16"
    "&sample_rate=16000&punctuate=true&interim_results=false"
)
CHUNK_SIZE = 4096  # 4 KB PCM-Chunks


def load_pcm(wav_path: Path) -> bytes:
    """Laedt eine WAV-Datei und gibt die rohen PCM-Frames zurueck (ohne Header)."""
    with wave.open(str(wav_path), "rb") as wf:
        return wf.readframes(wf.getnframes())


async def measure_once(api_key: str, pcm_data: bytes) -> dict:
    """Fuehrt eine einzelne STT-Messung durch.

    Returns:
        {"connect_ms", "send_ms", "ttft_ms", "total_ms", "transcript_len"}
        Bei Fehler: {"error": "..."}
    """
    headers = {"Authorization": f"Token {api_key}"}
    t_total_start = time.perf_counter()

    try:
        t_ws_start = time.perf_counter()
        async with ws_connect(
            DEEPGRAM_WS_URL,
            additional_headers=headers,
            ssl=_SSL_CTX,
            open_timeout=10,
            close_timeout=5,
        ) as ws:
            t_ws_connected = time.perf_counter()
            connect_ms = (t_ws_connected - t_ws_start) * 1000

            # Audio in Chunks senden
            t_first_chunk = None
            chunks = [pcm_data[i:i + CHUNK_SIZE] for i in range(0, len(pcm_data), CHUNK_SIZE)]
            for chunk in chunks:
                if t_first_chunk is None:
                    t_first_chunk = time.perf_counter()
                await ws.send(chunk)

            await ws.send(json.dumps({"type": "Finalize"}))
            await ws.send(json.dumps({"type": "CloseStream"}))
            t_send_done = time.perf_counter()
            send_ms = (t_send_done - (t_first_chunk or t_send_done)) * 1000

            t_first_final = None
            t_last_final = None
            segments = []

            async def _recv_finals():
                nonlocal t_first_final, t_last_final
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "Results" and msg.get("is_final"):
                        t_last_final = time.perf_counter()
                        if t_first_final is None:
                            t_first_final = t_last_final
                        alts = msg.get("channel", {}).get("alternatives", [{}])
                        text = alts[0].get("transcript", "") if alts else ""
                        if text:
                            segments.append(text)

            try:
                await asyncio.wait_for(_recv_finals(), timeout=20)
            except Exception:
                pass

            if t_first_final is None or t_first_chunk is None:
                return {"error": "no_final_result"}

            transcript = " ".join(segments)
            return {
                "connect_ms": round(connect_ms, 1),
                "send_ms": round(send_ms, 1),
                "ttft_ms": round((t_first_final - t_first_chunk) * 1000, 1),
                "total_ms": round((t_last_final - t_total_start) * 1000, 1),
                "transcript_len": len(transcript),
            }

    except TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)[:120]}
