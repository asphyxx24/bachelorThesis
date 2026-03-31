"""ElevenLabs TTS Messung — HTTP Streaming.

Sendet einen standardisierten Text und misst:
  TTFA = t(Request) -> t(erste Audio-Bytes empfangen)
"""

import time

import httpx

TEST_TEXT = "Das ist eine standardisierte Testantwort fuer die Bachelorarbeit."
TTS_MODEL = "eleven_flash_v2_5"
OUTPUT_FORMAT = "mp3_22050_32"


async def measure_once(api_key: str, voice_id: str) -> dict:
    """Fuehrt eine einzelne TTS-Messung durch.

    Returns:
        {"model", "ttfa_ms", "total_ms", "audio_bytes", "text_len"}
        Bei Fehler: {"error": "..."}
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    body = {
        "text": TEST_TEXT,
        "model_id": TTS_MODEL,
        "output_format": OUTPUT_FORMAT,
    }

    t_request = time.perf_counter()
    t_ttfa: float | None = None
    audio_bytes = 0

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                resp.raise_for_status()

                async for chunk in resp.aiter_bytes():
                    if chunk:
                        if t_ttfa is None:
                            t_ttfa = time.perf_counter()
                        audio_bytes += len(chunk)

        t_done = time.perf_counter()

        if t_ttfa is None:
            return {"error": "no_audio_received"}

        return {
            "model": TTS_MODEL,
            "ttfa_ms": round((t_ttfa - t_request) * 1000, 1),
            "total_ms": round((t_done - t_request) * 1000, 1),
            "audio_bytes": audio_bytes,
            "text_len": len(TEST_TEXT),
        }

    except httpx.TimeoutException:
        return {"error": "timeout"}
    except httpx.HTTPStatusError as e:
        return {"error": f"http_{e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)[:120]}
