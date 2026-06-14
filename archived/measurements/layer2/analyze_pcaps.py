"""Layer-2 Analyse: Extrahiert Protokoll-Zeiten aus PCAP-Dateien via tshark.

Ansatz: TCP-Ebene, weil TLS 1.3 den Handshake verschluesselt.
Wir sehen trotzdem alle Paketzeiten und -richtungen, daraus:

- TCP-Handshake-RTT (SYN → SYN-ACK)
- TLS-Handshake (ClientHello → ServerHello)
- Gesamter Verbindungsaufbau bis erste Anwendungsdaten
- Anzahl RTTs
- Paket-Timeline

Verwendung auf EC2:
  python measurements/layer2/analyze_pcaps.py [--pcap-dir data/layer2]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

FLAG_SYN     = "0x0002"
FLAG_SYNACK  = "0x0012"
FLAG_ACK     = "0x0010"
FLAG_PSHACK  = "0x0018"
FLAG_FIN     = "0x0011"
FLAG_FINACK  = "0x0019"
FLAG_RST     = "0x0004"


def tshark_packets(pcap: Path) -> list[dict]:
    cmd = [
        "tshark", "-r", str(pcap),
        "-T", "fields", "-E", "separator=|", "-E", "header=n",
        "-e", "frame.number",
        "-e", "frame.time_relative",
        "-e", "frame.len",
        "-e", "tcp.srcport",
        "-e", "tcp.dstport",
        "-e", "tcp.flags",
        "-e", "tcp.len",
        "-e", "ip.src",
        "-e", "ip.dst",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=30)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return []

    pkts = []
    for line in out.strip().splitlines():
        if not line.strip():
            continue
        p = line.split("|")
        if len(p) < 9:
            continue
        pkts.append({
            "num": int(p[0]),
            "t": float(p[1]),
            "frame_len": int(p[2]),
            "src_port": p[3],
            "dst_port": p[4],
            "flags": p[5],
            "tcp_len": int(p[6]) if p[6] else 0,
            "src_ip": p[7],
            "dst_ip": p[8],
        })
    return pkts


def analyze_one(pcap: Path) -> dict:
    name = pcap.stem.replace("capture_", "").rsplit("_", 2)[0]
    result = {"file": pcap.name, "provider": name}

    pkts = tshark_packets(pcap)
    result["total_packets"] = len(pkts)
    if not pkts:
        return result

    # Client/Server bestimmen (SYN geht zum Server)
    syn_pkt = next((p for p in pkts if p["flags"] == FLAG_SYN), None)
    if not syn_pkt:
        return result

    client_ip = syn_pkt["src_ip"]
    server_ip = syn_pkt["dst_ip"]
    t_syn = syn_pkt["t"]

    def is_client(p): return p["src_ip"] == client_ip
    def is_server(p): return p["src_ip"] == server_ip
    def ms_since_syn(p): return round((p["t"] - t_syn) * 1000, 2)

    # --- TCP SYN → SYN-ACK (= 1 RTT) ---
    synack = next((p for p in pkts if p["flags"] == FLAG_SYNACK), None)
    if synack:
        result["tcp_handshake_ms"] = round((synack["t"] - t_syn) * 1000, 2)
        result["rtt_ms"] = result["tcp_handshake_ms"]

    # --- Erster Client-Payload (= TLS ClientHello) ---
    first_client_data = next((p for p in pkts if is_client(p) and p["tcp_len"] > 0), None)
    if first_client_data:
        result["tls_clienthello_ms"] = ms_since_syn(first_client_data)

    # --- Erster Server-Payload (= TLS ServerHello) ---
    first_server_data = next((p for p in pkts if is_server(p) and p["tcp_len"] > 0), None)
    if first_server_data:
        result["tls_serverhello_ms"] = ms_since_syn(first_server_data)

    # --- Verbindung bereit: erstes grosses Client-Paket (>500B) nach
    #     dem initialen Handshake = Audio-/Request-Daten ---
    handshake_end = first_server_data["t"] if first_server_data else 0
    big_client = next(
        (p for p in pkts if is_client(p) and p["tcp_len"] > 500 and p["t"] > handshake_end + 0.005),
        None
    )
    if big_client:
        result["app_data_start_ms"] = ms_since_syn(big_client)
        if result.get("rtt_ms"):
            result["rtts_to_ready"] = round(result["app_data_start_ms"] / result["rtt_ms"], 1)

    # --- Erste Server-Antwort mit Inhalt (nach Request) ---
    if big_client:
        first_response = next(
            (p for p in pkts if is_server(p) and p["tcp_len"] > 0 and p["t"] > big_client["t"]),
            None
        )
        if first_response:
            result["first_response_ms"] = ms_since_syn(first_response)

    # --- Paket-Timeline (erste 30 Pakete) ---
    timeline = []
    for p in pkts[:30]:
        d = "C→S" if is_client(p) else "S→C"
        flags = p["flags"]
        if flags == FLAG_SYN:
            label = "SYN"
        elif flags == FLAG_SYNACK:
            label = "SYN-ACK"
        elif p["tcp_len"] == 0:
            label = "ACK"
        else:
            label = f"DATA({p['tcp_len']}B)"
        timeline.append(f"{ms_since_syn(p):>10.2f} ms  {d}  {label}")

    result["timeline"] = timeline
    return result


def main():
    parser = argparse.ArgumentParser(description="Layer-2 PCAP-Analyse")
    parser.add_argument("--pcap-dir", type=str, default="data/layer2")
    args = parser.parse_args()

    pcap_dir = Path(args.pcap_dir)
    pcaps = sorted(pcap_dir.glob("capture_*.pcap"))

    if not pcaps:
        print(f"Keine .pcap-Dateien in {pcap_dir}")
        sys.exit(1)

    print(f"=== Layer-2 Analyse: {len(pcaps)} Captures ===\n")

    all_results = []
    for pcap in pcaps:
        r = analyze_one(pcap)
        all_results.append(r)

        print(f"{'='*60}")
        print(f"  {r['provider']}  ({r['total_packets']} Pakete)")
        print(f"{'='*60}")
        if r.get("tcp_handshake_ms") is not None:
            print(f"  TCP-Handshake (1 RTT):      {r['tcp_handshake_ms']:>8.1f} ms")
        if r.get("tls_clienthello_ms") is not None:
            print(f"  TLS ClientHello:            {r['tls_clienthello_ms']:>8.1f} ms")
        if r.get("tls_serverhello_ms") is not None:
            print(f"  TLS ServerHello:            {r['tls_serverhello_ms']:>8.1f} ms")
        if r.get("app_data_start_ms") is not None:
            rtts = r.get("rtts_to_ready", "?")
            print(f"  App-Daten Start:            {r['app_data_start_ms']:>8.1f} ms  (~{rtts} RTTs)")
        if r.get("first_response_ms") is not None:
            print(f"  Erste Server-Antwort:       {r['first_response_ms']:>8.1f} ms")

        print(f"\n  Paket-Timeline:")
        for line in r.get("timeline", []):
            print(f"    {line}")
        print()

    # Zusammenfassung
    print("\n" + "=" * 85)
    print(f"  {'Provider':<18} {'RTT':>7} {'ClientHi':>9} {'ServerHi':>9} {'App Start':>10} {'#RTTs':>6} {'1st Resp':>9}")
    print("-" * 85)
    for r in all_results:
        prov = r["provider"]
        rtt = f"{r['rtt_ms']:.1f}" if r.get("rtt_ms") else "-"
        ch = f"{r['tls_clienthello_ms']:.1f}" if r.get("tls_clienthello_ms") else "-"
        sh = f"{r['tls_serverhello_ms']:.1f}" if r.get("tls_serverhello_ms") else "-"
        app = f"{r['app_data_start_ms']:.1f}" if r.get("app_data_start_ms") else "-"
        rtts = f"{r['rtts_to_ready']}" if r.get("rtts_to_ready") else "-"
        resp = f"{r['first_response_ms']:.1f}" if r.get("first_response_ms") else "-"
        print(f"  {prov:<18} {rtt:>7} {ch:>9} {sh:>9} {app:>10} {rtts:>6} {resp:>9}")
    print("=" * 85)

    # JSON-Export
    out_json = pcap_dir / "analysis_summary.json"
    with open(out_json, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nJSON-Export: {out_json}")


if __name__ == "__main__":
    main()
