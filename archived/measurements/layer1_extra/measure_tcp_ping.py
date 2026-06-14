"""TCP-SYN-Ping pro Endpoint auf Port 443.

Funktioniert auch wenn ICMP geblockt ist (Rev.ai). Misst die Zeit von
`socket.connect()` bis Erfolg = TCP-Handshake-RTT (1 RTT auf Layer 4).

Aufruf: python measure_tcp_ping.py [--n 10]
"""

from __future__ import annotations

import argparse
import csv
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "layer1_extra"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW = OUT_DIR / "ping_tcp_raw.jsonl"
CSV = OUT_DIR / "ping_tcp.csv"

ENDPOINTS = [
    "api.deepgram.com",
    "api.rev.ai",
    "italynorth.stt.speech.microsoft.com",
    "api.openai.com",
    "api.groq.com",
    "api.mistral.ai",
    "italynorth.tts.speech.microsoft.com",
]


def tcp_ping_once(host: str, port: int = 443, timeout: float = 5.0) -> dict:
    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "endpoint": host,
    }
    t0 = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        t1 = time.perf_counter()
        out["rtt_ms"] = round((t1 - t0) * 1000, 3)
        out["ok"] = True
        sock.close()
    except Exception as e:
        out["ok"] = False
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=10, help="Wiederholungen pro Endpoint")
    args = p.parse_args()

    summary = []
    with open(RAW, "w", encoding="utf-8") as fh:
        for host in ENDPOINTS:
            print(f"  {host} ...", flush=True)
            rtts = []
            for run in range(args.n):
                r = tcp_ping_once(host)
                r["run"] = run
                fh.write(json.dumps(r) + "\n")
                if r["ok"]:
                    rtts.append(r["rtt_ms"])
                time.sleep(0.2)

            if rtts:
                summary.append({
                    "endpoint": host,
                    "n": args.n,
                    "n_ok": len(rtts),
                    "min_ms": round(min(rtts), 3),
                    "median_ms": round(median(rtts), 3),
                    "mean_ms": round(mean(rtts), 3),
                    "max_ms": round(max(rtts), 3),
                    "stdev_ms": round(stdev(rtts), 3) if len(rtts) >= 2 else 0.0,
                })
            else:
                summary.append({
                    "endpoint": host, "n": args.n, "n_ok": 0,
                    "min_ms": None, "median_ms": None, "mean_ms": None,
                    "max_ms": None, "stdev_ms": None,
                })

    with open(CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)

    print(f"\nFertig. {len(summary)} Endpoints -> {CSV.relative_to(ROOT)}")
    print(f"Roh-Daten ({args.n} Pings pro Endpoint) -> {RAW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
