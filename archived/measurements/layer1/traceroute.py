"""Traceroute mit AS-Nummer-Aufloesung.

Fuehrt traceroute durch und loest fuer jede Hop-IP die AS-Nummer auf.
AS-Pfade sind zentral fuer die Netzwerk-Charakterisierung (Schicht 1).
"""

import re
import socket
import subprocess


def measure(host: str) -> dict:
    """Traceroute mit ASN-Aufloesung pro Hop.

    Returns:
        {"hops": [{"hop": 1, "ip": "...", "rtt_ms": float, "asn": int|null}],
         "total_hops": int, "destination_reached": bool,
         "as_path": [int, ...]}
    """
    try:
        out = subprocess.check_output(
            ["traceroute", "-n", "-w", "2", "-q", "1", "-m", "25", host],
            timeout=90, text=True, stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "hops": [], "as_path": []}
    except Exception as e:
        return {"error": str(e)[:80], "hops": [], "as_path": []}

    hops = []
    for line in out.strip().splitlines()[1:]:
        parts = line.split()
        if not parts:
            continue
        hop_num = int(parts[0]) if parts[0].isdigit() else None
        if hop_num is None:
            continue

        if parts[1] == "*":
            hops.append({"hop": hop_num, "ip": None, "rtt_ms": None, "asn": None})
            continue

        ip = parts[1]
        rtt_match = re.search(r"([\d.]+)\s+ms", line)
        rtt_ms = float(rtt_match.group(1)) if rtt_match else None
        asn = _lookup_asn(ip)
        hops.append({"hop": hop_num, "ip": ip, "rtt_ms": rtt_ms, "asn": asn})

    # AS-Pfad extrahieren (unique, geordnet, ohne None)
    as_path = []
    for h in hops:
        if h["asn"] and (not as_path or as_path[-1] != h["asn"]):
            as_path.append(h["asn"])

    # Ziel erreicht?
    destination_reached = _check_destination(hops, host)

    return {
        "hops": hops,
        "total_hops": len(hops),
        "destination_reached": destination_reached,
        "as_path": as_path,
    }


def _lookup_asn(ip: str) -> int | None:
    """ASN-Lookup via Team Cymru DNS (Standardmethode in der Internet-Messung).

    Fragt <reversed-ip>.origin.asn.cymru.com ab.
    Beispiel: 1.2.3.4 -> 4.3.2.1.origin.asn.cymru.com -> TXT "12345 | ..."
    """
    if not ip or ip.startswith("10.") or ip.startswith("172.") or ip.startswith("192.168."):
        return None

    try:
        reversed_ip = ".".join(reversed(ip.split(".")))
        query = f"{reversed_ip}.origin.asn.cymru.com"
        out = subprocess.check_output(
            ["dig", "+short", query, "TXT", "+time=2", "+tries=1"],
            timeout=5, text=True, stderr=subprocess.DEVNULL,
        )
        # Format: "12345 | 1.0.0.0/8 | US | arin | 2010-01-01"
        for line in out.strip().splitlines():
            line = line.strip('"')
            parts = line.split("|")
            if parts:
                asn_str = parts[0].strip()
                if asn_str.isdigit():
                    return int(asn_str)
    except Exception:
        pass
    return None


def _check_destination(hops: list[dict], host: str) -> bool:
    """Prueft ob der letzte Hop dem Ziel-Host entspricht."""
    try:
        target_ips = socket.gethostbyname_ex(host)[2]
        return any(h["ip"] in target_ips for h in hops if h["ip"])
    except Exception:
        return False
