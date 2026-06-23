# -*- coding: utf-8 -*-
"""
Folien fuer die Konsultation mit Prof. Waehlisch (2026-06-23).
Erzeugt zwei PDFs direkt mit reportlab (kein LaTeX/LibreOffice noetig):
  - folien_konsultation.pdf  : Praesentationsdeck (Anker-Stichpunkte, kein Fliesstext)
  - folien_sprechzettel.pdf  : Lern-/Sprechzettel (Anker + 'Sprecher:'-Satz je Folie)

Prinzipien: Sprecher-Stuetze statt Dokument · Inhaltsverzeichnis + Abschnitts-Trenner ·
nicht-blaue Palette (Warm Graphite & Amber) · Setup als Schwerpunkt · neutrale, praesentierbare
Formulierungen (keine internen Codes/Pfade/Meta-Notizen auf den Folien).
"""
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Frame, Paragraph, Spacer, Table, TableStyle, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import re, os

# ---------------------------------------------------------------- Geometrie (16:9)
PAGE_W, PAGE_H = 960, 540
M = 56
BAND_H = 84
BAND_BOTTOM = PAGE_H - BAND_H
CONTENT_TOP = BAND_BOTTOM - 16
FOOT_RULE_Y = 48
CONTENT_Y = 58
CONTENT_W = PAGE_W - 2 * M
CONTENT_H = CONTENT_TOP - CONTENT_Y

# ---------------------------------------------------------------- Palette: Warm Graphite & Amber
PRIMARY = HexColor("#2B2A28")
ACCENT  = HexColor("#C77A30")
INK     = HexColor("#23211E")
MUTE    = HexColor("#6E675E")
LIGHT   = HexColor("#F4F0EA")
PANEL   = HexColor("#E7E0D5")
SAND    = HexColor("#C9A98A")
RULE    = HexColor("#D8CFC1")
FAST    = HexColor("#4F7D5A")
MID     = HexColor("#C77A30")
SLOW    = HexColor("#B04A36")
NEGBG   = HexColor("#F6E8E1")
NEGBORD = HexColor("#B04A36")
FOOTINK = HexColor("#4A453E")

DECK_FOOT = "Bachelorarbeit · Latenzmessung kommerzieller Cloud-AI-APIs · A. Rusik · TU Dresden"

# ---------------------------------------------------------------- Markup / Styles
def md(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)

def style(name, size, leading=None, color=INK, bold=False, space=5, left=0,
          bullet=0, align=TA_LEFT):
    return ParagraphStyle(
        name, fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size, leading=leading or size + 4, textColor=color,
        spaceAfter=space, leftIndent=left, bulletIndent=bullet, alignment=align)

S_ANCHOR  = style("anchor", 15, 24, space=7, left=17, bullet=2)
S_ANCHOR_S = style("anchorS", 12.5, 18, space=4, left=17, bullet=2)
S_LEAD    = style("lead", 15, 20, color=PRIMARY, bold=True, space=8)
S_FOOT    = style("foot", 10, 14, color=FOOTINK, space=2)
S_CELLB   = style("cellb", 11, 14, space=0, bold=True, color=PRIMARY)

def anchor(t, s=S_ANCHOR):
    return Paragraph(md(t), s, bulletText="▪")

def frame(c, flow, x=M, y=CONTENT_Y, w=CONTENT_W, h=CONTENT_H):
    Frame(x, y, w, h, leftPadding=0, rightPadding=0, topPadding=0,
          bottomPadding=0, showBoundary=0).addFromList(flow, c)

def measure(flow):
    h = 0
    for f in flow:
        if isinstance(f, Spacer):
            h += f.height
        else:
            try:
                _, fh = f.wrap(CONTENT_W, CONTENT_H)
            except Exception:
                fh = 0
            h += fh
    return h

# ---------------------------------------------------------------- Master
def master(c, kicker, title, idx, total, backup=False):
    c.setFillColor(PRIMARY); c.rect(0, BAND_BOTTOM, PAGE_W, BAND_H, fill=1, stroke=0)
    c.setFillColor(ACCENT); c.rect(0, BAND_BOTTOM - 3, PAGE_W, 3, fill=1, stroke=0)
    c.setFillColor(SAND); c.setFont("Helvetica-Bold", 10.5)
    c.drawString(M, BAND_BOTTOM + 48, kicker.upper())
    c.setFillColor(white); c.setFont("Helvetica-Bold", 22)
    c.drawString(M, BAND_BOTTOM + 17, title)
    if backup:
        c.setFillColor(ACCENT); c.setFont("Helvetica-Bold", 10.5)
        c.drawRightString(PAGE_W - M, BAND_BOTTOM + 50, "BACKUP")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(MUTE)
    c.drawRightString(PAGE_W - M, 30, f"{idx} / {total}")

# ---------------------------------------------------------------- Tabellen
def table(data, colw, fs=10.3, align=None, extra=None, header=True):
    t = Table(data, colWidths=colw)
    cmds = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
            ("FONTSIZE", (0, 0), (-1, -1), fs), ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("TEXTCOLOR", (0, 0), (-1, -1), INK),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE)]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), PRIMARY), ("TEXTCOLOR", (0, 0), (-1, 0), white),
                 ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                 ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT])]
    if align:
        for col, a in align.items():
            cmds.append(("ALIGN", (col, 0), (col, -1), a))
    if extra:
        cmds += extra
    t.setStyle(TableStyle(cmds))
    return t

# ---------------------------------------------------------------- Custom Flowables
class HBar(Flowable):
    def __init__(self, data, width, height, unit="ms", maxval=None, note=None):
        super().__init__(); self.data = data; self.width = width; self.height = height
        self.unit = unit; self.note = note
        self.maxval = maxval or max(v for _, v, _ in data) * 1.18
    def wrap(self, *a): return (self.width, self.height)
    def draw(self):
        c = self.canv; n = len(self.data); labw = 80; x0 = labw
        plot_w = self.width - labw - 78; gap = 18
        nh = 16 if self.note else 0
        bh = (self.height - nh - (n - 1) * gap) / n
        y = self.height - bh
        for label, val, col in self.data:
            c.setFillColor(MUTE); c.setFont("Helvetica-Bold", 12.5)
            c.drawRightString(x0 - 10, y + bh / 2 - 4, label)
            c.setFillColor(LIGHT); c.rect(x0, y, plot_w, bh, fill=1, stroke=0)
            w = plot_w * (val / self.maxval)
            c.setFillColor(col); c.rect(x0, y, w, bh, fill=1, stroke=0)
            c.setFillColor(INK); c.setFont("Helvetica-Bold", 13)
            c.drawString(x0 + w + 9, y + bh / 2 - 4, f"~{val} {self.unit}")
            y -= bh + gap
        if self.note:
            c.setFillColor(MUTE); c.setFont("Helvetica-Oblique", 9)
            c.drawString(x0, 2, self.note)

class Layers(Flowable):
    def __init__(self, width, height):
        super().__init__(); self.width = width; self.height = height
    def wrap(self, *a): return (self.width, self.height)
    def draw(self):
        c = self.canv
        rows = [("LAYER 3  ·  API-Latenz (Cold-Start)",
                 "DNS / TCP / TLS / WS-Handshake  +  ttfp · ttft · ttfa  +  total",
                 "misst über die volle URL", ACCENT),
                ("LAYER 2  ·  Paketebene (PCAP)",
                 "SYN → SYN-ACK · Round-Trips · Inter-Arrival · Retransmits",
                 "eicht den Connect-Timer", HexColor("#7A6A55")),
                ("LAYER 1  ·  Infrastruktur",
                 "DNS · RTT/Ping (TCP primär, ICMP-Check) · TLS · Traceroute · ASN",
                 "misst die Netznähe zum Host", PRIMARY)]
        gap = 12; rh = (self.height - 2 * gap) / 3; y = self.height - rh
        for head, mid_, tail, col in rows:
            c.setFillColor(col); c.roundRect(0, y, self.width, rh, 7, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("Helvetica-Bold", 13.5)
            c.drawString(16, y + rh - 23, head)
            c.setFont("Helvetica", 10.5); c.drawString(16, y + rh - 41, mid_)
            c.setFont("Helvetica-Oblique", 10.5)
            c.drawRightString(self.width - 14, y + 10, tail)
            y -= rh + gap

class Box(Flowable):
    def __init__(self, text, bg, border, tcol, h=46, fs=14, width=None):
        super().__init__(); self.text = text; self.bg = bg; self.border = border
        self.tcol = tcol; self.h = h; self.fs = fs; self.width = width or CONTENT_W
    def wrap(self, *a): return (self.width, self.h)
    def draw(self):
        c = self.canv
        c.setFillColor(self.bg); c.setStrokeColor(self.border); c.setLineWidth(1.3)
        c.roundRect(0, 0, self.width, self.h, 8, fill=1, stroke=1)
        c.setFillColor(self.border); c.rect(0, 0, 6, self.h, fill=1, stroke=0)
        p = Paragraph(md(self.text), style("bx", self.fs, self.fs + 4, color=self.tcol,
                                           bold=True, space=0))
        w, hh = p.wrap(self.width - 34, self.h); p.drawOn(c, 20, (self.h - hh) / 2)

# ---------------------------------------------------------------- Spezial-Inhalte
def two_col(left, right, lw=0.42):
    t = Table([[left, right]], colWidths=[CONTENT_W * lw, CONTENT_W * (1 - lw)])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (0, 0), 0), ("LEFTPADDING", (1, 0), (1, 0), 20),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                           ("LINEAFTER", (0, 0), (0, 0), 0.6, RULE)]))
    return t

def extra_matrix():
    rows = [["Kat.", "Anbieter", "Modell", "Region (deklariert)", "Protokoll"],
            ["STT", "Deepgram", "Nova-3", "USA (Multi-DC, Round-Robin)", "WebSocket"],
            ["STT", "Rev.ai", "English", "USA", "WebSocket"],
            ["STT", "Azure", "Standard Neural", "Italien (Italy North)", "WebSocket"],
            ["LLM", "OpenAI", "gpt-4o-mini", "USA (GPU)", "HTTPS + SSE"],
            ["LLM", "Groq", "llama-3.1-8b-instant", "USA (LPU)", "HTTPS + SSE"],
            ["LLM", "Mistral", "mistral-small-2603", "EU / Frankreich", "HTTPS + SSE"],
            ["TTS", "Deepgram", "Aura-2", "USA (Multi-DC, Round-Robin)", "HTTPS Streaming"],
            ["TTS", "OpenAI", "tts-1", "USA", "HTTPS Streaming"],
            ["TTS", "Azure", "Standard Neural", "Italien (Italy North)", "HTTPS Streaming"]]
    return table(rows, [42, 84, 168, 226, 130], align={0: "CENTER"}, extra=[
        ("LINEABOVE", (0, 4), (-1, 4), 1.0, ACCENT), ("LINEABOVE", (0, 7), (-1, 7), 1.0, ACCENT),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 1), (0, -1), ACCENT)])

def extra_edge():
    rows = [["Terminierung", "Endpunkte", "RTT (FRA)", "Beleg"],
            ["EDGE (4/9)", "OpenAI · Groq · Mistral (LLM) + OpenAI-TTS", "~1 ms", "AS13335, Route endet im CDN-AS"],
            ["HOST (5/9)", "Deepgram STT+TTS (DNS-Round-Robin)", "~139 ms", "zwei US-Carrier: AS6461 / AS174"],
            ["HOST (5/9)", "Rev.ai (US)", "~140 ms", "AS16509 (AWS)"],
            ["HOST (5/9)", "Azure STT+TTS (Italy North)", "~11 ms", "AS8075 – echtes EU-RZ, kein CDN"]]
    return table(rows, [94, 312, 96, 208], fs=9.8, align={2: "CENTER"}, extra=[
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (0, 1), ACCENT), ("TEXTCOLOR", (0, 2), (0, -1), MUTE)])

def extra_eichung():
    rows = [["Anbieter", "RTT-Klasse", "App-Timer", "SYN→SYN-ACK", "Δ (Median)"],
            ["Azure (Italy North)", "~11 ms", "11,29 ms", "11,18 ms", "+0,11 ms"],
            ["Deepgram (US)", "~139 ms", "139,01 ms", "138,87 ms", "+0,12 ms"]]
    return table(rows, [176, 92, 166, 168, 96], align={1: "CENTER", 2: "CENTER", 3: "CENTER", 4: "CENTER"},
                 extra=[("TEXTCOLOR", (4, 1), (4, -1), FAST), ("FONTNAME", (4, 1), (4, -1), "Helvetica-Bold")])

def extra_asym():
    rows = [["Kategorie", "Primärmetrik", "Uhr startet bei", "Connect"],
            ["STT", "ttfp (endpointing-frei)", "erstem Audio-Chunk", "separat gemessen · 1×-Realtime"],
            ["LLM", "ttft", "Absenden des Requests", "enthalten (im ttft)"],
            ["TTS", "ttfa", "Absenden des Requests", "enthalten (im ttfa)"]]
    return table(rows, [80, 230, 230, 198], align={0: "CENTER"})

def extra_timeout():
    rows = [["Kategorie", "Connect-TO", "Response-TO", "Mindest-Output für „Erfolg“"],
            ["STT", "10 s", "30 s", "nicht-leeres Final-Transkript (≥ 1 Wort)"],
            ["LLM", "10 s", "30 s", "≥ 1 Wort UND ≥ 3 SSE-Content-Chunks"],
            ["TTS", "10 s", "30 s", "Audio-Body ≥ 1.000 Bytes (dekodierbar)"]]
    return table(rows, [92, 96, 110, 420], align={1: "CENTER", 2: "CENTER"})

def extra_messstack():
    rows = [["Layer", "Werkzeug / Library", "Kernfunktion / Metrik"],
            ["L1 · RTT", "Python socket", "create_connection(ip,443) → SYN→SYN-ACK = 1 RTT (min+median)"],
            ["L1 · DNS", "dig @ 8.8.8.8 / 1.1.1.1 / 9.9.9.9", "IPs je Resolver + TTL"],
            ["L1 · ASN", "Team-Cymru (dig TXT)", "ASN je IP → Edge-Beleg (Bed. b)"],
            ["L1 · TLS", "Python ssl + openssl s_client", "TLS-Version · Cipher · ALPN · Cert"],
            ["L1 · Route", "traceroute -T -p 443 + Cymru", "endet die Route im CDN-AS? (Bed. c)"],
            ["L2", "tcpdump → analyze.py", "SYN→SYN-ACK vs. App-Timer (Eichung)"],
            ["L3 · LLM/TTS", "httpx (HTTPS + SSE / Stream)", "ttft/ttfa ab Request · IPv4 · effective_model aus SSE"],
            ["L3 · STT", "websockets + asyncio.gather", "ttfp ab erstem Audio-Chunk · 1×-realtime gepaced"],
            ["Runner", "run.py", "interleaved Round-Robin · flock · Slot-Deadline → JSONL"]]
    return table(rows, [78, 232, 542], fs=9.5, extra=[
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 1), (0, -1), ACCENT)])

def extra_endpunkte():
    rows = [["Kat. · Anbieter", "Host", "Protokoll", "Auflösung (ASN · RTT)", "Term."],
            ["STT Deepgram", "api.deepgram.com", "WSS", "AS6461/AS174 US · ~101–148 ms", "Host"],
            ["STT Rev.ai", "api.rev.ai", "WSS", "AS16509 AWS-US · ~140 ms", "Host"],
            ["STT Azure", "italynorth.stt.speech.microsoft.com", "WSS", "AS8075 MS-Italy · ~11 ms", "Host"],
            ["LLM OpenAI", "api.openai.com", "HTTPS+SSE", "AS13335 Cloudflare · ~1 ms", "Edge"],
            ["LLM Groq", "api.groq.com", "HTTPS+SSE", "AS13335 Cloudflare · ~1 ms", "Edge"],
            ["LLM Mistral", "api.mistral.ai", "HTTPS+SSE", "AS13335 Cloudflare · ~1 ms", "Edge"],
            ["TTS Deepgram", "api.deepgram.com", "HTTPS-Stream", "AS6461/AS174 US · ~140 ms", "Host"],
            ["TTS OpenAI", "api.openai.com", "HTTPS-Stream", "AS13335 Cloudflare · ~1 ms", "Edge"],
            ["TTS Azure", "italynorth.tts.speech.microsoft.com", "HTTPS-Stream", "AS8075 MS-Italy · ~11 ms", "Host"]]
    return table(rows, [110, 250, 92, 246, 54], fs=9.2, align={2: "CENTER", 4: "CENTER"}, extra=[
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 1), (0, -1), PRIMARY),
        ("LINEABOVE", (0, 4), (-1, 4), 1.0, ACCENT), ("LINEABOVE", (0, 7), (-1, 7), 1.0, ACCENT)])

def extra_anatomie():
    rows = [["LLM", "DNS", "TCP (=RTT)", "TLS", "connect Σ", "ttft", "→ Backend"],
            ["Groq", "0,3", "1,3", "5,7", "~7,3", "~67", "~60"],
            ["Mistral", "0,3", "1,1", "5,8", "~7,2", "~279", "~272"],
            ["OpenAI", "1,4", "1,2", "4,9", "~7,5", "~487", "~479"]]
    return table(rows, [120, 92, 128, 88, 128, 100, 148], fs=11,
                 align={1: "CENTER", 2: "CENTER", 3: "CENTER", 4: "CENTER", 5: "CENTER", 6: "CENTER"}, extra=[
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 1), (0, -1), PRIMARY),
        ("FONTNAME", (4, 1), (4, -1), "Helvetica-Bold"), ("TEXTCOLOR", (4, 1), (4, -1), FAST),
        ("FONTNAME", (6, 1), (6, -1), "Helvetica-Bold"), ("TEXTCOLOR", (6, 1), (6, -1), SLOW)])

# ---------------------------------------------------------------- Folien-Daten
SLIDES = [
 dict(id="s00", kind="title", section="Rahmen", kicker="Konsultation · Setup-Stand",
      title="Erklärt Netznähe die Latenzunterschiede?",
      sub="Eine drei-schichtige Messstudie zu Cloud-AI-Sprachdiensten (STT · LLM · TTS) aus EU-Sicht",
      note="Ich zeige Ihnen heute Setup und Methodik der Messstudie und die Ergebnisse der abgeschlossenen Vollkampagne (56/56 Slots)."),

 dict(id="s01", kind="toc", section="Rahmen", kicker="Agenda", title="Agenda",
      note="Der Schwerpunkt liegt bewusst auf dem Setup, weil das Fundament zuerst stehen muss."),

 dict(id="s02", kind="content", section="Rahmen", kicker="Rahmen", title="Forschungsfrage",
      bullets=["Pipeline: **STT → LLM → TTS** (sequenziell)",
               "Latenz entscheidet die Nutzbarkeit",
               "**Kernfrage:** Netz/Infrastruktur vs. Backend?",
               "Faktoren: **RTT, Protokoll, Hosting-Region**",
               "Bewusst offen — **auch ein Nein zählt**",
               "Zweite Achse: **Verfügbarkeit** (separat)"],
      note="Ich frage, in welchem Maße Netznähe gegenüber der Backend-Verarbeitung die Latenzunterschiede erklärt — und 'Netz erklärt weniger' ist eine gültige Antwort."),

 dict(id="d1", kind="divider", section="Setup", num="1", title="Setup",
      subs=["Vantage Point", "Provider-Matrix", "Messdesign"],
      note="Das Setup ist der wichtigste Teil — hier zeige ich, womit und wie sauber gemessen wird."),

 dict(id="s03", kind="content", section="Setup", kicker="Setup · Vantage Point", title="Vantage Point",
      bullets=["**AWS EC2 eu-central-1** (Frankfurt)",
               "**c6i.large** — bewusst NICHT burstable",
               "Burstable würde drosseln → **Latenz-Sprünge ohne Netz-Ursache**",
               "**CPU-Steal-Time** je Slot geloggt",
               "**IPv4** durchgängig erzwungen",
               "**OpenSSL 3.x** (LibreSSL meldete TLS-Zeiten falsch)",
               "Limitation: **ein Vantage Point** — Kernbefund unberührt"],
      note="Ich nutze bewusst eine nicht-burstable Instanz und logge CPU-Steal-Time, damit kein Throttling als Latenz fehlinterpretiert wird."),

 dict(id="s04", kind="content", section="Setup", kicker="Setup · Provider-Matrix",
      title="Provider-Matrix · 9 Endpunkte",
      bullets=["**9 Endpunkte** über 6 Anbieter × 3 Kategorien",
               "Feste Inputs je Kategorie",
               "Fairer Cross-Provider-Vergleich"],
      extra="matrix", layout="top_bullets",
      note="Dieselben neun Endpunkte über drei Kategorien, mit fixen Inputs je Kategorie für einen fairen Vergleich; die Anbieter-Auswahl ist in der Methodik begründet."),

 dict(id="s05", kind="content", section="Setup", kicker="Setup · Messdesign",
      title="Messdesign · Cold-Start · interleaved",
      bullets=["**Cold-Start**: frische TCP+TLS je Call",
               "Kein Pooling · kein Keep-Alive",
               "**Feste Inputs** je Kategorie",
               "STT 5 s-WAV · LLM Capital-Prompt · TTS Gruß",
               "**Interleaved** Round-Robin, 100 Runden",
               "Startreihenfolge rotiert",
               "Fehlschlag blockiert die Runde nicht"],
      note="Jeder Call baut eine frische Verbindung auf — gemessen wird der Cold-Start; der LLM-Input ist exakt 'Reply in one short sentence: What is the capital of Germany?' (max_tokens=50, streaming)."),

 dict(id="d2", kind="divider", section="Methodik", num="2", title="Methodik",
      subs=["3 Schichten · RTT · Edge/Host", "Paket-Eichung · Metrik-Uhr", "Kampagne & Aggregation"],
      note="Jetzt zeige ich, wie ich messe und warum die Zahlen valide sind — inklusive der beiden kritischen Punkte zu Edge-RTT und Timer-Vertrauen."),

 dict(id="s06", kind="content", section="Methodik", kicker="Methodik · Architektur",
      title="Drei-Schichten-Architektur",
      bullets=["Die Frage liefert die **Zerlegung**",
               "**Layer 1 → Host**   ·   **Layer 3 → volle URL**",
               "Differenz = **Backend (Hardware + Modell)**",
               "**Layer 2** macht die Leitung prüfbar"],
      extra="layers", layout="bullets_then_diagram",
      note="Layer 1 misst zum Host, Layer 3 über die volle URL — die Differenz ist der Backend-Anteil, und Layer 2 macht die Leitung paketweise überprüfbar."),

 dict(id="s07", kind="content", section="Methodik", kicker="Methodik · Layer 1",
      title="Layer 1 · RTT via TCP-Handshake",
      bullets=["**TCP-Ping** (SYN→SYN-ACK :443) = primär",
               "Vergleichbar bei **allen 9** (ICMP teils geblockt)",
               "Trifft den **echten API-Port**",
               "Deckt sich mit dem **Connect-Timer aus Layer 3**",
               "Validierung: **TCP-Ping ≈ ICMP-Ping**"],
      note="TCP-SYN→SYN-ACK auf Port 443 ist eine RTT, funktioniert bei allen neun und entspricht genau dem Connect-Timer aus Layer 3; wo ICMP geht, validiere ich gegen den ICMP-Ping."),

 dict(id="s08", kind="content", section="Methodik", kicker="Methodik · Layer 1 · Edge oder Host?",
      title="Layer 1 · Edge oder Host?",
      frage="Offene Frage:  Drei Endpunkte antworten aus Frankfurt mit ~1 ms RTT — woher?",
      bullets=["**Erklärung:** Cloudflare-Edge FRA, nicht Backend",
               "~1 ms = reale Edge-Eigenschaft, kein Fehler",
               "**Edge nur, wenn alle drei zutreffen:**",
               "(a) **einstellige ms** aus FRA",
               "(b) Ziel-IP in **AS13335** (CDN)",
               "(c) Traceroute endet **im CDN-AS**"],
      extra="edge", layout="frage",
      note="Die niedrigen RTTs sind eine reale Cloudflare-Edge-Eigenschaft in Frankfurt — belegt über drei Bedingungen — und gelten nur für 4 von 9 Endpunkten; niedrige RTT heißt nicht automatisch Edge, Azure mit ~11 ms ist ein echter Host."),

 dict(id="s09", kind="content", section="Methodik", kicker="Methodik · Layer 2 · Paket-Eichung",
      title="Layer 2 · Paket-Eichung des Connect-Timers",
      frage="Validierung:  App-Timer unabhängig gegen die Paketebene (PCAP) geeicht.",
      bullets=["**30 Cold-Starts je Provider** (paketvalidiert: 30/30 bzw. 28/30)",
               "App-Timer vs. **SYN→SYN-ACK** (PCAP)",
               "Geeicht: **nur der Connect-Timer**",
               "ttft/ttfa: gleiche Uhr, aber **nicht direkt** paket-geeicht",
               "Layer 2 = **Konsistenz-Check**, kein 2. Beweis"],
      extra="eichung", layout="frage",
      tagline="→ Connect-Timer trifft die Latenz auf der Leitung auf ~0,1 ms genau (Median-Offset +0,11 ms; erster Messpunkt als Outlier entfernt).",
      note="Der Connect-Timer ist auf ~0,1 ms paketgenau geeicht — aber ehrlich nur er; ttft und ttfa nutzen dieselbe Uhr, starten erst beim Request-Absenden und sind nicht direkt paket-geeicht, deshalb ist Layer 2 ein Konsistenz-Check, kein zweiter Beweis."),

 dict(id="s10", kind="content", section="Methodik", kicker="Methodik · Metrik-Uhr",
      title="Metrik-Asymmetrie · ab wann läuft die Uhr?",
      bullets=["**Klar deklariert:** ab wann die Uhr läuft",
               "Jeder Call ist Cold-Start: Connect **immer** gemessen",
               "STT **ttfp**: nur Engine ab erstem Audio-Chunk (Connect **separat**)",
               "LLM/TTS **ttft/ttfa**: Connect **enthalten** (ab Request)",
               "E2E: jeder Anbieter-Connect **genau einmal**"],
      extra="asym", layout="bullets_then_table",
      note="Jeder Call ist ein Cold-Start mit frischer Verbindung — auch STT; bei STT wird der Connect aber als eigene Zahl geführt, und ttfp misst nur die Engine ab dem ersten Audio-Chunk (fairer Vergleich, weil die STT-Anbieter unterschiedlich weit weg sind: Azure ~11 ms, Deepgram/Rev.ai ~140 ms). LLM/TTS messen ab dem Request-Absenden, der Connect ist dort enthalten. In der E2E-Summe zählt jeder der drei Anbieter-Connects genau einmal: den STT-Connect addiere ich explizit, LLM- und TTS-Connect stecken schon in ttft/ttfa — so wird keiner doppelt gezählt; und es geht das STT-Final ein, nicht ttfp."),

 dict(id="s11", kind="content", section="Methodik", kicker="Methodik · Kampagne",
      title="Kampagne & Aggregation", extra="kampagne", layout="two_col",
      note="56 Slots = 50.400 Calls, alle erhoben und A4-ausgewertet (Vollkampagne); Bootstrap-CI noch ausstehend; die Headline ist der robuste Median der Slot-Mediane."),

 dict(id="d3", kind="divider", section="Analyse", num="3", title="Analyse",
      tag="Vollkampagne 56/56 · A4-Median",
      subs=["Kernbefund", "Interpretation", "Limitationen"],
      note="Alle folgenden Zahlen sind die A4-Auswertung über alle 56 Slots (Vollkampagne); Bootstrap-CI noch ausstehend — die Aussage selbst ist davon unberührt."),

 dict(id="s12", kind="content", section="Analyse", kicker="Analyse · Kernbefund",
      title="Kernbefund · gleicher Edge, ~7,3×", extra="c1", layout="chart",
      bullets=["Alle 3 LLM @ **Cloudflare FRA**",
               "**100 % des Traffics** belegt (2 CF-IPs, AS13335, ~1 ms)",
               "ttft streut **~7,3×** (Groq→Mistral→OpenAI)",
               "**Pro IP stabil** (kein Edge-Effekt)",
               "**Region-Reihenfolge gedreht**: Mistral (EU) langsamer als Groq (US)",
               "Gleiches Netz, ~7,3× → **Netznähe erklärt das nicht**"],
      note="Alle drei LLM terminieren am selben Cloudflare-Edge in Frankfurt mit ~1 ms — für 100% des Traffics belegt — und trotzdem streut ttft etwa 7,3-fach und ist pro IP stabil; die deklarierte Region ist sogar gedreht. Dasselbe Netz kann die Spreizung nicht erklären."),

 dict(id="s13", kind="content", section="Analyse", kicker="Analyse · Interpretation",
      title="Interpretation · der Kompass",
      negbox="Verteidigbar ist die negative Aussage:  ‚Netznähe erklärt die Latenzspreizung nicht.‘",
      bullets=["Schritt zu Backend trägt **Modellgrößen-Confound**",
               "Groq = kleinstes Modell **+ LPU**",
               "→ **Backend (Hardware + Modell) statt Geografie**",
               "**2. Beleg (TTS):** OpenAI-TTS @ CF-FRA: connect **~1 ms** gemessen, trotzdem **~942 ms** ttfa → **nicht durch EU-Netznähe erklärbar**"],
      note="Verteidigbar ist nur die negative Aussage; der Schritt zu 'Backend' trägt den Modellgrößen-Confound — Groq ist das kleinste Modell auf LPU-Hardware — deshalb 'Backend (Hardware + Modell) statt Geografie'. OpenAI-TTS terminiert am selben Cloudflare-Edge (connect ~1 ms gemessen), braucht aber ~942 ms bis zum ersten Audio — die EU-Netznähe kann das nicht erklären. 'Reines Backend' behaupte ich bewusst nicht (hinter dem Edge steckt auch unsichtbarer Backhaul); dass es Verarbeitung ist, zeigt der Vergleich bei identischem Netzpfad: OpenAI-LLM und -TTS teilen dieselben Cloudflare-IPs, differieren aber um ~455 ms — das kann kein Netz sein."),

 dict(id="d4", kind="divider", section="Abschluss", num="4", title="Abschluss",
      subs=["Stand", "Nächste Schritte", "Diskussion"],
      note="Zum Abschluss der Stand, die nächsten Schritte und eine Frage an Sie."),

 dict(id="s15", kind="content", section="Abschluss", kicker="Abschluss · Stand",
      title="Stand & nächste Schritte",
      bullets=["**Messinfrastruktur steht** und läuft stabil",
               "→ offene Punkte betreffen nur **Doku/Reporting**, nicht die Daten",
               "Stop ~23.06. → Statistik (**Bootstrap-CI + Inferenz**)",
               "Zweitgutachten: **Prof. Färber zugesagt** (Exposé, Gespräch Juli)"],
      note="Die Messinfrastruktur steht und läuft stabil; die offenen Punkte betreffen nur Doku und Reporting, nicht die Daten. Nach dem Stop folgt die Statistik (Bootstrap-CI und Inferenz); Prof. Färber hat das Zweitgutachten zugesagt."),

 dict(id="b1", kind="backup", section="Backup", kicker="Backup · Layer 1",
      title="Klassifikator & Per-IP-Belege",
      bullets=["Edge nur, wenn **alle drei** zutreffen",
               "(a) **einstellige ms** FRA :443",
               "(b) IP in **AS13335** (Team-Cymru)",
               "(c) Traceroute endet im CDN-AS",
               "Belegt über **alle getroffenen IPs**",
               "Deepgram: **zwei US-Carrier** (AS6461 / AS174), ~101–140 ms",
               "Rev.ai **AS16509** ~140 ms · Azure **AS8075** ~11 ms",
               "Bei Edge ist connect ≈ N×RTT zwangsläufig → **kein eigener Beleg**"],
      note="Der Klassifikator ist über alle getroffenen IPs belegt; bei Edge-Anbietern ist connect ≈ N×RTT zwangsläufig und zählt nicht — nur host-terminierte Anbieter stützen die Cross-Layer-Brücke. Die ASN-Belege liegen pro IP vor."),

 dict(id="b2", kind="backup", section="Backup", kicker="Backup · Statistik",
      title="Aggregation & Inferenz (Detail)",
      bullets=["p50/p90 slot-aufgelöst · p95 nur gepoolt + CI · p99 nicht",
               "Faustregel: **n·(1−q) ≥ 5–10**",
               "**Stark rechtsschief** → Bootstrap statt t",
               "E2E: **Monte-Carlo-Faltung** der 3 Phasen",
               "Joint-Completion / **Pareto-Front** (Latenz vs. Zuverlässigkeit)",
               "IP-Quelle: **aufgelöste Connect-IP** — Fehlschläge nie über Null-Werte filtern"],
      note="Wegen der starken Rechtsschiefe nutze ich Bootstrap statt t-Verteilung, p99 ist aus n=100 je Slot nicht belastbar, und E2E entsteht per Monte-Carlo-Faltung der drei Phasen."),

 dict(id="b3", kind="backup", section="Backup", kicker="Backup · Verfügbarkeit",
      title="Fehlerbehandlung & Verfügbarkeit",
      bullets=["Erfolg = **inhaltlich gültiger Output** (nicht nur Verbindung)",
               "Timeout-Filter: Teilstring **„ReadTimeout“** klassifizieren",
               "nicht nach error=='timeout' (verfehlt fast alle echten Timeouts)",
               "OpenAI-TTS **~3,1 % ReadTimeouts** (173/5600, Vollkampagne)",
               "→ Latenz nur erfolgreiche Calls + Asterisk"],
      extra="timeout", layout="top_bullets",
      note="Timeouts werden per Teilstring 'ReadTimeout' klassifiziert, weil ein naiver error=='timeout'-Filter die echten Timeouts verfehlt; OpenAI-TTS hat in der Vollkampagne ~3,1 % Fail-Rate (173/5600)."),

 dict(id="b4", kind="backup", section="Backup", kicker="Backup · Mess-Stack",
      title="Mess-Stack (Code)",
      bullets=["Pro Schicht ein eigenes Werkzeug: **CLI** für L1/L2, **Python-Timer** für die API-Latenz",
               "STT ohne SDK (**rohe WebSockets**) · IPv4 erzwungen · Cold-Start je Call"],
      extra="messstack", layout="top_bullets",
      note="Layer 1/2 nutzen Standard-CLI-Werkzeuge (socket, dig, traceroute, tcpdump, openssl); Layer 3 sind eigene Python-Wrapper — httpx für LLM/TTS, rohe websockets für STT, ein run.py-Runner orchestriert die Slots."),

 dict(id="b5", kind="backup", section="Backup", kicker="Backup · Endpunkte",
      title="Endpunkte & Auflösung",
      bullets=["**9 Endpunkte** über 6 Anbieter — live per DNS aufgelöst, per ASN + RTT klassifiziert"],
      extra="endpunkte", layout="top_bullets",
      note="Diese Tabelle ist die Kurzfassung; das separate Referenz-Blatt enthält die vollen URLs, Auth-Methoden, alle aufgelösten IPs und die fertigen ping/dig/traceroute-Befehle zum Selbst-Nachmessen."),

 dict(id="b6", kind="backup", section="Backup", kicker="Backup · Was ist eine Latenzzahl?",
      title="Anatomie einer Latenzzahl",
      bullets=["**ttft** = ab Request-Absenden bis erstes Token — connect-**inklusiv**",
               "darin: DNS + TCP + TLS = **connect-Σ ~7 ms** (für alle 3 ~gleich)",
               "davon nur **~1 ms reine TCP-RTT** (= Netznähe, Layer 1) · TLS ~5 ms",
               "Rest = **Backend** ~60 → ~479 ms → trägt die **~7,3×-Spreizung**"],
      extra="anatomie", layout="bullets_then_table",
      note="ttft enthält den Verbindungsaufbau; der ist mit ~7 ms für alle drei praktisch gleich (davon ~1 ms TCP-RTT, ~5 ms TLS). Die Spreizung von 67 auf 487 ms lebt also fast vollständig im Backend — das ist der direkte Beleg, dass nicht das Netz die Differenz macht."),
]

# ---------------------------------------------------------------- Renderer je Kind
def render_title(c, s):
    c.setFillColor(PRIMARY); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(ACCENT); c.rect(0, 150, PAGE_W, 4, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 33)
    c.drawString(M, PAGE_H - 232, s["title"])
    c.setFillColor(HexColor("#E7DDCD")); c.setFont("Helvetica", 16)
    c.drawString(M, PAGE_H - 268, s["sub"])
    bw, bh, bx, by = 250, 44, PAGE_W - M - 250, 78
    c.setFillColor(HexColor("#3A3733")); c.setStrokeColor(ACCENT); c.setLineWidth(1)
    c.roundRect(bx, by, bw, bh, 6, fill=1, stroke=1)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 10.5)
    c.drawCentredString(bx + bw / 2, by + bh / 2 - 4, "Konsultation · Setup-Stand")

def render_toc(c, s, idx, total):
    master(c, s["kicker"], s["title"], idx, total)
    items = [("1", "Setup", "Vantage Point · Provider-Matrix · Messdesign", True),
             ("2", "Methodik", "3 Schichten · Edge/Host · Eichung · Kampagne", False),
             ("3", "Analyse", "Kernbefund · Interpretation · Limitationen  (Vollkampagne)", False),
             ("4", "Abschluss", "Stand · nächste Schritte · Diskussion", False)]
    x = M; w = CONTENT_W; rh = 64; gap = 14; y = CONTENT_TOP - rh
    for num, ti, subc, hot in items:
        c.setFillColor(ACCENT if hot else PANEL)
        c.roundRect(x, y, w, rh, 8, fill=1, stroke=0)
        c.setFillColor(white if hot else PRIMARY); c.setFont("Helvetica-Bold", 30)
        c.drawString(x + 22, y + rh / 2 - 11, num)
        c.setFont("Helvetica-Bold", 19)
        c.drawString(x + 74, y + rh - 27, ti)
        c.setFillColor(HexColor("#F2EADF") if hot else MUTE); c.setFont("Helvetica", 11.5)
        c.drawString(x + 74, y + 13, subc)
        if hot:
            c.setFillColor(white); c.setFont("Helvetica-Bold", 9.5)
            c.drawRightString(x + w - 20, y + rh - 20, "SCHWERPUNKT")
        y -= rh + gap

def render_divider(c, s, idx, total):
    c.setFillColor(PRIMARY); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(HexColor("#3A352F")); c.setFont("Helvetica-Bold", 330)
    c.drawRightString(PAGE_W - 26, 40, s["num"])
    c.setFillColor(ACCENT); c.rect(M, PAGE_H - 232, 5, 150, fill=1, stroke=0)
    c.setFillColor(SAND); c.setFont("Helvetica-Bold", 12)
    c.drawString(M + 20, PAGE_H - 150, f"ABSCHNITT {s['num']}")
    c.setFillColor(white); c.setFont("Helvetica-Bold", 48)
    c.drawString(M + 20, PAGE_H - 200, s["title"])
    if s.get("tag"):
        c.setFillColor(ACCENT); c.setFont("Helvetica-Bold", 13)
        c.drawString(M + 22, PAGE_H - 226, s["tag"])
    yy = PAGE_H - 280
    c.setFont("Helvetica", 16)
    for sub in s["subs"]:
        c.setFillColor(ACCENT); c.rect(M + 22, yy + 3, 9, 9, fill=1, stroke=0)
        c.setFillColor(HexColor("#E7DDCD")); c.drawString(M + 42, yy, sub)
        yy -= 30
    c.setFillColor(SAND); c.setFont("Helvetica-Bold", 8)
    c.drawString(M, 30, f"{idx} / {total}")

def build_flow(s):
    flow = []
    layout = s.get("layout", "bullets")
    bullets = [anchor(b) for b in s.get("bullets", [])]
    extra = s.get("extra")

    if s.get("frage"):
        flow.append(Box(s["frage"], LIGHT, ACCENT, PRIMARY, h=42, fs=12.5))
        flow.append(Spacer(1, 9))
    if s.get("negbox"):
        flow.append(Box(s["negbox"], NEGBG, NEGBORD, NEGBORD, h=46, fs=14))
        flow.append(Spacer(1, 11))

    def add_extra():
        if extra == "matrix": flow.append(extra_matrix())
        elif extra == "edge": flow.append(extra_edge())
        elif extra == "eichung": flow.append(extra_eichung())
        elif extra == "asym": flow.append(extra_asym())
        elif extra == "timeout": flow.append(extra_timeout())
        elif extra == "messstack": flow.append(extra_messstack())
        elif extra == "endpunkte": flow.append(extra_endpunkte())
        elif extra == "anatomie": flow.append(extra_anatomie())
        elif extra == "layers": flow.append(Layers(CONTENT_W, 216))
        elif extra == "c1":
            chart = HBar([("Groq", 67, FAST), ("Mistral", 279, MID), ("OpenAI", 487, SLOW)],
                         width=CONTENT_W * 0.55, height=210,
                         note="LLM-ttft · connect-inkl. · 56/56 Slots, A4-Median")
            flow.append(two_col(chart, [anchor(b, S_ANCHOR_S) for b in s["bullets"]], lw=0.55))
        elif extra == "kampagne":
            left = [Paragraph("Kampagne", S_CELLB), Spacer(1, 4),
                    anchor("**7 Tage × 8 UTC-Slots × n=100**", S_ANCHOR_S),
                    anchor("= 56 Slots = **50.400 Calls**", S_ANCHOR_S),
                    anchor("UTC-verankert: US-Hoch + -Tief", S_ANCHOR_S),
                    anchor("Erhoben & ausgewertet: **alle 56 Slots** (A4)", S_ANCHOR_S)]
            right = [Paragraph("Aggregation &amp; Inferenz", S_CELLB), Spacer(1, 4),
                     anchor("Headline = **Median der Slot-Mediane**", S_ANCHOR_S),
                     anchor("Jede Zahl: **Bootstrap-95%-CI**", S_ANCHOR_S),
                     anchor("‚schneller‘ getestet mit **Mann-Whitney / Bootstrap**", S_ANCHOR_S),
                     anchor("**Verfügbarkeit** = eigene Achse", S_ANCHOR_S)]
            flow.append(two_col(left, right, lw=0.44))

    if layout in ("top_bullets", "bullets_then_table", "bullets_then_diagram"):
        flow += bullets; flow.append(Spacer(1, 11)); add_extra()
    elif layout == "frage":
        flow += bullets; flow.append(Spacer(1, 9)); add_extra()
        if s.get("tagline"):
            flow.append(Spacer(1, 9))
            flow.append(Paragraph(md(s["tagline"]), style("tl", 13, 17, color=PRIMARY, bold=True)))
    elif layout in ("two_col", "chart"):
        add_extra()
    else:
        flow += bullets

    if s.get("askbox"):
        flow.append(Spacer(1, 12)); flow.append(Box(s["askbox"], LIGHT, ACCENT, PRIMARY, h=48, fs=13.5))
    if s.get("foot"):
        flow.append(Spacer(1, 9)); flow.append(Paragraph(md(s["foot"]), S_FOOT))
    return flow

def render_content(c, s, idx, total):
    master(c, s["kicker"], s["title"], idx, total, backup=(s["kind"] == "backup"))
    flow = build_flow(s)
    pad = max(0.0, min((CONTENT_H - measure(flow)) / 2.0, 95.0))
    if pad > 6:
        flow = [Spacer(1, pad)] + flow
    frame(c, flow)

# ---------------------------------------------------------------- Deck
def build_deck(path):
    c = canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, start=1):
        k = s["kind"]
        if k == "title": render_title(c, s)
        elif k == "toc": render_toc(c, s, i, total)
        elif k == "divider": render_divider(c, s, i, total)
        else: render_content(c, s, i, total)
        c.showPage()
    c.save()
    print(f"OK deck -> {path} ({total} Seiten)")

# ---------------------------------------------------------------- Sprechzettel
def build_handout(path):
    PW, PH = 595, 842
    mx = 46
    c = canvas.Canvas(path, pagesize=(PW, PH))
    sec_for = {"d1": "1 · SETUP", "d2": "2 · METHODIK", "d3": "3 · ANALYSE", "d4": "4 · ABSCHLUSS"}
    y = [PH - 64]

    def header(title):
        c.setFillColor(PRIMARY); c.rect(0, PH - 40, PW, 40, fill=1, stroke=0)
        c.setFillColor(ACCENT); c.rect(0, PH - 43, PW, 3, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Helvetica-Bold", 13); c.drawString(mx, PH - 27, title)
        c.setFillColor(SAND); c.setFont("Helvetica", 9)
        c.drawRightString(PW - mx, PH - 26, "Konsultation 23.06. · Sprechzettel")

    def newpage(title):
        c.showPage(); header(title); y[0] = PH - 64

    header("Sprechzettel · Folie für Folie")
    num = 0; aw = PW - 2 * mx
    for s in SLIDES:
        if s["kind"] == "title":
            continue
        is_div = s["kind"] == "divider"
        if not is_div:
            num += 1
        bl = s.get("bullets", []) + (s.get("subs", []) if is_div else [])
        block_h = 30 + 12.5 * len(bl) + (34 if s.get("note") else 0)
        if y[0] - block_h < 56:
            newpage("Sprechzettel (Fortsetzung)")
        c.setFillColor(PRIMARY); c.setFont("Helvetica-Bold", 12)
        label = sec_for.get(s["id"], f"{num}.")
        c.drawString(mx, y[0], f"{label}   {s['title']}")
        y[0] -= 16
        c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(mx, y[0] + 6, PW - mx, y[0] + 6)
        y[0] -= 4
        for b in bl:
            p = Paragraph("• " + md(b), style("ho", 9.8, 12.5, color=INK, left=10, space=0))
            w, h = p.wrap(aw - 10, 100); p.drawOn(c, mx + 4, y[0] - h + 10); y[0] -= h + 1.5
        if s.get("note"):
            y[0] -= 2
            p = Paragraph("<b>Sprecher:</b> " + s["note"],
                          style("sp", 9.8, 13, color=HexColor("#6A4A1E"), left=10, space=0))
            w, h = p.wrap(aw - 10, 200)
            c.setFillColor(LIGHT); c.rect(mx, y[0] - h + 2, aw, h + 6, fill=1, stroke=0)
            c.setFillColor(ACCENT); c.rect(mx, y[0] - h + 2, 3, h + 6, fill=1, stroke=0)
            p.drawOn(c, mx + 8, y[0] - h + 7); y[0] -= h + 16
        else:
            y[0] -= 12
    c.save()
    print(f"OK handout -> {path}")


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    build_deck(os.path.join(here, "folien_konsultation.pdf"))
    build_handout(os.path.join(here, "folien_sprechzettel.pdf"))
