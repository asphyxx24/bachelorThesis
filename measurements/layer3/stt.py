"""
Layer 3 — STT-Caller (Deepgram / Rev.ai / Azure), rohe WebSockets.

Audio wird im 1x-REALTIME-TAKT gestreamt (nicht als Dump), gesendet UND empfangen LAUFEN PARALLEL
(asyncio.gather). Grund: nur bei echtzeit-eintreffendem Audio liefern ALLE Provider echte Interim-Wörter
(Deepgram sendet beim Dump keins), erst dadurch ist ttfp cross-provider fair UND pipeline-realistisch.
Parallel-Empfang ist nötig, damit ttfp gestempelt wird, wenn das Wort ankommt — nicht erst nach Upload.

STT-Metrik-Asymmetrie (s. messprotokoll.md). PRIMÄRMETRIK ist ttfp (First-Partial):
  ttfp_ms = t_first_partial - t_first_chunk
  -> Zeit bis zum ERSTEN Live-Wort (Interim/Partial/Hypothese). Endpointing-frei (das erste Live-Wort
  kommt VOR der Stille-Wartezeit). Enthält bauartbedingt ~1 In-Band-RTT (Audio hin + Partial zurück) ->
  "Netz-Roundtrip + Engine-Reaktion", NICHT reine Rechenzeit; Netz-Anteil via connect/RTT abschätzbar.
  ttft (Stream-Ende-Final) bleibt SEKUNDÄR: Zeit bis zum letzten finalisierten Segment (deepgram: letztes
  is_final, damit cross-provider vergleichbar mit Azure/Rev.ai). Das kleine Post-Audio-Warten (ttft −
  audio_upload, paced ~98 ms bei Azure) ist KEIN großer fester Stille-Timer — die im Dump beobachteten
  ~1722 ms waren Bulk-Verarbeitung, kein Endpointing-Fenster (s. AUDIT_stt_methodik_2026-06-16.md).
  Beide connect-EXKLUSIV (Uhr ab erstem Audio-Chunk).

  Zeitachse je Call (alles als ms, ein Nullpunkt t0 = vor dem Connect):
    ws_connect_ms   = TCP+TLS+WS-Upgrade
    session_init_ms = ws_done -> erster Audio-Chunk (Rev.ai wartet hier auf "connected"-Msg!)
    audio_upload_ms = erster -> letzter Chunk gesendet (~Audiodauer, da 1x-realtime getaktet)
    ttfp_ms         = erster Chunk -> erstes LIVE-Wort         (PRIMÄR, endpointing-frei)
    ttft_ms         = erster Chunk -> Stream-Ende-Final        (SEKUNDÄR; deepgram=letztes Segment-Final)
    total_ms        = t0 -> Final empfangen (connect-INKLUSIV, OHNE WS-Close)

Drei Protokolle (rohe WS, kein SDK), je getaktetes Senden + paralleler Empfang:
  - Deepgram: rohe PCM-Frames; Finalize+CloseStream beenden; Finals sammeln, Abbruch bei "Metadata"
  - Rev.ai:   erst "connected"-Msg; rohe PCM-Frames; "EOS" beendet; Partial/Final in elements
  - Azure:    Microsoft-Framing (speech.config + Audio-Messages mit 2-Byte-Header); Final = speech.phrase

Gespeichert (Lehren A5/A14): voller Transkript-STRING (für WER), resolved_ip, model_requested, Fehler.
Erfolg = nicht-leeres Final-Transkript (A7).
Hinweis: Die STT-Hosts liefern aktuell nur IPv4 — zur Konsistenz mit LLM/TTS (die IPv4 erzwingen)
wird IPv4 hier dennoch hart gepinnt (family=AF_INET), falls sich die DNS-Antwort mal ändert.

Ausführen (vom Repo-Wurzelverzeichnis, braucht Keys in .env + data/inputs/sample.wav):
  .venv/bin/python measurements/layer3/stt.py
"""

import asyncio
import json
import os
import socket
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
CHUNK_SIZE = 4096       # PCM-Chunk-Größe in Bytes
SAMPLE_RATE = 16000     # Hz (sample.wav)
BYTES_PER_SAMPLE = 2    # linear16 = 16 bit mono
# 1x-Realtime-Takt: ein 4096-B-Chunk = 4096/(16000*2) = 0,128 s Audio -> so schnell darf gesendet werden.
# Echtzeit-Pacing ist nötig, damit alle Provider echte Interim-Wörter liefern und ttfp cross-provider
# fair + pipeline-realistisch ist (sonst sendet Deepgram beim Dump kein Interim). S. messprotokoll.md.
CHUNK_SECONDS = CHUNK_SIZE / (SAMPLE_RATE * BYTES_PER_SAMPLE)


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


def _azure_body(raw):
    """Parst den JSON-Body einer Azure-Textmessage (nach dem \\r\\n\\r\\n). None bei Fehler."""
    i = raw.find("\r\n\r\n")
    if i == -1:
        return None
    try:
        return json.loads(raw[i + 4:])
    except Exception:
        return None


def _azure_text(raw):
    body = _azure_body(raw)
    return body.get("Text", "") if body else ""


# ---- Protokoll-I/O ----
# Jede Funktion sendet das Audio im 1x-Realtime-Takt (Sende-Coroutine) UND empfängt PARALLEL
# (Empfangs-Coroutine) via asyncio.gather. Parallel ist nötig, weil Interims WÄHREND des Sendens
# ankommen -> nur so wird ttfp dann gestempelt, wenn das Wort kommt (nicht erst nach dem Upload).
# Rückgabe je Funktion: dict mit
#   t_first   = erster Audio-Chunk gesendet        t_upload = letzter Chunk + End-Signal gesendet (~Audiodauer)
#   t_partial = erstes LIVE-Wort (Interim) -> ttfp (endpointing-frei, s. messprotokoll.md)
#   t_final   = STREAM-ENDE-Final -> ttft (sekundär; deepgram: letztes Segment-Final, damit cross-provider
#               vergleichbar mit Azure/Rev.ai. Unter Pacing ~am Audioende; KEIN Stille-Timer, s. messprotokoll.md)
#   transcript, ttfp_is_final/ttfp_text = Audit: WAS hat ttfp ausgelöst (Interim=False erwartet)
def _io_result(t_first, t_partial, t_upload, t_final, transcript, ttfp_is_final, ttfp_text):
    return {"t_first": t_first, "t_partial": t_partial, "t_upload": t_upload, "t_final": t_final,
            "transcript": transcript, "ttfp_is_final": ttfp_is_final, "ttfp_text": ttfp_text}


async def _paced_send(ws, pcm, wrap, end_msgs):
    """Sendet PCM im 1x-Realtime-Takt (Chunk -> sleep), dann die End-Signale.
    Gibt (t_first_chunk, t_upload_done) zurück. wrap() verpackt einen Chunk (z.B. Azure-Framing)."""
    t_first = None
    for i in range(0, len(pcm), CHUNK_SIZE):
        if t_first is None:
            t_first = time.perf_counter()
        await ws.send(wrap(pcm[i:i + CHUNK_SIZE]))
        await asyncio.sleep(CHUNK_SECONDS)
    for m in end_msgs:
        await ws.send(m)
    return t_first, time.perf_counter()


async def _io_deepgram(ws, pcm):
    async def recv():
        t_partial, t_final, p_final, p_text, segs = None, None, None, "", []
        async for raw in ws:
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "Results":
                alts = msg.get("channel", {}).get("alternatives", [{}])
                text = alts[0].get("transcript", "") if alts else ""
                if text and t_partial is None:                 # erstes Live-Wort (Interim ODER Final)
                    t_partial, p_final, p_text = time.perf_counter(), bool(msg.get("is_final")), text
                if msg.get("is_final") and text:
                    t_final = time.perf_counter()   # bei JEDEM Segment-Final neu -> letzter = Stream-Ende-Final
                    segs.append(text)               # (cross-provider vergleichbar mit Azure/Rev.ai-Final)
            elif mtype == "Metadata":          # nach allen Finals -> sauberer Abbruch (kein Hänger)
                break
        return t_partial, t_final, " ".join(segs), p_final, p_text

    send = _paced_send(ws, pcm, lambda c: c,
                       [json.dumps({"type": "Finalize"}), json.dumps({"type": "CloseStream"})])
    (t_first, t_upload), (t_partial, t_final, transcript, p_final, p_text) = await asyncio.gather(send, recv())
    return _io_result(t_first, t_partial, t_upload, t_final, transcript, p_final, p_text)


async def _io_revai(ws, pcm):
    connected = json.loads(await ws.recv())          # erst die "connected"-Message (Session-Init, ~1 RTT)
    if connected.get("type") != "connected":
        raise RuntimeError(f"rev.ai unerwartete erste Message: {connected.get('type')}")

    async def recv():
        t_partial, p_text = None, ""
        async for raw in ws:
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "partial" and t_partial is None:
                ptext = "".join(e.get("value", "") for e in msg.get("elements", []))
                if ptext.strip():
                    t_partial, p_text = time.perf_counter(), ptext
            elif mtype == "final":
                text = "".join(e.get("value", "") for e in msg.get("elements", []))
                return t_partial, time.perf_counter(), text, False, p_text
        return t_partial, None, "", False, p_text

    send = _paced_send(ws, pcm, lambda c: c, ["EOS"])
    (t_first, t_upload), (t_partial, t_final, transcript, p_final, p_text) = await asyncio.gather(send, recv())
    return _io_result(t_first, t_partial, t_upload, t_final, transcript, p_final, p_text)


async def _io_azure(ws, pcm):
    rid = uuid.uuid4().hex
    await ws.send(_azure_config_msg(rid))            # speech.config zuerst

    async def recv():
        t_partial, p_text = None, ""
        async for raw in ws:
            if isinstance(raw, bytes):
                continue
            if "speech.hypothesis" in raw and t_partial is None:   # Recognizing = erstes Live-Wort
                t_partial, p_text = time.perf_counter(), _azure_text(raw)
                continue
            if "speech.phrase" in raw:
                body = _azure_body(raw)
                if body and body.get("RecognitionStatus") == "Success":
                    return t_partial, time.perf_counter(), body.get("DisplayText", ""), False, p_text
        return t_partial, None, "", False, p_text

    send = _paced_send(ws, pcm, lambda c: _azure_audio_msg(rid, c), [_azure_audio_msg(rid, b"")])
    (t_first, t_upload), (t_partial, t_final, transcript, p_final, p_text) = await asyncio.gather(send, recv())
    return _io_result(t_first, t_partial, t_upload, t_final, transcript, p_final, p_text)


_IO = {"deepgram": _io_deepgram, "revai": _io_revai, "azure": _io_azure}


async def _run(name, ep, key, pcm):
    """Öffnet die WS, misst die Submetriken, dispatcht ans Protokoll. Gibt dict zurück."""
    out = {"ws_connect_ms": None, "session_init_ms": None, "audio_upload_ms": None,
           "ttfp_ms": None, "ttft_ms": None, "total_ms": None, "transcript": "",
           "ttfp_is_final": None, "ttfp_text": "", "resolved_ip": None, "error": None}

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
                              ping_interval=None,           # kein Keepalive-Ping auf der Mess-Verbindung
                              family=socket.AF_INET) as ws:  # IPv4 hart pinnen (Konsistenz mit LLM/TTS)
            t_ws_done = time.perf_counter()
            out["ws_connect_ms"] = round((t_ws_done - t0) * 1000, 2)
            out["resolved_ip"] = _peer_ip(ws)
            r = await asyncio.wait_for(_IO[name](ws, pcm), timeout=RESPONSE_TIMEOUT_S)
            t_done = time.perf_counter()                    # vor dem WS-Close gemessen
        out["total_ms"] = round((t_done - t0) * 1000, 2)
        if r["t_first"] is None or r["t_final"] is None:
            out["error"] = "kein finales Transkript"
            return out
        out["session_init_ms"] = round((r["t_first"] - t_ws_done) * 1000, 2)
        out["audio_upload_ms"] = round((r["t_upload"] - r["t_first"]) * 1000, 2)
        if r["t_partial"] is not None:                       # primär; None falls kein Interim kam
            out["ttfp_ms"] = round((r["t_partial"] - r["t_first"]) * 1000, 2)
            out["ttfp_is_final"] = r["ttfp_is_final"]        # Audit: war das erste Wort schon Final?
            out["ttfp_text"] = r["ttfp_text"]
        out["ttft_ms"] = round((r["t_final"] - r["t_first"]) * 1000, 2)
        out["transcript"] = r["transcript"]
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
        "ttfp_ms": None,            # PRIMÄR, endpointing-frei: t_first_partial - t_first_chunk
        "ttft_ms": None,            # SEKUNDÄR (enthält Endpointing): t_first_final - t_first_chunk
        "total_ms": None,           # connect-INKLUSIV (ohne WS-Close)
        "transcript": "",
        "ttfp_is_final": None,      # Audit: war das ttfp-auslösende Wort schon Final? (erwartet: False)
        "ttfp_text": "",            # Audit: Text des ttfp-auslösenden Live-Worts
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
    for k in ("ws_connect_ms", "session_init_ms", "audio_upload_ms", "ttfp_ms", "ttft_ms",
              "total_ms", "transcript", "ttfp_is_final", "ttfp_text", "resolved_ip", "error"):
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

    print(f"{'Provider':<10} {'ws_conn':>8} {'sess_in':>8} {'ttfp':>9} {'ttft':>9} {'total':>9} {'ok':>4}  Transkript / Fehler")
    for r in results:
        def f(x):
            return f"{x:.1f}" if x is not None else "-"
        ok = "ja" if r["success"] else "—"
        note = r["transcript"][:42] if r["success"] else (r["error"] or "")
        print(f"{r['provider']:<10} {f(r['ws_connect_ms']):>8} {f(r['session_init_ms']):>8} "
              f"{f(r['ttfp_ms']):>9} {f(r['ttft_ms']):>9} {f(r['total_ms']):>9} {ok:>4}  {note}")

    os.makedirs(DATA_DIR, exist_ok=True)
    out = DATA_DIR / "stt.jsonl"
    with open(out, "w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
