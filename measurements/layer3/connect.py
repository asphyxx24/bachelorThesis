"""
Layer 3 — Connect-Submetriken (atomar: dns / tcp / tls).

Misst den Verbindungsaufbau in EINZELNEN Phasen über einen WEGWERF-Socket.
Für LLM/TTS ist das die "Referenzmessung": das eigentliche ttft/ttfa wird
connect-INKLUSIV über die echte Anfrage gemessen (s. messprotokoll.md, Layer 3).

Ausführen (zum Testen, braucht keine Keys):
  .venv/bin/python measurements/layer3/connect.py
"""

import socket
import ssl
import time


def connect_submetrics(host, port=443, timeout=10.0):
    """Misst dns/tcp/tls atomar. Gibt dict zurück; Werte None + error bei Fehler."""
    rec = {
        "resolved_ip": None,
        "dns_ms": None,
        "tcp_handshake_ms": None,
        "tls_handshake_ms": None,
        "error": None,
    }

    try:
        t0 = time.perf_counter()
        ip = socket.gethostbyname(host)          # DNS getrennt (oft gecacht)
        t1 = time.perf_counter()
    except OSError as e:
        rec["error"] = f"dns: {e}"
        return rec
    rec["resolved_ip"] = ip
    rec["dns_ms"] = round((t1 - t0) * 1000, 2)

    ctx = ssl.create_default_context()
    ctx.set_alpn_protocols(["h2", "http/1.1"])
    try:
        t2 = time.perf_counter()
        sock = socket.create_connection((ip, port), timeout=timeout)   # SYN -> SYN-ACK = 1 RTT
        t3 = time.perf_counter()
        ssock = ctx.wrap_socket(sock, server_hostname=host)            # TLS-Handshake
        t4 = time.perf_counter()
        ssock.close()
    except OSError as e:
        rec["error"] = f"connect/tls: {e}"
        return rec
    rec["tcp_handshake_ms"] = round((t3 - t2) * 1000, 2)
    rec["tls_handshake_ms"] = round((t4 - t3) * 1000, 2)
    return rec


def main():
    # Test über alle eindeutigen Hosts aus der Config (keine Keys nötig).
    from config import LLM, TTS, STT
    hosts = sorted({ep["host"] for group in (LLM, TTS, STT) for ep in group.values()})

    print(f"{'Host':<40} {'dns':>7} {'tcp':>7} {'tls':>7}  IP / Fehler")
    for host in hosts:
        s = connect_submetrics(host)
        dns = f"{s['dns_ms']:.2f}" if s["dns_ms"] is not None else "-"
        tcp = f"{s['tcp_handshake_ms']:.2f}" if s["tcp_handshake_ms"] is not None else "-"
        tls = f"{s['tls_handshake_ms']:.2f}" if s["tls_handshake_ms"] is not None else "-"
        print(f"{host:<40} {dns:>7} {tcp:>7} {tls:>7}  {s['resolved_ip'] or s['error']}")


if __name__ == "__main__":
    main()
