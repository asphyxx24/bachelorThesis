# Befunde verstehen — zum Durcharbeiten

> **Zweck:** Dieses Dokument ist kein Spickzettel zum Vorlesen (das ist `spickzettel_prof.md`),
> sondern zum **Selbst-Durchdringen**. Lies es langsam, von oben nach unten. Jeder Befund hat
> dasselbe Muster:
> **🎯 Was wir gemessen haben · 📊 Die Zahl · 💡 Was es bedeutet · ⚔️ Die Falle (Prof-Frage) + deine Antwort · ✅ Selbsttest.**
>
> **Faustregel:** Wenn du einen Block zuklappst und den Befund **in zwei eigenen Sätzen** erklären
> kannst (inkl. „warum das nicht trivial ist"), besitzt du ihn. Wenn nicht — genau da nachfragen.
>
> Stand: 2026-06-09 · Zahlen = Juni-Kampagne (`data/`, 01.–07.06.2026).

---

## Teil 0 — Das große Bild (das musst du jederzeit aufsagen können)

**Die Forschungsfrage:** *In welchem Maße erklären Netzwerkeigenschaften (RTT, Protokoll,
Hosting-Region) — **im Vergleich zur Backend-Engine** — die Latenzunterschiede kommerzieller
Cloud-AI-APIs aus EU-Sicht?*

**Die Antwort (dein Kernbefund) in einem Satz:**
> Aus EU-Sicht dominiert im Kaltstart einer Voice-Pipeline **die Backend-Engine** die Latenz,
> **nicht die Netzwerknähe** — am schärfsten belegt durch die **STT/TTS-Inversion desselben
> Providers** (Azure verliert bei Spracherkennung, gewinnt bei Sprachausgabe).

**Warum das zählt:** „Näher = schneller" ist *die* Standard-Intuition in der Netzwerkwelt. Du
zeigst kontrolliert, dass sie hier **nicht** greift — und *wo* sie doch greift. Eine
Intuition-Widerlegung ist wissenschaftlich mehr wert als ein weiteres Provider-Ranking.

**Merke die Denk-Struktur:** Es gibt **drei Arten von Befunden**, und du musst wissen, welcher welcher ist:
1. **Der Kern (C1):** Engine schlägt Geografie — die inhaltliche Aussage. *(Befunde F6, F7, F8)*
2. **Die Methodik (C2):** Drei-Schichten-Zerlegung + Cloudflare-Grenze — *womit* du es beweist. *(F1, F2, F4, F9)*
3. **Die Implikation (E2E):** Was das für eine echte Voice-Pipeline heißt. *(F10, F11)*

---

## Teil 1 — Das Setup (in 5 Minuten verstanden)

Drei Begriffe musst du wasserdicht haben, sonst kippt jede Rückfrage:

**1. Cold-Start.** Jede einzelne Messung baut eine **neue** TCP+TLS-Verbindung auf — kein
Wiederverwenden (kein „Connection Pooling"). Du misst also den **Overhead jeder neuen
Gesprächssession**: der erste Satz nach einer Pause, ein frisch hochgefahrener Serverless-Worker.
→ *Warum wichtig:* Das ist der ungünstigste, aber realistische Fall. Warmes Verhalten = Future Work.
→ *Und du kannst beweisen, dass es echt Cold-Start ist:* die `connect`-Zeit bleibt über alle 100
Läufe eines Slots flach (kein Abfallen) → keine heimliche Wiederverwendung.

**2. Die drei Schichten.** Du misst dasselbe System aus drei Blickwinkeln:
- **Layer 1 (Netzwerk allein):** Ping/RTT, DNS, TLS-Version, Route — *ohne* die API zu benutzen.
  Sagt: wie weit weg, welches Protokoll, wer hostet.
- **Layer 2 (Pakete/PCAP):** Mitschnitt der echten Pakete beim Verbindungsaufbau. Deine
  **unabhängige Gegenkontrolle** — zeigt TLS 1.2 vs 1.3, Zahl der Handshake-RTTs, Cloudflare-Fronting.
- **Layer 3 (API-Latenz):** Die APIs wirklich aufrufen und stoppen: `connect`, `ttft`/`ttfa`
  (erstes Token/Audio), `total`. Die Latenz, die der **Nutzer spürt**.
→ *Der Trick:* Layer 3 zeigt den **Effekt** (wer ist schnell), Layer 1+2 liefern den **Beweis**,
  dass es **nicht** am Netzwerk liegt. Das ist dein Methoden-Kern.

**3. Die Metriken.** `connect_ms` = Verbindung steht. `ttft_ms`/`ttfa_ms` = erstes Token/erstes
Audio (das, was der Nutzer als „Reaktionszeit" erlebt). `total_ms` = alles fertig.
→ ⚠️ **Wichtigste Ehrlichkeit:** `connect_ms` misst bei STT etwas anderes als bei LLM/TTS
(STT am echten WebSocket, LLM/TTS an einem Wegwerf-Socket). **Deshalb vergleichst du quer NIE
rohes `connect_ms`, sondern nur „user-perceived Cold-Start"** = bei STT `connect+ttft`, bei
LLM/TTS `ttft`/`ttfa`. Das ist eine bewusste, deklarierte Entscheidung — kein Schlamperei-Punkt.

**Die Kampagne in Zahlen:** 7 Tage × 8 Slots/Tag = **56 Slots**, **n=100** pro Provider/Slot
→ **50.400 Einzelmessungen**, **0 % fehlende Werte**. Messpunkt: AWS Frankfurt (eu-central-1).

---

## Teil 2 — Die Befunde, einzeln durchgearbeitet

### Befund 1 — Engine schlägt Geografie bei STT *(der Kern, F6)*

**🎯 Was wir gemessen haben:** Time-to-first-token von drei Spracherkennungs-Diensten, identische
5-Sekunden-Audiodatei, aus Frankfurt.

**📊 Die Zahl:** Deepgram (US, RTT **138 ms**) liefert das erste Transkript-Token nach **~575 ms**.
Azure (EU/Italien, RTT **10 ms**) erst nach **~1715 ms**. In **56 von 56 Slots**, ohne eine einzige
Überlappung. Der *näher* gehostete Anbieter ist also **dreimal langsamer**.

**💡 Was es bedeutet:** Zerleg es: Azure spart durch die Nähe **~130 ms Netzwerk**, verliert aber
**~1130 ms** in der langsameren Erkennungs-Engine. Der Netzwerkvorteil wird von der Verarbeitung
*komplett aufgefressen*. → Nicht die Region entscheidet, sondern was das Backend rechnet.

**⚔️ Die Falle:** *„Ist ‚die Engine ist langsamer' nicht trivial?"*
→ Deine Antwort: **Nein — ich habe es zerlegt und beziffert.** Die Intuition sagt „EU-Server =
schneller, weil näher". Ich zeige, *um wie viel* (130 vs 1130 ms) der Netzwerkvorteil von der
Engine überkompensiert wird. „Gemessen und eingegrenzt" ist nicht „weiß man doch".

**✅ Selbsttest:** Kannst du erklären, warum 130 ms gespart und 1130 ms verloren *zusammen*
ergeben, dass Azure ~1140 ms langsamer ist? Und woher die 130 ms kommen (RTT-Differenz × Anzahl
Handshake-RTTs)?

---

### Befund 2 — Die Inversion bei TTS *(dein bester Beweis, F8)*

**🎯 Was wir gemessen haben:** Time-to-first-audio von drei Sprachausgabe-Diensten, identischer
Satz, aus Frankfurt. **Wichtig: Azure ist auch hier dabei — derselbe Anbieter, dieselbe Region wie bei STT.**

**📊 Die Zahl:** Jetzt **gewinnt** Azure (EU): ttfa **~67 ms** vs. Deepgram (US) **~557 ms** vs.
OpenAI (US) **~954 ms**.

**💡 Was es bedeutet — präzise (NICHT überziehen!):** Bei STT *verliert* Azure, bei TTS *gewinnt*
Azure. **Gleicher Standort, gleiche RTT (~10 ms), gegensätzliches Ergebnis.** Wenn allein die
geografische Lage die Latenz bestimmte, müsste Azure *immer* gleich abschneiden. Tut es nicht.
→ Damit ist die Hypothese **„die Region erklärt die Latenz"** sauber **widerlegt** (falsifiziert):
ein und derselbe Standort liefert entgegengesetzte Ergebnisse.

> ⚠️ **Wichtige Ehrlichkeit (sonst zerlegt dich der Prüfer):** Die Inversion ist **KEIN sauberes
> „natürliches Experiment"** und beweist **NICHT** „die Engine erklärt alles". Sie variiert nämlich
> *zwei* Dinge gleichzeitig — die **Aufgabe** (STT→TTS) *und* die **Engine**. Konstant gehalten ist
> nur die **Region**. Sie kann also nur die Geografie-Hypothese *kippen*, nicht die Engine-Hypothese
> *belegen*. (Sie ist sogar mit „STT ist generell teurer als TTS" verträglich.) Deine korrekte,
> wasserdichte Formulierung lautet daher: **„Die Region kann die Latenz nicht hinreichend erklären,
> weil derselbe Standort entgegengesetzte Ergebnisse liefert."** Mehr trägt das Design nicht — und
> mehr brauchst du auch nicht, denn die Forschungsfrage ist eine *Anteils*-Frage (Netzwerk vs.
> Engine), keine strenge Kausalfrage.

**⚔️ Die Falle:** *„Vielleicht ist Azures STT einfach ein schlechtes Produkt, kein genereller Effekt?"*
→ Deine Antwort: Genau das ist ja der Punkt — der treibende Faktor ist **Produkt/Engine**, nicht
Geografie. Ob Azures STT „schlecht" oder „anders ausgelegt" ist, ändert die Antwort auf die
Forschungsfrage nicht: die geografische Nähe ist es nicht. Ich mache bewusst eine **Anteils-Aussage**,
keine Kausalaussage über Engines im Allgemeinen (n=1 EU-Provider pro Kategorie — meine Limitation Nr. 1).

**✅ Selbsttest:** Was genau *widerlegt* die Inversion — und was *belegt* sie **nicht**?
(Wenn du hier „sie beweist, dass die Engine alles erklärt" sagst, bist du in der Falle.)

---

### Befund 3 — Das LLM-Ranking *(F7, der Nebenschauplatz mit Pointe)*

**🎯 Was wir gemessen haben:** Time-to-first-token von drei Sprachmodellen, identischer Prompt.

**📊 Die Zahl:** Groq **~68 ms** · Mistral **~231 ms** · OpenAI **~542 ms**. Groq ist ~8× schneller
als OpenAI. Alle drei sitzen hinter Cloudflare (RTT ~1 ms) — Netzwerk spielt hier praktisch keine Rolle.

**💡 Was es bedeutet:** Hier ist das Netzwerk *eliminiert* (alle ~1 ms entfernt), und es bleiben
**reine Engine-Unterschiede**. Groqs Spezial-Hardware (LPU) erklärt den Vorsprung. → Stützt den
Kern: wo Netzwerk wegfällt, sieht man die Engine pur.

**⚔️ Die Falle:** *„Groq hat aber 33 % Fehler — ist der Wert überhaupt belastbar?"*
→ Deine Antwort: Die **3755 erfolgreichen** Messungen sind statistisch reichlich. Die Fehler sind
ein **Free-Tier-Rate-Limit** (HTTP 429), kein Latenzproblem — siehe Befund 9 (Verfügbarkeit), wo
ich genau das offen behandle.

**✅ Selbsttest:** Warum ist es fair, Groqs Latenz trotz 33 % Fehlerrate zu berichten — und wo
gehört die Fehlerrate stattdessen hin?

---

### Befund 4 — Drei RTT-Klassen & die Cloudflare-Grenze *(die Methoden-Schicht, F1 + F4)*

**🎯 Was wir gemessen haben:** Layer 1 — reine Ping-RTT zu allen Endpunkten + Layer 2 — wer hinter
Cloudflare sitzt.

**📊 Die Zahl:** Drei saubere Klassen: **Cloudflare-Edge ~1 ms** (OpenAI, Groq, Mistral) ·
**Azure Italien ~10 ms** · **US ~140 ms** (Deepgram 138, Rev.ai 144). **4 von 9** Providern sitzen
hinter Cloudflare (Frankfurt-Edge).

**💡 Was es bedeutet — und warum das deine Gültigkeitsgrenze ist:** Bei den 4 Cloudflare-Providern
misst der Ping nur die **~1 ms zum Frankfurt-Edge**, *nicht* den Weg zum echten Backend dahinter.
Dort **kann** eine reine Netzwerkmessung den Backend-Anteil prinzipiell gar nicht mehr sehen. Das
markiert ehrlich die **Grenze**, ab der „Netzwerk erklärt Latenz" nicht mehr anwendbar ist.

**⚔️ Die Falle:** *„Dann ist Ihre Cross-Layer-Heuristik doch wertlos?"*
→ Deine Antwort: Für die 4 Cloudflare-Provider — ja, und das **sage ich offen**. Für die 4 direkt
gehosteten Provider (mit echtem Backend-RTT) gilt sie. Die Grenze zu *kennen und zu benennen* ist
selbst ein Methodenbeitrag.

**✅ Selbsttest:** Warum ergibt „N_RTTs × Edge-RTT" für einen Cloudflare-Provider Unsinn? (Was misst
der Edge-Ping nicht?)

---

### Befund 5 — Der TLS-1.2-Penalty bei Rev.ai *(F2, das schöne Protokoll-Detail)*

**🎯 Was wir gemessen haben:** Rev.ai nutzt als Einziger noch **TLS 1.2**, alle anderen TLS 1.3.

**📊 Die Zahl:** TLS 1.2 braucht **2 RTT** für den Handshake, TLS 1.3 nur **1 RTT**. Gemessener
Aufpreis: **+153 ms** (≈ genau eine zusätzliche US-RTT von ~144 ms). Im PCAP unabhängig bestätigt.

**💡 Was es bedeutet:** Ein reiner **Protokoll-Effekt** kostet messbar Zeit — sauber isoliert,
weil du die RTT kennst und einfach ein Handshake-RTT mehr zählst. Schönes Beispiel dafür, dass
deine Schichten-Methodik Einzeleffekte *trennen* kann.

**⚔️ Die Falle:** *„Woher wissen Sie, dass die 153 ms vom Protokoll kommen und nicht von Rev.ais Server?"*
→ Deine Antwort: Weil ich es im **Layer-2-PCAP** sehe — das ist die zusätzliche Round-Trip im
Handshake, *vor* jeder Server-Verarbeitung. Und die 153 ms ≈ eine RTT, exakt was ein zusätzliches
Handshake-RTT kosten muss.

**✅ Selbsttest:** Warum ist +153 ms ≈ 1 RTT ein in sich konsistentes Ergebnis (nicht zufällig)?

---

### Befund 6 — Das Cross-Layer-Modell *(F9, der Methoden-Baustein — Vorsicht!)*

**🎯 Was wir gemessen haben:** Hängt die Layer-3-`connect`-Zeit vorhersagbar mit der Layer-1-Ping-RTT zusammen?

**📊 Die Zahl:** Für die **4 direkt gehosteten** Provider gilt `connect_ms ≈ N_RTTs × ping + k` mit
**slope 1.006**, **k 10.7 ms**, r=0.999. N_RTTs kommt **aus dem Protokoll**, nicht aus dem Fit:
HTTPS TLS 1.3 = 2, WebSocket TLS 1.3 = 3, WebSocket TLS 1.2 = 4.

**💡 Was es bedeutet:** Aus einem **kostenlosen Ping** kannst du die connect-Latenz**klasse** eines
direkt gehosteten Providers vorhersagen, ohne teure API-Calls. Praktisch, aber **bewusst klein gehalten.**

**⚔️ Die Falle (DIE wichtigste hier):** *„r=0.999 bei nur 4 Punkten — soll mich das beeindrucken?"*
→ Deine Antwort: **Nein, und deshalb nenne ich r gar nicht als Gütemaß.** Mit 4 Punkten ist ein
hohes r fast geschenkt. Mein Argument ist **nicht** der Fit, sondern (a) dass die Steigung ~1 und
k ~10 ms *physikalisch plausibel* sind und (b) dass die **PCAP-Submetriken** (TCP/TLS/WS einzeln)
die Zerlegung unabhängig stützen. Das Modell ist ein **Methoden-Baustein, kein Headline-Befund** —
genau wegen n=4.
→ *(Beim Schreiben: „r=0.999" aus den Plot-Titeln nehmen, damit es nicht als Hauptbefund missverstanden wird.)*

**✅ Selbsttest:** Warum ist ein hohes r bei n=4 *kein* starkes Argument — und welche zwei Argumente
benutzt du stattdessen?

---

### Befund 7 — Die Pipeline verfehlt das 1-Sekunden-Budget *(F10, die Implikation)*

**🎯 Was wir gemessen haben:** Wir setzen aus den Einzelmessungen alle **27 Provider-Kombinationen**
(3 STT × 3 LLM × 3 TTS) einer sequentiellen Voice-Pipeline zusammen und prüfen: schafft eine davon
im Kaltstart < 1 Sekunde?

**📊 Die Zahl:** **0 von 27.** Die beste Kombi (Deepgram + Groq + Azure) liegt bei **~1134 ms**
(= stt_connect 425 + stt_ttft 575 + llm 68 + tts 67). Mit *warmen* Verbindungen (ohne stt_connect)
wären es ~666 ms — also nur mit persistenten Verbindungen unter 1 s erreichbar.

**💡 Was es bedeutet:** Cold-Start ist ein **reines Session-Start-Problem**: die 425 ms
Verbindungsaufbau bei Deepgram sind der Knackpunkt, nicht die Verarbeitung. Und: **STT dominiert**
im Schnitt **67 %** der gesamten Pipeline-Latenz (in allen 27 Kombis) — der Flaschenhals sitzt vorne.

**⚔️ Die Falle:** *„Haben Sie die Pipeline je als Ganzes gemessen, oder addieren Sie nur drei Mediane?"*
→ Deine Antwort: Aktuell **Median-Addition** — und ich habe sie **per Monte-Carlo validiert**
(siehe Befund 8). Ein einzelner echter End-to-End-Lauf ist als zusätzliche Validierung geplant.
→ *(Das „1 Sekunde" ist eine pragmatische Obergrenze für Assistenten; natürlicher Dialog braucht
eher 200–300 ms — das ordnest du in der Diskussion ein.)*

**✅ Selbsttest:** Warum ist „Cold-Start verfehlt 1 s, warm ~666 ms" *keine* Schwäche deiner
Provider, sondern eine Aussage über Verbindungsaufbau?

---

### Befund 8 — Monte-Carlo: ist die Median-Addition überhaupt erlaubt? *(A6, NEU diese Session)*

**🎯 Warum wir das gemacht haben:** „Drei Mediane addieren" ist angreifbar — **Mediane sind nicht
additiv** (der Median einer Summe ≠ Summe der Mediane). Statt das nur zuzugeben, haben wir es *getestet*.

**🎯 Was wir gemacht haben:** **Monte-Carlo-Faltung** — wir ziehen 20.000-mal zufällig je einen
echten gemessenen Wert aus jeder Stufe (STT, LLM, TTS), summieren sie, und schauen uns die
*Verteilung* der Pipeline-Summe an. So bekommen wir den **echten** Median der Summe plus p90/p95.

**📊 Die Zahl:** Der echte Median-der-Summe weicht nur **~1,4 % im Mittel** (max 3,7 %, beste Kombi
**+0,9 %**) von der einfachen Median-Addition ab. **→ Die Addition ist als Schätzer gerechtfertigt.**
Aber: p90 = **~1273 ms**, p95 = **~1350 ms**, und nur **~24 %** der Einzelläufe schaffen < 1 s
(~76 % liegen drüber).

**💡 Was es bedeutet — der Doppelschlag:** (1) Die einfache Methode war okay (du hast sie überprüft,
nicht nur behauptet). (2) Der **Median verschweigt die Streuung**: „0/27 unter 1 s" gilt nicht nur
im Median, sondern **erst recht** für den typischen Einzel-Lauf. Du hast die Aussage also *stärker*
und *ehrlicher* gemacht.

**⚔️ Die Falle:** *„Wo ist das Konfidenzintervall der 1134 ms?"*
→ Deine Antwort: **Hier** — p90 1273, p95 1350, und der Anteil der Läufe unter 1 s ist nur 24 %.
Die Punktschätzung 1134 ms ist der Median; die Streuung steht jetzt offen daneben.

**✅ Selbsttest:** Warum ist es ein *gutes* Ergebnis, dass Monte-Carlo und Median-Addition fast
gleich sind — obwohl Mediane „eigentlich nicht additiv" sind? (Was hast du damit entkräftet?)
Und: warum ist „nur 24 % der Läufe < 1 s" eine *stärkere* Aussage als „der Median ist > 1 s"?

---

### Befund 9 — Die schnellste Pipeline ist nicht die zuverlässigste *(A8/F11, NEU diese Session)*

**🎯 Warum wir das gemacht haben:** Alle Latenz-Zahlen oben sind „wie schnell, **wenn** es klappt".
Sie verschweigen, **wie oft** es überhaupt klappt. Genau das nutzt die „beste" Kombi aus — sie
basiert auf **Groq**, das ein Drittel der Anfragen ablehnt.

**🎯 Was wir gemacht haben:** Pro Provider die **Verfügbarkeit** = Erfolg / (Erfolg + Fehler)
berechnet, und daraus je Kombi die **Joint-Completion-Probability** = P(STT) · P(LLM) · P(TTS).

**📊 Die Zahl:** Verfügbarkeit: Groq **67 %**, Rev.ai 90 %, Mistral 96 %, Rest ≥ 99,96 %. Die
Pareto-Front (alle deepgram + azure, **nur das LLM wechselt** → das LLM ist der Hebel):

| Kombi | Latenz | läuft durch in… |
|---|---:|---:|
| deepgram + **groq** + azure | 1134 ms | **67 %** |
| deepgram + **mistral** + azure | 1297 ms (+163) | **96 %** |
| deepgram + **openai** + azure | 1608 ms (+474) | **99,9 %** |

**💡 Was es bedeutet:** Ein **Latenz-vs-Zuverlässigkeit-Tradeoff**. Die Latenz-Bestmarke läuft real
nur in 2 von 3 Fällen durch. +163 ms (Mistral statt Groq) kaufen +29 Prozentpunkte Zuverlässigkeit.
→ Deine **Empfehlung:** Mistral als robustere Default-Wahl.

**⚔️ Die Falle:** *„Ihre beste Pipeline nutzt Groq, das ein Drittel ablehnt — ist die 1134 ms-Marke
ehrlich?"*
→ Deine Antwort: Genau deshalb stelle ich die Verfügbarkeit **daneben**. Groqs Ablehnung ist ein
**Free-Tier-Quota** (HTTP 429), kein Latenzfehler — auf einem bezahlten Tier verschwände sie. Aber
als Eigenschaft *dieser* Konfiguration gehört sie offen zur Latenz, und ich empfehle Mistral.

**✅ Selbsttest:** Warum ist es sauber, Groqs 429 als „Tarif-Problem, kein Latenzfehler"
einzuordnen — und warum darf man es trotzdem nicht weglassen?

---

### Befund 10 — Warum wir das „Batch"-Szenario gestrichen haben *(A7, NEU — Beispiel für saubere Arbeit)*

**🎯 Worum es ging:** Eine frühere Version verglich „Streaming" mit „Batch" und behauptete
*„Streaming spart 3350 ms"*. Wir haben diesen Vergleich **entfernt**.

**💡 Warum (das ist die Lehre):** Die 3350 ms waren ein **Messartefakt**, kein echter Effekt. Unsere
Deepgram-Empfangsschleife brach nicht beim ersten Ergebnis ab, sondern las bis zum Verbindungsschluss
weiter — ~3,4 s **Leerlauf-Tail**. Azure/Rev.ai brachen beim ersten Ergebnis ab. Also maß `total_ms`
bei den Providern **Unterschiedliches**, und der „Batch-Nachteil" war zu ~100 % dieser Tail. Der Tail
ist auch **kein** Audio-Transfer (das Hochladen dauert nur 137 ms).

**⚔️ Die Falle (die wir uns erspart haben):** *„Deepgram total_ms ist 4,3 s bei 0,6 s ttft — was
passiert in den 3,7 s, und warum hat Azure die Lücke nicht?"*
→ Hätten wir „Batch" behalten, gäbe es darauf keine gute Antwort. Jetzt lautet die Antwort: das war
ein Schleifen-Artefakt unserer Messung, wir berichten `total_ms` nur provider-intern und die Pipeline
nur als Streaming. **Dokumentiert in `known_anomalies.md §5.1`.**

**✅ Selbsttest:** Kannst du in einem Satz erklären, warum man `total_ms` *nicht* zwischen Deepgram
und Azure vergleichen darf?

---

## Teil 3 — Deine Limitationen (nenne sie ZUERST, das entwaffnet)

Ein:e gute:r Prüfer:in fragt nach Schwächen. Wenn du sie selbst zuerst nennst, drehst du die Dynamik um.
Du musst diese fünf parat haben — **mit der Entschärfung gleich dahinter**:

1. **Region und Engine sind konfundiert** (nur 1 EU-Provider pro Kategorie). → Deshalb machst du eine
   **Anteils-Aussage** („Netzwerk erklärt *weniger als* die Engine"), **keine strenge Kausalaussage**.
   Die TTS-Inversion ist das Stärkste, was ohne randomisiertes Experiment geht.
2. **E2E nie als echte Pipeline gemessen** (Median-Addition). → Per Monte-Carlo validiert (Befund 8);
   ein echter Lauf ist geplant.
3. **Cross-Layer-Modell: nur n=4.** → Deshalb Methoden-Baustein, nicht Headline; r nicht als Gütemaß.
4. **Layer-2-PCAP: andere Instanz/Tag, n=1.** → Nur für **Struktur** (TLS-Version, Fronting,
   RTT-Anzahl), nie für Absolutzeiten.
5. **7 statt 14 Tage; nur Cold-Start; Deepgram-Anycast.** → Bewusste Scope-Grenzen, benannt.

Plus eine, die du **nicht** beheben kannst: **WER/Inhaltskorrektheit** (A14) — du hast nur
Transkript-*Längen* gespeichert, keine Texte. → Ehrliche Limitation, kein Nachmessen möglich.

---

## Teil 4 — Wie alles zusammenhängt (die eine Landkarte)

```
                    FORSCHUNGSFRAGE
     "Netzwerk vs. Engine — was erklärt die Latenz aus EU-Sicht?"
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   C1: DER KERN       C2: DIE METHODIK    IMPLIKATION
   Engine > Geografie  3 Schichten +       für echte Pipeline
                       Cloudflare-Grenze
        │                  │                  │
   F6 STT US>EU        F1 RTT-Klassen     F10 0/27 < 1 s
   F8 TTS-Inversion ◄─ F4 Cloudflare 4/9      │  (validiert: F8/A6)
     (der Beweis)      F2 TLS-1.2-Penalty  F11 Latenz vs.
   F7 LLM-Ranking      F9 Cross-Layer         Zuverlässigkeit
                          (Baustein, n=4)      (Tradeoff)
```

**Lies die Landkarte so:** Die linke Spalte *behauptet* (Engine schlägt Geografie), die mittlere
*beweist es methodisch* (und zieht die Cloudflare-Grenze), die rechte *zieht die praktische Konsequenz*.
Die **TTS-Inversion (F8)** sitzt in der Mitte, weil sie zugleich Kern-Befund **und** sauberster
methodischer Beweis ist.

---

## Teil 5 — Selbsttest: kannst du diese 10 Fragen frei beantworten?

Wenn ja, besitzt du die Arbeit. Wenn bei einer „äh" kommt — **dort** mit mir nachhaken.

1. Was ist deine Forschungsfrage, und warum ist sie in *beide* Richtungen beantwortbar?
2. Warum ist die STT/TTS-Inversion ein stärkeres Argument als der STT-Befund allein?
3. Warum vergleichst du quer nie rohes `connect_ms`?
4. Was misst der Ping bei einem Cloudflare-Provider — und was *nicht*?
5. Warum ist r=0.999 bei n=4 *kein* gutes Argument, und was nimmst du stattdessen?
6. Warum verfehlt die Pipeline 1 s im Kaltstart, schafft aber warm ~666 ms?
7. Was hat die Monte-Carlo-Rechnung *bewiesen* (zwei Dinge)?
8. Warum ist die schnellste Pipeline nicht die zuverlässigste — und was empfiehlst du?
9. Warum durftest du `total_ms` nicht zwischen Deepgram und Azure vergleichen?
10. Nenne drei Limitationen — jeweils mit der Entschärfung.

---

## Verwandte Dokumente
- `notes/spickzettel_prof.md` — dasselbe als **Sprech-Skript** fürs Prof-Gespräch (30-Sek-Pitch etc.)
- `notes/findings.md` — die Befunde als **Stichpunkte + Belegquellen** (welches Notebook/welche Tabelle)
- `analysis/07_e2e_pipeline.ipynb` — §6 Monte-Carlo, §7 Verfügbarkeit, §8 Hauptbefunde (Befunde 7–9 oben)
- `data/processed/known_anomalies.md` — Daten-Caveats (u. a. §5.1 zum `total_ms`-Tail)
