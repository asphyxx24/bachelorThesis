"""
Layer 3 — LLM-Caller (OpenAI / Groq / Mistral), HTTPS + SSE.

Misst je Provider über eine FRISCHE Verbindung (Cold-Start, kein Pooling):
  - ttft_ms : Zeit bis zum ersten Token (ab Request-Absenden -> connect-INKLUSIV)
  - total_ms: Zeit bis der Stream fertig ist (= Time-to-Last-Token)
  - n_chunks, output_text, output_tokens, effective_model (Backend-Drift, A2)
  - resolved_ip: echte Peer-IP des Mess-Requests (A5; Edge-vs-Backend-Beleg A3)
  - connect   : atomare dns/tcp/tls-Submetriken (Referenz, Wegwerf-Socket, TCP+TLS-only)
Erfolg = inhaltlich (>= LLM_MIN_CHARS Zeichen Antwort), A7/F3 — NICHT über Chunk-Zahl
  (providerspez. SSE-Batching, z.B. Mistral 1 Chunk, ist kein Fehler).

Ausführen (vom Repo-Wurzelverzeichnis, braucht Keys in .env):
  .venv/bin/python measurements/layer3/llm.py
"""

import json
import os
import time
import httpx
from datetime import datetime, timezone

from config import (LLM, LLM_PROMPT, MAX_TOKENS, CONNECT_TIMEOUT_S,
                    RESPONSE_TIMEOUT_S, LLM_MIN_CHARS, DATA_DIR, get_key)
from connect import connect_submetrics


def peer_ip(resp):
    """Tatsächliche Peer-IP der Mess-Verbindung (A5). None, wenn nicht ermittelbar."""
    try:
        ns = resp.extensions.get("network_stream")
        addr = ns.get_extra_info("server_addr") if ns else None
        return addr[0] if addr else None
    except Exception:
        return None


def call_llm(name, ep):
    """Ein Cold-Start-Call gegen einen LLM-Provider. Gibt IMMER einen Record zurück."""
    rec = {
        "provider": name,
        "category": "llm",
        "model_requested": ep["model"],
        "effective_model": None,
        "resolved_ip": None,         # echte Peer-IP des Mess-Requests (A5)
        "connect": None,             # dns/tcp/tls-Referenz (Wegwerf-Socket, nur TCP+TLS)
        "ttft_ms": None,
        "total_ms": None,
        "n_chunks": 0,
        "output_tokens": None,
        "output_text": "",
        "http_version": None,
        "status": None,
        "success": False,
        "error": None,
        "error_body": None,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    key = get_key(ep["key_env"])
    if not key:
        rec["error"] = f"kein API-Key ({ep['key_env']})"
        return rec

    # connect-Submetriken als Referenz (Wegwerf-Socket, getrennt vom Mess-Request)
    rec["connect"] = connect_submetrics(ep["host"], timeout=CONNECT_TIMEOUT_S)

    body = {"model": ep["model"],
            "messages": [{"role": "user", "content": LLM_PROMPT}],
            "stream": True,
            "max_tokens": MAX_TOKENS,
            "stream_options": {"include_usage": True}}   # F2: sonst liefert OpenAI keine usage/output_tokens
    headers = {"Authorization": f"Bearer {key}"}
    timeout = httpx.Timeout(connect=CONNECT_TIMEOUT_S, read=RESPONSE_TIMEOUT_S, write=10.0, pool=10.0)
    # IPv4 erzwingen (local_address=0.0.0.0): konsistent mit Layer 1 (gethostbyname/IPv4) und der
    # ASN/Edge-Klassifikation. Sonst wählt httpx auf Dual-Stack-Hosts (Cloudflare!) evtl. IPv6.
    transport = httpx.HTTPTransport(http2=True, local_address="0.0.0.0")

    t_req = None
    try:
        # frischer Client je Call -> keine Wiederverwendung der Verbindung (Cold-Start)
        with httpx.Client(transport=transport, timeout=timeout) as client:
            t_req = time.perf_counter()      # Uhr ab Request-Absenden (nach Client-Aufbau)
            with client.stream("POST", ep["url"], json=body, headers=headers) as resp:
                rec["http_version"] = resp.http_version
                rec["status"] = resp.status_code
                rec["resolved_ip"] = peer_ip(resp)
                if resp.status_code != 200:
                    rec["error"] = f"http_{resp.status_code}"
                    rec["error_body"] = resp.read()[:500].decode("utf-8", "replace")
                    return rec
                for line in resp.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("model"):
                        rec["effective_model"] = obj["model"]
                    usage = obj.get("usage")
                    if usage and usage.get("completion_tokens") is not None:
                        rec["output_tokens"] = usage["completion_tokens"]
                    choices = obj.get("choices") or [{}]
                    delta = (choices[0].get("delta") or {}).get("content")
                    if delta:
                        if rec["ttft_ms"] is None:
                            rec["ttft_ms"] = round((time.perf_counter() - t_req) * 1000, 2)
                        rec["n_chunks"] += 1
                        rec["output_text"] += delta
        rec["total_ms"] = round((time.perf_counter() - t_req) * 1000, 2)
        rec["success"] = len(rec["output_text"].strip()) >= LLM_MIN_CHARS   # F3: inhaltlich, nicht Chunk-Zahl
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        if t_req is not None and rec["total_ms"] is None:
            rec["total_ms"] = round((time.perf_counter() - t_req) * 1000, 2)   # Zeit bis Abbruch
    return rec


def main():
    results = [call_llm(name, ep) for name, ep in LLM.items()]

    print(f"{'Provider':<10} {'ttft':>8} {'total':>8} {'chunks':>7} {'ok':>4}  Modell / Fehler")
    for r in results:
        ttft = f"{r['ttft_ms']:.1f}" if r["ttft_ms"] is not None else "-"
        total = f"{r['total_ms']:.1f}" if r["total_ms"] is not None else "-"
        ok = "ja" if r["success"] else "—"
        note = r["effective_model"] or r["error"] or ""
        print(f"{r['provider']:<10} {ttft:>8} {total:>8} {r['n_chunks']:>7} {ok:>4}  {note}")

    os.makedirs(DATA_DIR, exist_ok=True)
    out = DATA_DIR / "llm.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
