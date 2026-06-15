"""
Layer 1 — DNS-Auflösung (Multi-Resolver) + TTL.

Was es misst:
  Jeden Host über DREI öffentliche Resolver (Google/Cloudflare/Quad9) auflösen
  und die aufgelösten IPv4-Adressen je Resolver festhalten — plus die DNS-TTL.
  Zweck: zeigt Round-Robin/Anycast-Streuung (verschiedene Resolver bzw. Zeitpunkte
  können verschiedene IPs liefern, s. Deepgram Multi-DC, A9) und liefert die
  Roh-IPs als Grundlage für den ASN-/Edge-Schritt.

Werkzeug: `dig` (auf macOS vorhanden; auf frischem Ubuntu/EC2 ggf. nachinstallieren:
  sudo apt-get install dnsutils). Fehlt dig, crasht das Skript NICHT — es schreibt
  leere Ergebnisse mit Hinweis.

Ausführen (vom Repo-Wurzelverzeichnis):
  .venv/bin/python measurements/layer1/dns_lookup.py
"""

import subprocess
import json
import os
import re
from datetime import datetime, timezone

from hosts import HOSTS

RESOLVERS = {"google": "8.8.8.8", "cloudflare": "1.1.1.1", "quad9": "9.9.9.9"}
IPV4 = re.compile(r"^\d+\.\d+\.\d+\.\d+$")


def dig(args):
    """Ruft dig mit den gegebenen Argumenten auf. Gibt stdout (Text) oder '' zurück (kein Crash)."""
    try:
        out = subprocess.run(["dig"] + args + ["+time=3", "+tries=1"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout
    except (subprocess.TimeoutExpired, OSError):   # OSError fängt auch fehlendes dig (FileNotFoundError)
        return ""


def resolve_via(host, resolver_ip):
    """Löst host über einen bestimmten Resolver auf. Gibt die Liste der IPv4s zurück."""
    stdout = dig([f"@{resolver_ip}", host, "A", "+short"])
    return [line for line in stdout.split() if IPV4.match(line)]


def get_ttl(host):
    """Holt die DNS-TTL (Sekunden) über den Google-Resolver.
    Hinweis: das ist die VERBLEIBENDE Cache-TTL des Resolvers (zählt herunter), nicht die autoritative TTL."""
    # Answer-Zeile: "api.openai.com.   4   IN   A   172.66.0.243" -> TTL ist Feld 2
    for line in dig([f"@{RESOLVERS['google']}", host, "A", "+noall", "+answer"]).splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[3] == "A":
            return int(parts[1])
    return None


def lookup_host(host):
    """Löst einen Host über alle Resolver auf. Gibt IMMER einen Record zurück."""
    rec = {
        "host": host,
        "resolvers": {},     # je Resolver die Liste der IPv4s
        "ttl_s": None,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    for name, ip in RESOLVERS.items():
        rec["resolvers"][name] = resolve_via(host, ip)
    rec["ttl_s"] = get_ttl(host)
    return rec


def main():
    results = [lookup_host(h) for h in HOSTS]

    print(f"{'Host':<40} {'TTL':>5}  IPs (google | cloudflare | quad9)")
    for r in results:
        cols = " | ".join(",".join(r["resolvers"][name]) or "-" for name in RESOLVERS)
        ttl = r["ttl_s"] if r["ttl_s"] is not None else "-"
        print(f"{r['host']:<40} {ttl:>5}  {cols}")

    os.makedirs("data/layer1", exist_ok=True)
    out = "data/layer1/dns_lookup.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
