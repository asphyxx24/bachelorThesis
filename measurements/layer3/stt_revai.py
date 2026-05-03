"""Rev.ai STT Messung — WebSocket Streaming.

Sendet Audio als raw binary Frames ueber WebSocket (Audio-Dump).
Rev.ai verarbeitet Audio schneller als Echtzeit — gleiche Methodik
wie Deepgram und Azure.
Cold-Start: Jede Messung baut eine neue WebSocket-Verbindung auf.
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

_WS_URL = (
    "wss://api.rev.ai/speechtotext/v1/stream"
    "?content_type=audio/x-raw;layout=interleaved;rate=16000;format=S16LE;channels=1"
)
CHUNK_SIZE = 4096


def load_pcm(wav_path: Path) -> bytes:
    with wave.open(str(wav_path), "rb") as wf:
        return wf.readframes(wf.getnframes())


async def measure_once(api_key: str, pcm_data: bytes) -> dict:
    url = f"{_WS_URL}&access_token={api_key}"
    t_total_start = time.perf_counter()

    try:
        t_ws_start = time.perf_counter()
        async with ws_connect(
            url,
            ssl=_SSL_CTX,
            open_timeout=10,
            close_timeout=5,
        ) as ws:
            t_ws_connected = time.perf_counter()
            connect_ms = (t_ws_connected - t_ws_start) * 1000

            connected_msg = await asyncio.wait_for(ws.recv(), timeout=5)
            connected = json.loads(connected_msg)
            if connected.get("type") != "connected":
                return {"error": f"unexpected_connect: {connected.get('type')}"}

            t_first_chunk = None
            chunks = [pcm_data[i:i + CHUNK_SIZE] for i in range(0, len(pcm_data), CHUNK_SIZE)]
            for chunk in chunks:
                if t_first_chunk is None:
                    t_first_chunk = time.perf_counter()
                await ws.send(chunk)

            await ws.send("EOS")
            t_send_done = time.perf_counter()
            send_ms = (t_send_done - (t_first_chunk or t_send_done)) * 1000

            t_final = None
            transcript = ""
            async with asyncio.timeout(20):
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "final":
                        t_final = time.perf_counter()
                        elements = msg.get("elements", [])
                        transcript = "".join(
                            e.get("value", "") for e in elements
                        )
                        break

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
