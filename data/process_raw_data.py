"""
Rohdaten aufbereiten: data/layer1/ + data/layer3/ -> data/processed/

Ausgabe:
  Layer 3 (Parquet):
    layer3_stt.parquet    - deepgram, revai, azure
    layer3_llm.parquet    - openai, groq, mistral
    layer3_tts.parquet    - deepgram, openai, azure
    layer3_errors.parquet - alle Fehlerzeilen

  Layer 1 (CSV):
    layer1_ping.csv
    layer1_dns.csv
    layer1_tls.csv
    layer1_traceroute.csv
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

ROOT = Path(__file__).parent.parent
L3_DIR = ROOT / "data" / "layer3"
L1_DIR = ROOT / "data" / "layer1"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Provider-Zuordnung
# ---------------------------------------------------------------------------
STT_APIS   = {"deepgram", "revai", "azure_stt"}
LLM_APIS   = {"openai", "groq", "mistral"}
TTS_APIS   = {"deepgram_tts", "openai_tts", "azure_tts"}

# Bereinigte Namen für Plots/Thesis (Implementierungsdetail-Suffixe weg)
API_RENAME = {
    "azure_stt":    "azure",
    "deepgram_tts": "deepgram",
    "openai_tts":   "openai",
    "azure_tts":    "azure",
}

CATEGORY_MAP = {
    **{a: "STT" for a in STT_APIS},
    **{a: "LLM" for a in LLM_APIS},
    **{a: "TTS" for a in TTS_APIS},
}

# ---------------------------------------------------------------------------
# Layer 3
# ---------------------------------------------------------------------------
print("=== Layer 3 ===")

stt_rows, llm_rows, tts_rows, err_rows = [], [], [], []

for f in sorted(L3_DIR.glob("*.jsonl")):
    with open(f, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            api = d.get("api", "")
            if api not in CATEGORY_MAP:
                continue

            if d.get("error"):
                # HTTP-Status aus dem Error-String extrahieren
                err_str = str(d["error"])
                http_status = None
                if err_str.startswith("HTTP "):
                    try:
                        http_status = int(err_str.split()[1].rstrip(":"))
                    except (IndexError, ValueError):
                        pass
                err_rows.append({
                    "ts":          d.get("ts"),
                    "api":         api,
                    "category":    CATEGORY_MAP[api],
                    "http_status": http_status,
                    "error_msg":   err_str[:120],
                })
                continue

            ts = pd.to_datetime(d["ts"], utc=True)
            base = {
                "ts":      ts,
                "date":    ts.date().isoformat(),
                "hour":    ts.hour,
                "weekday": ts.weekday(),  # 0=Montag
                "run":     d.get("run"),
                "api":     API_RENAME.get(api, api),
            }

            if api in STT_APIS:
                stt_rows.append({**base,
                    "connect_ms": d.get("connect_ms"),
                    "send_ms":    d.get("send_ms"),
                    "ttft_ms":    d.get("ttft_ms"),
                    "total_ms":   d.get("total_ms"),
                })
            elif api in LLM_APIS:
                llm_rows.append({**base,
                    "connect_ms":  d.get("connect_ms"),
                    "headers_ms":  d.get("headers_ms"),
                    "ttft_ms":     d.get("ttft_ms"),
                    "ttl_ms":      d.get("ttl_ms"),
                    "total_ms":    d.get("total_ms"),
                })
            elif api in TTS_APIS:
                tts_rows.append({**base,
                    "connect_ms": d.get("connect_ms"),
                    "ttfa_ms":    d.get("ttfa_ms"),
                    "total_ms":   d.get("total_ms"),
                })

for name, rows, path in [
    ("STT",    stt_rows, OUT_DIR / "layer3_stt.parquet"),
    ("LLM",    llm_rows, OUT_DIR / "layer3_llm.parquet"),
    ("TTS",    tts_rows, OUT_DIR / "layer3_tts.parquet"),
    ("Errors", err_rows, OUT_DIR / "layer3_errors.parquet"),
]:
    df = pd.DataFrame(rows)
    df.to_parquet(path, index=False)
    print(f"  {name:6}: {len(df):>6} Zeilen -> {path.name}")

# ---------------------------------------------------------------------------
# Layer 1
# ---------------------------------------------------------------------------
print("\n=== Layer 1 ===")

ping_rows, dns_rows, tls_rows, tr_rows = [], [], [], []

for f in sorted(L1_DIR.glob("*.jsonl")):
    with open(f, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts  = pd.to_datetime(d.get("ts"), utc=True)
            ep  = d.get("endpoint", "")
            typ = d.get("type", "")
            dat = d.get("data", {})

            base = {
                "ts":       ts,
                "date":     ts.date().isoformat(),
                "hour":     ts.hour,
                "endpoint": ep,
            }

            if typ == "ping":
                if dat.get("icmp_blocked"):
                    continue
                ping_rows.append({**base,
                    "avg_ms":       dat.get("avg_ms"),
                    "min_ms":       dat.get("min_ms"),
                    "max_ms":       dat.get("max_ms"),
                    "mdev_ms":      dat.get("mdev_ms"),
                    "packet_loss":  dat.get("packet_loss"),
                })

            elif typ == "dns":
                ips = [ip for ip in dat.get("ips", []) if not ip.endswith(".")]
                dns_rows.append({**base,
                    "anycast_likely": dat.get("anycast_likely"),
                    "ttl":            dat.get("ttl"),
                    "primary_ip":     ips[0] if ips else None,
                    "ip_count":       len(ips),
                })

            elif typ == "tls":
                tls_rows.append({
                    "date":          ts.date().isoformat(),
                    "endpoint":      ep,
                    "handshake_ms":  dat.get("handshake_ms"),
                    "tls_version":   dat.get("version"),
                })

            elif typ == "traceroute":
                hops = dat.get("hops", [])
                asns = []
                for h in hops:
                    a = h.get("asn")
                    if a and (not asns or asns[-1] != a):
                        asns.append(a)
                final_rtt = hops[-1].get("rtt_ms") if hops else None
                tr_rows.append({
                    "date":               ts.date().isoformat(),
                    "endpoint":           ep,
                    "hop_count":          len(hops),
                    "final_rtt_ms":       final_rtt,
                    "asn_path":           ",".join(str(a) for a in asns),
                    "destination_reached": final_rtt is not None,
                })

pd.DataFrame(ping_rows).to_csv(OUT_DIR / "layer1_ping.csv", index=False)
print(f"  Ping:       {len(ping_rows):>4} Zeilen -> layer1_ping.csv")

pd.DataFrame(dns_rows).to_csv(OUT_DIR / "layer1_dns.csv", index=False)
print(f"  DNS:        {len(dns_rows):>4} Zeilen -> layer1_dns.csv")

pd.DataFrame(tls_rows).to_csv(OUT_DIR / "layer1_tls.csv", index=False)
print(f"  TLS:        {len(tls_rows):>4} Zeilen -> layer1_tls.csv")

pd.DataFrame(tr_rows).to_csv(OUT_DIR / "layer1_traceroute.csv", index=False)
print(f"  Traceroute: {len(tr_rows):>4} Zeilen -> layer1_traceroute.csv")

print("\nFertig.")
