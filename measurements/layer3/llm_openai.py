"""Requesty LLM Messung — HTTPS + Server-Sent Events (SSE).

Sendet einen standardisierten Prompt und misst:
  TTFT = t(Request) -> t(erstes delta.content)
  TTL  = t(Request) -> t([DONE])
"""

import json
import time

import httpx

TEST_PROMPT = (
    "Erklaere in 3-4 Saetzen, wie ein Sprachassistent funktioniert "
    "und welche Komponenten dabei eine Rolle spielen."
)
TEST_MODEL = "google/gemini-2.5-flash"
MAX_TOKENS = 150


async def measure_once(api_key: str, base_url: str) -> dict:
    """Fuehrt eine einzelne LLM-Messung durch.

    Returns:
        {"model", "headers_ms", "ttft_ms", "ttl_ms", "token_count", "response_len"}
        Bei Fehler: {"error": "..."}
    """
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": TEST_MODEL,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "stream": True,
        "max_tokens": MAX_TOKENS,
    }

    t_request = time.perf_counter()
    t_headers: float | None = None
    t_ttft: float | None = None
    t_done: float | None = None
    token_count = 0
    full_text = ""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                resp.raise_for_status()
                t_headers = time.perf_counter()

                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        t_done = time.perf_counter()
                        break
                    if not payload:
                        continue

                    try:
                        chunk = json.loads(payload)
                    except Exception:
                        continue

                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        if t_ttft is None:
                            t_ttft = time.perf_counter()
                        token_count += 1
                        full_text += content

        if t_ttft is None or t_done is None or t_headers is None:
            return {"error": "incomplete_stream"}

        return {
            "model": TEST_MODEL,
            "headers_ms": round((t_headers - t_request) * 1000, 1),
            "ttft_ms": round((t_ttft - t_request) * 1000, 1),
            "ttl_ms": round((t_done - t_request) * 1000, 1),
            "token_count": token_count,
            "response_len": len(full_text),
        }

    except httpx.TimeoutException:
        return {"error": "timeout"}
    except httpx.HTTPStatusError as e:
        return {"error": f"http_{e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)[:120]}
