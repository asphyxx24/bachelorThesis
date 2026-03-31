"""TLS-Handshake und Protokoll-Analyse via curl.

Zerlegt den Verbindungsaufbau in DNS, TCP, TLS-Handshake und TTFB.
Erkennt HTTP-Version (1.1, 2, 3).
"""

import subprocess


def measure(url: str) -> dict:
    """curl-Timing fuer DNS, TCP, TLS-Handshake, TTFB.

    Returns:
        {"dns_ms": float, "tcp_ms": float, "tls_handshake_ms": float,
         "ttfb_ms": float, "total_ms": float, "http_version": str}
    """
    fmt = (
        "dns_ms:%{time_namelookup}\n"
        "tcp_connect_ms:%{time_connect}\n"
        "tls_done_ms:%{time_appconnect}\n"
        "ttfb_ms:%{time_starttransfer}\n"
        "total_ms:%{time_total}\n"
        "http_version:%{http_version}\n"
    )
    try:
        out = subprocess.check_output(
            ["curl", "-s", "-o", "/dev/null", "-w", fmt, "--connect-timeout", "10", url],
            timeout=15, text=True, stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)[:80]}

    result = {}
    for line in out.strip().splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if key == "http_version":
            result[key] = val
        else:
            try:
                result[key] = round(float(val) * 1000, 1)
            except ValueError:
                pass

    # Abgeleitete Werte: reine TCP- und TLS-Zeit
    if "tcp_connect_ms" in result and "dns_ms" in result:
        result["tcp_ms"] = round(result["tcp_connect_ms"] - result["dns_ms"], 1)
    if "tls_done_ms" in result and "tcp_connect_ms" in result:
        result["tls_handshake_ms"] = round(result["tls_done_ms"] - result["tcp_connect_ms"], 1)

    return result
