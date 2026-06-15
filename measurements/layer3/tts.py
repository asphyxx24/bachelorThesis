"""
Layer 3 — TTS-Caller (Deepgram / OpenAI / Azure), HTTPS-Streaming.

Misst je Provider über eine FRISCHE Verbindung (Cold-Start, kein Pooling):
  - ttfa_ms : Zeit bis zum ersten Audio-Byte (ab Request-Absenden -> connect-INKLUSIV)
  - total_ms: Zeit bis das Audio vollständig empfangen ist
  - audio_bytes, n_chunks (erkennt Block- vs. Streaming-Lieferung), resolved_ip (A5),
    model_requested + effective_model (A2), connect (dns/tcp/tls-Referenz)
Erfolg = Audio-Body >= TTS_MIN_BYTES (A7).

Hinweis: audio_bytes ist nur Erfolgs-Gate, KEIN Cross-Provider-Vergleichsmaß — die
mp3-Bitraten/Sampleraten der drei Anbieter unterscheiden sich (nur Format mp3 gepinnt, A8).

Drei Anbieter, unterschiedliche Auth + Body:
  - Deepgram: "Authorization: Token", JSON {"text": ...}
  - OpenAI:   "Authorization: Bearer", JSON {model,input,voice,response_format}
  - Azure:    "Ocp-Apim-Subscription-Key", Body = SSML (Stimme aus Config)

Ausführen (vom Repo-Wurzelverzeichnis, braucht Keys in .env):
  .venv/bin/python measurements/layer3/tts.py
"""

import json
import os
import time
import httpx
from datetime import datetime, timezone

from config import (TTS, TTS_TEXT, CONNECT_TIMEOUT_S, RESPONSE_TIMEOUT_S,
                    TTS_MIN_BYTES, DATA_DIR, get_key)
from connect import connect_submetrics


def peer_ip(resp):
    """Tatsächliche Peer-IP der Mess-Verbindung (A5). None, wenn nicht ermittelbar."""
    try:
        ns = resp.extensions.get("network_stream")
        addr = ns.get_extra_info("server_addr") if ns else None
        return addr[0] if addr else None
    except Exception:
        return None


def build_request(ep, key):
    """Baut (headers, json_body, content_body) je nach Provider-Auth-Schema."""
    auth = ep["auth"]
    if auth == "token":        # Deepgram
        return {"Authorization": f"Token {key}"}, {"text": TTS_TEXT}, None
    if auth == "bearer":       # OpenAI
        return ({"Authorization": f"Bearer {key}"},
                {"model": ep["model"], "input": TTS_TEXT,
                 "voice": ep.get("voice", "alloy"), "response_format": ep.get("format", "mp3")},
                None)
    if auth == "azure":        # Azure: SSML-Body
        ssml = (f"<speak version='1.0' xml:lang='en-US'>"
                f"<voice name='{ep['voice']}'>{TTS_TEXT}</voice></speak>")
        headers = {"Ocp-Apim-Subscription-Key": key,
                   "Content-Type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3"}
        return headers, None, ssml
    raise ValueError(f"unbekanntes auth-Schema: {auth}")


def call_tts(name, ep):
    """Ein Cold-Start-Call gegen einen TTS-Provider. Gibt IMMER einen Record zurück."""
    rec = {
        "provider": name,
        "category": "tts",
        "model_requested": ep.get("model") or ep.get("voice"),
        "effective_model": None,
        "resolved_ip": None,
        "connect": None,
        "ttfa_ms": None,
        "total_ms": None,
        "audio_bytes": 0,
        "n_chunks": 0,
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

    rec["connect"] = connect_submetrics(ep["host"], timeout=CONNECT_TIMEOUT_S)
    timeout = httpx.Timeout(connect=CONNECT_TIMEOUT_S, read=RESPONSE_TIMEOUT_S, write=10.0, pool=10.0)
    transport = httpx.HTTPTransport(http2=True, local_address="0.0.0.0")   # IPv4 erzwingen (wie llm.py)

    t_req = None
    try:
        headers, json_body, content_body = build_request(ep, key)   # im try -> Record-Garantie
        kwargs = {"headers": headers}
        if json_body is not None:
            kwargs["json"] = json_body
        if content_body is not None:
            kwargs["content"] = content_body

        with httpx.Client(transport=transport, timeout=timeout) as client:
            t_req = time.perf_counter()
            with client.stream("POST", ep["url"], **kwargs) as resp:
                rec["http_version"] = resp.http_version
                rec["status"] = resp.status_code
                rec["resolved_ip"] = peer_ip(resp)
                rec["effective_model"] = resp.headers.get("dg-model-name")   # opportunistisch (A2; v.a. Deepgram)
                if resp.status_code != 200:
                    rec["error"] = f"http_{resp.status_code}"
                    rec["error_body"] = resp.read()[:500].decode("utf-8", "replace")
                    return rec
                for chunk in resp.iter_bytes():
                    if not chunk:
                        continue
                    if rec["ttfa_ms"] is None:
                        rec["ttfa_ms"] = round((time.perf_counter() - t_req) * 1000, 2)
                    rec["n_chunks"] += 1
                    rec["audio_bytes"] += len(chunk)
        rec["total_ms"] = round((time.perf_counter() - t_req) * 1000, 2)
        rec["success"] = rec["audio_bytes"] >= TTS_MIN_BYTES
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        if t_req is not None and rec["total_ms"] is None:
            rec["total_ms"] = round((time.perf_counter() - t_req) * 1000, 2)
    return rec


def main():
    results = [call_tts(name, ep) for name, ep in TTS.items()]

    print(f"{'Provider':<10} {'ttfa':>8} {'total':>8} {'bytes':>8} {'chunks':>7} {'ok':>4}  Fehler")
    for r in results:
        ttfa = f"{r['ttfa_ms']:.1f}" if r["ttfa_ms"] is not None else "-"
        total = f"{r['total_ms']:.1f}" if r["total_ms"] is not None else "-"
        ok = "ja" if r["success"] else "—"
        print(f"{r['provider']:<10} {ttfa:>8} {total:>8} {r['audio_bytes']:>8} {r['n_chunks']:>7} {ok:>4}  {r['error'] or ''}")

    os.makedirs(DATA_DIR, exist_ok=True)
    out = DATA_DIR / "tts.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
