# Modul 15 — MEDIUM-Punkte & Confounds

**Ziel:** Die wichtigsten Reporting- und Interpretations-Fallen aus dem Audit kennen und sauber entkräften. Klar trennen, welche Punkte nur das *Reporting* (wie man Zahlen aufschreibt) und welche die *Interpretation* (wie man Zahlen kausal deutet) betreffen.

> **Namens-Warnung (wichtig):** Die hier behandelten Punkte **M1, M2, M3, …** sind die **MEDIUM-Audit-Punkte** aus dem Code-/Methoden-Audit — **NICHT** die Lernmodule. Im Text durchgängig „**MEDIUM-Punkt M3**" o. Ä. sagen, damit nichts mit den Lernmodulen verwechselt wird.

> **Zahlen-Status:** Alle Zahlen sind die **finalen Vollkampagne-Werte (56/56 Slots, A4 = Median der Slot-Mediane, success-only)**. **Bootstrap-CI noch ausstehend.** Die Ordnung der Anbieter ändert sich nicht.

## 15.1 Begriffe

- **Reporting-Punkt:** betrifft, *wie* eine Zahl/Formel aufgeschrieben wird. Macht eine Zahl falsch, ist aber leicht korrigierbar.
- **Interpretations-Punkt:** betrifft, *wie* die Zahlen **kausal** gedeutet werden (Ursache/Wirkung). Kann eine ganze Schlussfolgerung kippen → die gefährlicheren Punkte.
- **Edge / CDN-Edge:** Randknoten eines Content-Delivery-Netzwerks (z. B. Cloudflare), der die Verbindung *nahe Frankfurt* terminiert (~1 ms), nicht am US-Server.
- **ASN (Autonomous System Number):** Kennung eines Betreibernetzes. `AS13335 = Cloudflare`.
- **Backhaul:** Zubringerstrecke von der CDN-Edge (Frankfurt) weiter zum eigentlichen Origin-Server (meist USA).
- **Confound (Störfaktor):** versteckte Variable, die eine Schlussfolgerung verfälschen könnte.
- **identical-edge:** Aufbau, bei dem mehrere Anbieter an *derselben* Edge (gleiche IPs/ASN/RTT) terminieren → die Netzvariable ist konstant.
- **RTT (Round-Trip-Zeit):** Zeit, die ein Paket zum Ziel und zurück braucht.
- **TLS-Handshake:** Aushandeln der verschlüsselten Verbindung vor dem ersten Request.
- **Diurnal-Effekt:** Tageszeit-Abhängigkeit einer Messgröße.

## 15.2 Übersichtstabelle der Punkte

| Punkt | Thema | Typ | Kurzfazit |
|-------|-------|-----|-----------|
| **M1** | E2E-Formel | Reporting | Sequenzielles E2E braucht `stt_ttft` (Final), nicht `ttfp` |
| **M2** | OpenAI-TTS @ Cloudflare | **Interpretation** | Zweite identical-edge-Instanz → stützt C1; „trotz US-Konkurrenz" nur ggü. Deepgram |
| **M3** | Backhaul-Confound | **Interpretation** | Mit eigenen Daten widerlegbar (Groq/OpenAI = gleicher Pfad, ~420 ms Differenz) |
| **M4** | TLS-1.2-RTT (rev.ai) | **Interpretation** | +1 RTT (~143 ms) ist **Protokoll, nicht Geografie** |
| **M6** | Round 0 | Reporting/Sauberkeit | Extra-kalter Cold-Start; Median immun → Round 0 als Warm-up |
| **M9** | Deepgram-Textmix | **Interpretation (teils)** | Scheintagesgang = Längeneffekt (corr `0,915`) |
| **M10** | OpenAI-TTS Fail/Diurnal | Reporting | Fail-Rate real **3,1 % (173/5600)** (nicht 8 %); Diurnal **unbestätigt** |

## 15.3 MEDIUM-Punkt M1 — Die E2E-Formel (Reporting)

**E2E (End-to-End):** Latenz der gesamten Pipeline über alle drei Stufen (STT → LLM → TTS). Die Pipeline ist **sequenziell**: das LLM startet erst, wenn das **vollständige (finale) Transkript** vorliegt.

Für STT gibt es zwei Metriken:

- **`ttfp` (Time-to-first-Partial):** erstes live erkanntes Wort *während* des Sprechens.
- **`ttft` (Final-Transkript):** Erkennung vollständig abgeschlossen.

| In die E2E-Summe gehört | Falsch wäre |
|-------------------------|-------------|
| `connect_total + stt_ttft` (Final) | eine `ttfp`-Summe |

**Falle:** Eine `ttfp`-Summe würde die STT-Phase um **~3,7 bis 3,9 s** *unterschätzen* (fast 4 s zu wenig), weil das LLM eben nicht auf das erste angetippte Wort, sondern auf das fertige Transkript wartet.

**`ttfp` ist trotzdem nicht wertlos:** es beschreibt die *Standalone-Responsiveness* der Spracherkennung — nur eben nicht die Pipeline.

## 15.4 MEDIUM-Punkt M2 — OpenAI-TTS @ Cloudflare (Interpretation)

**Befund:** OpenAI-TTS terminiert **ebenfalls bei Cloudflare Frankfurt** (`AS13335`, **gleiche IPs / dieselbe Edge wie die OpenAI-LLM**, **~1 ms connect**). Damit ist es eine **zweite identical-edge-Instanz**: gleiche Edge, trotzdem hohe Latenz (`ttfa` ~942 ms ≈ reines Backend, connect-exkl. ~941 ms) → **stützt C1 zusätzlich**.

**Konsequenz für die Azure-Aussage:** „Azure = schnellstes TTS *trotz US-Konkurrenz*" gilt **sauber nur gegenüber Deepgram** (andere Netzlage, echter US-Transit). Gegenüber OpenAI-TTS an der **gemeinsamen** Cloudflare-Edge ist es wieder eine saubere identical-edge-Aussage.

→ **Interpretations-Punkt**, weil er ändert, *gegen wen* die Azure-Behauptung kausal belastbar ist, und C1 einen zweiten Beleg liefert.

## 15.5 MEDIUM-Punkt M3 — Backhaul-Confound (Interpretation) ⚠️ Kernpunkt

**Der Einwand (scharf):** „~1 ms an der Edge" schließt **nicht automatisch** aus, dass die Strecke Cloudflare → US-Origin (der **Backhaul**) Zeit kostet — und zwar pro Anbieter unterschiedlich viel. Vielleicht sitzt die Spreizung im unsichtbaren Backhaul, nicht im Backend.

**So entkräftest du M3 (mit den eigenen Daten):**

1. Groq und OpenAI teilen **denselben** CF-Frankfurt-→-US-Pfad (gleicher Backhaul).
2. Sie differieren trotzdem **~420 ms** (Groq 66,9 ms vs. OpenAI 486,6 ms, A4).
3. Wäre der Backhaul die Ursache, müssten zwei Anbieter mit *demselben* Backhaul ähnlich schnell sein. Sind sie nicht.
4. → Die Spreizung liegt **nicht in der EU-Edge-Nähe und nicht im gemeinsamen Backhaul**, sondern **dahinter, im Backend**.

> **Merksatz:** Gleicher Pfad bis tief in die USA, trotzdem ~420 ms Unterschied → es kann nicht der Pfad sein.

## 15.6 MEDIUM-Punkt M4 — TLS-1.2-RTT bei rev.ai (Interpretation)

**Hintergrund:** Der **TLS-Handshake** handelt die Verschlüsselung vor dem ersten Request aus. **TLS 1.2** braucht dafür **eine ganze zusätzliche RTT** mehr als **TLS 1.3**.

**Befund:** rev.ai nutzt **TLS 1.2** statt 1.3 → das kostet **eine zusätzliche RTT (~143 ms)**.

**Pointe:** Diese ~143 ms sind **Protokoll, nicht Geografie**. rev.ai *wirkt* langsamer, aber nicht wegen Distanz, sondern weil das ältere Protokoll von Natur aus eine Runde mehr braucht.

→ **Interpretations-Punkt**: scheinbare Distanz entpuppt sich als Protokollwahl.

## 15.7 MEDIUM-Punkt M6 — Round 0 als Warm-up (Reporting/Sauberkeit)

**Befund:** Der **allererste Call eines Slots (Round 0)** ist ein **extra-kalter Cold-Start** (alles erstmalig hochgefahren) und verzerrt die **Tails** (die hohen Perzentile / Ausreißer).

- **Der Median ist immun** — ein einzelner Extremwert verschiebt die Mitte nicht.
- Nur Ränder/hohe Perzentile leiden.

**Behandlung:** **Round 0 als Warm-up** behandeln und aus der Tail-Analyse herausnehmen.

## 15.8 MEDIUM-Punkte M9 / M10 — Deepgram-Textmix & OpenAI-TTS (gemischt)

**M9 — Deepgram-Textmix (Interpretation):** Die scheinbare `ttfp`-**Tageskurve** ist ein **Input-Text-Artefakt**, kein echter Tagesgang. Die `ttfp` korreliert mit der **Textlänge** zu **`0,915`** (sehr hoch). Was wie ein Diurnal aussah, ist ein Längeneffekt des Inputs.

- **Konsequenz:** Deepgram-`ttfp` nach **`ttfp_text` (Textlänge) stratifizieren**, statt einen Tagesgang zu behaupten. Klassische aufgedeckte Scheinkausalität.

**M10 — OpenAI-TTS Verfügbarkeit/Diurnal (Reporting):**

- **Fail-Rate real `3,1 %` (173/5600, ReadTimeout)** (nicht 8 %) — Korrektur muss überall einheitlich gezogen werden; Latenz nur success-only. Jedes Quantil oberhalb 3,1 % ist zensiert → Survivorship-/Asterisk-Beispiele bleiben gültig.
- **Diurnal-Effekt unbestätigt:** zu dünn für eine belastbare Tageszeit-Aussage. Keinen Diurnal behaupten.

## 15.9 Welche Punkte betreffen die INTERPRETATION?

| Punkt | Interpretation? | Warum |
|-------|-----------------|-------|
| M2 | **Ja** | Ordnet OpenAI-TTS als 2. identical-edge ein; schärft die Azure-Aussage |
| M3 | **Ja** | Widerlegt den Backhaul-Einwand → sichert C1 ab |
| M4 | **Ja** | Erklärt scheinbare Distanz als reine Protokollwahl |
| M9 | **teilweise** | Entlarvt Scheintagesgang als Längeneffekt |
| M1 | Nein (Reporting) | Richtige Formel, keine Kausal-Änderung |
| M6 | Nein (Sauberkeit) | Tail-Hygiene, Median ohnehin immun |
| M10 (Fail-Rate) | Nein (Reporting) | Zahl korrigieren (3,1 %, 173/5600), keine Kausal-Änderung |

**Kernsatz fürs Gespräch:** Die Interpretations-Punkte sind **M2, M3, M4 (und teils M9)**, weil sie ändern, *wie* man die Zahlen kausal deutet; die übrigen sind Reporting- oder Sauberkeits-Punkte.

## Prüf-Fragen

1. Welche Punkte betreffen die Interpretation (nicht nur Reporting)?
2. Wie entkräftest du M3 (Backhaul-Confound)?
