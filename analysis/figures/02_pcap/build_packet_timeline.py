#!/usr/bin/env python
"""
Paket-Level-Timeline (Layer 2) fuer STT-Provider — entzerrte Neugestaltung.

Sieger-Design (Juror-Urteil 2026-06-09): Entwurf 3 (Neugestaltung) mit dem
Hybrid-Feinschliff aus Entwurf 1. EINE Figur, drei vertikal grosszuegig
getrennte Panels statt der gedraengten Broken-Axis-Fassung:

  (A1) Handshake-ZOOM (0..55 ms, linear): TCP- und TLS-Handshake als zwei
       getrennte, farbcodierte Phasenbaender (je ~1 RTT). SYN-ACK und ClientHello
       liegen eng beieinander -> per horizontalem Versatz + Leader-Linie
       auseinandergezogen (Technik aus Entwurf 1).
  (A2) Volle, UNGEBROCHENE lineare Achse (0..t_burst): die ~358-ms-Client-
       Sendeluecke (Azure) erscheint als BUCHSTAEBLICH leerer Raum zwischen der
       gruenen connect_ms-Linie (~50 ms, sendebereit) und der blauen
       app_data_start-Linie (~446 ms). Die ehrliche Kernaussage „Client wartet,
       kein Server-Processing" traegt der Weissraum SELBST. Bei Deepgram (kein
       Client-Gap) zeigt A2 stattdessen den lueckenlosen, RTT-dominierten Aufbau.
  (B)  Inter-Arrival-Time je Paket (log): Δt-Stem ab SYN, Client/Server getrennt
       eingefaerbt; die langen Wartezeiten als umkreiste Ausreisser.

Erfuellt die drei Prof-Vorgaben sichtbar UND quantitativ:
  1) TCP- und TLS-Handshake GETRENNT erkennbar (A1, zwei Baender je 1 RTT mit Zahl).
  2) Inter-Arrival-Time sichtbar/auswertbar (B: Δt je Paket, log, paketweise ab SYN).
  3) Client/Server-Richtung getrennt (Farbe = Richtung, zwei y-Spuren).

Methodische Wahrheit (Azure): die ~358 ms zwischen Setup-Ende (~87 ms) und
Audio-Upload (~446 ms) sind CLIENT-Wartezeit, KEIN Server-Processing
(App ist bei connect_ms ~49 ms sendebereit). app_data_start (446 ms) != connect_ms (49 ms).
Das echte Server-Processing (~776 ms) erscheint separat im IAT-Stem.

Deepgram-Kontrast: RTT-dominierter Aufbau (TCP ~148, TLS ~150 ms = je 1 RTT),
KEINE Client-Sendeluecke — die groesste Pre-Audio-Luecke ist exakt 1 RTT
(der TLS-Handshake selbst). Methodischer Beleg: bei hoher RTT faellt
app_data_start mit connect_ms zusammen, bei Azure (niedrige RTT) klafft die
Client-Sendeluecke dazwischen. Das belegt, dass connect_ms sauber ist und die
PCAP-"proto_setup"-Zeit bei Azure ein Client-Artefakt ist, kein Server-Processing.

n=1 Capture pro Provider -> strukturelle Illustration, KEINE Verteilung.

Wiederverwendbar: plot_packet_timeline(provider) -> Figure. 1:1 in NB02 uebernehmbar.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
import numpy as np
from scapy.all import rdpcap, IP, TCP
from collections import Counter

# ---------------------------------------------------------------------------
# Konfiguration pro Provider — PCAP-Pfad, Layer-3-connect_ms (Median, Juni),
# Mess-Metadaten und die Panel-Fenster der NEUEN Drei-Panel-Figur:
#   zoom_xlim  : x-Bereich des Handshake-Zooms A1 (0..~55 ms / RTT-Klasse)
#   zoom_xticks: x-Ticks fuer A1
#   full_xticks: x-Ticks der ungebrochenen Vollachse A2 (bis t_burst)
# Alle Zeit-/Luecken-Zahlen werden aus dem PCAP SELBST berechnet (s.u.).
# gap_kind steuert die Erzaehlung von A2 (client = leere Wartezeit / none = RTT-Aufbau).
# ---------------------------------------------------------------------------
PCAP_DIR = "data/layer2"

PROVIDERS = {
    "azure_stt": {
        "pcap": "capture_azure_stt_20260608_1627.pcap",
        "label": "Azure STT",
        "region": "eu-central-1 → Italy North (EU)",
        "connect_ms": 49.5,          # Layer-3-Median (Juni-Kampagne)
        "zoom_xlim": (-3, 55),       # A1 Handshake-Zoom (TCP 18 / TLS 13 ms)
        "zoom_xticks": [0, 10, 20, 30, 40, 50],
        "full_xticks": [0, 50, 100, 150, 200, 250, 300, 350, 400, 450],
        "gap_kind": "client",        # die markante Pre-Audio-Luecke ist Client-Wartezeit
    },
    "deepgram_stt": {
        "pcap": "capture_deepgram_stt_20260608_1627.pcap",
        "label": "Deepgram STT",
        "region": "eu-central-1 → USA / Anycast",
        "connect_ms": 425.0,         # Layer-3-Median (Juni-Kampagne)
        "zoom_xlim": (-12, 330),     # A1 Handshake-Zoom (RTT-dominiert: TCP 148 / TLS 150 ms)
        "zoom_xticks": [0, 50, 100, 150, 200, 250, 300],
        "full_xticks": [0, 100, 200, 300, 400, 500],
        "gap_kind": "none",          # keine markante Client-Wartezeit
    },
}

# Farben — KONSISTENT: Farbe = RICHTUNG (nicht Provider).
C_CLIENT = "#1f6fb2"   # Client -> Server (Upload)
C_SERVER = "#c44e1b"   # Server -> Client (Download)
C_CONNECT = "#2a8f3c"  # connect_ms (App sendebereit) — gruen
C_GAP_CLIENT = "#b03a4a"   # Client-Wartezeit (rot)
C_GAP_SERVER = "#8a5a00"   # Server-Processing (braun)
# Phasen-Hintergrundbaender (dezent)
C_TCP = "#cfe3f2"
C_TLS = "#dceccd"
C_WS  = "#efe0cf"
C_SETUP = "#dceccd"    # zusammengefasstes Setup-Band auf der A2-Vollachse
C_GAPBAND = "#f6eef0"
C_AUDIO = "#dfe7f5"


# ---------------------------------------------------------------------------
# PCAP einlesen + auf den dominanten Flow beschraenken
# ---------------------------------------------------------------------------
def _load_flow(pcap_path):
    """Liest das PCAP, gibt die Pakete des groessten TCP-Flows zurueck.

    Rueckgabe: dict mit numpy-Arrays t (ms, relativ zum 1. Paket), dirn ('C'/'S'),
    flags (str), plen (Payload-Bytes), dt (Inter-Arrival zum Vorpaket, ms).
    """
    pkts = rdpcap(pcap_path)
    t0 = None
    rows = []
    for p in pkts:
        if not (p.haslayer(TCP) and p.haslayer(IP)):
            continue
        if t0 is None:
            t0 = float(p.time)
        t = (float(p.time) - t0) * 1000.0
        tcp = p[TCP]
        d = "C" if tcp.dport == 443 else ("S" if tcp.sport == 443 else "?")
        rows.append((t, d, str(tcp.flags), len(bytes(tcp.payload)),
                     p[IP].src, p[IP].dst, tcp.sport, tcp.dport))
    # dominanter Flow (normalisiertes 4-Tupel)
    def key(r):
        return (r[4], r[5], r[6], r[7]) if r[1] == "C" else (r[5], r[4], r[7], r[6])
    main = Counter(key(r) for r in rows).most_common(1)[0][0]
    rows = [r for r in rows if key(r) == main]
    t = np.array([r[0] for r in rows])
    return {
        "t": t,
        "dirn": np.array([r[1] for r in rows]),
        "flags": [r[2] for r in rows],
        "plen": np.array([r[3] for r in rows]),
        "dt": np.concatenate([[np.nan], np.diff(t)]),
        "n": len(rows),
    }


def _milestones(F):
    """Leitet die Phasen-Meilensteine aus den Paketen ab (selbst nachgerechnet)."""
    t, dirn, flags, plen, dt = F["t"], F["dirn"], F["flags"], F["plen"], F["dt"]
    n = F["n"]
    i_syn = 0
    i_synack = next(i for i in range(n) if flags[i] == "SA")
    i_chlo = next(i for i in range(n) if dirn[i] == "C" and plen[i] > 0)
    i_shlo = next(i for i in range(n) if dirn[i] == "S" and plen[i] > 1000)
    # Audio-Burst-Start: erstes Client-Payload >1000B mit >=2 weiteren binnen 6 ms
    i_burst = None
    for i in range(n - 1):
        if dirn[i] == "C" and plen[i] > 1000:
            w = [j for j in range(i, min(i + 6, n))
                 if dirn[j] == "C" and plen[j] > 1000 and t[j] - t[i] < 6]
            if len(w) >= 2:
                i_burst = i
                break
    # groesste Pre-Audio-Luecke (vor dem Burst) und groesste Server-Luecke (ab Burst)
    pre = sorted(((dt[k], k) for k in range(1, i_burst)), reverse=True)
    g_pre, k_pre = pre[0]
    post = sorted(((dt[k], k) for k in range(i_burst, n)), reverse=True)
    g_srv, k_srv = post[0]
    return {
        "i_syn": i_syn, "i_synack": i_synack, "i_chlo": i_chlo, "i_shlo": i_shlo,
        "i_burst": i_burst, "t_burst": t[i_burst],
        "g_pre": g_pre, "k_pre": k_pre,        # Index k_pre -> k_pre+1 ist die Luecke
        "g_srv": g_srv, "k_srv": k_srv,
        "t_synack": t[i_synack], "t_chlo": t[i_chlo], "t_shlo": t[i_shlo],
    }


# ---------------------------------------------------------------------------
# Zeichen-Helfer
# ---------------------------------------------------------------------------
YC, YS = 1.0, 0.0   # y-Spuren: Client oben, Server unten


def _draw_packets(ax, F, lo, hi, ms_pay=7.0, ms_ack=5.0):
    """Pakete als Punkte auf zwei Richtungs-Spuren. Voll=Payload, hohl=reines ACK."""
    t, dirn, plen = F["t"], F["dirn"], F["plen"]
    for i in range(F["n"]):
        if not (lo <= t[i] <= hi):
            continue
        y = YC if dirn[i] == "C" else YS
        col = C_CLIENT if dirn[i] == "C" else C_SERVER
        if plen[i] > 0:
            ax.plot(t[i], y, "o", color=col, ms=ms_pay, zorder=5)
        else:
            ax.plot(t[i], y, "o", mfc="white", mec=col, mew=1.3, ms=ms_ack, zorder=4)


def _phase_band(ax, x0, x1, color, label, y0=-0.70, y1=1.62, labely=1.66, fs=10.0):
    """Dezentes Phasen-Hintergrundband mit zentrierter Beschriftung darueber."""
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                           facecolor=color, edgecolor="none", alpha=0.9, zorder=0))
    ax.text((x0 + x1) / 2, labely, label, ha="center", va="bottom",
            fontsize=fs, color="#2a2a2a", linespacing=1.1)


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------
def plot_packet_timeline(provider):
    """Baut die entzerrte Paket-Level-Figur (A1-Zoom / A2-Vollachse / B-Stem).

    provider: 'azure_stt' | 'deepgram_stt'
    Rueckgabe: matplotlib.figure.Figure

    Eine Figur, drei vertikal grosszuegig getrennte Panels (Entwurf 3, Sieger).
    A2 ist UNGEBROCHEN-linear: der Client-Gap (Azure) ist echter Weissraum.
    """
    cfg = PROVIDERS[provider]
    F = _load_flow(os.path.join(PCAP_DIR, cfg["pcap"]))
    M = _milestones(F)
    has_gap = cfg["gap_kind"] == "client"

    # abgeleitete Zahlen (aus PCAP — nichts hartkodiert)
    tcp_ms = M["t_synack"]
    tls_ms = M["t_shlo"] - M["t_chlo"]
    t_chlo = M["t_chlo"]
    t_shlo = M["t_shlo"]
    t_burst = M["t_burst"]
    g_pre = M["g_pre"]
    g_srv = M["g_srv"]
    connect_ms = cfg["connect_ms"]
    # letztes Setup-Paket VOR der groessten Pre-Audio-Luecke (Milestone-abgeleitet,
    # ersetzt den frueheren harten Index F["t"][13] -> robust gegen neue Captures).
    t_setup_end = F["t"][M["k_pre"] - 1]

    # =====================================================================
    # Figur-Gerust: A1 (Handshake-Zoom) / A2 (Vollachse) / B (IAT-Stem)
    # =====================================================================
    fig = plt.figure(figsize=(13.0, 9.6))
    gs = fig.add_gridspec(
        3, 1, height_ratios=[0.62, 1.0, 1.15],
        hspace=0.66, left=0.085, right=0.975, top=0.885, bottom=0.085,
    )
    axZoom = fig.add_subplot(gs[0, 0])   # A1 Handshake-Zoom
    axFull = fig.add_subplot(gs[1, 0])   # A2 volle, ungebrochene Achse
    axStem = fig.add_subplot(gs[2, 0])   # B Inter-Arrival

    # gemeinsame Spuren-Kosmetik (Client oben, Server unten)
    for ax in (axZoom, axFull):
        ax.set_yticks([YS, YC])
        ax.set_yticklabels(["Server→Client", "Client→Server"], fontsize=10.5)
        ax.axhline(YC, color="#c4c4c4", lw=0.7, zorder=0)
        ax.axhline(YS, color="#c4c4c4", lw=0.7, zorder=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="x", labelsize=10)
    axZoom.set_ylim(-1.60, 1.80)   # mehr Luft unten fuer die nach unten gesetzten Event-Labels
    axFull.set_ylim(-1.25, 2.05)

    # =================== (A1) Handshake-Zoom: TCP vs. TLS getrennt =========
    z0, z1 = cfg["zoom_xlim"]
    axZoom.set_xlim(z0, z1)
    tls_lo = tcp_ms
    tls_hi = t_shlo + 0.5 * tls_ms
    _phase_band(axZoom, z0, tls_lo, C_TCP, f"TCP-Handshake · {tcp_ms:.0f} ms (1 RTT)",
                y0=-1.45, y1=1.45, labely=1.50, fs=10.5)
    _phase_band(axZoom, tls_lo, tls_hi, C_TLS, f"TLS-1.3 · {tls_ms:.0f} ms (1 RTT)",
                y0=-1.45, y1=1.45, labely=1.50, fs=10.5)
    _phase_band(axZoom, tls_hi, z1, C_WS, "WS-Upgrade / Session-Init",
                y0=-1.45, y1=1.45, labely=1.50, fs=10.5)
    _draw_packets(axZoom, F, z0, z1, ms_pay=8.0, ms_ack=5.5)
    # Event-Labels: SYN-ACK und ClientHello liegen eng beieinander -> horizontaler
    # Versatz + Leader-Linie (Hybrid-Feinschliff aus Entwurf 1). dx in x-Einheiten.
    span = z1 - z0
    dx = span * 0.055
    ev = [(0.0,     "SYN",         0.0),
          (tcp_ms,  "SYN-ACK",    -dx),    # leicht nach links
          (t_chlo,  "ClientHello", dx),    # leicht nach rechts
          (t_shlo,  "ServerHello", 0.0)]
    for x, lab, off in ev:
        axZoom.axvline(x, color="#777", lw=0.8, ls=":", zorder=1)
        axZoom.annotate(lab, xy=(x, YS), xytext=(x + off, -1.52),
                        rotation=90, ha="center", va="bottom",
                        fontsize=9.2, color="#333",
                        arrowprops=dict(arrowstyle="-", color="#999", lw=0.7))
    # connect_ms (App sendebereit)
    axZoom.axvline(connect_ms, color=C_CONNECT, lw=2.0, ls="--", zorder=3)
    if has_gap:
        axZoom.text(connect_ms + span * 0.02, 0.50,
                    f"connect_ms\n≈ {connect_ms:.0f} ms\n(App sendebereit)",
                    fontsize=9.6, color=C_CONNECT, va="center", ha="left", fontweight="bold")
    else:
        # Deepgram: connect_ms (425) liegt weit rechts -> Label nach links, knapp
        axZoom.text(connect_ms - span * 0.02, 0.50,
                    f"connect_ms\n≈ {connect_ms:.0f} ms",
                    fontsize=9.6, color=C_CONNECT, va="center", ha="right", fontweight="bold")
    axZoom.set_xticks(cfg["zoom_xticks"])
    axZoom.set_xlabel("Zeit seit SYN [ms] — Handshake-Zoom (linear, Ausschnitt aus A2)",
                      fontsize=10.5)
    axZoom.set_title("(A1)  Verbindungsaufbau: TCP- und TLS-Handshake getrennt (je ~1 RTT)",
                     fontsize=11.5, loc="left", fontweight="bold", pad=10)

    # =================== (A2) Volle, UNGEBROCHENE lineare Achse ============
    f1 = t_burst * 1.06
    f0 = -f1 * 0.018
    axFull.set_xlim(f0, f1)
    if has_gap:
        # Azure: Setup-Block, dann LEERE Client-Sendeluecke, dann Audio.
        _phase_band(axFull, f0, t_setup_end, C_SETUP, "Setup\n(TCP+TLS+WS)",
                    labely=1.66, fs=10.0)
        _phase_band(axFull, t_setup_end, t_burst, C_GAPBAND,
                    "Client-Sendelücke — keine Datenpakete", labely=1.66, fs=10.5)
        _phase_band(axFull, t_burst, f1, C_AUDIO, "Audio-Upload\n(Burst)",
                    labely=1.66, fs=10.0)
    else:
        # Deepgram: lueckenloser RTT-Aufbau — TCP-RTT, TLS-RTT, kurzes Setup, Audio.
        # Die Luecken zwischen den Phasen SIND die RTTs (kein leerer Client-Wait).
        _phase_band(axFull, f0, tcp_ms, C_TCP, "TCP\n(1 RTT)", labely=1.66, fs=9.5)
        _phase_band(axFull, tcp_ms, t_shlo, C_TLS, "TLS-1.3\n(1 RTT)", labely=1.66, fs=9.5)
        _phase_band(axFull, t_shlo, t_burst, C_WS, "WS-Upgrade /\nSession-Init",
                    labely=1.66, fs=9.5)
        _phase_band(axFull, t_burst, f1, C_AUDIO, "Audio-Upload\n(Burst)",
                    labely=1.66, fs=9.5)
    _draw_packets(axFull, F, f0, f1, ms_pay=6.5, ms_ack=4.5)
    # connect_ms- und app_data_start-Marker. Liegen die beiden Linien eng beieinander
    # (Deepgram: 425 vs. 478 ms, kein Client-Gap), werden die Labels vertikal gestapelt,
    # damit sie nicht ineinanderlaufen; bei grossem Abstand (Azure) je aussen.
    axFull.axvline(connect_ms, color=C_CONNECT, lw=1.8, ls="--", zorder=3)
    axFull.axvline(t_burst, color=C_CLIENT, lw=1.8, ls="--", zorder=3)
    if (t_burst - connect_ms) < f1 * 0.18:
        # eng -> stapeln: connect_ms tiefer, app_data_start hoeher; beide nach links
        axFull.text(connect_ms - f1 * 0.012, -1.16,
                    f"connect_ms ≈ {connect_ms:.0f} ms (sendebereit)",
                    fontsize=9.2, color=C_CONNECT, va="bottom", ha="right", fontweight="bold")
        axFull.text(t_burst + f1 * 0.012, -0.95,
                    f"app_data_start ≈ {t_burst:.0f} ms",
                    fontsize=9.2, color=C_CLIENT, va="bottom", ha="left", fontweight="bold")
    else:
        axFull.text(connect_ms + f1 * 0.012, -0.95,
                    f"connect_ms ≈ {connect_ms:.0f} ms (sendebereit)",
                    fontsize=9.2, color=C_CONNECT, va="bottom", ha="left", fontweight="bold")
        axFull.text(t_burst - f1 * 0.012, -0.95, f"app_data_start ≈ {t_burst:.0f} ms",
                    fontsize=9.2, color=C_CLIENT, va="bottom", ha="right", fontweight="bold")
    if has_gap:
        # Doppelpfeil ueber der leeren Luecke + Kernzahl. Der Weissraum SELBST traegt die Aussage.
        yarr = 0.96
        axFull.annotate("", xy=(t_burst, yarr), xytext=(t_setup_end, yarr),
                        arrowprops=dict(arrowstyle="<->", color=C_GAP_CLIENT, lw=2.2))
        axFull.text((t_setup_end + t_burst) / 2, yarr + 0.14,
                    f"~{g_pre:.0f} ms — CLIENT wartet (kein Server-Processing)",
                    ha="center", va="bottom", fontsize=11.0, color=C_GAP_CLIENT, fontweight="bold")
        a2_title = ("(A2)  Sendebereit nach ~{:.0f} ms, Audio erst nach ~{:.0f} ms — "
                    "die Lücke ist leerer Raum (Client-Wartezeit)").format(connect_ms, t_burst)
    else:
        a2_title = ("(A2)  Lückenloser, RTT-dominierter Aufbau — "
                    "jede Pause ist eine RTT, KEINE Client-Wartezeit")
    axFull.set_xticks([x for x in cfg["full_xticks"] if f0 <= x <= f1])
    axFull.set_xlabel("Zeit seit SYN [ms] — gesamte Verbindung bis Audio (linear, ungebrochen)",
                      fontsize=10.5)
    axFull.set_title(a2_title, fontsize=11.5, loc="left", fontweight="bold", pad=8)

    # =================== (B) Inter-Arrival-Time je Paket (log) =============
    valid = ~np.isnan(F["dt"])
    xi = np.arange(F["n"])[valid]
    yi = F["dt"][valid]
    cols = [C_CLIENT if d == "C" else C_SERVER for d in F["dirn"][valid]]
    ml, sl, bl = axStem.stem(xi, yi, basefmt=" ")
    plt.setp(sl, linewidth=1.0, color="#d2d2d2")
    ml.set_visible(False)
    axStem.scatter(xi, yi, s=34, c=cols, zorder=3, edgecolors="white", linewidths=0.4)
    axStem.set_yscale("log")
    axStem.set_ylim(0.3, g_srv * 9.0)   # Headroom fuer Ausreisser-Labels
    axStem.set_xlim(xi.min() - 3, xi.max() + 3)
    axStem.set_xlabel("Paket-Index (chronologisch, ab SYN)", fontsize=10.5)
    axStem.set_ylabel("Inter-Arrival Δt zum\nVorpaket [ms, log]", fontsize=10.5)
    axStem.grid(axis="y", ls=":", lw=0.7, alpha=0.6, which="both")
    axStem.tick_params(labelsize=10)
    # 1-RTT-Referenzlinie
    axStem.axhline(tcp_ms, color="#5a8f4f", ls="--", lw=1.0, alpha=0.85)
    axStem.text(xi.max(), tcp_ms * 1.16, f"1 RTT ≈ {tcp_ms:.0f} ms",
                ha="right", va="bottom", fontsize=9.5, color="#3a6f30")

    nmax = xi.max()

    def _mark(k_gap, label, color, tx, ty, ha):
        yv = F["dt"][k_gap]
        axStem.scatter([k_gap], [yv], s=240, facecolors="none",
                       edgecolors=color, linewidths=2.2, zorder=4)
        axStem.annotate(f"{label}\nΔt ≈ {yv:.0f} ms",
                        xy=(k_gap, yv), xytext=(tx, ty),
                        ha=ha, va="center", fontsize=10.0, color=color, fontweight="bold",
                        arrowprops=dict(arrowstyle="-", color=color, lw=1.0))

    if has_gap:
        _mark(M["k_pre"], "Client-Sendelücke\n(sendebereit ~49 ms,\nAudio erst ~446 ms)",
              C_GAP_CLIENT, tx=M["k_pre"] + nmax * 0.16, ty=g_pre * 4.0, ha="left")
        _mark(M["k_srv"], "Server-Processing\n(Warten aufs Transkript)",
              C_GAP_SERVER, tx=M["k_srv"] - nmax * 0.05, ty=g_srv * 0.26, ha="right")
    else:
        _mark(M["k_srv"], "Server-Processing\n(Warten aufs Transkript)",
              C_GAP_SERVER, tx=M["k_srv"] - nmax * 0.06, ty=g_srv * 0.30, ha="right")

    axStem.text(0.015, 0.06,
                "Setup- und Burst-Pakete: Δt im Sub-ms- bis RTT-Bereich",
                transform=axStem.transAxes, ha="left", va="bottom",
                fontsize=9.5, color="#666", style="italic")
    stem_title = ("(B)  Inter-Arrival-Time je Paket (log): "
                  + ("Client-Sendelücke und Server-Processing als die zwei Ausreisser"
                     if has_gap else
                     "nur Server-Processing als Ausreisser — KEINE Client-Sendelücke"))
    axStem.set_title(stem_title, fontsize=11.5, loc="left", fontweight="bold", pad=8)

    # =================== Legende (Farbe = Richtung) =======================
    leg = [
        Line2D([0], [0], marker="o", color="w", mfc=C_CLIENT, ms=9, label="Client→Server (Payload)"),
        Line2D([0], [0], marker="o", color="w", mfc="white", mec=C_CLIENT, mew=1.3, ms=8, label="reines ACK"),
        Line2D([0], [0], marker="o", color="w", mfc=C_SERVER, ms=9, label="Server→Client (Payload)"),
        Line2D([0], [0], color=C_CONNECT, ls="--", lw=2.0, label=f"connect_ms ({connect_ms:.0f} ms)"),
    ]
    fig.legend(handles=leg, loc="lower center", ncol=4, fontsize=10.0,
               frameon=False, bbox_to_anchor=(0.5, 0.012))

    # =================== Titel (Aussage + Zahl) + Untertitel ==============
    if has_gap:
        title = (f"{cfg['label']} auf Paket-Ebene: 3-RTT-Handshake in ~{connect_ms:.0f} ms, "
                 f"dann ~{g_pre:.0f} ms Client-Sendelücke vor dem Audio-Upload")
    else:
        title = (f"{cfg['label']} auf Paket-Ebene: RTT-dominierter Aufbau "
                 f"(TCP {tcp_ms:.0f} ms, TLS {tls_ms:.0f} ms je 1 RTT) — "
                 f"KEINE Client-Sendelücke")
    fig.suptitle(title, fontsize=14.0, fontweight="bold", y=0.975)
    fig.text(0.5, 0.928,
             f"Quelle: {cfg['pcap']} ({cfg['region']}) · n=1 Mitschnitt "
             f"(strukturelle Illustration, keine Verteilung) · "
             f"Farbe = Paketrichtung, nicht Provider · Vantage Point AWS eu-central-1",
             ha="center", fontsize=9.0, color="#555")
    return fig


# ---------------------------------------------------------------------------
def main():
    out_png = "analysis/figures/02_pcap/png"
    out_pdf = "analysis/figures/02_pcap/pdf"
    os.makedirs(out_png, exist_ok=True)
    os.makedirs(out_pdf, exist_ok=True)
    for provider in ("azure_stt", "deepgram_stt"):
        fig = plot_packet_timeline(provider)
        base = f"02_packet_timeline_{provider}"
        fig.savefig(os.path.join(out_png, base + ".png"), dpi=120, bbox_inches="tight")
        fig.savefig(os.path.join(out_pdf, base + ".pdf"), bbox_inches="tight")
        plt.close(fig)
        print(f"saved {base}.png/.pdf")


if __name__ == "__main__":
    main()
