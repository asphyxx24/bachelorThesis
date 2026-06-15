"""
Layer 1 — ASN-/Netz-Lookup je IP (Edge-Klassifikator, Bedingung b).

Was es misst:
  Zu welchem Netz/Autonomen System (AS) gehört jede aufgelöste IP eines Hosts?
  Liegt sie z.B. in Cloudflare (AS13335)? Das ist Bedingung (b) des Edge-/Host-
  Klassifikators (s. messprotokoll.md, A3): zusammen mit der niedrigen TCP-RTT (a)
  belegt eine CDN-ASN, dass die Verbindung an einem Edge terminiert.

Werkzeug: Team-Cymru-DNS (whois-Daten über DNS-TXT-Abfragen mit `dig`).
  Es werden ALLE aufgelösten IPv4s je Host nachgeschlagen (Audit B: "ASN pro IP").
  Fehlt dig (frisches Ubuntu/EC2), crasht das Skript NICHT — die ASN bleibt None.

Die Funktion asn_of_ip() wird auch von traceroute_asn.py wiederverwendet.

Ausführen (vom Repo-Wurzelverzeichnis):
  .venv/bin/python measurements/layer1/asn_lookup.py
"""

import subprocess
import socket
import json
import os
from datetime import datetime, timezone

from hosts import HOSTS


def cymru_txt(name):
    """Eine Team-Cymru-TXT-Abfrage. Gibt die erste echte TXT-Zeile zurück oder None."""
    try:
        out = subprocess.run(["dig", "+short", name, "TXT", "+time=2", "+tries=1"],
                             capture_output=True, text=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError):   # OSError fängt auch fehlendes dig
        return None
    if out.returncode != 0:                         # dig-Fehler nicht als Inhalt missdeuten
        return None
    for line in out.stdout.splitlines():            # +short kann mehrere Zeilen liefern
        line = line.strip().strip('"')
        if line and not line.startswith(";;"):      # ";;"-Zeilen sind dig-Diagnosen, kein Inhalt
            return line
    return None


def asn_of_ip(ip):
    """Schlägt ASN + Org-Name für eine IPv4 nach. Gibt {ip, asn, org, cymru_raw} zurück."""
    rev = ".".join(reversed(ip.split(".")))               # 1.2.3.4 -> 4.3.2.1
    origin = cymru_txt(f"{rev}.origin.asn.cymru.com")     # "13335 | 104.18.0.0/20 | US | arin | ..."
    if not origin:
        return {"ip": ip, "asn": None, "org": None, "cymru_raw": None}
    asn = origin.split("|")[0].split()[0].strip()         # erstes Token (bei Multi-Origin mehrere ASNs)
    if not asn.isdigit():                                 # nur eine echte ASN-Nummer weiterverwenden
        return {"ip": ip, "asn": None, "org": None, "cymru_raw": origin}
    name = cymru_txt(f"AS{asn}.asn.cymru.com")            # "13335 | US | arin | ... | CLOUDFLARENET, US"
    org = name.split("|")[-1].strip() if name else None
    return {"ip": ip, "asn": asn, "org": org, "cymru_raw": origin}


def get_ipv4s(host):
    """Alle IPv4-Adressen eines Hosts (dedupliziert, sortiert)."""
    infos = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


def lookup_host(host):
    """Löst alle IPv4s auf und schlägt je IP die ASN nach. Gibt IMMER einen Record zurück."""
    rec = {"host": host, "ips": [], "error": None, "ts": datetime.now(timezone.utc).isoformat()}
    try:
        ips = get_ipv4s(host)
    except OSError as e:
        rec["error"] = f"dns: {e}"
        return rec
    rec["ips"] = [asn_of_ip(ip) for ip in ips]
    return rec


def main():
    results = [lookup_host(h) for h in HOSTS]

    print(f"{'Host':<40} {'IP':<16} {'ASN':>7}  Org")
    for r in results:
        if not r["ips"]:
            print(f"{r['host']:<40} {'-':<16} {'-':>7}  {r['error'] or '-'}")
        for entry in r["ips"]:
            print(f"{r['host']:<40} {entry['ip']:<16} {entry['asn'] or '-':>7}  {entry['org'] or '-'}")

    os.makedirs("data/layer1", exist_ok=True)
    out = "data/layer1/asn_lookup.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
