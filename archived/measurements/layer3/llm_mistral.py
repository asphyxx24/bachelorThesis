"""Mistral LLM Messung — HTTPS + SSE Streaming (OpenAI-kompatibel).

Cold-Start: Jede Messung baut eine neue TCP+TLS-Verbindung auf.
Misst connect_ms (TCP+TLS), headers_ms, ttft_ms, ttl_ms, total_ms.
"""

import asyncio
import json
import ssl
import time

import certifi
import httpx

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

_HOST = "api.mistral.ai"
_URL = "https://api.mistral.ai/v1/chat/completions"
_MODEL = "mistral-small-2603"
_PROMPT = "Reply in one short sentence: What is the capital of Germany?"
_MAX_TOKENS = 50


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
                    "model": _MODEL,
                    "messages": [{"role": "user", "content": _PROMPT}],
                    "max_tokens": _MAX_TOKENS,
                    "stream": True,
                },
            ) as response:
                t_headers = time.perf_counter()
                headers_ms = (t_headers - t_req) * 1000

                if response.status_code != 200:
                    body = (await response.aread()).decode(errors="replace")[:200]
                    return {"error": f"HTTP {response.status_code}: {body}"}

                t_first_content = None
                t_last_chunk = None
                token_count = 0
                parts = []

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        t_last_chunk = time.perf_counter()
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            if t_first_content is None:
                                t_first_content = time.perf_counter()
                            token_count += 1
                            parts.append(content)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

                if t_first_content is None or t_last_chunk is None:
                    return {"error": "no_content_received"}

                return {
                    "connect_ms": round(connect_ms, 1),
                    "headers_ms": round(headers_ms, 1),
                    "ttft_ms": round((t_first_content - t_req) * 1000, 1),
                    "ttl_ms": round((t_last_chunk - t_req) * 1000, 1),
                    "total_ms": round((t_last_chunk - t_start) * 1000, 1),
                    "token_count": token_count,
                    "response_len": len("".join(parts)),
                }

    except TimeoutError:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)[:120]}
