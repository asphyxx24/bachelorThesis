"""TLS-Handshake-Messung pro Endpoint.

Misst pro Endpoint N mal:
  - Handshake-Zeit (Wallclock von socket-connect bis ssl-Handshake fertig)
  - TLS-Version (TLSv1.2 / TLSv1.3)
  - Cipher Suite
  - ALPN-Selektion (HTTP/1.1, h2, etc.)
  - Server-Cert-Subject (Hauptname)

Schreibt JSONL mit einer Zeile pro Versuch nach data/layer1_extra/tls_raw.jsonl
und aggregiert anschliessend in tls.csv (pro endpoint × run).

Aufruf: python measure_tls.py [--n 5]
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "layer1_extra"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW = OUT_DIR / "tls_raw.jsonl"
CSV = OUT_DIR / "tls.csv"

ENDPOINTS = [
    "api.deepgram.com",
    "api.rev.ai",
    "italynorth.stt.speech.microsoft.com",
    "api.openai.com",
    "api.groq.com",
    "api.mistral.ai",
    "italynorth.tts.speech.microsoft.com",
]


def measure_one(host: str, port: int = 443, timeout: float = 5.0) -> dict:
    """Ein TLS-Handshake. Misst Connect+Handshake getrennt."""
    ctx = ssl.create_default_context()
    # ALPN anbieten, damit wir sehen was Server zurueckwaehlt
    ctx.set_alpn_protocols(["h2", "http/1.1"])

    out: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "endpoint": host,
    }

    t0 = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        t_tcp_done = time.perf_counter()
        ssock = ctx.wrap_socket(sock, server_hostname=host)
        t_tls_done = time.perf_counter()

        out["tcp_connect_ms"] = round((t_tcp_done - t0) * 1000, 3)
        out["tls_handshake_ms"] = round((t_tls_done - t_tcp_done) * 1000, 3)
        out["tls_version"] = ssock.version()
        out["cipher"] = ssock.cipher()[0] if ssock.cipher() else None
        out["alpn"] = ssock.selected_alpn_protocol()
        cert = ssock.getpeercert()
        subj = cert.get("subject", ())
        out["cert_cn"] = next(
            (v for rdn in subj for k, v in rdn if k == "commonName"), None
        )
        ssock.close()
        out["ok"] = True
    except Exception as e:
        out["ok"] = False
        out["error"] = f"{type(e).__name__}: {e}"

    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5, help="Wiederholungen pro Endpoint")
    args = parser.parse_args()

    rows = []
    with open(RAW, "w", encoding="utf-8") as fh:
        for host in ENDPOINTS:
            print(f"  {host} ...", flush=True)
            for run in range(args.n):
                r = measure_one(host)
                r["run"] = run
                fh.write(json.dumps(r) + "\n")
                rows.append(r)
                time.sleep(0.2)  # kleine Pause zwischen Wiederholungen

    # CSV aggregieren (eine Zeile pro Versuch)
    import csv

    fields = [
        "ts", "endpoint", "run", "ok", "tcp_connect_ms", "tls_handshake_ms",
        "tls_version", "cipher", "alpn", "cert_cn", "error",
    ]
    with open(CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})

    print(f"\nFertig. {len(rows)} Zeilen -> {CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
