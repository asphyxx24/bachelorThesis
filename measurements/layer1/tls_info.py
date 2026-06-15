"""
Layer 1 — TLS-Info + Handshake-Timing.

Was es misst:
  Pro Host: ausgehandelte TLS-Version, Cipher-Suite (+ Bit-Stärke), ALPN-Protokoll,
  Zertifikat-Common-Name und SAN — plus die Zeiten für TCP-Connect und TLS-Handshake
  getrennt. Die tcp_ms/tls_ms stammen aus EINEM Connect (kein min-über-N wie
  tcp_ping.py) — die belastbare RTT liefert tcp_ping.py.

WICHTIG (A1 — TLS-Version auf macOS unzuverlässig):
  macOS-Python ist gegen LibreSSL gelinkt und cappt auf TLS 1.2 -> es meldet ALLE
  Hosts fälschlich als 1.2. Das Skript LÄUFT trotzdem (Timing/Cipher/ALPN stimmen),
  warnt aber, wenn es auf LibreSSL läuft. Die TLS-VERSION ist nur auf der EC2
  (echtes OpenSSL 3.x) belastbar. Wir cappen maximum_version NICHT und prüfen die
  Version nach dem Handshake als weichen Guard.

Ausführen (vom Repo-Wurzelverzeichnis):
  .venv/bin/python measurements/layer1/tls_info.py
"""

import ssl
import socket
import time
import json
import os
from datetime import datetime, timezone

from hosts import HOSTS

PORT = 443
TIMEOUT = 10.0
IS_LIBRESSL = "LibreSSL" in ssl.OPENSSL_VERSION


def cert_common_name(cert):
    """Zieht den Common Name (CN) aus einem geparsten Zertifikat. None, falls keiner da."""
    for rdn in (cert or {}).get("subject", ()):
        for key, value in rdn:
            if key == "commonName":
                return value
    return None


def tls_info(host):
    """Baut eine TLS-Verbindung auf und liest die TLS-Details. Gibt IMMER einen Record zurück."""
    rec = {
        "host": host,
        "resolved_ip": None,
        "tcp_ms": None,            # Zeit für den TCP-Connect
        "tls_ms": None,            # Zeit für den TLS-Handshake (danach)
        "tls_version": None,
        "cipher": None,
        "cipher_bits": None,
        "alpn": None,
        "cert_cn": None,
        "cert_san": None,
        "openssl": ssl.OPENSSL_VERSION,   # damit LibreSSL-Zeilen erkennbar sind (A1)
        "warning": None,
        "error": None,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    try:
        rec["resolved_ip"] = socket.gethostbyname(host)
    except OSError as e:
        rec["error"] = f"dns: {e}"
        return rec

    ctx = ssl.create_default_context()
    ctx.set_alpn_protocols(["h2", "http/1.1"])
    # maximum_version bewusst NICHT cappen -> TLS 1.3 bleibt möglich (A1)

    # TCP-Connect (zur IP, NICHT zum Hostnamen -> DNS-Zeit landet nicht im Timing)
    try:
        t0 = time.perf_counter()
        sock = socket.create_connection((rec["resolved_ip"], PORT), timeout=TIMEOUT)
        t1 = time.perf_counter()
    except OSError as e:
        rec["error"] = f"tcp: {e}"
        return rec
    rec["tcp_ms"] = round((t1 - t0) * 1000, 2)   # bleibt erhalten, auch wenn TLS scheitert

    # TLS-Handshake
    try:
        ssock = ctx.wrap_socket(sock, server_hostname=host)
        t2 = time.perf_counter()
    except OSError as e:
        sock.close()
        rec["error"] = f"tls: {e}"
        return rec

    rec["tls_ms"] = round((t2 - t1) * 1000, 2)
    rec["tls_version"] = ssock.version()
    cipher = ssock.cipher()                 # (name, protocol, secret_bits)
    rec["cipher"] = cipher[0]
    rec["cipher_bits"] = cipher[2]
    rec["alpn"] = ssock.selected_alpn_protocol()
    cert = ssock.getpeercert()
    rec["cert_cn"] = cert_common_name(cert)
    rec["cert_san"] = [v for (typ, v) in (cert or {}).get("subjectAltName", ()) if typ == "DNS"]
    # Weicher A1-Guard: auf echtem OpenSSL sollte die Version nicht < 1.2 sein
    if not IS_LIBRESSL and rec["tls_version"] in ("TLSv1", "TLSv1.1", None):
        rec["warning"] = "tls_version unerwartet niedrig trotz OpenSSL — möglicher Lib-Cap (A1)"
    ssock.close()
    return rec


def main():
    if IS_LIBRESSL:
        print(f"⚠️  LibreSSL erkannt ({ssl.OPENSSL_VERSION}) -> tls_version ist hier UNZUVERLÄSSIG (A1). "
              f"Verlässlich nur auf der EC2.\n")

    results = [tls_info(h) for h in HOSTS]

    print(f"{'Host':<40} {'TLS':<8} {'ALPN':<9} {'tcp':>7} {'tls':>7}")
    for r in results:
        tcp = f"{r['tcp_ms']:.2f}" if r["tcp_ms"] is not None else "-"
        tls = f"{r['tls_ms']:.2f}" if r["tls_ms"] is not None else "-"
        print(f"{r['host']:<40} {str(r['tls_version'] or '-'):<8} {str(r['alpn'] or '-'):<9} {tcp:>7} {tls:>7}")

    os.makedirs("data/layer1", exist_ok=True)
    out = "data/layer1/tls_info.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
