# Modul 7 — Layer 2: Paket-Eichung

**Ziel:** Erklären, was „geeicht" konkret heißt — der App-Timer `tcp_handshake_ms` stimmt mit der echten Wire-Latenz überein — und ebenso ehrlich, was **nicht** geeicht ist (nur der Connect-Timer, H2-Reichweite).

> **Hinweis zu den Zahlen:** Die Eichwerte stammen aus je **N≈30 Cold-Starts** (2026-06-16). Alle Kampagnen-Zahlen sind A4-Mediane über **56 von 56 Slots** (Vollkampagne, abgeschlossen; success-only); die Bootstrap-Konfidenzintervalle stehen noch aus. Die Punktschätzer sind final, die Ordnung ist stabil.

## 7.1 Begriffe

Damit der Rest des Moduls trägt, zuerst die Vokabeln — jede beim ersten Auftreten definiert.

- **Eichung / Kalibrierung** — ein Messinstrument gegen eine vertrauenswürdige Referenz prüfen: dieselbe Sache mit **zwei** Methoden messen und schauen, ob beide dasselbe liefern. Stimmen sie überein, ist das Instrument geeicht und vertrauenswürdig. Hier: App-Timer (Python) gegen echte Paketmitschrift (Leitung). Motiv: Prof. Wählisch „vertraut den Daten nicht" — die Eichung beantwortet das mit Paketen.
- **tcpdump / PCAP** — `tcpdump` ist ein Programm, das **allen** Netzwerkverkehr einer Netzwerkkarte mitschneidet (jedes einzelne Paket: wann, woher, wohin, welche Flags). Die Aufzeichnung landet in einer Datei namens **PCAP** (Packet Capture). tcpdump arbeitet **unterhalb** der Anwendung, direkt am Netzwerk → es sieht die Wirklichkeit auf der Leitung, unabhängig davon, was der Code glaubt. Daher eine unabhängige Referenz.
- **SYN / SYN-ACK (TCP-Handshake)** — vor jedem Datenaustausch baut TCP eine Verbindung über ein Begrüßungsritual auf. Der Client (Mess-Instanz Frankfurt) sendet ein Paket mit Flag **`SYN`** (synchronize = „ich will verbinden"). Der Server antwortet mit **`SYN`+`ACK`** (acknowledge = „verstanden, ich auch"). Die Zeit `SYN → SYN-ACK` ist **genau 1 RTT** (Round-Trip-Zeit, einmal hin und zurück). Genau diese Größe prüfen wir: App nennt sie `tcp_handshake_ms`, die Leitung nennt sie `SYN → SYN-ACK`.
- **Kernel-Zeitstempel** — der Kernel ist die innerste OS-Schicht, die direkt mit der Netzwerkkarte spricht. Trifft ein Paket ein, vergibt der Kernel **sofort** einen sehr genauen Zeitstempel. tcpdump schreibt diese Kernel-Zeitstempel in die PCAP. Sie entstehen **ganz nah an der Leitung**, fast ohne Umweg — die App erfährt erst später vom Paket (siehe Offset, 7.4).
- **Quell-Port (source port)** — jede Verbindung bekommt vom OS einen eigenen, eindeutigen lokalen Port. Das Ziel ist immer `:443` (Standard für TLS), aber der Quell-Port ist je Cold-Start **neu und einzigartig**. Er ist der **Paarungs-Schlüssel** (siehe 7.3).
- **`perf_counter`** — die Stoppuhr im Python-Code (`time.perf_counter()`): **monoton** (kann nicht rückwärts springen, anders als die Systemuhr) und **hochauflösend** (Bruchteile einer Millisekunde), nur für Dauer-Messungen gedacht. **Wichtig:** Derselbe `perf_counter` misst auch `ttft`/`ttfa`/`ttfp` — das wird in 7.5 entscheidend.

## 7.2 Das Eich-Experiment — was gegen was verglichen wird

Auf der EC2 (Frankfurt) werden **N ≈ 30 Cold-Start-Connects** ausgeführt (jeder frisch aufgebaut und sofort geschlossen, kein Pooling — Code: `measurements/layer2/capture.py`). **Währenddessen** läuft extern `tcpdump` und schneidet den echten Verkehr in eine PCAP.

Verglichen werden **zwei Messungen derselben Sache**:

| Seite | Messung | Quelle | Was sie repräsentiert |
|-------|---------|--------|------------------------|
| **App** | `tcp_handshake_ms` | `perf_counter` im Python-Code (`capture.py` / produktiv `connect.py`) | was die **Anwendung** zu messen glaubt |
| **Wire (Leitung)** | `SYN → SYN-ACK` | Kernel-Zeitstempel in der PCAP (geparst via `tcpdump -r`, `analyze.py`) | was **wirklich** auf der Leitung passierte |

Gepaart wird über den **Quell-Port** (7.3). So entsteht je Connect ein Paar `(app_ms, wire_ms)`, und man rechnet die Differenz.

**Wahl des Anbieters (bewusst):** geeicht wird gegen einen **host-terminierten** Provider (**Azure**, **Deepgram**), **nicht** gegen einen Cloudflare-Edge-Knoten. Begründung im Code-Kommentar von `capture.py`: am Edge wäre der Vergleich **tautologisch** (`connect ≈ N×ping` am selben Knoten). Außerdem wird **eine feste Ziel-IP** (`--ip`) fixiert, damit bei Round-Robin-Hosts (Deepgram) Capture-Filter und alle 30 Connects denselben Knoten treffen.

## 7.3 Warum die Paarung über den Quell-Port funktioniert

Hinterher liegen ~30 App-Messungen und ein Haufen Pakete vor. Man muss wissen, **welches** Paket-Paar zu **welcher** App-Messung gehört. Der Quell-Port ist der gemeinsame Schlüssel:

- **`capture.py`** liest direkt nach `socket.create_connection` den Quell-Port aus (`sock.getsockname()[1]`) und schreibt ihn zusammen mit `app_tcp_handshake_ms` ins App-Log.
- In der **PCAP** tragen `SYN` und `SYN-ACK` denselben Quell-Port (im 4-Tupel `src-ip/src-port/dst-ip/dst-port`).
- **`analyze.py`** baut `{src_port: wire_handshake_ms}` und paart per Quell-Port gegen das App-Log: `pairs.append((r["app_tcp_handshake_ms"], wire[sp]))`.

Ohne den Quell-Port hätte man nur einen ununterscheidbaren Haufen Zeiten und Pakete. **Mit** ihm wird daraus eine saubere **1:1-Paarung** — Connect Nr. 1 ↔ sein `SYN→SYN-ACK`-Paar, Nr. 2 ↔ seins usw.

## 7.4 Ergebnis — ~0,1-ms-Übereinstimmung und der +Offset

Übereinstimmung auf **rund 0,1 ms** — und zwar **an beiden Enden der RTT-Skala** (Quelle: `messprotokoll.md`, Layer-2-Status, Eichung 2026-06-16, je N=30):

| Provider | RTT-Klasse | App `tcp_handshake` (Median) | Wire `SYN→SYN-ACK` (Median) | Differenz |
|----------|-----------|------------------------------|------------------------------|-----------|
| **Azure** (Italy North) | ~11 ms | 11,29 ms | 11,18 ms | **+0,11 ms** |
| **Deepgram** (US) | ~139 ms | 139,01 ms | 138,89 ms | **+0,12 ms** |

(Validiert: Azure 30/30, Deepgram 28/30; idx0-Cold-Start-Outlier ausgeschlossen.)

**Der entscheidende Punkt:** Ob der Handshake 11 ms oder 139 ms dauert (Faktor >12), die Differenz bleibt fast gleich bei ~0,1 ms. → Der **Connect-Timer ist paket-validiert** = **Contribution C2**.

**Was der `+0,1`-ms-Offset bedeutet:** Die App misst **minimal mehr** als die Leitung, weil zwischen dem **Kernel-Ereignis** (SYN-ACK trifft auf der NIC ein, Kernel setzt seinen Zeitstempel) und dem Moment, in dem die **Python-App** die Kontrolle zurückbekommt und `perf_counter` stoppt, eine winzige **Kernel-Returnzeit** liegt (`connect()` kehrt erst nach SYN-ACK + Aufwecken der App zurück). Diese Zeit misst nur die App mit, nicht der Kernel-Zeitstempel → konstantes **Pluszeichen**.

> **Klein UND konstant** über sehr unterschiedliche Handshake-Dauern (11 ms wie 139 ms) ist genau das **Zeichen einer sauberen Messung**, **kein Fehler**. Würde der Offset mit der Dauer mitwachsen, läge ein systematischer Timer-Bug vor. Tut er nicht → fester, vernachlässigbarer, erklärbarer Versatz = **Gütesiegel**. (`analyze.py` druckt entsprechend `GEEICHT` bei `abs(median(diff)) < 2`.)

## 7.5 H2-Reichweite — was NICHT geeicht ist (entscheidend, ehrlich)

Es wäre verlockend zu behaupten, jetzt seien **alle** Layer-3-Zahlen paket-validiert. Das ist **falsch** und der Prof würde es durchschauen. Diese Reichweiten-Grenze heißt im Audit **H2**.

- **Geeicht:** **nur** der Connect-Timer `tcp_handshake_ms` (SYN → SYN-ACK).
- **NICHT direkt paket-geeicht:** `ttft` (Zeit bis erstes Token), `ttfa` (Zeit bis erstes Audio), `ttfp` (Zeit bis erstes Partial).

**Warum nicht?** `ttft`/`ttfa`/`ttfp` nutzen **denselben** `perf_counter`, starten aber erst **beim Absenden des Requests** — und zwar tief im **produktiven Stack** (`httpx` für HTTPS, `websockets` für WS), **nicht** im rohen Socket-Eichpfad von `capture.py`. Die Pakete decken den **Handshake**-Teil ab, nicht den Engine-/Antwort-Teil.

**Erlaubte vs. verbotene Formulierung:**

- ❌ „Alle Layer-3-Zahlen sind paket-validiert."
- ✅ „Validiert ist der **Verbindungsaufbau-Teil**. `ttft`/`ttfa`/`ttfp` laufen über **denselben validierten Uhren-Mechanismus** wie der geeichte Connect-Timer (Vertrauens-Transfer über den geteilten Timer), sind aber **nicht** direkt paket-geeicht."

(Optionaler Ausbau in der Analyse-Phase: erstes Antwort-Paket aus der PCAP gegen `ttft` paaren. Für die Eichung selbst nicht nötig.)

## 7.6 Merksätze

1. **Geeicht =** zwei unabhängige Messungen derselben Sache stimmen überein: App-`perf_counter` ↔ Wire-Kernel-Zeitstempel, gepaart über den eindeutigen **Quell-Port**.
2. **Ergebnis:** ~0,1 ms Übereinstimmung an **beiden** Enden (11 ms wie 139 ms) → Connect-Timer paket-validiert (**C2**).
3. **+Offset** = Kernel-Returnzeit; **klein + konstant = Gütesiegel**, kein Fehler.
4. **H2-Grenze:** geeicht ist **nur** der Connect-Timer; `ttft`/`ttfa`/`ttfp` erben das Vertrauen nur über den geteilten `perf_counter`.

## Prüf-Fragen

1. Was wird gegen was verglichen?
2. Was bedeutet der +0,1-ms-Offset?
3. Welche Zahlen sind NICHT geeicht und warum?
