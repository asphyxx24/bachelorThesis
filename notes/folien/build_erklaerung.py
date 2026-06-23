# -*- coding: utf-8 -*-
"""Rendert folien_erklaerung.md zu einem lesbaren A4-PDF (reportlab Platypus)."""
import re, html, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, ListFlowable, ListItem)
from reportlab.lib.styles import ParagraphStyle

PRIMARY = HexColor("#2B2A28"); ACCENT = HexColor("#C77A30"); INK = HexColor("#23211E")
MUTE = HexColor("#6E675E"); LIGHT = HexColor("#F4F0EA"); PANEL = HexColor("#E7E0D5"); RULE = HexColor("#D8CFC1")

S_H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=PRIMARY, spaceBefore=6, spaceAfter=10)
S_H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14.5, leading=18, textColor=PRIMARY, spaceBefore=14, spaceAfter=5)
S_H3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=ACCENT, spaceBefore=8, spaceAfter=3)
S_BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14.5, textColor=INK, spaceAfter=5)
S_BULLET = ParagraphStyle("bul", fontName="Helvetica", fontSize=10, leading=14.5, textColor=INK, leftIndent=14, bulletIndent=2, spaceAfter=3)
S_SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=HexColor("#413d37"), leftIndent=30, bulletIndent=18, spaceAfter=2)
S_QUOTE = ParagraphStyle("q", fontName="Helvetica-Oblique", fontSize=9.8, leading=14, textColor=HexColor("#5a4a33"),
                         leftIndent=12, backColor=LIGHT, borderColor=ACCENT, borderWidth=0, spaceBefore=3, spaceAfter=5)
S_CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=9.3, leading=12, textColor=INK)
S_CELLH = ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=9.3, leading=12, textColor=white)

def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<font face="Courier" size="9">\1</font>', t)
    # Kursiv nur bei sauberem Paar (kein Leerraum direkt neben den Sternen) -> Einzel-* bleiben literal
    t = re.sub(r"(?<!\*)\*(?=\S)(.+?)(?<=\S)\*(?!\*)", r"<i>\1</i>", t)
    return t

def _is_block_start(s):
    return (s.startswith("#") or s.startswith(">") or s.startswith("|") or s == "---"
            or bool(re.match(r"^-\s", s)) or bool(re.match(r"^\d+\.\s", s)))

def _normalize(raw_lines):
    """Harte Zeilenumbrüche zu logischen Blöcken zusammenführen (sonst brechen **fett**-Spannen)."""
    norm = []; buf = None
    for raw in raw_lines:
        s = raw.strip()
        if s == "":
            if buf is not None: norm.append(buf); buf = None
            norm.append("")
        elif s.startswith(">"):
            cont = s[1:].lstrip()
            if cont == "":                                   # leere Zitatzeile = Absatztrenner
                if buf is not None: norm.append(buf); buf = None
            elif buf is not None and buf.lstrip().startswith(">"):
                buf = buf.rstrip() + " " + cont               # Zitat-Zeilen zusammenführen
            else:
                if buf is not None: norm.append(buf)
                buf = "> " + cont
        elif _is_block_start(s):
            if buf is not None: norm.append(buf)
            buf = raw  # Einrückung der ersten Zeile bewahren (Sub-Bullet-Erkennung)
        else:
            buf = raw if buf is None else (buf.rstrip() + " " + s)
    if buf is not None: norm.append(buf)
    return norm

def build(md_path, pdf_path):
    lines = _normalize(open(md_path, encoding="utf-8").read().split("\n"))
    flow = []; i = 0; n = len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1; continue
        # Tabelle
        if s.startswith("|") and i + 1 < n and set(lines[i+1].strip()) <= set("|-: "):
            rows = []
            header = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            data = [[Paragraph(inline(c), S_CELLH) for c in header]] + \
                   [[Paragraph(inline(c), S_CELL) for c in r] for r in rows]
            ncol = len(header); avail = 170 * mm
            colw = [avail * 0.34] + [avail * 0.66 / (ncol - 1)] * (ncol - 1) if ncol > 1 else [avail]
            t = Table(data, colWidths=colw)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT]),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
            flow.append(Spacer(1, 4)); flow.append(t); flow.append(Spacer(1, 6))
            continue
        if s.startswith("# "):
            flow.append(Paragraph(inline(s[2:]), S_H1))
            flow.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=8))
        elif s.startswith("## "):
            flow.append(Paragraph(inline(s[3:]), S_H2))
        elif s.startswith("### "):
            flow.append(Paragraph(inline(s[4:]), S_H3))
        elif s.startswith("> "):
            flow.append(Paragraph(inline(s[2:]), S_QUOTE))
        elif s == "---":
            flow.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=6, spaceAfter=6))
        elif re.match(r"^\s*-\s+", ln):
            indent = len(ln) - len(ln.lstrip())
            style = S_SUB if indent >= 2 else S_BULLET
            flow.append(Paragraph(inline(re.sub(r"^\s*-\s+", "", ln)), style, bulletText="–" if indent >= 2 else "•"))
        else:
            flow.append(Paragraph(inline(s), S_BODY))
        i += 1

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title="Folien-Erklärung")
    def footer(canv, d):
        canv.setFont("Helvetica", 7.5); canv.setFillColor(MUTE)
        canv.drawRightString(A4[0] - 20 * mm, 10 * mm, f"{d.page}")
        canv.drawString(20 * mm, 10 * mm, "Folien-Erklärung · Vortragsbegleiter · A. Rusik")
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(f"OK -> {pdf_path}")

if __name__ == "__main__":
    here = os.path.dirname(__file__)
    build(os.path.join(here, "folien_erklaerung.md"), os.path.join(here, "folien_erklaerung.pdf"))
