# Figur 6 — Latenz vs. Zuverlässigkeit der E2E-Pipeline

![](07_e2e_availability.png)

## Worum es geht

Die Figur stellt für alle 27 möglichen Voice-Pipelines (3 STT × 3 LLM × 3 TTS) zwei Dimensionen gegenüber: die End-to-End-Latenz (wie schnell die Pipeline antwortet) und die Joint-Completion-Probability (wie zuverlässig die Kombination technisch vollständig durchläuft). Sie zeigt, dass die latenzschnellste Pipeline nicht die zuverlässigste ist — es existiert ein Zielkonflikt, der eine differenzierte Provider-Empfehlung erzwingt.

## Was auf der Figur zu sehen ist

- **x-Achse:** „E2E-Latenz Median (ms, Cold-Start Streaming)", linear skaliert (keine Log-Achse), von ca. 1100 ms bis ca. 3600 ms. Niedriger ist besser (weiter links).
- **y-Achse:** „Joint-Completion-Probability (%)", linear, von ca. 60 % bis 100 %. Höher ist besser (weiter oben).
- **Punkte:** Jeder Punkt ist eine der 27 Pipeline-Kombinationen, eingefärbt nach der LLM-Komponente (Legende rechts unten):
  - **Lila** = LLM Groq
  - **Braun** = LLM Mistral
  - **Rot** = LLM OpenAI
- **Vertikale Lage der Farben:** Die roten (OpenAI) und braunen (Mistral) Punkte liegen oben (~86–100 %), die lila (Groq) Punkte bilden ein klar abgesetztes unteres Band bei ~67 % bzw. ~60 %. Die Farbe — also das LLM — bestimmt damit fast vollständig die y-Position: Die Zuverlässigkeit hängt an der LLM-Komponente, weil dort der einzige nennenswerte Ausfallfaktor sitzt. (Das untere lila Band bei ~60 % und die braunen/roten Punkte bei ~86–90 % stammen aus Kombinationen mit Rev.ai-STT, dessen Verfügbarkeit den jeweiligen LLM-Wert zusätzlich nach unten zieht.)
- **Grüne gepunktete Referenzlinie** bei y = 95 %, beschriftet „95 % Verfügbarkeit". Sie markiert eine konventionelle Schwelle, ab der eine Pipeline als praktisch einsetzbar gilt. Punkte unterhalb fallen durch.
- **Schwarze gestrichelte Linie (Pareto-Front):** Verbindet die drei nicht-dominierten Kombinationen, also jene, für die es keine andere Pipeline gibt, die gleichzeitig schneller UND zuverlässiger ist. Drei Punkte sind annotiert:
  - **deepgram+groq+azure — 1134 ms · 67,0 %** (ganz links unten: schnellste, aber unter 95 %)
  - **deepgram+mistral+azure — 1297 ms · 95,9 %** (knapp über der grünen Linie)
  - **deepgram+openai+azure — 1608 ms · 99,9 %** (oben: zuverlässigste der drei)
- **Titel (zweizeilig):** „Latenz vs. Joint-Completion je Pipeline (27 Kombinationen)" und als Befund-Zeile „Die schnellste Pipeline (Groq) läuft real nur in ~67 % der Fälle durch".

## Die Messwerte (mit Zahlen)

Quelle der Punkte: `analysis/tables/07_pipeline_availability.csv` (Spalte `stream_e2e` für x, `jcp_pct` für y, `pareto` markiert die Front). Die drei Pareto-Punkte:

| Pipeline | E2E-Latenz Median | JCP | P(STT) | P(LLM) | P(TTS) |
|---|---:|---:|---:|---:|---:|
| deepgram+groq+azure | 1134 ms | **67,0 %** | 99,96 % | 67,05 % | 99,96 % |
| deepgram+mistral+azure | 1297 ms | **95,9 %** | 99,96 % | 96,0 % | 99,96 % |
| deepgram+openai+azure | 1608 ms | **99,9 %** | 99,96 % | 99,96 % | 99,96 % |

- **Wie die E2E-Latenz zustande kommt:** Die x-Achse summiert die Komponenten-Mediane des Cold-Start-Streamings: `stt_connect + stt_ttft + llm_ttft + tts_ttfa`. Dass diese Summe den Verbindungsaufbau nicht doppelt zählt, liegt an einer Metrik-Asymmetrie: Die STT-ttft ist connect-*exklusiv* (gemessen ab dem ersten Audio-Chunk, also nach dem Connect), weshalb der STT-Connect separat aufaddiert wird; LLM-ttft und TTS-ttfa sind dagegen connect-*inklusiv* (ihr eigener Verbindungsaufbau steckt bereits im Wert). Für die beste Kombi: 425 (stt_connect) + 575 (stt_ttft) + 68 (llm) + 67 (tts) ≈ 1134 ms.
- **JCP-Berechnung:** Joint-Completion = P(STT) × P(LLM) × P(TTS) unter Unabhängigkeitsannahme. Die LLM-Komponente dominiert das Ergebnis: Groq 67,05 %, Mistral 96,0 %, OpenAI 99,96 %. STT (Deepgram) und TTS (Azure) liegen je bei ~99,96 % und ziehen das Produkt kaum.
- **Groqs 67 %:** Laut `known_anomalies.md` Abschnitt 1.1 kommen pro Slot konstant **67 erfolgreiche Runs** (min 67, median 67, max 70 über alle 56 Slots) durch, danach HTTP 429. Das ist ein deterministisches Free-Tier-RPM-Quota, kein zufälliges Versagen — die 67,05 % sind der Anteil 67/100 je Slot, nicht eine i.i.d.-Erfolgswahrscheinlichkeit pro Anfrage.
- **Rev.ai-Pipelines** (alle Kombinationen mit STT=revai) liegen latenzmäßig weiter rechts und in der Zuverlässigkeit tiefer, weil Rev.ais STT-Verfügbarkeit nur ~89,8 % beträgt (Provider-Flakiness, 571/5600 Connection-Failures = 10,2 % Errors, `known_anomalies.md` 1.3) — z. B. revai+groq+azure 2152 ms · 60,2 %.
- **Latenz-Plausibilisierung** via `07_pipeline_montecarlo.csv`: Der Monte-Carlo-Median der besten Kombi (1145 ms, Faltung der empirischen Verteilungen) weicht nur 0,93 % von der Median-Summe (1134 ms) ab. p95 liegt bei ~1350 ms; nur **24,2 %** der Einzelläufe der besten Kombi liegen unter 1000 ms (Spalte `p_under_1s`). Keine der 27 Kombis erreicht im Median die 1-Sekunden-Marke (0/27).

## Was man daraus ableitet (der Befund)

Der Befund ist ein **Latenz-Zuverlässigkeits-Tradeoff**: Die latenzschnellste Pipeline (deepgram+groq+azure, 1134 ms) ist mit 67 % JCP unter der 95-%-Schwelle und damit nicht produktionstauglich. Wer Zuverlässigkeit will, zahlt Latenz: deepgram+mistral+azure (+163 ms → 95,9 %) oder deepgram+openai+azure (+474 ms → 99,9 %). Die Pareto-Front macht explizit, dass keine Pipeline in beiden Dimensionen optimal ist.

Das ist nicht trivial, weil eine reine Latenz-Tabelle (vorige E2E-Latenz-Figur) Groq als klaren Sieger ausweist und damit zu einer falschen Empfehlung führen würde. Erst die zweite Dimension fängt die operative Realität (das Free-Tier-Quota) ein und korrigiert die Empfehlung. Für die Forschungsfrage liefert die Figur den anwendungsnahen Schluss: Die Provider-Wahl an der LLM-Stelle entscheidet die Pipeline-Zuverlässigkeit fast allein, und die schnellste Backend-Verarbeitung ist nicht automatisch die einsetzbare — wobei die hier gemessene Unzuverlässigkeit von Groq ein Artefakt des kostenlosen Tarifs ist, keine intrinsische Engine-Eigenschaft.

## Rolle im Gespräch

Diese Figur ist die **praktische Implikation** am Ende des E2E-Strangs. Nachdem die vorherigen Figuren gezeigt haben, dass aus EU-Sicht die Backend-Verarbeitung die Latenz dominiert (die STT/TTS-Inversion *falsifiziert* die Hypothese, die Region erkläre die Latenz hinreichend) und dass keine Cold-Start-Pipeline die 1-Sekunden-Marke im Median erreicht, übersetzt diese Figur die Befunde in eine umsetzbare Provider-Empfehlung. Sie verhindert die naive Schlussfolgerung „nimm das schnellste LLM" und zeigt, dass eine seriöse Empfehlung beide Achsen — Latenz und Verfügbarkeit — braucht.

## Grenzen / ehrliche Caveats

- **JCP ist eine obere Schranke, kein i.i.d.-Zufall:** Joint-Completion = P(STT)·P(LLM)·P(TTS) setzt Unabhängigkeit der drei Stufen voraus. Groqs 67 % ist ein **deterministisches Free-Tier-Quota** (HTTP 429 nach ~67 Erfolgen/Slot), keine echte Per-Request-Wahrscheinlichkeit. Die JCP-Zahl ist daher als obere Schranke bzw. Tarif-Artefakt zu lesen, nicht als exakte Erfolgswahrscheinlichkeit pro Anfrage. Mit einem bezahlten Tarif entfällt dieser Punkt — Groq läge dann oben.
- **Median statt Verteilung:** Die x-Achse zeigt den Latenz-Median. Die Einzelläufe streuen erheblich (p95 der besten Kombi ~1350 ms; nur ~24 % unter 1 s). Die Figur zeigt nicht die Tail-Latenz; dafür ist die Monte-Carlo-Tabelle zuständig.
- **Mediane sind nicht additiv:** Die E2E-Latenz auf der x-Achse ist eine Summe von Komponenten-Medianen. Die Monte-Carlo-Faltung (`07_pipeline_montecarlo.csv`) bestätigt die Größenordnung (Abweichung der besten Kombi 0,93 %), aber für einzelne Kombinationen mit Mistral/OpenAI treten Abweichungen bis ~3,7 % auf.
- **Cold-Start-Streaming:** Die Latenzen gelten für den Cold-Start (neue TCP+TLS-Verbindung je Session). Warm wäre die Pipeline deutlich schneller (~666 ms in der Warm-Schätzung ohne stt_connect).
- **Keine WER/Qualität:** Die Figur misst nur den technischen Durchlauf-Erfolg (Completion), nicht Transkriptions- oder Antwortqualität.
- **n=1 EU-Provider je Kategorie:** Die Aussage „Engine vor Region" ist eine Anteils-, keine Kausalaussage — Region und Engine sind konfundiert, da pro Kategorie nur ein EU-Provider gemessen wurde.

## Wenn der Prof fragt

- **„Warum ist Groqs 67 % keine echte Wahrscheinlichkeit?"** Weil es ein deterministisches Free-Tier-RPM-Limit ist: Pro Slot kommen konstant ~67 Runs durch (min 67, median 67), danach HTTP 429. Das ist kein zufälliges Versagen, sondern ein hartes Quota. Die JCP-Zahl ist daher eine obere Schranke unter der Unabhängigkeitsannahme und ein Artefakt des kostenlosen Tarifs — mit bezahltem Tarif läge Groq oben.
- **„Warum nicht einfach die schnellste Pipeline empfehlen?"** Weil die schnellste (deepgram+groq+azure, 1134 ms) mit 67 % unter der 95-%-Schwelle liegt — unter der gegebenen Messbedingung läuft etwa jede dritte Anfrage nicht durch. Die saubere Empfehlung für den Produktivbetrieb ist deepgram+mistral+azure (1297 ms, 95,9 %) oder, wenn maximale Zuverlässigkeit zählt, deepgram+openai+azure (1608 ms, 99,9 %).
- **„Warum dominiert die Farbe (LLM) die y-Achse so stark?"** Weil STT (Deepgram/Azure) und TTS (Azure) je ~99,96 % Verfügbarkeit haben; der einzige nennenswerte Ausfallfaktor sitzt beim LLM (Groq 67 %, Mistral 96 %, OpenAI 99,96 %). Rev.ai-STT (~89,8 %) zieht zusätzlich die Pipelines mit revai nach unten — daher das untere Band bei ~60 % (Rev.ai × Groq).
- **„Zählt die E2E-Summe den Connect doppelt?"** Nein. Die STT-ttft ist connect-exklusiv (ab dem ersten Audio-Chunk gemessen), weshalb der STT-Connect separat addiert wird; LLM-ttft und TTS-ttfa sind connect-inklusiv. Die Summe `stt_connect + stt_ttft + llm_ttft + tts_ttfa` ist daher korrekt und zählt den Verbindungsaufbau nicht doppelt.
