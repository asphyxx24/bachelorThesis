# Prof-Gespräch — kompakt (Stand 2026-06-09)

Ein Blatt zum Zeigen und Sagen. Reihenfolge ist auch die Gesprächsreihenfolge.

## 1. Wo ich stehe
Datenerhebung und Analyse abgeschlossen (Juni-Kampagne: 7 Tage × 8 Slots, n=100, 50.400 Cold-Start-Records, 0 % NaN, von einer zweiten EC2-Instanz validiert). Geschrieben ist noch nichts — das Methodik-Kapitel (Ihre Hauptkritik vom April) ist der nächste Schritt.

## 2. Pitch (30 Sekunden)
„Ich messe die Latenz von neun kommerziellen Cloud-AI-APIs — Spracherkennung, Sprachmodell, Sprachausgabe — aus EU-Sicht von AWS Frankfurt, im Cold-Start, über drei Schichten: Infrastruktur (Ping/TLS), Paketmitschnitt und API-Latenz. Die naive Erwartung ist, dass die geografische Nähe die Latenz erklärt. Mein Kernbefund widerlegt das: Derselbe EU-Provider, Azure mit 10 ms RTT, liefert bei der Spracherkennung das erste Token erst nach 1715 ms, bei der Sprachausgabe das erste Audio aber schon nach 67 ms — gleiche Region, gleiche RTT, gegensätzliches Ergebnis. Die Region kann die Latenz also nicht hinreichend erklären; den Hauptanteil trägt die Backend-Engine. Ihre Kritik ‚Methodik unklar' habe ich zum Zentrum gemacht: Layer 1 und 2 sind die unabhängige Kontrolle, die belegt, dass die Differenz nicht am Netzwerk liegt.“

## 3. Gesprächsablauf (4 Schritte)
1. **Befund vorweg, nicht das Setup.** Mit dem Ergebnis öffnen (Pitch oben), dann sofort der Beleg.
2. **Money-Figure zeigen** (`05_tts_ttfa_cdf.png`), daran das Argument führen, den STT-Wert mündlich danebenstellen (575 vs. 1715 ms). Erst danach das Messdesign — so begründet die Methodik einen bereits gezeigten Befund.
3. **Drei-Schichten-Methodik als Beweisführung**: L1/L2 sind die Kontrolle (RTT-Klassen, TLS-Version, Cloudflare-Grenze, unabhängig aus dem PCAP), nicht Dekoration. Hier die connect_ms-Asymmetrie offen deklarieren.
4. **Limitationen selbst eröffnen** (siehe §7), schließen mit 2–3 offenen Fragen an ihn (Titel anmelden, Schreibreihenfolge, ob ein echter E2E-Lauf erwartet wird).

## 4. Was ich zeige

| Befund | Zahl | Figure / Tabelle |
|---|---|---|
| **STT/TTS-Inversion desselben Providers** (Azure, Region konstant) — Kernbeleg | STT-TTFT 1715 ms vs. TTFA 67 ms | `05_tts/png/05_tts_ttfa_cdf.png` + `03_stt/png/03_stt_cdf.png` |
| STT: Engine überlagert Netzwerknähe | Deepgram (US, RTT 138) 575 ms vs. Azure (EU, RTT 10) 1715 ms; 56/56 Slots ohne Überlappung | `03_stt/png/03_stt_cdf.png`; `tables/03_stt_statistics.csv` |
| LLM bei neutralisiertem Netzwerk (alle hinter Cloudflare, RTT ~1 ms) | Groq 68 ms, Mistral 231 ms, OpenAI 542 ms | `04_llm/png/04_llm_ttft_cdf.png` |
| Drei RTT-Klassen (die naive Erwartung) | EU-direkt ~1–2 ms, Azure-EU ~10 ms, US ~140 ms | `01_layer1/png/01_ping_rtt_boxplot.png` |
| Latenz vs. Zuverlässigkeit (Tradeoff) | beste Kombi 1134 ms läuft nur in 67 % durch; +163 ms (Mistral) → 96 % | `07_e2e/png/07_e2e_availability.png`; `tables/07_pipeline_availability.csv` |
| Cold-Start verfehlt 1-s-Budget (Monte-Carlo-geprüft) | 0/27 < 1000 ms; p95 ~1350 ms; nur ~24 % der Einzelläufe < 1 s | `07_e2e/png/07_e2e_montecarlo.png` |

**Money-Figure für den Einstieg:** `05_tts_ttfa_cdf.png`. **Nicht** mit dem Cross-Layer-Scatter (Steigung ~1, n=4) eröffnen — das ist der schwache Aufhänger.
**Weglassen im Gespräch** (zu detailliert): Fehlerraten-Plot, TLS-1.2-Penalty-Detail, die `*_connect_anteil`-Reihe.

## 5. Methodik in 5 Sätzen (gegen „Methodik unklar“)
1. Ich messe nutzerseitige Latenz auf Layer 3 (connect_ms, ttft_ms/ttfa_ms, total_ms) und liefere mit Layer 1 (Ping, TLS) und Layer 2 (PCAP) zwei unabhängige Schichten, die die Latenz *erklären* statt nur ranken.
2. Cold-Start ist eine geprüfte Designentscheidung: die connect_ms-Zeit ist über 100 Läufe flach (Deepgram 424,8–425,8 ms), was heimliche TLS-Session-Resumption ausschließt.
3. Für den Quervergleich vergleiche ich nur den user-perceived Cold-Start und deklariere offen, dass die connect_ms-Submetrik je nach Protokoll (WebSocket vs. HTTPS) unterschiedlich zusammengesetzt ist.
4. Das Datenfundament ist cross-vantage validiert: eine zweite Instanz reproduziert 8/9 RTTs unter 1 ms und 7/7 TLS-Versionen; die einzige Abweichung (Deepgram-Anycast) ist als Routing-Eigenschaft dokumentiert.
5. Den E2E-Schätzer (Median-Addition) habe ich per Monte-Carlo-Faltung der empirischen Verteilungen abgesichert (mittlere Abweichung 1,4 %) und gebe p90/p95 statt nur Mediane an.

## 6. Wenn er fragt …
- **Region/Engine konfundiert (nur 1 EU-Provider je Kategorie) — was belegt die Inversion?** Sie belegt nichts über Engines „allgemein“, und das behaupte ich nicht. Bei konstanter Region (Azure, Italy North) liefert dieselbe Region entgegengesetzte Ergebnisse — damit ist die Hypothese „Region erklärt die Latenz hinreichend“ falsifiziert. Das ist eine Anteils-, keine Kausalaussage.
- **WER/Qualität — ist Azure langsamer, weil gründlicher?** 1715 ms bis zum ersten Token sind für einen Echtzeit-Dialog disqualifizierend, unabhängig von der Transkriptqualität; `transcript_len` zeigt keinen Ausschuss. Korrektheit ist eine orthogonale Achse (Future Work) — die Transkript-Texte wurden nicht gespeichert, das ist eine bewusste Scope-Grenze.
- **Woher die 1-s-Schwelle, wo Dialog 200–300 ms braucht?** Die 200–300 ms sind der mittlere menschliche Antwort-Gap aus der Turn-Taking-Literatur; 1 s setze ich als großzügige Obergrenze, nicht als Zielwert. Der Befund ist robust: 0/27 Läufe < 1 s, p95 ~1350 ms — auch bei 1,5 s scheitert die Mehrheit.
- **Cross-Layer n=4, hohe Korrelation — trivial?** Es ist kein Fit, sondern eine deduktive Vorhersage-Prüfung: die Steigung folgt aus der RTT-Zahl des Protokolls (erwartet 1,0, gemessen 1,006; Achsenabschnitt 10,7 ms). Das r führe ich bei n=4 bewusst nicht als Gütemaß; das Modell ist Methoden-Baustein, kein Kernbefund, und bricht sichtbar bei den 4/9 Cloudflare-Providern.

## 7. Meine ehrlichen Limitationen (mit Entschärfung)
- **Region/Engine konfundiert** (n=1 EU-Provider je Kategorie). → durchgängig als Anteils-Aussage formuliert; die Inversion falsifiziert die Geografie-Hypothese, ohne die Engine-Hypothese zu beweisen.
- **E2E ist Median-Addition**, keine end-to-end gemessene Pipeline. → Monte-Carlo-Faltung (1,4 % Abweichung) rechtfertigt den Schätzer und liefert p90/p95.
- **Keine Qualitäts-/WER-Achse** — nur Latenz, nur Transkript-Längen gespeichert. → als orthogonaler Scope deklariert; „Engine schlägt Geografie“ ≠ „schnell schlägt gründlich“.
- **Vantage-Point**: L3-Kampagne lief auf anderem AWS-Account (eu-central-1). → dokumentiert; nur Deepgram (Anycast) weicht ab, sonst cross-vantage reproduziert.

## 8. Nächster Schritt
Analyse-Reste der Welle 2 (A10 Mistral-Output-Degeneration, A12 Phantom-Slot), dann **Methodik-Kapitel zuerst** schreiben — dort die 1-s-Schwelle mit Turn-Taking-Quelle belegen und WER als Scope-Grenze ausformulieren.

---
*Vollständige Vorbereitung: `PROF_VORBEREITUNG_2026-06-09.md` · Befunde zum Durchdringen: `notes/befunde_verstehen.md` · Sprech-Skript: `notes/spickzettel_prof.md`*
