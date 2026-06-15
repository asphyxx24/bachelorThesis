"""
Layer 1 — TCP-Ping (primäre RTT-Metrik).

Was es misst:
  Die Round-Trip-Time (RTT) per TCP-Handshake auf Port 443:
  ein SYN raus, ein SYN-ACK zurück = 1 RTT. Das funktioniert bei ALLEN
  Hosts (jeder API-Endpunkt muss TCP auf Port 443 annehmen) — auch bei
  denen, die normales ICMP-`ping` blocken.
  Begründung/Methodik: setup/messprotokoll.md (Layer 1) + setup/mess_kommandos.md.

Zwei Feinheiten, die das Ergebnis korrekt machen:
  1. DNS wird EINMAL vorab aufgelöst; danach verbinden wir zur IP — sonst
     würde die DNS-Zeit fälschlich in der RTT stecken.
  2. Wir pingen N-mal und nehmen den MINIMUM-Wert als Schätzer der reinen
     Pfadlatenz (das Minimum ist am wenigsten durch Stau/Queueing verfälscht).
     Den Median speichern wir zusätzlich (der enthält Queueing).

Ausführen (vom Repo-Wurzelverzeichnis):
  .venv/bin/python measurements/layer1/tcp_ping.py
"""

import socket
import time
import json
import os
import statistics
from datetime import datetime, timezone

from hosts import HOSTS   # die 7 API-Hosts, zentral in hosts.py

N = 20          # Pings pro Host (Audit: >= 20 für einen stabilen min-Schätzer)
PORT = 443
TIMEOUT = 5.0   # Sekunden, ab denen ein einzelner Ping als Fehlschlag gilt


def tcp_ping_once(ip):
    """Ein TCP-Handshake zur IP. Gibt die RTT in ms zurück, oder None bei Fehler."""
    start = time.perf_counter()
    try:
        sock = socket.create_connection((ip, PORT), timeout=TIMEOUT)
    except OSError:
        return None
    rtt = (time.perf_counter() - start) * 1000   # Uhr stoppen, BEVOR wir schließen ...
    sock.close()                                 # ... damit close() nicht zur RTT zählt
    return rtt


def measure_host(host):
    """Löst den Host einmal auf und pingt ihn N-mal. Gibt IMMER einen Record zurück (auch bei Fehler)."""
    # Record-Grundgerüst — wird unten Schritt für Schritt gefüllt.
    rec = {
        "host": host,
        "resolved_ip": None,        # welche IP gepingt wurde (wichtig bei Round-Robin)
        "n": N,
        "n_ok": 0,
        "min_ms": None,
        "median_ms": None,
        "rtts_ms": [],              # alle Roh-Werte
        "error": None,             # Grund, falls der Host komplett ausfällt
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    # DNS einmalig auflösen (NICHT in der RTT). Schlägt es fehl, markieren wir den Host
    # als Fehlschlag und kehren zurück — KEIN Crash, die anderen Hosts laufen weiter.
    try:
        rec["resolved_ip"] = socket.gethostbyname(host)
    except OSError as e:
        rec["error"] = f"dns: {e}"
        return rec

    # N-mal pingen, dann auswerten.
    rtts = [tcp_ping_once(rec["resolved_ip"]) for _ in range(N)]
    ok = [r for r in rtts if r is not None]                       # nur die erfolgreichen Pings
    rec["n_ok"] = len(ok)
    rec["rtts_ms"] = [round(r, 2) if r is not None else None for r in rtts]
    if ok:
        rec["min_ms"] = round(min(ok), 2)
        rec["median_ms"] = round(statistics.median(ok), 2)
    return rec


def main():
    results = [measure_host(h) for h in HOSTS]

    # 1) Lesbare Tabelle in die Konsole
    print(f"{'Host':<40} {'IP':<16} {'min ms':>8} {'med ms':>8}  ok")
    for r in results:
        ip = r["resolved_ip"] or "-"     # bei DNS-Fehler ist resolved_ip None
        mn = f"{r['min_ms']:.2f}" if r["min_ms"] is not None else "-"
        md = f"{r['median_ms']:.2f}" if r["median_ms"] is not None else "-"
        print(f"{r['host']:<40} {ip:<16} {mn:>8} {md:>8}  {r['n_ok']}/{r['n']}")

    # 2) Rohdaten als JSONL speichern (eine Zeile pro Host)
    os.makedirs("data/layer1", exist_ok=True)
    out = "data/layer1/tcp_ping.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nRohdaten gespeichert: {out}")


if __name__ == "__main__":
    main()
