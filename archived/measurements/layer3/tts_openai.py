"""OpenAI TTS Messung — HTTPS Streaming (tts-1).

Cold-Start: Jede Messung baut eine neue TCP+TLS-Verbindung auf.
Misst connect_ms (TCP+TLS), ttfa_ms (Time to First Audio), total_ms, audio_bytes.
"""

import asyncio
import ssl
import time

import certifi
import httpx

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

_HOST = "api.openai.com"
_URL = "https://api.openai.com/v1/audio/speech"
_TEXT = "Good morning! How can I assist you today?"


async def _measure_connect(host: str, port: int = 443) -> float:
    t0 = time.perf_counter()
    _reader, writer = await asyncio.open_connection(host, port, ssl=_SSL_CTX)
    t1 = time.perf_counter()
    writer.close()
    try:
        await writer.wait_closed()
    except ssl.SSLError:
        pass
    return (t1 - t0) * 1000


async def measure_once(api_key: str) -> dict:
    t_start = time.perf_counter()

    try:
        connect_ms = await asyncio.wait_for(_measure_connect(_HOST), timeout=10)

        async with httpx.AsyncClient(verify=certifi.where(), timeout=30) as client:
            t_req = time.perf_counter()

            async with client.stream(
                "POST",
                _URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "tts-1",
                    "voice": "alloy",
                    "input": _TEXT,
                },
            ) as response:
                t_headers = time.perf_counter()

                if response.status_code != 200:
                    body = (await response.aread()).decode(errors="replace")[:200]
                    return {"error": f"HTTP {response.status_code}: {body}"}

                t_first_audio = None
                audio_bytes = 0

                async for chunk in response.aiter_bytes():
                    if t_first_audio is None:
                        t_first_audio = time.perf_counter()
                    audio_bytes += len(chunk)

                t_done = time.perf_counter()

                if t_first_audio is None:
                    return {"error": "no_audio_received"}

                return {
                    "connect_ms": round(connect_ms, 1),
                    "ttfa_ms": round((t_first_audio - t_req) * 1000, 1),
                    "total_ms": round((t_done - t_start) * 1000, 1),
                    "audio_bytes": audio_bytes,
                    "text_len": len(_TEXT),
                }

    except TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)[:120]}
