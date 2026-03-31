"""DNS-Analyse: Multi-Resolver-Abfrage, TTL, Anycast-Erkennung.

Misst DNS-Aufloesung ueber 3 oeffentliche Resolver (Google, Cloudflare, Quad9).
Erkennt Anycast-Hinweise wenn verschiedene Resolver unterschiedliche IPs liefern.
"""

import subprocess

from measurements.config import DNS_RESOLVERS


def measure(host: str) -> dict:
    """DNS-Aufloesung gegen 3 Resolver; erkennt ob IPs variieren (Anycast-Hinweis).

    Returns:
        {"ips": [...], "ttl": int, "resolvers": {...}, "anycast_likely": bool}
    """
    resolver_results: dict[str, list[str]] = {}

    for resolver in DNS_RESOLVERS:
        try:
            out = subprocess.check_output(
                ["dig", f"@{resolver}", host, "A", "+short", "+time=3", "+tries=1"],
                timeout=5, text=True, stderr=subprocess.DEVNULL,
            )
            ips = [line.strip() for line in out.strip().splitlines() if line.strip()]
            resolver_results[resolver] = ips
        except Exception:
            resolver_results[resolver] = []

    all_ips = list({ip for ips in resolver_results.values() for ip in ips})

    # Anycast-Hinweis: verschiedene Resolver geben unterschiedliche IPs
    unique_sets = [frozenset(ips) for ips in resolver_results.values() if ips]
    anycast_likely = len(set(unique_sets)) > 1 if unique_sets else False

    ttl = _get_ttl(host)

    return {
        "ips": all_ips,
        "ttl": ttl,
        "resolvers": resolver_results,
        "anycast_likely": anycast_likely,
    }


def _get_ttl(host: str) -> int | None:
    """TTL-Wert aus dig +noall +answer."""
    try:
        out = subprocess.check_output(
            ["dig", host, "A", "+noall", "+answer", "+time=3", "+tries=1"],
            timeout=5, text=True, stderr=subprocess.DEVNULL,
        )
        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[3] == "A":
                return int(parts[1])
    except Exception:
        pass
    return None
