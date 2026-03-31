"""RTT-Messung via ICMP Ping.

Sendet N Pings und parst min/avg/max/mdev sowie Paketverlust.
Funktioniert auf Linux (rtt) und macOS (round-trip).
"""

import re
import subprocess


def measure(host: str, count: int = 10) -> dict:
    """Ping-Messung: N ICMP Echo Requests.

    Returns:
        {"count": N, "min_ms": float, "avg_ms": float, "max_ms": float,
         "mdev_ms": float, "packet_loss": int}
    """
    try:
        out = subprocess.check_output(
            ["ping", "-c", str(count), "-W", "2", host],
            timeout=30, text=True, stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except subprocess.CalledProcessError as e:
        out = e.output or ""

    # Paketverlust
    loss_match = re.search(r"(\d+)%\s+packet loss", out)
    packet_loss = int(loss_match.group(1)) if loss_match else 100

    # RTT-Statistik (Linux: "rtt", macOS: "round-trip")
    rtt_match = re.search(
        r"(?:rtt|round-trip) min/avg/max/\S+ = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", out
    )
    if rtt_match:
        return {
            "count": count,
            "min_ms": float(rtt_match.group(1)),
            "avg_ms": float(rtt_match.group(2)),
            "max_ms": float(rtt_match.group(3)),
            "mdev_ms": float(rtt_match.group(4)),
            "packet_loss": packet_loss,
        }

    if packet_loss == 100:
        return {"count": count, "packet_loss": 100, "icmp_blocked": True}
    return {"count": count, "packet_loss": packet_loss, "error": "no_rtt_stats"}
