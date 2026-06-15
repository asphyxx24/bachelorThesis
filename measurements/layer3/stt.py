"""
Layer 3 — STT-Caller (Deepgram / Rev.ai / Azure), rohe WebSockets.

STT-Metrik-Asymmetrie (s. messprotokoll.md): ttft_ms = t_first_final - t_first_chunk
  -> connect-EXKLUSIV (Uhr startet beim ERSTEN Audio-Chunk, NACH dem Connect).
  Da Audio als Dump (nicht echtzeit-getaktet) gesendet wird, enthält ttft die Upload-Zeit
  + Provider-Endpointing + Engine. Diese Anteile sind über die Roh-Submetriken trennbar:

  Zeitachse je Call (alles als ms, ein Nullpunkt t0 = vor dem Connect):
    ws_connect_ms   = TCP+TLS+WS-Upgrade
    session_init_ms = ws_done -> erster Audio-Chunk (Rev.ai wartet hier auf "connected"-Msg!)
    audio_upload_ms = erster Chunk -> letzter Chunk gesendet
    ttft_ms         = erster Chunk -> erstes finales Transkript   (connect-EXKLUSIV)
    total_ms        = t0 -> Final empfangen (connect-INKLUSIV, OHNE WS-Close)

Drei Protokolle (rohe WS, kein SDK):
  - Deepgram: rohe PCM-Frames; CloseStream beendet; Finals sammeln, Abbruch bei "Metadata"
  - Rev.ai:   erst "connected"-Msg; rohe PCM-Frames; "EOS" beendet; Final in elements
  - Azure:    Microsoft-Framing (speech.config + Audio-Messages mit 2-Byte-Header); Final = speech.phrase

Gespeichert (Lehren A5/A14): voller Transkript-STRING (für WER), resolved_ip, model_requested, Fehler.
Erfolg = nicht-leeres Final-Transkript (A7).
Hinweis: Die STT-Hosts sind IPv4-only (keine AAAA) -> kein IPv6-Drift, kein Forcing nötig.

Ausführen (vom Repo-Wurzelverzeichnis, braucht Keys in .env + data/inputs/sample.wav):
  .venv/bin/python measurements/layer3/stt.py
"""

import asyncio
import json
import os
import ssl
import struct
import time
import uuid
import wave
from datetime import datetime, timezone

import certifi
from websockets.asyncio.client import connect as ws_connect

from config import (STT, STT_WAV, CONNECT_TIMEOUT_S, RESPONSE_TIMEOUT_S,
                    ROOT, DATA_DIR, get_key)
from connect import connect_submetrics

_SSL = ssl.create_default_context(cafile=certifi.where())
CHUNK_SIZE = 4096   # PCM-Chunk-Größe in Bytes


def load_pcm(path):
    """Liest die rohen PCM-Frames aus der WAV (ohne Header)."""
    with wave.open(str(path), "rb") as wf:
        return wf.readframes(wf.getnframes())


def _peer_ip(ws):
    """Tatsächliche Peer-IP der WS-Verbindung (A5). None, wenn nicht ermittelbar."""
    try:
        peer = ws.transport.get_extra_info("peername")
        return peer[0] if peer else None
    except Exception:
        return None


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ---- Azure Microsoft-Framing-Helfer ----
def _azure_config_msg(rid):
    headers = (f"Path: speech.config\r\nX-RequestId: {rid}\r\n"
               f"X-Timestamp: {_now_iso()}\r\nContent-Type: application/json\r\n\r\n")
    body = json.dumps({"context": {
        "system": {"version": "1.0.00000"},
        "os": {"platform": "Python", "name": "Python", "version": "3.9"},
        "audio": {"source": {"bitspersample": 16, "channelcount": 1, "connectivity": "Unknown",
                             "manufacturer": "Speech SDK", "model": "Speech SDK",
                             "samplerate": 16000, "type": "Microphones"}}}})
    return headers + body


def _azure_audio_msg(rid, data):
    h = (f"Path: audio\r\nX-RequestId: {rid}\r\n"
         f"X-Timestamp: {_now_iso()}\r\nContent-Type: audio/x-wav\r\n").encode("ascii")
    return struct.pack(">H", len(h)) + h + data


# ---- Protokoll-I/O: gibt jeweils (t_first_chunk, t_upload_done, t_first_final, transcript) ----
async def _io_deepgram(ws, pcm):
    t_first = None
    for i in range(0, len(pcm), CHUNK_SIZE):
        if t_first is None:
            t_first = time.perf_counter()
        await ws.send(pcm[i:i + CHUNK_SIZE])
    await ws.send(json.dumps({"type": "Finalize"}))
    await ws.send(json.dumps({"type": "CloseStream"}))
    t_upload = time.perf_counter()
    t_final, segs = None, []
    async for raw in ws:
        msg = json.loads(raw)
        mtype = msg.get("type")
        if mtype == "Results" and msg.get("is_final"):
            alts = msg.get("channel", {}).get("alternatives", [{}])
            text = alts[0].get("transcript", "") if alts else ""
            if text:
                if t_final is None:
                    t_final = time.perf_counter()
                segs.append(text)
        elif mtype == "Metadata":          # kommt nach allen Finals -> sauberer Abbruch (kein Hänger)
            break
    return t_first, t_upload, t_final, " ".join(segs)


async def _io_revai(ws, pcm):
    connected = json.loads(await ws.recv())          # erst die "connected"-Message (Session-Init, ~1 RTT)
    if connected.get("type") != "connected":
        raise RuntimeError(f"rev.ai unerwartete erste Message: {connected.get('type')}")
    t_first = None
    for i in range(0, len(pcm), CHUNK_SIZE):
        if t_first is None:
            t_first = time.perf_counter()
        await ws.send(pcm[i:i + CHUNK_SIZE])
    await ws.send("EOS")
    t_upload = time.perf_counter()
    async for raw in ws:
        msg = json.loads(raw)
        if msg.get("type") == "final":
            text = "".join(e.get("value", "") for e in msg.get("elements", []))
            return t_first, t_upload, time.perf_counter(), text
    return t_first, t_upload, None, ""


async def _io_azure(ws, pcm):
    rid = uuid.uuid4().hex
    await ws.send(_azure_config_msg(rid))
    t_first = None
    for i in range(0, len(pcm), CHUNK_SIZE):
        if t_first is None:
            t_first = time.perf_counter()
        await ws.send(_azure_audio_msg(rid, pcm[i:i + CHUNK_SIZE]))
    await ws.send(_azure_audio_msg(rid, b""))         # leere Audio-Message = Ende
    t_upload = time.perf_counter()
    async for raw in ws:
        if isinstance(raw, bytes):
            continue
        if "speech.phrase" in raw:
            body_start = raw.find("\r\n\r\n")
            if body_start == -1:
                continue
            body = json.loads(raw[body_start + 4:])
            if body.get("RecognitionStatus") == "Success":
                return t_first, t_upload, time.perf_counter(), body.get("DisplayText", "")
    return t_first, t_upload, None, ""


_IO = {"deepgram": _io_deepgram, "revai": _io_revai, "azure": _io_azure}


async def _run(name, ep, key, pcm):
    """Öffnet die WS, misst die Submetriken, dispatcht ans Protokoll. Gibt dict zurück."""
    out = {"ws_connect_ms": None, "session_init_ms": None, "audio_upload_ms": None,
           "ttft_ms": None, "total_ms": None, "transcript": "", "resolved_ip": None, "error": None}

    if name == "deepgram":
        url, headers = ep["url"], {"Authorization": f"Token {key}"}
    elif name == "revai":
        url, headers = ep["url"] + f"&access_token={key}", None
    elif name == "azure":
        url, headers = ep["url"] + "?language=en-US&format=detailed", {"Ocp-Apim-Subscription-Key": key}
    else:
        out["error"] = f"unbekannter Provider: {name}"
        return out

    t0 = time.perf_counter()
    try:
        async with ws_connect(url, additional_headers=headers, ssl=_SSL,
                              open_timeout=CONNECT_TIMEOUT_S, close_timeout=2,
                              ping_interval=None) as ws:    # kein Keepalive-Ping auf der Mess-Verbindung
            t_ws_done = time.perf_counter()
            out["ws_connect_ms"] = round((t_ws_done - t0) * 1000, 2)
            out["resolved_ip"] = _peer_ip(ws)
            t_first, t_upload, t_final, transcript = await asyncio.wait_for(
                _IO[name](ws, pcm), timeout=RESPONSE_TIMEOUT_S)
            t_done = time.perf_counter()                    # vor dem WS-Close gemessen
        out["total_ms"] = round((t_done - t0) * 1000, 2)
        if t_first is None or t_final is None:
            out["error"] = "kein finales Transkript"
            return out
        out["session_init_ms"] = round((t_first - t_ws_done) * 1000, 2)
        out["audio_upload_ms"] = round((t_upload - t_first) * 1000, 2)
        out["ttft_ms"] = round((t_final - t_first) * 1000, 2)
        out["transcript"] = transcript
    except asyncio.TimeoutError:
        out["error"] = "timeout"
        out["total_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {str(e)[:120]}"
        out["total_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return out


def call_stt(name, ep, pcm):
    """Ein Cold-Start-STT-Call. Gibt IMMER einen Record zurück."""
    rec = {
        "provider": name,
        "category": "stt",
        "model_requested": ep.get("model"),
        "resolved_ip": None,
        "connect": None,            # dns/tcp/tls-Referenz (Wegwerf-Socket)
        "ws_connect_ms": None,      # echter WS-Connect (TCP+TLS+WS-Upgrade)
        "session_init_ms": None,    # ws_done -> erster Audio-Chunk (Rev.ai: "connected"-Wartezeit)
        "audio_upload_ms": None,    # erster -> letzter Audio-Chunk gesendet
        "ttft_ms": None,            # connect-EXKLUSIV: t_first_final - t_first_chunk
        "total_ms": None,           # connect-INKLUSIV (ohne WS-Close)
        "transcript": "",
        "n_chars": 0,
        "success": False,
        "error": None,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    key = get_key(ep["key_env"])
    if not key:
        rec["error"] = f"kein API-Key ({ep['key_env']})"
        return rec

    rec["connect"] = connect_submetrics(ep["host"], timeout=CONNECT_TIMEOUT_S)
    res = asyncio.run(_run(name, ep, key, pcm))
    for k in ("ws_connect_ms", "session_init_ms", "audio_upload_ms", "ttft_ms",
              "total_ms", "transcript", "resolved_ip", "error"):
        rec[k] = res[k]
    rec["n_chars"] = len(rec["transcript"])
    rec["success"] = bool(rec["transcript"].strip())
    return rec


def main():
    wav = ROOT / STT_WAV
    if not wav.exists():
        print(f"FEHLT: {wav} — bitte sample.wav anlegen.")
        return
    pcm = load_pcm(wav)
    results = [call_stt(name, ep, pcm) for name, ep in STT.items()]

    print(f"{'Provider':<10} {'ws_conn':>8} {'sess_in':>8} {'ttft':>9} {'total':>9} {'ok':>4}  Transkript / Fehler")
    for r in results:
        def f(x):
            return f"{x:.1f}" if x is not None else "-"
        ok = "ja" if r["success"] else "—"
        note = r["transcript"][:42] if r["success"] else (r["error"] or "")
        print(f"{r['provider']:<10} {f(r['ws_connect_ms']):>8} {f(r['session_init_ms']):>8} "
              f"{f(r['ttft_ms']):>9} {f(r['total_ms']):>9} {ok:>4}  {note}")

    os.makedirs(DATA_DIR, exist_ok=True)
    out = DATA_DIR / "stt.jsonl"
    with open(out, "w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
