"""
Layer 1 — ICMP-Ping (sekundäre RTT-Metrik, Cross-Check zum TCP-Ping).

Was es misst:
  Die klassische RTT per ICMP-Echo (das normale `ping`). Dient als Gegenprobe
  zum TCP-Ping: wo BEIDE funktionieren, sollte tcp_ping ≈ icmp_ping sein — das
  validiert, dass der TCP-Ping ein gültiger RTT-Proxy ist (s. messprotokoll.md).
  Manche Hosts (z.B. rev.ai) blocken ICMP — die werden sauber als "geblockt"
  markiert, nicht als Crash.

Damit der Cross-Check fair ist:
  Wir lösen den Host EINMAL selbst zur IPv4 auf (wie tcp_ping.py) und pingen
  diese IP — so messen beide Layer garantiert dieselbe IP (wichtig bei Round-Robin).

Warum subprocess-Timeout statt `-W`:
  `-W` bedeutet unter Linux Sekunden, unter macOS Millisekunden (A9). Statt uns
  darauf zu verlassen, geben wir dem GANZEN ping-Kommando einen subprocess-Timeout.

Ausführen (vom Repo-Wurzelverzeichnis):
  .venv/bin/python measurements/layer1/icmp_ping.py
"""

import subprocess
import socket
import json
import os
import re
from datetime import datetime, timezone

from hosts import HOSTS

N = 10            # ICMP-Pakete pro Host (nur Cross-Check; ping sendet 1/s -> 10 hält die Laufzeit im Rahmen)
TIMEOUT_S = 30    # subprocess-Timeout fürs gesamte ping-Kommando


def icmp_ping(host):
    """Pingt einen Host N-mal per ICMP. Gibt IMMER einen Record zurück."""
    rec = {
        "host": host,
        "resolved_ip": None,
        "n": N,
        "n_ok": 0,
        "min_ms": None,
        "avg_ms": None,
        "max_ms": None,
        "raw": None,        # die volle ping-Ausgabe (roh, für spätere Fragen)
        "error": None,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    try:
        rec["resolved_ip"] = socket.gethostbyname(host)
    except OSError as e:
        rec["error"] = f"dns: {e}"
        return rec

    try:
        out = subprocess.run(["ping", "-c", str(N), rec["resolved_ip"]],
                             capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        rec["error"] = "timeout"
        return rec
    except OSError as e:                       # z.B. ping nicht im PATH
        rec["error"] = f"ping nicht ausführbar: {e}"
        return rec
    rec["raw"] = out.stdout.strip()

    # "X packets transmitted, Y (packets )received" -> empfangene Pakete = n_ok
    recv = re.search(r"(\d+)\s+(?:packets\s+)?received", out.stdout)
    rec["n_ok"] = int(recv.group(1)) if recv else 0

    # Zusammenfassungszeile: ".../min/avg/max[/stddev] = 1.2/3.4/5.6[/0.7] ms"
    stats = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)", out.stdout)
    if stats:
        rec["min_ms"] = float(stats.group(1))
        rec["avg_ms"] = float(stats.group(2))
        rec["max_ms"] = float(stats.group(3))
    elif rec["n_ok"] == 0:
        # Keine Statistik-Zeile und 0 empfangen: echter Fehler (stderr) ODER ICMP geblockt.
        err = out.stderr.strip()
        rec["error"] = err if err else "keine ICMP-Antwort (evtl. geblockt)"
    return rec


def main():
    results = [icmp_ping(h) for h in HOSTS]

    print(f"{'Host':<40} {'min ms':>8} {'avg ms':>8} {'max ms':>8}  ok")
    for r in results:
        mn = f"{r['min_ms']:.2f}" if r["min_ms"] is not None else "-"
        av = f"{r['avg_ms']:.2f}" if r["avg_ms"] is not None else "-"
        mx = f"{r['max_ms']:.2f}" if r["max_ms"] is not None else "-"
        print(f"{r['host']:<40} {mn:>8} {av:>8} {mx:>8}  {r['n_ok']}/{r['n']}")

    os.makedirs("data/layer1", exist_ok=True)
    out = "data/layer1/icmp_ping.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
