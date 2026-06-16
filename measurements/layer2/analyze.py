"""
Layer 2 — Handshake-Eichung (Analyse-Teil).

Liest die PCAP (via `tcpdump -r`, KEINE Extra-Library) + das App-Log von capture.py und vergleicht
**Wire-SYN→SYN-ACK** gegen den App-`tcp_handshake_ms` — gepaart über den Quell-Port.

Ergebnis: stimmt der App-Timer mit der Wire-Latenz überein (Differenz nahe 0), ist die Layer-3-
Zeitmessung damit am Paket-Level GEEICHT (Contribution C2). Das ist der Beleg, der „ich vertraue den
Daten nicht" mit Daten beantwortet.

Ausführen:
  .venv/bin/python measurements/layer2/analyze.py --pcap data/layer2/cap_deepgram.pcap \
      --applog data/layer2/applog_deepgram.jsonl
"""

import argparse
import json
import re
import statistics as st
import subprocess

# tcpdump -tt -n Zeile: "<epoch> IP <src>.<port> > <dst>.<port>: Flags [..], ..."
_LINE = re.compile(r"^([\d.]+) IP (\S+) > (\S+): Flags \[([^\]]+)\]")


def _ip_port(endpoint):
    """'1.2.3.4.5678' -> ('1.2.3.4', '5678')  (Port ist das letzte dotted-Segment)."""
    ip, port = endpoint.rsplit(".", 1)
    return ip, port


def parse_pcap(pcap, server_ip, server_port="443"):
    """Gibt {src_port: wire_handshake_ms} = SYN(client->server) bis SYN-ACK(server->client)."""
    out = subprocess.run(["tcpdump", "-r", pcap, "-tt", "-n", "tcp port " + server_port],
                         capture_output=True, text=True).stdout
    syn, synack = {}, {}
    for ln in out.splitlines():
        m = _LINE.match(ln)
        if not m:
            continue
        ts = float(m.group(1))
        (sip, sp), (dip, dp), flags = _ip_port(m.group(2)), _ip_port(m.group(3)), m.group(4)
        is_syn = "S" in flags and "." not in flags        # reiner SYN
        is_synack = "S" in flags and "." in flags          # SYN-ACK
        if is_syn and dip == server_ip:                    # client(sp) -> server
            syn.setdefault(sp, ts)
        elif is_synack and sip == server_ip:               # server -> client(dp)
            synack.setdefault(dp, ts)
    wire = {}
    for sp, t0 in syn.items():
        if sp in synack:
            wire[sp] = round((synack[sp] - t0) * 1000, 2)
    return wire


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pcap", required=True)
    ap.add_argument("--applog", required=True)
    a = ap.parse_args()

    applog = [json.loads(l) for l in open(a.applog) if l.strip()]
    ok = [r for r in applog if r.get("app_tcp_handshake_ms") is not None]
    server_ip = next(r["ip"] for r in ok)
    wire = parse_pcap(a.pcap, server_ip)

    pairs = []   # (app_ms, wire_ms)
    for r in ok:
        sp = str(r.get("src_port"))
        if sp in wire:
            pairs.append((r["app_tcp_handshake_ms"], wire[sp]))

    print(f"Host {ok[0]['host']} ({server_ip}) — {len(pairs)}/{len(ok)} Calls per Quell-Port gepaart\n")
    if not pairs:
        print("KEINE Paarung — Filter/IP prüfen.")
        return
    app = [p[0] for p in pairs]
    wir = [p[1] for p in pairs]
    diff = [a_ - w_ for a_, w_ in pairs]
    print(f"{'':14}{'median':>9}{'min':>9}{'max':>9}")
    print(f"{'App tcp_hs':<14}{st.median(app):>9.2f}{min(app):>9.2f}{max(app):>9.2f}")
    print(f"{'Wire SYN-SA':<14}{st.median(wir):>9.2f}{min(wir):>9.2f}{max(wir):>9.2f}")
    print(f"{'Differenz':<14}{st.median(diff):>9.2f}{min(diff):>9.2f}{max(diff):>9.2f}")
    print(f"\nEICHUNG: App-Timer liegt im Median {st.median(diff):+.2f} ms neben der Wire-Latenz "
          f"({'GEEICHT ✓' if abs(st.median(diff)) < 2 else 'PRÜFEN'} — App misst minimal mehr, da "
          f"connect() erst nach dem SYN-ACK + Kernel-Returnzeit zurückkehrt).")


if __name__ == "__main__":
    main()
