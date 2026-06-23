# -*- coding: utf-8 -*-
"""Messziele-Referenz (A4 quer) — Endpunkte + Auflösung + fertige Nachmess-Befehle. Keine API-Keys."""
import os, html
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, XPreformatted)
from reportlab.lib.styles import ParagraphStyle

PRIMARY = HexColor("#2B2A28"); ACCENT = HexColor("#C77A30"); INK = HexColor("#23211E")
MUTE = HexColor("#6E675E"); LIGHT = HexColor("#F4F0EA"); RULE = HexColor("#D8CFC1")

H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=PRIMARY, spaceAfter=2)
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=8.5, leading=11, textColor=MUTE, spaceAfter=8)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=PRIMARY, spaceBefore=10, spaceAfter=4)
CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=10, textColor=INK)
CELLH = ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=white)
CELLB = ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=PRIMARY)
MONO = ParagraphStyle("mono", fontName="Courier", fontSize=7, leading=9.6, textColor=INK)
NOTE = ParagraphStyle("note", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTE, spaceBefore=4)

def P(t, s=CELL): return Paragraph(t, s)

def build(path):
    flow = []
    flow.append(Paragraph("Messziele-Referenz — Endpunkte zum Nachpingen", H1))
    flow.append(Paragraph("Vantage Point: AWS EC2 eu-central-1 (Frankfurt) · IPs aus DNS-Auflösung 2026-06-14, "
                          "per Layer 1 (ASN/RTT) bestätigt · CDN-/Round-Robin-Hosts ggf. live anders auflösen · "
                          "<b>keine API-Keys enthalten</b>.", SUB))

    # ---- Tabelle: Endpunkte ----
    head = [P(x, CELLH) for x in ["Kat. · Anbieter", "Host", "Prot.", "Aufgelöste IPs (2026-06-14)", "ASN / Org · RTT", "Term."]]
    rows = [
        ["STT Deepgram", "api.deepgram.com", "WSS", "208.184.56.200 · 38.68.64.131/.132 (~6 IPs, Round-Robin)", "AS6461 Zayo / AS174 Cogent (US) · ~101–148 ms", "Host"],
        ["STT Rev.ai", "api.rev.ai", "WSS", "52.36.23.89 · 52.32.160.52 · 32.186.17.136", "AS16509 Amazon (US) · ~140 ms", "Host"],
        ["STT Azure", "italynorth.stt.speech.microsoft.com", "WSS", "4.232.100.212", "AS8075 Microsoft (Italy North) · ~11 ms", "Host"],
        ["LLM OpenAI", "api.openai.com", "HTTPS+SSE", "172.66.0.243 · 162.159.140.245", "AS13335 Cloudflare · ~1 ms", "Edge"],
        ["LLM Groq", "api.groq.com", "HTTPS+SSE", "172.64.149.20 · 104.18.38.236", "AS13335 Cloudflare · ~1 ms", "Edge"],
        ["LLM Mistral", "api.mistral.ai", "HTTPS+SSE", "172.66.2.203 · 162.159.142.207", "AS13335 Cloudflare · ~1 ms", "Edge"],
        ["TTS Deepgram", "api.deepgram.com", "HTTPS-Stream", "wie STT-Deepgram (Round-Robin, ~6 IPs)", "AS6461 Zayo / AS174 Cogent (US) · ~140 ms", "Host"],
        ["TTS OpenAI", "api.openai.com", "HTTPS-Stream", "172.66.0.243 · 162.159.140.245", "AS13335 Cloudflare · ~1 ms", "Edge"],
        ["TTS Azure", "italynorth.tts.speech.microsoft.com", "HTTPS-Stream", "4.232.100.220", "AS8075 Microsoft (Italy North) · ~11 ms", "Host"],
    ]
    data = [head] + [[P(r[0], CELLB), P(r[1]), P(r[2]), P(r[3]), P(r[4]), P(r[5])] for r in rows]
    t = Table(data, colWidths=[92, 188, 66, 196, 168, 42])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT]),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
        ("LINEABOVE", (0, 4), (-1, 4), 0.8, ACCENT), ("LINEABOVE", (0, 7), (-1, 7), 0.8, ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]))
    flow.append(t)

    # ---- Volle URLs & Auth ----
    flow.append(Paragraph("Volle URLs &amp; Auth (Platzhalter &lt;KEY&gt;)", H2))
    urls = (
        "STT Deepgram — wss://api.deepgram.com/v1/listen?model=nova-3&language=en&encoding=linear16&sample_rate=16000&interim_results=true\n"
        "   Auth: Header  Authorization: Token <KEY>\n"
        "STT Rev.ai   — wss://api.rev.ai/speechtotext/v1/stream?content_type=audio/x-raw;rate=16000;format=S16LE;channels=1\n"
        "   Auth: Query   &access_token=<KEY>\n"
        "STT Azure    — wss://italynorth.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1\n"
        "   Auth: Header  Ocp-Apim-Subscription-Key: <KEY>\n"
        "LLM OpenAI   — https://api.openai.com/v1/chat/completions    ·  gpt-4o-mini-2024-07-18 · stream · max_tokens=50\n"
        "LLM Groq     — https://api.groq.com/openai/v1/chat/completions   ·  llama-3.1-8b-instant\n"
        "LLM Mistral  — https://api.mistral.ai/v1/chat/completions    ·  mistral-small-2603\n"
        "   Auth (alle LLM): Header  Authorization: Bearer <KEY>\n"
        "TTS Deepgram — https://api.deepgram.com/v1/speak?model=aura-2-asteria-en&encoding=mp3    ·  Header  Authorization: Token <KEY>\n"
        "TTS OpenAI   — https://api.openai.com/v1/audio/speech    ·  tts-1 · voice=alloy · mp3    ·  Header  Authorization: Bearer <KEY>\n"
        "TTS Azure    — https://italynorth.tts.speech.microsoft.com/cognitiveservices/v1    ·  SSML en-US-JennyNeural · Header  Ocp-Apim-Subscription-Key: <KEY>"
    )
    flow.append(XPreformatted(html.escape(urls), MONO))

    # ---- Befehle ----
    flow.append(Paragraph("Selbst nachmessen (DNS-Resolver: 8.8.8.8 · 1.1.1.1 · 9.9.9.9)", H2))
    cmds = (
        "# DNS live auflösen (Round-Robin sichtbar)\n"
        "dig <host> A +short            # oder: dig @1.1.1.1 <host> A +short\n\n"
        "# ICMP-Ping\n"
        "ping -c 5 <host>\n\n"
        "# TCP-Ping auf Port 443 (eine RTT, genau wie in der Studie)\n"
        "python3 - <<'PY'\n"
        "import socket, time\n"
        "h = \"<host>\"; ip = socket.gethostbyname(h)\n"
        "t = time.perf_counter(); socket.create_connection((ip, 443), timeout=5).close()\n"
        "print(round((time.perf_counter() - t) * 1000, 2), \"ms ->\", ip)\n"
        "PY\n\n"
        "# Route + ob sie im CDN-AS endet (TCP-Traceroute, braucht sudo)\n"
        "sudo traceroute -T -p 443 -n <host>\n\n"
        "# TLS-Version / Zertifikat\n"
        "openssl s_client -connect <host>:443 -servername <host> </dev/null 2>/dev/null | openssl x509 -noout -subject\n\n"
        "# ASN einer IP (Team-Cymru)\n"
        "dig +short $(echo <ip> | awk -F. '{print $4\".\"$3\".\"$2\".\"$1}').origin.asn.cymru.com TXT"
    )
    flow.append(XPreformatted(html.escape(cmds), MONO))
    flow.append(Paragraph("Hinweis: Aus Frankfurt sollten OpenAI/Groq/Mistral (+ OpenAI-TTS) ~1 ms zeigen (Cloudflare-Edge), "
                          "Azure ~11 ms (EU-RZ), Deepgram/Rev.ai ~100–145 ms (US). Andere Standorte/Resolver → andere IPs/RTTs.", NOTE))

    doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=14 * mm, bottomMargin=12 * mm, title="Messziele-Referenz")
    def footer(canv, d):
        canv.setFont("Helvetica", 7); canv.setFillColor(MUTE)
        canv.drawString(18 * mm, 7 * mm, "Messziele-Referenz · Latenzmessung Cloud-AI-APIs · A. Rusik")
        canv.drawRightString(landscape(A4)[0] - 18 * mm, 7 * mm, f"{d.page}")
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(f"OK -> {path}")

if __name__ == "__main__":
    build(os.path.join(os.path.dirname(__file__), "messziele_referenz.pdf"))
