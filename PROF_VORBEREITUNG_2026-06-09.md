# Prof-Vorbereitung & Stand — 2026-06-09

> Erzeugt aus einem 12-Agenten-Workflow (8 Figure-Checks + Audit-Status + Strategie + Pitch +
> Prüfer-Anwalt). Zweck: (1) Ist-Stand der Figures, (2) Audit-Status A1–A14, (3) was du ins
> Prof-Gespräch mitbringst, (4) die härtesten Angriffsfragen mit ehrlicher Einschätzung,
> (5) priorisierte nächste Schritte.
>
> **Wichtigste Botschaft:** Die Analyse ist solide und reproduzierbar. Aber es gibt **drei
> Stellen, an denen du noch NICHT verteidigt bist** (Fragen 1, 3, 6 unten) und **drei Figure-/
> Doku-Reste**, die deiner eigenen Korrektur widersprechen. Beides ist konkret behebbar — und
> genau das macht den Unterschied im Gespräch.

---

## 1. Figure-Status — alle Notebooks auf Juni-Daten verifiziert

Alle 8 Notebooks wurden frisch headless ausgeführt (heute, 09:27–09:28) und laufen **fehlerfrei**
auf den Juni-Parquets. Die Figures auf Platte sind damit aktuell.

| NB | Läuft | Juni-Daten | Figures | Anmerkung |
|----|:----:|:----------:|---------|-----------|
| 00 data_quality | ✅ | ✅ | — (nur Tabellen) | sauber |
| 01 layer1 | ✅ | ✅ | ping_rtt_boxplot, tls_handshake | sauber |
| 02 pcap | ✅ | ✅ | communication_matrix, submetrics_stacked | ⚠️ **Stale-Titel (s.u.)** |
| 03 stt | ✅ | ✅ | stt_cdf, stt_connect_anteil | ⚠️ r=0.999 in Markdown |
| 04 llm | ✅ | ✅ | ttft_cdf, error_rates, connect_anteil | ℹ️ Titel „<2%" ungenau |
| 05 tts | ✅ | ✅ | ttfa_cdf, connect_anteil, total_ms | sauber |
| 06 cross_layer | ✅ | ✅ | scatter, tls12_penalty, pcap_submetrics_vs_l3, provider_quadrant | ⚠️ r=0.999 in print |
| 07 e2e | ✅ | ✅ | stacked_bar, budget, **montecarlo, availability** | sauber (A6/A7/A8 drin) |

**→ Antwort auf deine Frage:** Ja, alles ist auf den neuen Daten — NB07 von heute, NB01–06 frisch
nachgerendert und verifiziert. NB02 braucht **kein** tshark (nutzt scapy), läuft also auch.

### Konkrete Figure-/Doku-Reste (zu fixen, klein)

1. **🔴 NB02 `02_submetrics_stacked` — Figure-Titel ist FALSCH.** Er sagt noch
   *„Azure-STT zu 93 % Server-Processing (414 ms Proto-Setup)"* — das ist die **Mai-Fehlinterpretation**,
   die wir in `CLAUDE.md` ausdrücklich korrigiert haben (korrekt: Azure-STT proto_setup ~13 ms,
   connect ~49 ms, sauberer 3-RTT-Handshake). Die 414 ms waren die Audio-Sendelücke, kein
   Server-Processing. **Das widerspricht deiner eigenen Doku — unbedingt vor dem Prof fixen.**
2. **🟡 NB03 (Markdown §6.8)** und **NB06 (print in Zelle 5):** `r=0.999` steht noch als
   Gütemaß/Schlagzeile. Laut Reframe (A1) soll r **nirgends** als Headline stehen. Letzte Reste.
3. **🟢 NB04 Titel** sagt connect_ms „<2 % der TTFT" — gilt nur für OpenAI/Mistral; bei Groq sind
   es 16 % (weil Groqs TTFT winzig ist). Schreibphase-Politur, kein Fehler.

> ⚠️ **Das bedeutet: A1 ist NICHT vollständig erledigt** (im Audit als „erledigt" markiert) — die
> r=0.999-Reste in NB03/NB06 + der NB02-Titel sind die letzten 20 % davon.

---

## 2. Audit-Status A1–A14 (Stand 2026-06-09)

| ID | Thema | Status |
|----|-------|--------|
| A1 | r=0.999 überverkauft → Reframe | 🟡 **fast** (Reste in NB02/03/06, s.o.) |
| A3 | connect_ms cross-Kategorie verschieden | ✅ erledigt (Submetrik-Doku) |
| A6 | E2E Median-Addition ohne CI | ✅ **erledigt heute** (Monte-Carlo) |
| A7 | Batch/`total_ms`-Tail-Artefakt | ✅ **erledigt heute** (gestrichen) |
| A8 | Verfügbarkeit ignoriert | ✅ **erledigt heute** (Joint-Completion) |
| A4 | STT misst Batch-Dump, kein Streaming | 🔧 **Welle 3** (analytisch) |
| A10 | Mistral-Output-Degeneration ungeprüft | 🔧 **Welle 2** (aus Roh-JSONL) |
| A12 | Phantom-57.-Slot (Timestamp-Spillover) | 🔧 **Welle 2** (nach `tag` gruppieren) |
| A2 | Limitations verschweigen die Löcher | ✍️ Schreibphase |
| A5 | 1-s-Budget ohne Quelle (vs Jacoby 300 ms) | ✍️ Schreibphase |
| A9 | Layer-2 als „Validierung" zu stark | ✍️ Schreibphase |
| A11 | token_count zählt SSE-Chunks | ✍️ Schreibphase |
| A13 | TTS-E2E ignoriert Playback | ✍️ Schreibphase |
| A14 | Keine STT-Korrektheit/WER | ❌ nicht machbar → Limitation |

**Erledigt: 4,5 von 14.** Welle 1 (A6/A7/A8) komplett. Offen analytisch: A1-Reste, A4, A10, A12.
Der Rest ist Schreibphase oder Limitation.

---

## 3. Was du ins Prof-Gespräch mitbringst

### 30-Sekunden-Pitch
Ich messe, wie schnell kommerzielle KI-Sprach-APIs aus Europa antworten — und **warum**. Kernbefund:
Nicht die geografische Nähe entscheidet, sondern die Backend-Engine. Ein US-Anbieter (RTT 138 ms)
schlägt einen EU-Anbieter (RTT 10 ms), weil sein Modell schneller rechnet. Bester Beleg: derselbe
EU-Anbieter (Azure) verliert bei Spracherkennung und gewinnt bei Sprachausgabe — gleicher Standort,
gegensätzliches Ergebnis. Beitrag: kontrollierte Widerlegung der „näher = schneller"-Intuition +
die Drei-Schichten-Methodik, die zeigt, *wann* Netzwerknähe die Latenz erklärt und wann nicht.

### Die 3 Befunde zum Eröffnen
1. **STT — US schlägt EU:** Deepgram (US, 138 ms) ttft ~575 ms vs. Azure (EU, 10 ms) ~1715 ms — 56/56 Slots.
2. **TTS-Inversion:** Azure gewinnt jetzt — ttfa ~67 ms vs. Deepgram ~557 vs. OpenAI ~954. Gleiche Region, anderes Ergebnis.
3. **LLM bei eliminiertem Netz:** alle hinter Cloudflare (~1 ms) → reine Engine: Groq ~68 vs. Mistral ~231 vs. OpenAI ~542 ms.

### Die neue Robustheits-Arbeit (zeigt: du hast den Audit ernst genommen)
- **Monte-Carlo (A6):** Median-Addition validiert (Δ ~1,4 %) **und** Streuung gezeigt (p90 1273, p95 1350 ms, nur ~24 % der Läufe < 1 s). Doppelter Gewinn: Methode geprüft + Aussage ehrlicher.
- **Verfügbarkeit (A8):** Latenz-vs-Zuverlässigkeit-Tradeoff — die schnellste Kombi (Groq) läuft nur in ~67 % durch; +163 ms (Mistral) → ~96 %. Konkrete Empfehlung statt nur Bestmarke.
- **Batch gestrichen (A7):** ein nicht verteidigbares Artefakt entfernt + sauber dokumentiert, warum.

### 5 Fragen, die DU im Gespräch aktiv stellen solltest
1. **Echter E2E-Lauf nötig?** Median-Addition + Monte-Carlo-Validierung — oder erwartet er einen echten verketteten Messlauf?
2. **Titel anmelden:** „Engine schlägt Geografie: …" passt? So anmelden?
3. **Limitations-Scope ok?** 7 statt 14 Tage, nur Cold-Start, n=1 EU-Provider/Kategorie (Anteils- statt Kausalaussage), WER nicht nachmessbar.
4. **Cross-Layer-Modell:** als Methoden-Baustein (n=4, r nicht als Gütemaß) ausreichend, oder mehr erwartet?
5. **Schreib-Reihenfolge:** Methodik-Kapitel zuerst (war seine Hauptkritik) — richtig so?

---

## 4. Die härtesten Prüfer-Fragen (ehrliche Selbsteinschätzung)

> Aus dem „Prüfer-Anwalt"-Agenten. Status: ✅ verteidigt · 🟡 teilweise · 🔴 nicht verteidigt.
> **Die zwei wirklich gefährlichen sind 1 und 6 — sie können deinen Kernbefund inhaltlich umdeuten.**

### 🔴 Frage 1 — Region/Engine-Konfundierung (existenziell)
*„Sie haben pro Kategorie nur EINEN EU-Provider. Region und Engine sind perfekt konfundiert. Die
TTS-Inversion zeigt nur, dass ein Azure-Produkt bei STT schlecht und bei TTS gut ist — wie ist das
ein Beleg über Engines *allgemein*?"*

**Status: 🟡 teilweise — und hier ist eine WICHTIGE Korrektur an deinem Verständnis:**
Die TTS-Inversion ist **kein sauberes natürliches Experiment** (so steht es aktuell falsch in
`befunde_verstehen.md`). Sie variiert **zwei Dinge gleichzeitig**: die Aufgabe (STT→TTS) *und* die
Engine. Konstant ist nur die **Region**. Was die Inversion sauber kann: die Hypothese **„Region
erklärt alles" falsifizieren**. Was sie **nicht** kann: „Engine erklärt alles" beweisen.
→ **Deine korrekte Formulierung:** *„Die Region kann die Latenz nicht hinreichend erklären, weil
derselbe Standort entgegengesetzte Ergebnisse liefert."* Nicht mehr behaupten. Das ist immer noch
ein starkes, gültiges Argument — nur ehrlich begrenzt.

### 🔴 Frage 3 — Die 1-Sekunde-Schwelle ist willkürlich
*„Woher kommt die 1 Sekunde? Sie schreiben selbst, Dialog brauche 200–300 ms. Cherry-picked?"*

**Status: 🔴 nicht verteidigt.** Es gibt **keine zitierte Quelle** (= Audit A5, noch offen). Fix:
(a) eine echte Quelle (Turn-Taking-Literatur / ~200 ms Gap / Produkt-SLA), (b) 1 s als *großzügige*
Obergrenze rahmen („selbst bei 1 s scheitern alle"), (c) Robustheit zeigen (gilt 0/27 auch bei 800/1500 ms?).

### 🔴 Frage 6 — Latenz ohne Qualität (WER)
*„Sie ranken STT nach Tempo, aber messen nicht, ob das Transkript korrekt ist. Vielleicht ist Azure
langsamer, weil gründlicher. ‚Engine schlägt Geografie' könnte ‚schludrig schlägt gründlich' heißen."*

**Status: 🔴 nicht verteidigt** (nur „nicht messbar", A14). **Das ist die Trivialisierungs-Falle.**
Fix — du musst eine *inhaltliche* Entschärfung formulieren: (a) Größenordnung schützt — 1,7 s bis
zum *ersten* Token ist für Echtzeit zu langsam, egal wie gut; (b) `transcript_len` als schwacher
Proxy (keine Engine liefert offensichtlichen Müll); (c) als **Scope-Grenze** rahmen: „Diese Arbeit
ist die Latenz-Achse; Qualität ist orthogonal und Future Work."

### 🟡 Frage 2 — STT-`connect_ms` in der E2E-Summe
*„Sie sagen, connect_ms sei cross-Kategorie nicht vergleichbar — stecken es aber als größten Posten
(425 ms) in die 1134-ms-Summe. Bricht Ihre Headline-Zahl die eigene Regel?"*

**Status: 🟡 teilweise.** Auflösung (musst du explizit sagen): *„Cross-Provider verbiete ich rohes
connect; **innerhalb einer Pipeline** ist stt_connect ein realer, sequentieller, vom Nutzer erlebter
Kaltstart-Posten derselben STT-Session."* Diese Unterscheidung steht nirgends explizit — nachtragen.

### 🟡 Frage 4 — Cross-Layer n=4 / r=0.999
*„Gerade durch 4 Punkte, r=0.999 — trivial. Und Sie verstecken Ihr einziges Gütemaß. Warum kein Fußnote?"*

**Status: 🟡 teilweise.** Verteidigung ist gut (r nicht als Gütemaß; N_RTTs aus Protokoll, nicht Fit
→ es ist eine **deduktive Vorhersage-Prüfung**, keine Regression). Aber: r steht noch in
findings/NB03/NB06 — **Konsistenz herstellen**, sonst „warum steht es dreimal da?".

### 🟡 Frage 5 — Vantage Point / fremder AWS-Account
*„Maßgebliche Kampagne auf fremder, heute nicht mehr kontrollierter Instanz. Bei Deepgram (Anycast,
Ihrem Kernbefund!) schwankt die RTT 102–148 ms. Wie viel ist Provider, wie viel diese eine Instanz?"*

**Status: 🟡 teilweise.** Validierung (i-045, 8/9 RTT <1 ms) deckt die **Netz-Schicht**, nicht die
**Engine-Zeiten**. Fehlender Robustheits-Satz: *„Selbst bei Deepgrams ungünstigster Anycast-RTT
(148 ms) bleibt der US-Provider ~1100 ms schneller als Azure — der Befund überlebt die gesamte
beobachtete Vantage-Spanne."* Dazu offen in die Limitationen: „diese Instanz heute nicht reproduzierbar".

---

## 5. Priorisierte nächste Schritte

**Vor dem Prof-Gespräch (höchster Hebel, klein):**
1. **Verteidigung für Frage 1 + 6 ausformulieren** (Konfundierung ehrlich rahmen, WER-Entschärfung) —
   das sind die zwei Fragen, die den Kernbefund umdeuten könnten. `befunde_verstehen.md` Befund 2 korrigieren.
2. **Figure-/r-Reste fixen:** NB02-Submetrik-Titel (414-ms-Fehlinterpretation), r=0.999 aus NB03/NB06.
   → schließt A1 wirklich ab.
3. **arXiv-Zitate prüfen** (2603.11006 / 2603.05413) — existieren die wirklich? Sonst steht die
   Submetrik-Methodik zitationslos da.

**Analyse-Reste (Welle 2/3, optional vor Schreiben):**
4. A10 (Mistral-Degeneration, Roh-JSONL) · A12 (Phantom-Slot) · A4 (STT-Pacing-Sensitivität).

**Dann die eigentliche Arbeit:**
5. **Methodik-Kapitel schreiben** (Wählischs Hauptkritik) — mit connect_ms-Asymmetrie-Tabelle +
   STT-Batch-Dump-Deklaration als Herzstück. Schreiben zwingt zum Verstehen.

**Strategischer Hinweis aus der Standortbestimmung:** Das Material ist Überproduktion (8 NB, ~19
Figures). Die Kunst der nächsten Wochen ist **Reduktion + Schreiben**, nicht Messen. Behalten:
NB03 (STT), NB05 (TTS-Inversion), NB02 (Cloudflare), NB00/01 (Datenqualität). Schrumpfen: NB06 auf
½ Seite. Entschärfen: NB07.

---

## Quell-Dokumente
- `notes/befunde_verstehen.md` — zum Durcharbeiten (⚠️ Befund 2 braucht die Korrektur aus Frage 1)
- `notes/spickzettel_prof.md` — Sprech-Skript · `notes/findings.md` — Befunde + Belege
- `PRUEFER_AUDIT_2026-06-08.md` — die 14 Findings · `STANDORTBESTIMMUNG_2026-06-08.md` — Strategie
