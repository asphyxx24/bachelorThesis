# Figur 3 — Die Inversion (TTS): Derselbe Azure gewinnt

![](05_tts_ttfa_cdf.png)

## Worum es geht

Diese Figur zeigt die Zeit bis zum ersten Audio-Byte (TTFA) der drei TTS-Provider im Cold-Start. Sie ist die Beleg-Figur des Reframes: Azure (EU/Italy North) gewinnt hier klar — obwohl genau dieselbe Region bei STT (Figur zur STT-TTFT) zuletzt landet. Region konstant, Ergebnis invertiert.

## Was auf der Figur zu sehen ist

Es handelt sich um drei empirische kumulative Verteilungsfunktionen (CDFs).

- **X-Achse:** `TTFA (ms)` — Time to First Audio in Millisekunden, lineare Skala (kein Log), Bereich 0 bis 2500 ms. TTFA ist hier connect-INKLUSIV, d. h. der Verbindungsaufbau ist in der gemessenen Zeit bereits enthalten (anders als bei STT-TTFT, das connect-exklusiv ab dem ersten Audio-Chunk misst).
- **Y-Achse:** `Kumulative Wahrscheinlichkeit` von 0,0 bis 1,0. Ein Punkt (x, y) liest sich als: „in einem Anteil y aller Läufe war das erste Audio nach höchstens x ms da". Je weiter eine Kurve nach links, desto schneller der Provider.
- **Drei Kurven / Farben (Legende):**
  - **Azure — grün:** ganz links, steigt fast senkrecht bei ~60–80 ms von 0 auf nahe 1 an. Eine extrem schmale, schnelle Verteilung.
  - **Deepgram — blau:** mittig. Setzt erst bei ~400 ms ein, hat eine sichtbare Schulter bei etwa 0,29 (~500 ms — nahe der gestrichelten Budgetlinie), steigt dann steil bei ~560–600 ms auf nahe 1.
  - **OpenAI — rot:** ganz rechts, die breiteste und langsamste Kurve. Beginnt bei ~500 ms, steigt flach mit Zwischenstufen bis ~1300 ms, ein langer Schwanz reicht über 2000 ms hinaus.
- **Referenzlinie:** graue gestrichelte Vertikale bei **500 ms („500 ms Budget")** — eine gesetzte Orientierungsmarke für TTS-Reaktionszeit. Azure liegt komplett links davon; Deepgram kreuzt sie knapp; OpenAI beginnt rechts davon.
- **Titel (oben):** „Azure: erstes Audio nach 67 ms — Deepgram 557 ms, OpenAI 954 ms (Median)". Die 67 ms im Titel sind die auf ganze Millisekunden gerundete Form des CSV-Medians 66,6 ms.
- **Annotation unten rechts:** `n = 5.598 / 5.599 / 5.599 (Azure / Deepgram / OpenAI)` — die Stichprobengrößen je Provider.

## Die Messwerte (mit Zahlen)

Quelle: `analysis/tables/05_tts_statistics.csv`, Metrik `ttfa_ms`, p50 (Median); F8 in `notes/findings.md`.

| Provider | Region | n | TTFA-Median | connect-Median | proc-Median |
|---|---|---:|---:|---:|---:|
| Azure | EU (Italy North) | 5.598 | **66,6 ms** | 33,3 ms | 33,2 ms |
| Deepgram | US (Anycast) | 5.599 | 556,5 ms | 290,8 ms | 262,3 ms |
| OpenAI | US (Cloudflare) | 5.599 | 954,2 ms | 9,2 ms | 943,6 ms |

- Azure ist im Median ~8,4× schneller als Deepgram und ~14,3× schneller als OpenAI.
- **Azures Vorteil ist kombiniert:** niedriger connect (EU, 33 ms) UND schnelle Backend-Verarbeitung (proc 33 ms).
- **OpenAI hat den niedrigsten connect** (9,2 ms, Cloudflare-Edge), wird aber von der langsamsten Verarbeitung (proc 943,6 ms) aufgezehrt — der Netzwerkvorteil zählt nicht durch.
- Die Tails (p99) sind aussagekräftig: Azure 475,6 ms, Deepgram 630,8 ms, OpenAI 2742,5 ms — OpenAIs breite rote Kurve ist genau dieser lange Schwanz.

## Was man daraus ableitet (der Befund / der Fortschritt)

Bei STT ist Azure der langsamste Provider (TTFT 1715 ms gegenüber Deepgram 575 ms), obwohl Azure mit RTT ~10 ms netzwerknäher ist als das US-Deepgram (RTT ~138 ms). Bei TTS dreht sich das Bild um: **derselbe Azure aus derselben Region (Italy North) gewinnt** mit 67 ms deutlich.

Das ist der entscheidende Schritt im Argument: Wäre die Latenz hinreichend durch die Hosting-Region/Netzwerknähe erklärt, müsste Azure in beiden Kategorien ähnlich abschneiden — die Region ist ja konstant. Sie tut es nicht. Damit **falsifiziert die STT/TTS-Inversion die Hypothese „die Region erklärt die Latenz hinreichend".** Was sich zwischen STT und TTS ändert, ist nicht die Geografie, sondern die Backend-Verarbeitung (anderes Modell, anderer Verarbeitungspfad). Der Befund stützt die Forschungsfrage direkt — Netzwerk- vs. Backend-Anteil —: hier dominiert messbar der Backend-Anteil.

Nicht-trivial ist das, weil die Intuition (näheres Rechenzentrum = niedrigere Latenz) hier widerlegt wird, und zwar per Within-Provider-Vergleich, der Region und Routing konstant hält.

## Rolle im Gespräch

Dies ist die zentrale Figur des Sets. Die STT-Figur zeigt das kontraintuitive Einzelergebnis (US schlägt EU); diese TTS-Figur liefert das **Argument durch Inversion**: nur durch Wechsel der Aufgabe — bei festgehaltenem Provider und fester Region — kehrt sich das Ranking um. Sie kommt direkt nach der STT-Figur und macht aus „ein überraschendes Ergebnis" ein **falsifizierendes Argument** gegen die Geografie-Hypothese. Sie trägt Contribution C1 („Engine schlägt Geografie").

## Grenzen / ehrliche Caveats

- **Anteils-, keine Kausalaussage.** Die Inversion falsifiziert „Region erklärt alles hinreichend"; sie beweist NICHT „die Engine erklärt alles". Es gibt je Kategorie nur n=1 EU-Provider; Region und Engine sind konfundiert. Daher von „Backend-Verarbeitung" sprechen, nicht kausal von „der Engine".
- **TTFA misst connect-inklusiv**, also Verbindungsaufbau plus Verarbeitung gemischt. Die Zerlegung in connect_ms vs. proc_ms (Tabelle) ist nötig, um den Anteil zu trennen — die CDF allein zeigt nur die Summe.
- **OpenAI sitzt hinter Cloudflare.** Sein connect_ms (~9 ms) misst den Cloudflare-Edge, nicht das US-Backend; cross-Provider ist connect nur für die direkten Provider (Azure, Deepgram) sauber vergleichbar.
- TTFA ist nicht wahrgenommene Sprachqualität oder Audio-Vollständigkeit — nur Zeit bis zum ersten Byte. `total_ms` (Vollständigkeit) steht separat in der Tabelle.
- Die „500 ms Budget"-Linie ist eine gesetzte Orientierungsmarke, keine aus den Daten abgeleitete Schwelle.

## Wenn der Prof fragt

**„Beweist die Inversion, dass die Engine die Latenz erklärt?"**
Nein. Sie falsifiziert nur die Gegenhypothese, dass die Region hinreichend erklärt: derselbe Provider in derselben Region invertiert sein Ranking je nach Aufgabe — also kann die Region es nicht hinreichend erklären. Eine kausale Aussage „die Engine erklärt alles" ist nicht zulässig, weil je Kategorie nur ein EU-Provider vorliegt und Region/Engine konfundiert sind. Es ist eine Anteilsaussage über die Backend-Verarbeitung.

**„Warum ist OpenAI so langsam und so breit gestreut, obwohl es den niedrigsten connect hat?"**
OpenAIs connect liegt bei ~9 ms (Cloudflare-Edge), aber die proc-Zeit liegt im Median bei ~944 ms mit großer Streuung (p99 ~2742 ms) — daher die breite rote Kurve mit langem Tail. Der minimale Netzwerkvorteil wird vollständig von der langsamen Verarbeitung aufgezehrt. Das ist exakt die Pointe: nicht das Netzwerk, sondern die Backend-Verarbeitung bestimmt hier die TTFA.
