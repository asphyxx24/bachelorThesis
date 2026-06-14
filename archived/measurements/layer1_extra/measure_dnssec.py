"""DNSSEC-Check pro Endpoint (Prof-Punkt 1).

Prueft fuer jeden Hostnamen:
  1. AD-Flag in DNS-Antwort (Authenticated Data) — Resolver hat DNSSEC validiert
  2. DS-Records bei der Elternzone — signiert die Zone ueberhaupt?
  3. RRSIG-Records bei der Antwort — A-Record selbst signiert?

Brauche dnspython: pip install dnspython

Aufruf: python measure_dnssec.py
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import dns.flags
import dns.message
import dns.name
import dns.query
import dns.rdatatype
import dns.resolver

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "layer1_extra"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW = OUT_DIR / "dnssec_raw.jsonl"
CSV = OUT_DIR / "dnssec.csv"

ENDPOINTS = [
    "api.deepgram.com",
    "api.rev.ai",
    "italynorth.stt.speech.microsoft.com",
    "api.openai.com",
    "api.groq.com",
    "api.mistral.ai",
    "italynorth.tts.speech.microsoft.com",
]

# Cloudflare DNSSEC-validierender Resolver. AWS-Resolver (169.254.169.253)
# validiert ebenfalls; Cloudflare ist deterministischer fuer den AD-Flag-Check.
RESOLVER_IP = "1.1.1.1"


def parent_zone(name: str) -> str:
    """'api.deepgram.com' -> 'deepgram.com'"""
    labels = name.rstrip(".").split(".")
    if len(labels) < 2:
        return name
    return ".".join(labels[-2:])


def check_ad_flag(host: str) -> dict:
    """A-Record mit DO-Flag (DNSSEC OK) abfragen und AD-Flag im Response pruefen."""
    out = {"ad_flag": False, "rrsig_in_answer": False, "ad_error": None}
    try:
        q = dns.message.make_query(host, dns.rdatatype.A, want_dnssec=True)
        r = dns.query.udp(q, RESOLVER_IP, timeout=5)
        out["ad_flag"] = bool(r.flags & dns.flags.AD)
        # Auf RRSIG in Answer-Section pruefen
        for rrset in r.answer:
            if rrset.rdtype == dns.rdatatype.RRSIG:
                out["rrsig_in_answer"] = True
                break
    except Exception as e:
        out["ad_error"] = f"{type(e).__name__}: {e}"
    return out


def check_ds(zone: str) -> dict:
    """DS-Record fuer die Zone direkt bei einem DNSSEC-validierenden Resolver
    abfragen (nicht ueber System-Resolver, der DS oft nicht weiterleitet).
    Existiert ein DS, ist die Zone signiert.
    """
    out = {"ds_present": False, "ds_count": 0, "ds_error": None}
    try:
        q = dns.message.make_query(zone, dns.rdatatype.DS, want_dnssec=True)
        r = dns.query.udp(q, RESOLVER_IP, timeout=5)
        for rrset in r.answer:
            if rrset.rdtype == dns.rdatatype.DS:
                out["ds_present"] = True
                out["ds_count"] = len(rrset)
                break
    except Exception as e:
        out["ds_error"] = f"{type(e).__name__}: {e}"
    return out


def classify(ad: bool, ds: bool, rrsig: bool) -> str:
    if ad and ds and rrsig:
        return "DNSSEC validiert"
    if ds and rrsig and not ad:
        return "Signiert, Resolver liefert AD nicht"
    if not ds:
        return "Zone NICHT signiert"
    return "Ungeklaert"


def main() -> None:
    rows = []
    with open(RAW, "w", encoding="utf-8") as fh:
        for host in ENDPOINTS:
            print(f"  {host} ...", flush=True)
            zone = parent_zone(host)
            ad_info = check_ad_flag(host)
            ds_info = check_ds(zone)

            row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "endpoint": host,
                "parent_zone": zone,
                "ad_flag": ad_info["ad_flag"],
                "rrsig_in_answer": ad_info["rrsig_in_answer"],
                "ds_present_parent": ds_info["ds_present"],
                "ds_count": ds_info["ds_count"],
                "ad_error": ad_info["ad_error"],
                "ds_error": ds_info["ds_error"],
                "classification": classify(
                    ad_info["ad_flag"], ds_info["ds_present"], ad_info["rrsig_in_answer"]
                ),
            }
            rows.append(row)
            fh.write(json.dumps(row) + "\n")

    with open(CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nFertig. {len(rows)} Endpoints -> {CSV.relative_to(ROOT)}")
    print("\nZusammenfassung:")
    for r in rows:
        print(f"  {r['endpoint']:40s} {r['classification']}")


if __name__ == "__main__":
    main()
