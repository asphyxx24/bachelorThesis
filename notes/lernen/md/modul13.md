# Modul 13 — Aggregation (A4) & Verfügbarkeit

**Ziel:** Erklären, wie aus 5.600 Einzelwerten je Endpunkt eine ehrliche Headline-Zahl wird (zweistufiger Median + Gegenprobe + Bootstrap-CI) — und warum Verfügbarkeit eine eigene Achse ist, getrennt von der Latenz.

> **Datenbasis:** Alle Zahlen unten sind die finalen Werte aus der **Vollkampagne (56 von 56 Slots)** (A4 = Median der Slot-Mediane, success-only). **Bootstrap-CI noch ausstehend.**

## 13.1 Statistik-Vorlauf (Begriffe)

- **Mittelwert vs. Median:** Der **Mittelwert** (Durchschnitt) wird von einem einzelnen Ausreißer stark nach oben gezogen. Der **Median** ist der mittlere Wert der sortierten Stichprobe (50 % darunter, 50 % darüber) und ist **robust** gegen Extremwerte. Unsere Latenz-Verteilungen sind **rechtsschief** (langer Tail nach oben, `CV ~87 %` in der Vorkampagne) → wir nehmen grundsätzlich den **Median**.
- **Perzentil (`p50`/`p90`/`p95`/`p99`):** Der Wert, unter dem ein bestimmter Anteil der Messungen liegt. `p50` = Median. `p90` = 90 % liegen darunter. `p95`/`p99` beschreiben den **langsamen Tail** (die schlimmsten Fälle).
- **Bootstrap-Konfidenzintervall:** Man zieht aus den vorhandenen Messwerten viele tausend Mal (≥10.000) zufällig eine neue Stichprobe **mit Zurücklegen**, rechnet jedes Mal die Kennzahl (z. B. den Median) neu und liest die Streuung ab. Das **95-%-CI** ist der Bereich, in dem 95 % dieser nachgespielten Schätzungen liegen — eine ehrliche Spannweite statt eines nackten Punktschätzers. **Warum Bootstrap statt t-Intervall:** die Verteilungen sind schief, das t-Intervall unterstellt Symmetrie.
- **Pareto-Front:** Vergleich nach **zwei** Gütedimensionen gleichzeitig (hier: Latenz vs. Verfügbarkeit). Ein Kandidat liegt auf der Front, wenn ihn kein anderer in **beiden** Dimensionen zugleich schlägt (= „nicht dominiert"). Macht sichtbar, dass schnell und zuverlässig verschiedene Qualitäten sind.
- **Zensur (censoring):** Man kennt den wahren Wert nicht, weiß nur, dass er **oberhalb einer Grenze** liegt. Bei uns ist die Grenze der **Timeout (~30 s)**: Ein abgebrochener Call hatte eine echte Latenz `> 30 s`, aber wie groß genau, ist unbekannt → der Wert ist zensiert.

## 13.2 Die Aggregationsregel (A4): zweistufiger Median

**Headline je Endpunkt = Median der Slot-Mediane** (zweistufig):

1. **Stufe 1:** pro (Endpunkt × Slot-`tag`) den Median über die ~700 Runs (7 Tage × 100) bilden → **8 Slot-Mediane** (einer je Tageszeit-Slot).
2. **Stufe 2:** der **Median dieser 8 Slot-Mediane** = die Headline-Zahl.

Dazu kommt als **Gegenprobe** der **gepoolte Median** (alle Rohwerte zusammen) und ein **Bootstrap-95-%-CI**.

## 13.3 Warum Median der Slot-Mediane statt poolen

**Poolen** = alle ~5.600 Rohwerte in einen Topf, einmal Median. Zwei Fallen:

| Falle | Effekt beim Poolen | Was der zweistufige Median tut |
|-------|--------------------|--------------------------------|
| Ungleiche Erfolgs-Zahlen je Slot | Slots mit mehr **erfolgreichen** Runs werden stärker gewichtet → Tageszeiten mit besserer Verfügbarkeit ziehen die Zahl zu sich (verschönert bei US-Stoßzeiten-Rate-Limits) | gibt **jeder Tageszeit gleiches Gewicht** |
| Tagesgang (Diurnal-Effekt, US-Backend-Last) | ungewichtet vermischt | robust gegen einzelne Ausreißer-Slots |

- **Sensitivität:** Stimmen zweistufiger und gepoolter Median überein → Befund **robust**. Laufen sie auseinander → das ist **selbst ein Befund** (diurnal/ausfallabhängig).
- **Bootstrap-Status:** Das **Bootstrap-CI ist noch ausstehend**; bis dahin **immer gegen die gepoolte Variante gegenprüfen**. Mit **56 von 56 Slots** ist das Slot-Bootstrap belastbar.
- **Bonus:** Die 8 Slot-Mediane sind zugleich das **Tageszeit-Profil** je Endpunkt (Auswerteachse für US-Backend-Last).

## 13.4 Perzentil-Regel: `p95`/`p99` nur über die volle Kampagne

| Perzentil | Auflösung | Begründung |
|-----------|-----------|------------|
| `p50`, `p90` | **slot-aufgelöst** belastbar | n=100 je Slot reicht |
| `p95` | **nur gepoolt** (alle 56 Slots) + Bootstrap-CI | zu wenig Runs pro Slot |
| `p99` | **nur gepoolt** | `p99` von 100 ≈ das Maximum (Zufallstreffer, keine stabile Schätzung) |

**Faustregel (festgeschrieben):** ein Perzentil `q` ist erst stabil, wenn `n·(1−q) ≥ 5–10`. Für `p99` braucht man also **viele hundert Werte** — die ein einzelner Slot mit n=100 nicht liefert.

## 13.5 Verfügbarkeit als eigene Achse (Pareto)

- **Latenz = success-only:** nur über erfolgreiche Calls berechnet (ein Fail hat keine sinnvolle Latenz).
- **Verfügbarkeit** (Erfolgs- bzw. Fail-Rate) wird **separat** geführt — eine eigene, zweite Achse.
- **Darstellung = Pareto-Front:** Latenz **gegen** Verfügbarkeit, weil schnell und zuverlässig zwei verschiedene Gütedimensionen sind. Ein „Gewinner" wird erst **nach** der Front benannt.
- **Beispiel:** **OpenAI-TTS** ist beim Median **schnell**, hat aber **3,1 % Fails (173/5600)**. Wer nur den Median sieht, übersieht die gescheiterten Anfragen. → „Schnellstes TTS" nur **mit Ausfall-Asterisk**.

## 13.6 Survivorship-Zensur: schnell UND schlechtestes Tail

Die Prüfer-Frage: Wie kann OpenAI-TTS gleichzeitig einen schnellen `p50` und das schlechteste Tail haben?

- Bei **3,1 % Fails (173/5600)** ist **jedes Quantil oberhalb der Fail-Rate** durch den Timeout **zensiert**.
- `p95` und `p99` landen im Bereich der gescheiterten Calls → sie liegen bei **~30 s** (dem **Cap**, dem Timeout).
- Diese ~30 s sind **KEIN echtes Backend-Tail**, sondern der **abgeschnittene Timeout** (Survivorship-Bias: nur die „Überlebenden" haben echte Latenzen, die Fails sitzen alle am Cap).
- → So koexistieren ein **schneller `p50`** (erfolgreiche Calls) und ein **katastrophales `p95`/`p99`** (= zensierter Timeout).

**Berichtsregel (immer beides nebeneinander):**

> `p95 = X` (nur erfolgreiche Calls, also über die **96,9 %**, die durchkamen) — **Gesamtverfügbarkeit separat** daneben.

## 13.7 E2E = Monte-Carlo-Faltung (nicht Median-Addition)

Die Pipeline-Gesamtlatenz (STT → LLM → TTS) **nicht** durch Addition der Mediane bestimmen (alter Fehler), sondern durch **Faltung** der Phasen-Verteilungen per Simulation:

1. aus jeder Phasen-Verteilung (`stt_ttft`, `llm_ttft`, `tts_ttfa`) **zufällig einen Wert ziehen**,
2. die drei Werte **summieren**,
3. das **~10.000-mal** wiederholen.

→ daraus die echte **E2E-Verteilung** mit `p50`/`p90`/`p95` **+ Konfidenzintervall**.

**Kernsatz:** Das `p95` der Summe ist **nicht** die Summe der `p95`-Werte. Es ist extrem unwahrscheinlich, dass alle drei Phasen im selben Call gleichzeitig ihren schlechtesten Wert treffen — die Addition der hohen Perzentile unterstellt genau das und überschätzt den Tail dramatisch. Die Faltung würfelt die Phasen unabhängig zusammen und trifft die realistische Mischung.

> Ergänzend: **Joint-Completion / Pareto-Front** auch für E2E — Latenz gegen Zuverlässigkeit; OpenAI-TTS ist nicht der langsamste, aber mit Fails → nicht pauschal „beste Pipeline".

## Prüf-Fragen

1. Warum Median der Slot-Mediane statt poolen?
2. Warum p95 nur über die volle Kampagne?
3. Warum Verfügbarkeit getrennt?
4. Warum kann OpenAI-TTS gleichzeitig schnell (p50) und das schlechteste Tail haben?
