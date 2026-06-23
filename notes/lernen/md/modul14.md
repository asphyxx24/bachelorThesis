# Modul 14 — HIGH-Auflagen H1–H4

**Ziel:** Die vier wichtigsten Audit-Befunde (H1–H4) als **Stärke** präsentieren — Selbstkorrektur statt Makel — und je eine ruhige Ein-Satz-Antwort an einen skeptischen Prüfer parat haben.

## 14.0 Rahmen: Was ist das Audit, was heißt „GO mit Auflagen"?

- **Audit** = systematische Selbstprüfung der Arbeit. Hier: ein großer automatisierter Durchgang am **2026-06-18** mit **72 Prüf-Agenten**, die Methodik und Daten Stück für Stück gegengelesen haben.
- **Urteil:** **GO-mit-Auflagen** — die Arbeit darf weiterlaufen, die Kernmethodik ist gültig, aber eine Liste von Punkten muss **vor der Auswertung** sitzen. Insgesamt **85 Befunde**.
- Die vier wichtigsten tragen die Kürzel **H1–H4**. Das **H** steht für **HIGH** (hohe Priorität).
- **Leitgedanke (zentral):** Diese Punkte selbst gefunden und korrigiert zu haben — bevor ein Prüfer sie sieht — ist ein **Vertrauens-Plus**, kein Makel. Wissenschaftliches Arbeiten heißt, die eigenen Daten kritisch zu prüfen und Reporting-Fehler an sich selbst zu melden.
- **Wichtig zu allen Zahlen:** Maßgeblich sind die **finalen 56-von-56-Slot-Zahlen** (Vollkampagne, abgeschlossen; A4 = Median der Slot-Mediane, success-only). Ein **Slot** = festgelegtes Messfenster (8/Tag). **Bootstrap-CI noch ausstehend.**

> **Gemeinsamer Nenner aller vier Auflagen:** Es sind **durchweg Doku-/Reporting-Korrekturen, KEINE Neumessungen.** C1 (die Kernaussage „Backend statt Geografie") ist von keinem Punkt inhaltlich bedroht — sie steht danach auf festerem Grund.

## 14.1 H1 — Headline-Zahlen: Pilot vs. Kampagne

**Begriffe:**
- **Predeploy-Pilot** = kleiner Vorab-Testlauf (`n=200`, **2 Slots**), um zu prüfen, ob das Setup funktioniert, bevor die große Kampagne startet.
- **Kampagne** = der Hauptlauf (7 Tage × 8 Slots).
- **`ttft`** (Time-to-first-Token) = Spanne vom Absenden der Anfrage bis zum ersten zurückkommenden Antwort-Stück.

**Das Problem:** Früher zitiert wurden für LLM-`ttft` die Werte **75 / 268 / 476 ms**. Diese stammen aus dem **Piloten** und **reproduzieren aus keinem Kampagnendatensatz** — sie sehen aus wie Befunde, sind aber Pilot-Artefakte.

**Die Korrektur:** Maßgeblich sind die **Kampagnenzahlen** (56 von 56 Slots, A4):

| Anbieter | LLM-`ttft` (56 Slots, A4) |
|----------|---------------------------|
| Groq | **66,9 ms** |
| Mistral | **278,9 ms** |
| OpenAI | **486,6 ms** |

- **Ordnung identisch:** `groq < mistral < openai`.
- **Kernaussage identisch:** Die Spreizung entsteht trotz nahezu gleichem Netz.
- **Faktor:** rund **7,3×** (A4; gepoolt 8,3×). Der finale Faktor ist sogar **größer** als der Pilot-Faktor 6,4× — die Ordnung ist identisch, der Kernbefund wird dadurch **stärker** (die Spreizung ist real und groß).

**Ruhige Ein-Satz-Antwort:** *Die früher zitierten 75/268/476 ms stammen aus dem Predeploy-Piloten und reproduzieren aus keinem Kampagnendatensatz; maßgeblich sind die Kampagnenzahlen 66,9 / 278,9 / 486,6 ms — Ordnung und Kernaussage bleiben identisch, der Faktor (~7,3×, gepoolt 8,3×) ist sogar größer als im Piloten, der Kernbefund wird dadurch stärker.*

## 14.2 H2 — Reichweite der Eichung

**Begriffe:**
- **Eichung** = das Messinstrument gegen eine unabhängige Wahrheit prüfen und zeigen, dass es richtig misst.
- **Layer 2** = Paketaufzeichnung (Mitschnitt des echten Netzwerkverkehrs).
- **Connect-Timer** = die Software-Uhr, die den Verbindungsaufbau (TCP-Handshake) stoppt.
- **`ttfa`** (Time-to-first-Audio) = Spanne bis zum ersten hörbaren Stück Sprachausgabe (TTS).
- **`perf_counter`** = der hochauflösende Zeitzähler im Programm.

**Das Problem:** Die Versuchung wäre zu sagen „alle meine Latenzmessungen sind paket-geeicht". Das wäre zu viel behauptet.

**Was tatsächlich gilt:**

| Messgröße | Paket-geeicht? | Mechanismus |
|-----------|----------------|-------------|
| `tcp_handshake` (Connect-Timer) | **Ja**, ±0,1 ms | App-Timer vs. Wire-Pakete verglichen |
| `ttft` | **Nein** (nicht direkt) | gleicher `perf_counter`, startet aber erst beim Request-Absenden tief im httpx/websockets-Stack |
| `ttfa` | **Nein** (nicht direkt) | wie `ttft` |

- Der **Connect-Timer** liegt nur ~**0,1 ms** neben den echten Paketen → paket-validiert.
- `ttft`/`ttfa` nutzen **denselben** `perf_counter`, sind aber **nicht direkt** gegen Pakete validiert, weil sie später starten.

**Der ehrliche Umgang:** Das **aktiv dazusagen** statt verschweigen — präzise sagen, welcher Teil geeicht ist und welcher nicht.

**Ruhige Ein-Satz-Antwort:** *Paket-geeicht ist nur der Connect-Timer (±0,1 ms); `ttft` und `ttfa` nutzen denselben `perf_counter`, sind aber nicht direkt paket-validiert — und genau das sage ich aktiv dazu.*

## 14.3 H3 — Fehler-Filter: es gibt kein Enum

**Begriffe:**
- **Enum** = Aufzählung fester, erlaubter Werte (z. B. ein Feld `error_kind` mit Werten `timeout`, `server_error`, …).
- **Roh-String** = der Fehler wird als freier Text geloggt, so wie die Fehlermeldung anfällt.
- **Bucketing** = Sortieren in „Eimer" (Kategorien) — hier per **Teilstring-Suche**.

**Das Problem:** Es gibt **kein** `error_kind`-Enum im Code. Fehler liegen als **Roh-String** vor. Ein naiver Filter `error == "timeout"` (exakte Gleichheit) verfehlt **158 von 161** echten Timeouts, weil die echten Fehlertexte anders lauten — das ergäbe eine grob falsche Fehlerstatistik.

**Die Korrektur:** Den Roh-String **per Teilstring** in dokumentierte Buckets sortieren:

| Teilstring im Roh-Text | Bucket | Vor allem |
|------------------------|--------|-----------|
| `ReadTimeout` | Lese-Timeout | OpenAI-TTS |
| `http_503` | Server überlastet | — |
| `timeout` | allgemeiner Timeout | — |

Das Mapping wird **dokumentiert**, damit die Failure-Gruppierung nachvollziehbar bleibt.

**Ruhige Ein-Satz-Antwort:** *Fehler liegen als Roh-String vor, es gibt kein `error_kind`-Enum; weil ein naiver Gleichheitsfilter 158 von 161 Timeouts verfehlt, bucketiere ich den Roh-String per Teilstring (z. B. `ReadTimeout`, `http_503`, `timeout`) und dokumentiere das Mapping.*

## 14.4 H4 — Layer-1-Datensatz: macOS vs. EC2

**Begriffe:**
- **Layer 1** = Infrastruktur-Schicht (DNS, RTT, TLS, Traceroute).
- **RTT** (Round-Trip-Zeit) = Zeit, die ein Paket zum Server und zurück braucht.
- **Vantage Point** = der Ort, von dem aus gemessen wird.
- **Edge-Knoten** = netznaher Vorposten eines Anbieters (z. B. Cloudflare Frankfurt).

**Das Problem:** Es existieren **zwei** Layer-1-Läufe, leicht zu verwechseln:

| Lauf | Ort | RTT (Cloudflare) | Maßgeblich? |
|------|-----|------------------|-------------|
| `data/layer1/` im Repo | macOS-Dev-Rechner (Heim-Internet dazwischen) | ~17–21 ms | **Nein** |
| EC2-Lauf (`l1_rtt_per_ip.md`) | Frankfurter Cloud-Server, neben dem Edge | ~1 ms | **Ja** |

Würden versehentlich die Mac-Zahlen verwendet, wäre die Netznähe-Grundlage der gesamten Kern-Argumentation verfälscht.

**Die Korrektur (klare Regel):** Der **macOS-Dev-Lauf fließt NICHT** in die Auswertung. Maßgeblich ist **allein der EC2-Lauf** (`l1_rtt_per_ip.md`).

**Ruhige Ein-Satz-Antwort:** *`data/layer1/` im Repo ist ein macOS-Dev-Lauf und fließt nicht in die Auswertung; maßgeblich ist allein der EC2-Lauf (`l1_rtt_per_ip.md`).*

## 14.5 Zusatz (wie H3) — `ttl_ms` existiert nicht → Pro-Token-Rate korrekt rechnen

**Im selben Geist wie H3:** Die Doku behauptete etwas, das es im Code nicht gibt.

- **`ttl_ms`** (Time-to-Last-Token, Zeit bis zum letzten Token) **existiert weder in Code noch in Daten** — wurde nie erhoben.
- Die **Pro-Token-Normalisierung** (wie lange braucht das Modell im Schnitt pro ausgegebenem Token?) läuft daher **nicht über `ttl_ms`**, sondern aus vorhandenen Größen:

```
pro_token_rate = (total_ms − ttft_ms) / output_tokens
```

Das ist die reine Erzeugungsrate pro Token, **ohne** den Anlauf bis zum ersten Token (`ttft`). Auch hier: eine Doku-Behauptung an sich selbst korrigiert, statt mit einer nicht existenten Größe zu rechnen.

## 14.6 Der rote Faden

- Alle vier Auflagen + der Zusatz sind **Doku-/Reporting-Korrekturen, keine Neumessungen**. Keine Zahl war „falsch gemessen".
- Es ging stets um **Präzision**: was gemessen wurde, welche Daten maßgeblich sind, wie ausgewertet wird.
- **C1 ist von keinem Punkt bedroht** — sie steht danach fester.
- **Gesprächs-Reflex:** Zeigt der Prüfer auf eine Stelle → „Das habe ich selbst gefunden und korrigiert, und in einem Satz: warum es die Schlussfolgerung nicht kippt." **Selbstkorrektur = Vertrauens-Plus.**

## Prüf-Fragen

1. **H1:** Formuliere eine ruhige Ein-Satz-Antwort (Pilot- vs. Kampagnenzahlen).
2. **H2:** Formuliere eine ruhige Ein-Satz-Antwort (Reichweite der Eichung).
3. **H3:** Formuliere eine ruhige Ein-Satz-Antwort (Fehler-Filter, kein Enum).
4. **H4:** Formuliere eine ruhige Ein-Satz-Antwort (Layer-1-Datensatz macOS vs. EC2).
