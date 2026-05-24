"""Helper fuer NB 02: PCAP -> IPs + ASN-Lookup + TLS-Details.

tshark wird via subprocess aufgerufen (Windows-Pfad fest verdrahtet, fallback auf PATH).

ASN-Lookup via Team-Cymru-DNS-Service:
  dig +short AS<reversed-ip>.origin.asn.cymru.com TXT
liefert "asn | prefix | country | registry | date".
Plus zweite Query gegen AS<asn>.asn.cymru.com fuer den Organisationsnamen.

Vorteile gegenueber ipinfo: kein API-Key, kein Rate-Limit, lange etabliert.
Nachteil: braucht funktionierende DNS-Resolution (haben wir hier sowieso).
"""

from __future__ import annotations

import functools
import json
import shutil
import subprocess
import socket
from pathlib import Path

# Wireshark-Pfad auf Windows; fallback auf PATH
TSHARK = (
    r"C:\Program Files\Wireshark\tshark.exe"
    if Path(r"C:\Program Files\Wireshark\tshark.exe").exists()
    else (shutil.which("tshark") or "tshark")
)


def tshark_run(pcap: Path, fields: list[str], extra_args: list[str] | None = None) -> list[list[str]]:
    """Ruft tshark mit -T fields fuer die gegebenen Felder, gibt Rows zurueck."""
    cmd = [TSHARK, "-r", str(pcap), "-T", "fields", "-E", "separator=|", "-E", "header=n"]
    for f in fields:
        cmd += ["-e", f]
    if extra_args:
        cmd += extra_args
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=60)
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rows.append(line.split("|"))
    return rows


def is_private_ip(ip: str) -> bool:
    """RFC1918 + Loopback. EC2-VPC nutzt 172.31.x.x (AWS-Default-VPC)."""
    if not ip:
        return False
    if ip.startswith(("10.", "127.", "192.168.")):
        return True
    if ip.startswith("172."):
        try:
            second = int(ip.split(".")[1])
            return 16 <= second <= 31
        except (IndexError, ValueError):
            return False
    return False


def extract_ip_summary(pcap: Path) -> list[dict]:
    """Pro Destination-IP: Paketzahl, Bytes, dst-Ports.

    Geht nur ueber Pakete mit IP-Layer; ignoriert ARP etc.
    Filtert lokale (RFC1918) IPs als "uns selbst" heraus.
    """
    rows = tshark_run(pcap, ["ip.src", "ip.dst", "frame.len", "tcp.dstport", "udp.dstport"])

    # EC2-eigene IPs: alle privaten + die haeufigste private (falls mehrere)
    local_ips: set[str] = set()
    src_counts: dict[str, int] = {}
    for r in rows:
        if len(r) >= 1 and r[0]:
            src_counts[r[0]] = src_counts.get(r[0], 0) + 1
            if is_private_ip(r[0]):
                local_ips.add(r[0])
    # Falls keine private IP gesehen wurde, fallback auf haeufigste IP als lokal
    if not local_ips and src_counts:
        local_ips.add(max(src_counts, key=src_counts.get))
    local_ip = next(iter(local_ips))  # fuer das untere len-Check

    # Aggregat pro (peer_ip, dst_port). peer = Gegenseite (nicht local_ip).
    agg: dict[tuple, dict] = {}
    for r in rows:
        if len(r) < 5:
            continue
        src, dst, length, tcp_port, udp_port = r[0], r[1], r[2], r[3], r[4]
        if not src or not dst:
            continue
        if src in local_ips:
            peer = dst
            port = tcp_port or udp_port
        elif dst in local_ips:
            peer = src
            port = tcp_port or udp_port  # bei eingehenden Paketen ist es src-port der Quelle
        else:
            continue  # kein Bezug zu uns
        if peer in local_ips:
            continue  # interner Verkehr (sollte selten sein)

        key = (peer, port)
        e = agg.setdefault(key, {"peer_ip": peer, "port": port, "packets": 0, "bytes": 0})
        e["packets"] += 1
        try:
            e["bytes"] += int(length)
        except ValueError:
            pass

    return sorted(agg.values(), key=lambda d: -d["packets"])


def extract_tls_handshake(pcap: Path) -> dict:
    """Extrahiert TLS-Version und Cipher aus dem ersten TLS-Handshake im PCAP.

    Funktioniert nur bei TLS-Handshakes, die tshark dissecten konnte (Pakete
    nicht abgeschnitten, Standard-Port etc.).
    """
    # tshark 4.6 Field-Namen ermittelt durch Trial:
    # tls.handshake.extensions.supported_version (Dot vor supported, kein Plural)
    # tls.handshake.extensions_alpn_str (Underscore)
    rows = tshark_run(pcap, [
        "tls.handshake.type",
        "tls.handshake.version",
        "tls.record.version",
        "tls.handshake.extensions.supported_version",
        "tls.handshake.ciphersuite",
        "tls.handshake.extensions_alpn_str",
    ], extra_args=["-Y", "tls.handshake"])
    out = {"client_hello_version": None, "server_hello_version": None,
           "negotiated_version": None, "cipher": None, "alpn": None}

    # TLS-Versions-Codes -> Klartext
    VERS = {"0x0303": "TLS1.2", "0x0304": "TLS1.3", "0x0302": "TLS1.1", "0x0301": "TLS1.0"}
    # Cipher-Codes -> Klartext (nur die haeufigsten)
    CIPH = {
        "0x1301": "TLS_AES_128_GCM_SHA256",
        "0x1302": "TLS_AES_256_GCM_SHA384",
        "0x1303": "TLS_CHACHA20_POLY1305_SHA256",
        "0xc02f": "ECDHE-RSA-AES128-GCM-SHA256",
        "0xc030": "ECDHE-RSA-AES256-GCM-SHA384",
        "0xc02b": "ECDHE-ECDSA-AES128-GCM-SHA256",
        "0xc02c": "ECDHE-ECDSA-AES256-GCM-SHA384",
    }
    for r in rows:
        if len(r) < 6:
            continue
        ht, hsv, rv, supv, cipher, alpn = r
        if ht == "1":  # ClientHello
            out["client_hello_version"] = VERS.get(hsv or rv, hsv or rv)
            if alpn:
                out["alpn"] = alpn.split(",")[0]
        elif ht == "2":  # ServerHello (nur in TLS 1.2 sichtbar, in TLS 1.3 verschluesselt)
            out["server_hello_version"] = VERS.get(hsv or rv, hsv or rv)
            # Bei TLS 1.3 ist die "echte" Version in extensions_supported_version
            if supv:
                out["negotiated_version"] = VERS.get(supv.split(",")[-1], supv.split(",")[-1])
            elif hsv:
                out["negotiated_version"] = VERS.get(hsv, hsv)
            if cipher:
                # Cipher kann mehrere Werte enthalten (ClientHello-Liste) — bei ServerHello ist es 1 Wert
                cipher_code = cipher.split(",")[0]
                out["cipher"] = CIPH.get(cipher_code, cipher_code)
    return out


# -------------------------------------------------------------------------
# ASN-Lookup via Team-Cymru-DNS
# -------------------------------------------------------------------------
@functools.lru_cache(maxsize=4096)
def asn_lookup(ip: str) -> dict:
    """Liefert {asn, prefix, country, org_name} fuer eine IPv4. ASN als int oder None."""
    out = {"asn": None, "prefix": None, "country": None, "org_name": None}
    try:
        reversed_ip = ".".join(reversed(ip.split(".")))
        # 1) ASN-Origin-Query
        q = f"{reversed_ip}.origin.asn.cymru.com"
        rec = _dns_txt(q)
        if not rec:
            return out
        # Antwortformat: '"asn | prefix | country | registry | date"'
        parts = [p.strip() for p in rec.strip('"').split("|")]
        if len(parts) >= 3:
            asn_str = parts[0].split()[0]  # bei multi-origin: nur erste ASN
            out["asn"] = int(asn_str) if asn_str.isdigit() else None
            out["prefix"] = parts[1]
            out["country"] = parts[2]

        # 2) ASN-Description-Query
        if out["asn"]:
            q2 = f"AS{out['asn']}.asn.cymru.com"
            rec2 = _dns_txt(q2)
            if rec2:
                parts2 = [p.strip() for p in rec2.strip('"').split("|")]
                if len(parts2) >= 5:
                    out["org_name"] = parts2[4]
    except Exception:
        pass
    return out


def _dns_txt(name: str) -> str | None:
    """Einfacher DNS-TXT-Lookup via socket.getaddrinfo geht nicht — wir nutzen dnspython."""
    try:
        import dns.resolver
        ans = dns.resolver.resolve(name, "TXT", lifetime=5)
        return str(ans[0])
    except Exception:
        return None
