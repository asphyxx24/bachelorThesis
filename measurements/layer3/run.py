"""
Layer 3 — Runner: ein Slot, interleaved Round-Robin über alle 9 Endpunkte.

Pro Runde EIN Cold-Start-Call je Endpunkt; n Runden. Startreihenfolge je Runde rotiert.
Jeder Call baut eine frische Verbindung auf (Cold-Start). Ein Fehlschlag blockiert die Runde
nicht — die Caller geben IMMER einen Record zurück (Verfügbarkeit, A8).

Robust für unbeaufsichtigten 7-Tage-cron-Betrieb:
  - flock-Single-Instance-Lock: nie zwei Slots parallel (kein Cold-Start-Confound bei Überlauf)
  - Slot-Deadline (--max-min): bricht VOR einer Runde sauber ab, statt in den nächsten cron-Slot zu laufen
  - harter Per-Call-Timeout: kein einzelner hängender Call (z.B. DNS) friert den Slot ein
  - SIGTERM: stoppt sauber zwischen Runden
  - run_meta (Start) + run_end (Ende) inkl. CPU-Steal Start/Ende (A6), git_commit+dirty (A5)

Schreibt pro Slot eine JSONL: 1. Zeile run_meta · je Call ein Record · letzte Zeile run_end.

Ausführen (vom Repo-Wurzelverzeichnis):
  .venv/bin/python measurements/layer3/run.py --n 100 --tag 09h
  .venv/bin/python measurements/layer3/run.py --n 2 --tag pilot --dry-run
cron (unbuffered + Lock + Log):
  flock -n /tmp/layer3.lock .venv/bin/python -u measurements/layer3/run.py --n 100 --tag 09h >> data/layer3/cron.log 2>&1
"""

import argparse
import fcntl
import hashlib
import json
import os
import platform
import ssl
import subprocess
import signal
import threading
import time
import urllib.request
from datetime import datetime, timezone

from config import LLM, TTS, STT, STT_WAV, ROOT, DATA_DIR
from llm import call_llm
from tts import call_tts
from stt import call_stt, load_pcm

MEASUREMENT_DELAY_S = 1.5     # Pause zwischen Einzelmessungen (Rate-Limit-Schutz)
CALL_HARD_TIMEOUT_S = 75      # harte Obergrenze je Call (> Summe der Einzel-Timeouts ~50-60s)
DEFAULT_MAX_MIN = 150         # Slot-Deadline: passt in den 3-h-cron-Takt mit Puffer

_stop = {"flag": False}       # wird von SIGTERM gesetzt -> sauberer Stopp zwischen Runden


def endpoints(api):
    groups = {"llm": LLM, "tts": TTS, "stt": STT}
    chosen = groups if api == "all" else {api: groups[api]}
    return [(cat, name, ep) for cat, group in chosen.items() for name, ep in group.items()]


def measure(cat, name, ep, pcm):
    """Dispatch an den richtigen Caller (synchron)."""
    if cat == "llm":
        return call_llm(name, ep)
    if cat == "tts":
        return call_tts(name, ep)
    return call_stt(name, ep, pcm)


def measure_bounded(cat, name, ep, pcm):
    """measure() mit hartem Wall-Clock-Timeout (Thread). Kein Call kann den Slot einfrieren."""
    box = {}
    th = threading.Thread(target=lambda: box.update(rec=measure(cat, name, ep, pcm)), daemon=True)
    th.start()
    th.join(CALL_HARD_TIMEOUT_S)
    if th.is_alive() or "rec" not in box:        # Call hängt -> aufgeben (daemon-Thread stirbt mit Prozess)
        return {"provider": name, "category": cat, "success": False,
                "error": "call_timeout", "ts": datetime.now(timezone.utc).isoformat()}
    return box["rec"]


def _ec2_meta():
    """Best-effort EC2-Instanz-Metadaten (IMDSv2). Leeres dict + Fehlergrund, wenn nicht auf EC2."""
    try:
        req = urllib.request.Request("http://169.254.169.254/latest/api/token", method="PUT",
                                     headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"})
        token = urllib.request.urlopen(req, timeout=1).read().decode()

        def g(path):
            r = urllib.request.Request(f"http://169.254.169.254/latest/meta-data/{path}",
                                       headers={"X-aws-ec2-metadata-token": token})
            return urllib.request.urlopen(r, timeout=1).read().decode()

        az = g("placement/availability-zone")
        return {"instance_id": g("instance-id"), "instance_type": g("instance-type"),
                "ami_id": g("ami-id"), "az": az, "region": az[:-1]}
    except Exception as e:
        return {"ec2_meta_error": repr(e)[:120]}


def _cpu_steal():
    """Kumulative CPU-Steal-Ticks aus /proc/stat (A6). None auf nicht-Linux."""
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()
        return int(parts[8]) if len(parts) > 8 else None      # Feld 8 = steal
    except Exception:
        return None


def _cmd(args_list):
    """Best-effort-Shell-Kommando (für git/chrony/iface). Gibt stdout.strip() oder None."""
    try:
        r = subprocess.run(args_list, capture_output=True, text=True, timeout=5, cwd=ROOT)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _requirements_sha():
    try:
        return hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest()[:12]
    except Exception:
        return None


def run_meta(tag, n, api):
    meta = {
        "record_type": "run_meta", "tag": tag, "n": n, "api": api,
        "delay_s": MEASUREMENT_DELAY_S, "call_timeout_s": CALL_HARD_TIMEOUT_S,
        "python": platform.python_version(), "openssl": ssl.OPENSSL_VERSION,
        "platform": platform.platform(), "kernel": platform.release(),
        "git_commit": _cmd(["git", "rev-parse", "--short", "HEAD"]),
        "git_dirty": bool(_cmd(["git", "status", "--porcelain"])),
        "requirements_sha": _requirements_sha(),
        "chrony": _cmd(["chronyc", "-n", "tracking"]),
        "iface": next((i for i in (os.listdir("/sys/class/net") if os.path.isdir("/sys/class/net") else [])
                       if i != "lo"), None),
        "cpu_steal_start": _cpu_steal(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    meta.update(_ec2_meta())
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100, help="Messungen pro Endpunkt (Runden)")
    ap.add_argument("--tag", required=True, help="Slot-Label (z.B. 09h, pilot)")
    ap.add_argument("--api", default="all", choices=["all", "stt", "llm", "tts"])
    ap.add_argument("--max-min", type=int, default=DEFAULT_MAX_MIN, help="Slot-Deadline in Minuten")
    ap.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur drucken")
    args = ap.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    # Single-Instance-Lock: ein laufender Slot blockiert einen zweiten Start (Anti-Überlapp).
    lock_fh = open(DATA_DIR / "run.lock", "w")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Ein Slot läuft bereits — übersprungen.", flush=True)
        return

    signal.signal(signal.SIGTERM, lambda *_: _stop.__setitem__("flag", True))

    eps = endpoints(args.api)
    pcm = load_pcm(ROOT / STT_WAV) if any(c == "stt" for c, _, _ in eps) else None

    out_dir = DATA_DIR / "campaign"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{args.tag}_{stamp}.jsonl"

    meta = run_meta(args.tag, args.n, args.api)
    print(f"Slot '{args.tag}': n={args.n} × {len(eps)} = {args.n * len(eps)} Calls | "
          f"git={meta['git_commit']}{'(dirty)' if meta['git_dirty'] else ''} "
          f"instanz={meta.get('instance_id', 'lokal')} dry-run={args.dry_run}", flush=True)

    fh = None
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        fh = open(out_path, "w")
        fh.write(json.dumps(meta) + "\n")

    t_start = time.monotonic()
    deadline = t_start + args.max_min * 60
    ok = fail = done_rounds = 0
    aborted = None
    try:
        for rnd in range(args.n):
            if _stop["flag"]:
                aborted = "sigterm"
                break
            if time.monotonic() > deadline:
                aborted = "deadline"
                break
            shift = rnd % len(eps)                       # Startreihenfolge je Runde rotieren
            for cat, name, ep in eps[shift:] + eps[:shift]:
                rec = measure_bounded(cat, name, ep, pcm)
                rec["tag"], rec["round"], rec["endpoint"] = args.tag, rnd, f"{cat}_{name}"
                ok += 1 if rec.get("success") else 0
                fail += 0 if rec.get("success") else 1
                if fh:
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()                           # Absturz verliert höchstens den laufenden Call
                time.sleep(MEASUREMENT_DELAY_S)
            done_rounds = rnd + 1
            if done_rounds % 10 == 0 or done_rounds == args.n:
                print(f"  Runde {done_rounds}/{args.n} — ok={ok} fail={fail}", flush=True)
    finally:
        end = {"record_type": "run_end", "rounds_done": done_rounds, "n": args.n,
               "n_ok": ok, "n_fail": fail, "aborted": aborted,
               "duration_s": round(time.monotonic() - t_start, 1),
               "cpu_steal_end": _cpu_steal(), "ts_end": datetime.now(timezone.utc).isoformat()}
        if fh:
            fh.write(json.dumps(end) + "\n")
            fh.close()
        note = f"abgebrochen ({aborted})" if aborted else "vollständig"
        print(f"\n{note}: {done_rounds}/{args.n} Runden, {ok} ok, {fail} Fehlschläge"
              + (f"  -> {out_path}" if fh else "  (dry-run)"), flush=True)


if __name__ == "__main__":
    main()
