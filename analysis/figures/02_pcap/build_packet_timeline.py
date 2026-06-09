#!/usr/bin/env python
"""
Paket-Level-Timeline (Layer 2) fuer STT-Provider — Hybrid-Design.

Sieger-Design (Juror-Urteil 2026-06-09): Entwurf 2 (Broken-Axis-Timeline,
TCP/TLS getrennt) als oberer Block + Inter-Arrival-Stem (Entwurf 3) als
unterer Block. Erfuellt die drei Prof-Vorgaben sichtbar UND quantitativ:

  1) TCP- und TLS-Handshake GETRENNT erkennbar (Panel A spreizt 0..X ms linear,
     zwei farbcodierte Baender mit eigenen Event-Markern).
  2) Inter-Arrival-Time der Pakete sichtbar UND auswertbar (Panel B: Δt je
     Paket auf Log-Achse; die langen Luecken werden zu umkreisten Ausreissern).
  3) Betrachtung ab SYN-ACK / paketweise (zwei Richtungs-Spuren, jedes Paket
     ein eigener Punkt, SYN-ACK explizit markiert).

Methodische Wahrheit (Azure): die ~358 ms zwischen Setup-Ende (~87 ms) und
Audio-Upload (~446 ms) sind CLIENT-Wartezeit, KEIN Server-Processing
(App ist bei connect_ms ~49 ms sendebereit). app_data_start (446 ms) != connect_ms (49 ms).
Das echte Server-Processing (~776 ms) erscheint separat im IAT-Stem.

Deepgram-Kontrast: RTT-dominierter Aufbau (TCP ~148, TLS ~150 ms = je 1 RTT),
KEINE Client-Sendeluecke — die groesste Pre-Audio-Luecke ist exakt 1 RTT
(der TLS-Handshake selbst). Beleg fuer „Engine/Geografie schlaegt Verarbeitung
NICHT": Azure verschenkt seinen RTT-Vorteil an eine Client-Wartezeit.

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
# Handshake-RTT-Klasse und die Panel-Fenster der gebrochenen x-Achse.
# Alle Zeit-/Luecken-Zahlen werden aus dem PCAP SELBST berechnet (s.u.),
# hier stehen nur Mess-Metadaten + Layout-Fenster.
# ---------------------------------------------------------------------------
PCAP_DIR = "data/layer2"

PROVIDERS = {
    "azure_stt": {
        "pcap": "capture_azure_stt_20260608_1627.pcap",
        "label": "Azure STT",
        "region": "eu-central-1 → Italy North (EU)",
        "connect_ms": 49.5,          # Layer-3-Median (Juni-Kampagne)
        # Panel-Fenster: A=Handshake-Zoom, B=Client-Sendeluecke (komprimiert), C=Audio-Burst
        "winA": (-4, 95),            # Handshake-Detail linear
        "winB": (90, 446),           # grosse Luecke, komprimiert
        "winC": (444, 470),          # Audio-Burst linear
        "panel_ratios": [3.2, 1.6, 2.2],
        "xticksA": [0, 20, 40, 60, 80],
        "xticksB": [150, 250, 350],
        "xticksC": [445, 455, 465],
        "gap_kind": "client",        # die markante Pre-Audio-Luecke ist Client-Wartezeit
    },
    "deepgram_stt": {
        "pcap": "capture_deepgram_stt_20260608_1627.pcap",
        "label": "Deepgram STT",
        "region": "eu-central-1 → USA / Anycast",
        "connect_ms": 425.0,         # Layer-3-Median (Juni-Kampagne)
        "winA": (-15, 465),          # Handshake-Detail linear (RTT-dominiert, breiter); endet vor dem Burst
        "winB": None,                # KEINE Client-Sendeluecke -> kein Kompressions-Panel
        "winC": (470, 660),          # Audio-Burst linear
        "panel_ratios": [4.0, 2.4],
        "xticksA": [0, 150, 300, 450],
        "xticksB": None,
        "xticksC": [480, 540, 600, 660],
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
C_GAPBAND = "#f3e1e4"
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


def _draw_packets(ax, F, lo, hi):
    """Pakete als Punkte auf zwei Richtungs-Spuren. Voll=Payload, hohl=reines ACK."""
    t, dirn, plen = F["t"], F["dirn"], F["plen"]
    for i in range(F["n"]):
        if not (lo <= t[i] <= hi):
            continue
        y = YC if dirn[i] == "C" else YS
        col = C_CLIENT if dirn[i] == "C" else C_SERVER
        if plen[i] > 0:
            ax.plot(t[i], y, "o", color=col, ms=6, zorder=5)
        else:
            ax.plot(t[i], y, "o", mfc="white", mec=col, mew=1.2, ms=4.5, zorder=4)


def _band(ax, x0, x1, color, label, ymin=-0.62, ymax=1.62):
    ax.add_patch(Rectangle((x0, ymin), x1 - x0, ymax - ymin,
                           facecolor=color, edgecolor="none", alpha=0.85, zorder=0))
    ax.text((x0 + x1) / 2, 1.66, label, ha="center", va="bottom",
            fontsize=8.4, color="#333", linespacing=1.05)


def _break_marks(axl, axr):
    """Diagonale //-Bruchmarken zwischen zwei Panels einer gebrochenen Achse."""
    d = 0.013
    for ax, x in ((axl, 1.0), (axr, 0.0)):
        kw = dict(transform=ax.transAxes, color="#333", clip_on=False, lw=1.1)
        ax.plot((x - d, x + d), (-d, +d), **kw)
        ax.plot((x - d, x + d), (1 - d, 1 + d), **kw)
    axl.spines["right"].set_visible(False)
    axr.spines["left"].set_visible(False)


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------
def plot_packet_timeline(provider):
    """Baut die Paket-Level-Timeline-Figur fuer einen STT-Provider.

    provider: 'azure_stt' | 'deepgram_stt'
    Rueckgabe: matplotlib.figure.Figure
    """
    cfg = PROVIDERS[provider]
    F = _load_flow(os.path.join(PCAP_DIR, cfg["pcap"]))
    M = _milestones(F)
    t = F["t"]
    has_gap = cfg["winB"] is not None

    # abgeleitete Zahlen (aus PCAP)
    tcp_ms = M["t_synack"]
    tls_ms = M["t_shlo"] - M["t_chlo"]
    t_burst = M["t_burst"]
    g_pre = M["g_pre"]
    g_srv = M["g_srv"]
    connect_ms = cfg["connect_ms"]

    # =====================================================================
    # Figur-Gerust: oben Timeline (broken axis), unten IAT-Stem
    # =====================================================================
    fig = plt.figure(figsize=(12.4, 7.6))
    n_top = len(cfg["panel_ratios"])
    gs = fig.add_gridspec(
        2, n_top, height_ratios=[1.0, 1.05],
        width_ratios=cfg["panel_ratios"],
        hspace=0.46, wspace=0.07,
    )
    top_axes = [fig.add_subplot(gs[0, j]) for j in range(n_top)]
    axB_stem = fig.add_subplot(gs[1, :])

    for ax in top_axes:
        ax.set_ylim(-0.92, 1.95)
        ax.set_yticks([YS, YC])
        ax.set_yticklabels([])
        ax.axhline(YC, color="#bbb", lw=0.6, zorder=0)
        ax.axhline(YS, color="#bbb", lw=0.6, zorder=0)
        ax.spines["top"].set_visible(False)
        ax.tick_params(axis="x", labelsize=8)
    top_axes[0].set_yticklabels(["Server→Client", "Client→Server"], fontsize=8.6)

    # ---------------- Panel A: Handshake-Detail (TCP/TLS getrennt) ---------
    axA = top_axes[0]
    a0, a1 = cfg["winA"]
    axA.set_xlim(a0, a1)
    # Bandgrenzen: TCP bis kurz vor ClientHello, TLS bis kurz nach ServerHello, WS bis Panelende
    tls_lo = M["t_synack"]
    tls_hi = M["t_shlo"] + max(8, 0.4 * (M["t_shlo"] - M["t_chlo"]))
    _band(axA, a0, tls_lo, C_TCP, "TCP-Handshake\n(1 RTT)")
    _band(axA, tls_lo, tls_hi, C_TLS, "TLS-1.3-Handshake\n(1 RTT)")
    _band(axA, tls_hi, a1, C_WS, "WS-Upgrade /\nSession-Init")
    _draw_packets(axA, F, a0, a1)
    # Schluessel-Events: gestrichelte Linie + gedrehtes Label
    ev = [(0.0, "SYN", YC), (M["t_synack"], "SYN-ACK", YS),
          (M["t_chlo"], "ClientHello", YC), (M["t_shlo"], "ServerHello", YS)]
    for x, lab, y in ev:
        axA.axvline(x, color="#666", lw=0.7, ls=":", zorder=1)
        axA.annotate(lab, xy=(x, y), xytext=(x, 1.34 if y == YC else -0.34),
                     rotation=90, ha="center", va="bottom" if y == YC else "top",
                     fontsize=7.4, color="#333",
                     arrowprops=dict(arrowstyle="-", color="#999", lw=0.6))
    # connect_ms (App sendebereit) — gruene Linie, klar von app_data_start getrennt.
    # Label-Seite je nach Position im Panel waehlen, damit es nicht am Rand abschneidet.
    axA.axvline(connect_ms, color=C_CONNECT, lw=1.6, ls="--", zorder=3)
    if connect_ms > a0 + 0.72 * (a1 - a0):   # nahe rechtem Rand -> Label nach links
        axA.text(connect_ms - (a1 - a0) * 0.015, 0.50,
                 f"connect_ms\n≈ {connect_ms:.0f} ms\n(App sendebereit)",
                 fontsize=7.8, color=C_CONNECT, va="center", ha="right", fontweight="bold")
    else:
        axA.text(connect_ms + (a1 - a0) * 0.015, 0.50,
                 f"connect_ms\n≈ {connect_ms:.0f} ms\n(App sendebereit)",
                 fontsize=7.8, color=C_CONNECT, va="center", ha="left", fontweight="bold")
    # IAT-Beispiel: SYN -> SYN-ACK = 1 RTT (Vorgabe 2, quantitativ)
    axA.annotate("", xy=(M["t_synack"], -0.66), xytext=(0.0, -0.66),
                 arrowprops=dict(arrowstyle="<->", color="#777", lw=0.9))
    axA.text(M["t_synack"] / 2, -0.74,
             f"IAT Δ {tcp_ms:.1f} ms  (= 1 RTT)",
             ha="center", va="top", fontsize=7.4, color="#555")
    axA.set_xlabel("Zeit seit SYN [ms]  —  Handshake-Detail (linear)", fontsize=8.6)
    axA.set_xticks(cfg["xticksA"])
    axA.set_title("(A)  Verbindungsaufbau: TCP- und TLS-Handshake getrennt",
                  fontsize=9.6, loc="left", fontweight="bold", pad=6)

    # ---------------- Panel B: Client-Sendeluecke (nur Azure) --------------
    if has_gap:
        axB = top_axes[1]
        b0, b1 = cfg["winB"]
        axB.set_xlim(b0, b1)
        _band(axB, b0, b1, C_GAPBAND, "Client-Sendelücke\n(keine Pakete)")
        _draw_packets(axB, F, b0, b1)
        # Kein Doppelpfeil: dessen Endpunkte (87 / 445 ms) liegen ausserhalb des komprimierten
        # Panel-Fensters -> erschiene als verirrtes Symbol. Der leere Panel + Text tragen die Aussage.
        xmid = (b0 + b1) / 2  # in der sichtbaren Panel-Mitte zentrieren (nicht am Daten-Midpoint -> sonst Clipping)
        axB.text(xmid, 0.70,
                 f"~{g_pre:.0f} ms\nCLIENT wartet",
                 ha="center", va="bottom", fontsize=9.2, color=C_GAP_CLIENT, fontweight="bold")
        axB.text(xmid, 0.18,
                 "App bei ~49 ms sendebereit,\nsendet Audio aber erst bei ~446 ms\n→ KEIN Server-Processing",
                 ha="center", va="top", fontsize=7.2, color="#7a2733", style="italic")
        axB.set_xlabel("(x-Achse komprimiert)", fontsize=8.6, color="#444")
        axB.set_xticks(cfg["xticksB"])
        i_c, i_burst_panel = 1, 2
    else:
        i_c, i_burst_panel = None, 1

    # ---------------- Panel C: Audio-Upload-Burst -------------------------
    axC = top_axes[i_burst_panel]
    c0, c1 = cfg["winC"]
    axC.set_xlim(c0, c1)
    _band(axC, c0, c1, C_AUDIO, "Audio-Upload\n(Burst)")
    _draw_packets(axC, F, c0, c1)
    axC.axvline(t_burst, color=C_CLIENT, lw=1.3, ls="--", zorder=3)
    axC.text(t_burst + (c1 - c0) * 0.02, -0.58,
             f"app_data_start\n{t_burst:.0f} ms",
             fontsize=7.4, color=C_CLIENT, va="bottom", fontweight="bold")
    axC.text((c0 + c1) / 2, 1.40, "dichte Client-Pakete\n(IAT meist < 0,1 ms)",
             ha="center", va="top", fontsize=7.6, color=C_CLIENT)
    axC.set_xlabel("Zeit seit SYN [ms]  —  Audio-Burst (linear)", fontsize=8.6)
    axC.set_xticks(cfg["xticksC"])

    # ---------------- Broken-Axis-Bruchmarken ------------------------------
    for j in range(n_top - 1):
        _break_marks(top_axes[j], top_axes[j + 1])

    # ---------------- Panel B (unten): Inter-Arrival-Stem ------------------
    valid = ~np.isnan(F["dt"])
    xi = np.arange(F["n"])[valid]
    yi = F["dt"][valid]
    cols = [C_CLIENT if d == "C" else C_SERVER for d in F["dirn"][valid]]
    ml, sl, bl = axB_stem.stem(xi, yi, basefmt=" ")
    plt.setp(sl, linewidth=0.9, color="#cfcfcf")
    ml.set_visible(False)
    axB_stem.scatter(xi, yi, s=26, c=cols, zorder=3, edgecolors="white", linewidths=0.3)
    axB_stem.set_yscale("log")
    axB_stem.set_ylim(0.3, max(g_srv, g_pre) * 6.0)   # Headroom fuer Ausreisser-Labels
    axB_stem.set_xlim(xi.min() - 2, xi.max() + 2)
    axB_stem.set_xlabel("Paket-Index (chronologisch, ab SYN)", fontsize=9.2)
    axB_stem.set_ylabel("Inter-Arrival Δt\nzum Vorpaket [ms, log]", fontsize=9.2)
    axB_stem.grid(axis="y", ls=":", lw=0.6, alpha=0.6, which="both")
    # 1-RTT-Referenzlinie
    axB_stem.axhline(tcp_ms, color="#5a8f4f", ls="--", lw=0.9, alpha=0.85)
    axB_stem.text(xi.max(), tcp_ms * 1.12, f"1 RTT ≈ {tcp_ms:.0f} ms",
                  ha="right", va="bottom", fontsize=7.8, color="#3a6f30")

    # Ausreisser markieren: Kreis am Datenpunkt + Label per Leader-Linie seitlich,
    # damit nichts den Panel-Titel beruehrt.
    nmax = xi.max()

    def _mark(k_gap, label, color, tx, ty, ha):
        yv = F["dt"][k_gap]
        axB_stem.scatter([k_gap], [yv], s=170, facecolors="none",
                         edgecolors=color, linewidths=1.9, zorder=4)
        axB_stem.annotate(f"{label}\nΔt ≈ {yv:.0f} ms",
                          xy=(k_gap, yv), xytext=(tx, ty),
                          ha=ha, va="center", fontsize=8.0, color=color, fontweight="bold",
                          arrowprops=dict(arrowstyle="-", color=color, lw=0.8))

    if has_gap:
        # Azure: Client-Luecke links unterhalb des Punkts, Server-Luecke rechts unterhalb
        _mark(M["k_pre"], "Client-Sendelücke\n(sendebereit ~49 ms,\nAudio erst ~446 ms)",
              C_GAP_CLIENT, tx=M["k_pre"] + nmax * 0.18, ty=g_pre * 3.2, ha="left")
        _mark(M["k_srv"], "Server-Processing\n(Warten aufs Transkript)",
              C_GAP_SERVER, tx=M["k_srv"] - nmax * 0.04, ty=g_srv * 0.30, ha="right")
    else:
        # Deepgram: nur Server-Processing, Label links neben dem Punkt
        _mark(M["k_srv"], "Server-Processing\n(Warten aufs Transkript)",
              C_GAP_SERVER, tx=M["k_srv"] - nmax * 0.06, ty=g_srv * 0.32, ha="right")

    axB_stem.text(0.015, 0.04,
                  "Setup-/Burst-Pakete: Δt im Sub-ms- bis RTT-Bereich",
                  transform=axB_stem.transAxes,
                  ha="left", va="bottom", fontsize=7.8, color="#666", style="italic")
    stem_title = ("(B)  Inter-Arrival-Time je Paket (log): "
                  + ("Client-Sendelücke und Server-Processing als die zwei Ausreisser"
                     if has_gap else
                     "nur Server-Processing als Ausreisser — KEINE Client-Sendelücke"))
    axB_stem.set_title(stem_title, fontsize=9.6, loc="left", fontweight="bold", pad=6)

    # ---------------- Legende (Farbe = Richtung) ---------------------------
    leg = [
        Line2D([0], [0], marker="o", color="w", mfc=C_CLIENT, ms=7, label="Client→Server (Payload)"),
        Line2D([0], [0], marker="o", color="w", mfc="white", mec=C_CLIENT, mew=1.2, ms=6, label="reines ACK"),
        Line2D([0], [0], marker="o", color="w", mfc=C_SERVER, ms=7, label="Server→Client (Payload)"),
        Line2D([0], [0], color=C_CONNECT, ls="--", lw=1.5, label=f"connect_ms ({connect_ms:.0f} ms)"),
    ]
    fig.legend(handles=leg, loc="lower center", ncol=4, fontsize=8.4,
               frameon=False, bbox_to_anchor=(0.5, -0.005))

    # ---------------- Titel (Aussage + Zahl) + Untertitel ------------------
    if has_gap:
        title = (f"{cfg['label']} auf Paket-Ebene: 3-RTT-Handshake in {connect_ms:.0f} ms, "
                 f"dann ~{g_pre:.0f} ms Client-Sendelücke vor dem Audio-Upload")
    else:
        title = (f"{cfg['label']} auf Paket-Ebene: RTT-dominierter Aufbau "
                 f"(TCP {tcp_ms:.0f} ms, TLS {tls_ms:.0f} ms je 1 RTT) — "
                 f"KEINE Client-Sendelücke")
    fig.suptitle(title, fontsize=12.0, fontweight="bold", y=0.995)
    fig.text(0.5, 0.945,
             f"Quelle: {cfg['pcap']} ({cfg['region']}) · gebrochene x-Achse · "
             f"n=1 Mitschnitt (strukturelle Illustration, keine Verteilung) · "
             f"Farbe = Paketrichtung, nicht Provider · Vantage Point AWS eu-central-1",
             ha="center", fontsize=7.9, color="#555")

    fig.subplots_adjust(top=0.90, bottom=0.075, left=0.085, right=0.975)
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
        fig.savefig(os.path.join(out_png, base + ".png"), dpi=110, bbox_inches="tight")
        fig.savefig(os.path.join(out_pdf, base + ".pdf"), bbox_inches="tight")
        plt.close(fig)
        print(f"saved {base}.png/.pdf")


if __name__ == "__main__":
    main()
