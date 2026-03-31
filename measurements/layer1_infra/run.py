"""Schicht 1 Runner: Infrastruktur-Charakterisierung.

Fuehrt DNS, Ping, Traceroute und TLS-Analyse fuer alle 3 API-Endpoints durch.

Verwendung:
  python measurements/layer1_infra/run.py [--mode background|full] [--dry-run]

  --mode background  Nur DNS + Ping (stuendlicher Cron, ~15s)
  --mode full        + Traceroute + TLS (taeglicher Cron, ~3min)
  --dry-run          Keine Datei schreiben, Ergebnis auf stdout
"""

import argparse
import json
import sys
from pathlib import Path

# Repo-Root zum Python-Path hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from measurements.config import ENDPOINTS
from measurements.layer1_infra import dns, ping, traceroute, tls
from measurements.lib.output import now_iso, output_path, write_jsonl


def run(mode: str, dry_run: bool) -> None:
    ts = now_iso()
    records: list[dict] = []

    for ep in ENDPOINTS:
        name = ep["name"]
        host = ep["host"]

        # DNS — immer
        print(f"  [{name}] DNS...", end=" ", flush=True)
        dns_data = dns.measure(host)
        records.append({"ts": ts, "endpoint": host, "type": "dns", "data": dns_data})
        ips = dns_data.get("ips", [])
        print(f"OK ({len(ips)} IPs, TTL={dns_data.get('ttl', '?')})")

        # Ping — immer
        print(f"  [{name}] Ping...", end=" ", flush=True)
        ping_data = ping.measure(host)
        records.append({"ts": ts, "endpoint": host, "type": "ping", "data": ping_data})
        print(f"OK (avg={ping_data.get('avg_ms', '?')} ms)")

        if mode == "full":
            # Traceroute + ASN — nur im full-Modus
            print(f"  [{name}] Traceroute + ASN...", end=" ", flush=True)
            tr_data = traceroute.measure(host)
            records.append({"ts": ts, "endpoint": host, "type": "traceroute", "data": tr_data})
            as_path = tr_data.get("as_path", [])
            print(f"OK ({tr_data.get('total_hops', '?')} hops, AS-path={as_path})")

            # TLS-Handshake — nur im full-Modus
            print(f"  [{name}] TLS...", end=" ", flush=True)
            tls_data = tls.measure(ep["url"])
            records.append({"ts": ts, "endpoint": host, "type": "tls", "data": tls_data})
            print(f"OK (TLS={tls_data.get('tls_handshake_ms', '?')} ms, HTTP/{tls_data.get('http_version', '?')})")

    # Output
    if dry_run:
        for r in records:
            print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        path = output_path("layer1", mode=mode)
        for r in records:
            write_jsonl(path, r)
        print(f"\nGeschrieben: {path} ({len(records)} Records)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Schicht 1: Infrastruktur-Charakterisierung")
    parser.add_argument("--mode", choices=["background", "full"], default="background",
                        help="background=DNS+Ping, full=+Traceroute+TLS (default: background)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Keine Datei schreiben, Ergebnis auf stdout")
    args = parser.parse_args()

    print(f"=== Schicht 1: Infrastruktur === mode={args.mode}")
    run(mode=args.mode, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
