"""
Layer 2 — Handshake-Eichung (Capture-Teil).

Zweck (C2): belegt, dass der App-Timer `tcp_handshake_ms` aus Layer 3 (connect.py, gemessen um
`socket.create_connection`) die ECHTE Wire-Latenz misst. Dazu wird WÄHREND dieses Skripts (extern)
`tcpdump` mitgeschnitten; `analyze.py` vergleicht danach Wire-SYN→SYN-ACK gegen den hier gemessenen
App-`tcp_handshake_ms` — gepaart über den Quell-Port.

Wir messen gegen einen HOST-terminierten Provider (Azure/Deepgram), NICHT gegen Cloudflare-Edge:
dort wäre der Vergleich tautologisch (connect ≈ N×ping am selben Knoten).

Jeder der N Calls ist ein Cold-Start (frischer Socket, danach geschlossen) — identische Technik wie
connect.py. Wir fixieren EINE Ziel-IP (Round-Robin-Hosts: --ip übergeben), damit Capture + Filter sauber
auf denselben Knoten zeigen.

Ausführen (auf der EC2, parallel zu tcpdump — s. mess_kommandos.md):
  .venv/bin/python measurements/layer2/capture.py --host api.deepgram.com --ip 216.200.21.204 \
      --n 30 --out data/layer2/applog_deepgram.jsonl
"""

import argparse
import json
import socket
import ssl
import time
from datetime import datetime, timezone


def one_connect(ip, host, port=443, timeout=10.0):
    """Ein Cold-Start-Connect wie connect.py. Gibt (src_port, tcp_handshake_ms) zurück."""
    ctx = ssl.create_default_context()
    ctx.set_alpn_protocols(["h2", "http/1.1"])
    t0 = time.perf_counter()
    sock = socket.create_connection((ip, port), timeout=timeout)   # SYN -> SYN-ACK = 1 RTT
    t1 = time.perf_counter()
    src_port = sock.getsockname()[1]                               # zum Paaren mit der PCAP
    try:
        ssock = ctx.wrap_socket(sock, server_hostname=host)        # TLS, damit der Handshake realistisch ist
        ssock.close()
    except OSError:
        sock.close()
    return src_port, round((t1 - t0) * 1000, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--ip", default=None, help="feste Ziel-IP (bei Round-Robin-Hosts nötig)")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--delay", type=float, default=0.5, help="Pause zwischen Cold-Starts (s)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ip = a.ip or socket.gethostbyname(a.host)
    rows = []
    for i in range(a.n):
        try:
            sp, ms = one_connect(ip, a.host)
            rows.append({"idx": i, "src_port": sp, "ip": ip, "host": a.host,
                         "app_tcp_handshake_ms": ms,
                         "ts": datetime.now(timezone.utc).isoformat()})
        except OSError as e:
            rows.append({"idx": i, "ip": ip, "host": a.host, "error": str(e)})
        time.sleep(a.delay)

    with open(a.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    ok = [r for r in rows if "app_tcp_handshake_ms" in r]
    med = sorted(r["app_tcp_handshake_ms"] for r in ok)[len(ok) // 2] if ok else None
    print(f"{a.host} ({ip}): {len(ok)}/{a.n} ok, App-tcp_handshake Median = {med} ms -> {a.out}")


if __name__ == "__main__":
    main()
