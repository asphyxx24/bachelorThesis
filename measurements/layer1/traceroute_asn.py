"""
Layer 1 — Traceroute + AS-Pfad (Edge-Klassifikator, Bedingung c).

Was es misst:
  Den Netzwerk-Pfad (Hop für Hop) zu jedem Host und das Netz/AS je Hop. Zweck:
  Bedingung (c) des Edge-/Host-Klassifikators (s. messprotokoll.md, A3). Edge-Indiz ist
  NICHT "Route bricht ab", sondern: die Ziel-IP wird erreicht (`reached_dest=True`) und der
  letzte antwortende Hop liegt SELBST im CDN-AS (AS13335) bei ~1 ms — der Edge IST der Endpunkt.

Zur IP-Auflösung (ehrlich): Jedes L1-Skript löst SELBST auf; bei Round-Robin-Hosts kann der Trace
  eine andere Pool-IP treffen als tcp_ping/asn_lookup. Unkritisch (alle Pool-IPs je Host gleiche
  ASN/RTT-Klasse). Die getracte IP steht je Record drin. `reached_dest` = ob der letzte
  antwortende Hop die Ziel-IP war.

Werkzeug: `traceroute` (auf macOS vorhanden; auf frischem Ubuntu/EC2 nachinstallieren:
  sudo apt-get install traceroute). Fehlt es, crasht das Skript NICHT.
  Cloudflare/Azure filtern oft Hops (erscheinen als `*`) — das ist normal.

OFFEN (mit Anton zu besprechen): die TCP-SYN-Variante `-T -p 443` (messprotokoll A3, c)
  deckt gefilterte CDN-Routen besser auf, braucht aber root/sudo -> läuft NICHT
  ohne sudo auf dem Mac. Hier vorerst die Standard-(UDP-)Traceroute ohne sudo.

Ausführen (vom Repo-Wurzelverzeichnis):
  .venv/bin/python measurements/layer1/traceroute_asn.py
"""

import subprocess
import socket
import json
import os
import re
import ipaddress
from datetime import datetime, timezone

from hosts import HOSTS
from asn_lookup import asn_of_ip   # ASN-Lookup wiederverwenden (eine Quelle)

MAX_HOPS = 25          # deckungsgleich mit mess_kommandos.md
WAIT_S = 2             # -w 2 (mess_kommandos.md): Sekunden Wartezeit je Hop
TIMEOUT_S = 90         # subprocess-Timeout fürs gesamte traceroute je Host
IPV4 = re.compile(r"\d+\.\d+\.\d+\.\d+")

_asn_cache = {}        # IP -> {asn, org, ...}: identische Hops nicht doppelt bei Cymru abfragen


def cached_asn(ip):
    if ip not in _asn_cache:
        _asn_cache[ip] = asn_of_ip(ip)
    return _asn_cache[ip]


def is_public(ip):
    """True, wenn die IP öffentlich routbar ist (private/Sonder-IPs beim ASN-Lookup überspringen)."""
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def parse_hops(stdout):
    """Liest aus der traceroute-Ausgabe je Zeile die erste IPv4 (oder None bei '*')."""
    hops = []
    for line in stdout.splitlines()[1:]:    # erste Zeile ist der "traceroute to ..."-Header
        m = IPV4.search(line)
        hops.append(m.group(0) if m else None)
    return hops


def trace_host(host):
    """Traced einen Host und schlägt je Hop die ASN nach. Gibt IMMER einen Record zurück."""
    rec = {
        "host": host,
        "resolved_ip": None,
        "hops": [],          # je Hop: {hop, ip, asn, org}
        "reached_dest": False,
        "raw": None,         # volle traceroute-Ausgabe (roh)
        "error": None,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    try:
        rec["resolved_ip"] = socket.gethostbyname(host)
    except OSError as e:
        rec["error"] = f"dns: {e}"
        return rec

    stderr = ""
    try:
        out = subprocess.run(
            ["traceroute", "-n", "-w", str(WAIT_S), "-q", "1", "-m", str(MAX_HOPS), rec["resolved_ip"]],
            capture_output=True, text=True, timeout=TIMEOUT_S)
        stdout, stderr = out.stdout, out.stderr
    except subprocess.TimeoutExpired as e:
        rec["error"] = "timeout"
        stdout = e.stdout or ""                          # bis dahin gesammelte Hops retten
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
    except OSError as e:                                 # z.B. traceroute nicht installiert
        rec["error"] = f"traceroute nicht ausführbar: {e}"
        return rec

    rec["raw"] = stdout.strip()
    for i, ip in enumerate(parse_hops(stdout), start=1):
        if ip and is_public(ip):
            info = cached_asn(ip)
            rec["hops"].append({"hop": i, "ip": ip, "asn": info["asn"], "org": info["org"]})
        else:
            rec["hops"].append({"hop": i, "ip": ip, "asn": None, "org": None})

    answered = [h["ip"] for h in rec["hops"] if h["ip"]]
    rec["reached_dest"] = bool(answered) and answered[-1] == rec["resolved_ip"]
    if not rec["error"] and not answered:                # kein Hop geantwortet -> echter Fehlschlag sichtbar machen
        rec["error"] = stderr.strip() or "keine antwortenden Hops"
    return rec


def main():
    results = [trace_host(h) for h in HOSTS]

    for r in results:
        flag = " [Ziel erreicht]" if r["reached_dest"] else ""
        print(f"\n{r['host']} -> {r['resolved_ip'] or '?'}{flag}" + (f"  [{r['error']}]" if r["error"] else ""))
        for hop in r["hops"]:
            ip = hop["ip"] or "*"
            asn = f"AS{hop['asn']}" if hop["asn"] else ""
            print(f"  {hop['hop']:>2}  {ip:<16} {asn:<8} {hop['org'] or ''}")

    os.makedirs("data/layer1", exist_ok=True)
    out = "data/layer1/traceroute_asn.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
