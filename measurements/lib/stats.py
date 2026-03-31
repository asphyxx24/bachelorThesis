"""Statistische Hilfsfunktionen fuer Messauswertung."""

import statistics


def compute_stats(values: list[float]) -> dict:
    """Berechnet Summary-Statistiken: mean, p50, p95, p99, stdev, min, max.

    Verwendet fuer Summary-Zeilen in JSONL-Output.
    """
    if not values:
        return {}
    s = sorted(values)
    n = len(s)

    def pct(p: float) -> float:
        idx = min(int(n * p), n - 1)
        return round(s[idx], 1)

    return {
        "mean": round(statistics.mean(s), 1),
        "p50": pct(0.50),
        "p95": pct(0.95),
        "p99": pct(0.99),
        "stdev": round(statistics.stdev(s) if n > 1 else 0.0, 1),
        "min": round(s[0], 1),
        "max": round(s[-1], 1),
    }
